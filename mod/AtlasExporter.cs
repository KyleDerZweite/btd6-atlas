using System.Collections;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;
using BTD_Mod_Helper;
using BTD_Mod_Helper.Extensions;
using BTD_Mod_Helper.Api.ModOptions;
using Il2CppAssets.Scripts.Data;
using Il2CppAssets.Scripts.Data.MapSets;
using Il2CppAssets.Scripts.Models.Map;
using Il2CppAssets.Scripts.Simulation.SMath;
using Il2CppAssets.Scripts.Unity;
using Il2CppAssets.Scripts.Unity.Menu;
using Il2CppAssets.Scripts.Unity.UI_New;
using Il2CppAssets.Scripts.Unity.UI_New.InGame;
using Il2CppAssets.Scripts.Unity.UI_New.Main;
using Il2CppAssets.Scripts.Unity.UI_New.Popups;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using MelonLoader;
using MelonLoader.Utils;

[assembly: MelonInfo(
    typeof(Btd6Atlas.AtlasExporter),
    "BTD6 Atlas exporter",
    Btd6Atlas.AtlasExporter.ModVersion,
    "btd6-atlas")]
[assembly: MelonGame("Ninja Kiwi", "BloonsTD6")]

namespace Btd6Atlas;

// Reads already loaded real-match maps and writes their geometry. Never mutates
// progression, never calls the network. Manual mode exports the current map;
// auto mode walks every map through the normal game loader (takes a while).
public sealed class AtlasExporter : BloonsTD6Mod
{
    public const string ModVersion = "0.2.2";
    private const string Format = "btd6-atlas-map";
    private const string FormatVersion = "0.1";
    private static readonly TimeSpan LoadTimeout = TimeSpan.FromMinutes(2);
    private static readonly TimeSpan MenuTimeout = TimeSpan.FromMinutes(1);
    private static readonly TimeSpan InitialMenuTimeout = TimeSpan.FromMinutes(5);
    private static readonly TimeSpan ConfirmWindow = TimeSpan.FromSeconds(60);
    private static readonly HashSet<string> AllowedMelons = new(StringComparer.Ordinal)
    {
        "BloonsTD6 Mod Helper",
        "BTD6 Mod Helper",
        "BTD6 Atlas exporter",
        "Updater Plugin"
    };
    private static bool autoRunning;
    private static readonly HashSet<string> SkippedMapIds = new(StringComparer.Ordinal)
    {
        // Map-editor base template (static export flags: isBrowserOnly, not
        // IsStandard). Not loadable through the normal game loader: the load
        // enumerator wedges on the loading screen and never yields back.
        "BaseEditorMap"
    };
    private static bool autoFaulted;
    private static DateTimeOffset? autoArmedAt;

    public static readonly ModSettingButton ExportAtlasDataButton = new(ExportAtlasData)
    {
        displayName = "Export Atlas Data",
        buttonText = "Export",
        description =
            "Writes the current map's route/area/blocker geometry for an already " +
            "loaded real match. Use Mod Helper's Export Game Data button first for " +
            "the static tower/enemy/round catalog; this adds the spatial layer on top."
    };

    public static readonly ModSettingButton ExportAllMapsButton = new(ConfirmExportAllMaps)
    {
        displayName = "Export All Maps (auto)",
        buttonText = "Run",
        description =
            "Loads every map one by one through the normal game loader and exports " +
            "each. Takes a long time and drives the game automatically. Press once " +
            "to arm, press again within 60 seconds to confirm, then close Mod " +
            "settings to a clean main menu with no popups open."
    };

    private static void ExportAtlasData()
    {
        if (autoRunning)
        {
            ShowStatus("Automatic export is already running.");
            return;
        }
        try
        {
            var inGame = InGame.instance;
            var mapModel = inGame != null ? inGame.GetGameModel()?.map : null;
            if (mapModel is null)
                throw new InvalidOperationException(
                    "No real-match map is loaded. Start a solo match, pause, then export.");
            var written = WriteAtlasMap(mapModel.mapName ?? "active-map", mapModel);
            ShowStatus($"Atlas export complete: {written.FileName}");
        }
        catch (Exception exception)
        {
            ModHelper.Error<AtlasExporter>(exception);
            ShowStatus($"Export failed: {exception.GetType().Name}. Check the MelonLoader log.");
        }
    }

    private static void ConfirmExportAllMaps()
    {
        if (autoRunning)
        {
            ModHelper.Msg<AtlasExporter>("Export All Maps pressed while a run is already active.");
            ShowStatus("Automatic export is already running.");
            return;
        }
        if (autoFaulted)
        {
            ModHelper.Msg<AtlasExporter>("Export All Maps pressed after a fault; restart required.");
            ShowStatus("Automatic export stopped on a fault. Restart BTD6 before retrying.");
            return;
        }
        var now = DateTimeOffset.UtcNow;
        if (autoArmedAt is null || now - autoArmedAt > ConfirmWindow)
        {
            autoArmedAt = now;
            ModHelper.Msg<AtlasExporter>("Export All Maps armed; press again within 60 seconds to confirm.");
            ShowStatus(
                "Armed: pressing Export All Maps again within 60 seconds will load " +
                "every map automatically. This takes a long time. Do not touch the game.");
            return;
        }
        autoArmedAt = null;
        if (InGame.instance != null)
        {
            ModHelper.Msg<AtlasExporter>("Export All Maps confirmed while in a match; needs the main menu.");
            ShowStatus("Return to the main menu before running the automatic export.");
            return;
        }
        autoRunning = true;
        // Log only here: a status popup would itself block the clean main menu
        // the run is about to wait for.
        ModHelper.Msg<AtlasExporter>(
            "Automatic export starting. Close Mod settings now so the game sits on " +
            "a clean main menu with no popups open.");
        MelonCoroutines.Start(RunAllMapsSafely());
    }

    private static IEnumerator RunAllMapsSafely()
    {
        var enumerator = RunAllMaps();
        Exception fault = null;
        var done = false;
        while (!done)
        {
            object current = null;
            try
            {
                done = !enumerator.MoveNext();
            }
            catch (Exception exception)
            {
                fault = exception;
                done = true;
            }
            if (!done)
            {
                try
                {
                    current = enumerator.Current;
                }
                catch (Exception exception)
                {
                    fault = exception;
                    done = true;
                }
            }
            if (!done) yield return current;
        }
        (enumerator as IDisposable)?.Dispose();
        autoRunning = false;
        if (fault is null)
        {
            ShowStatus("Automatic export complete: every map exported.");
            ModHelper.Msg<AtlasExporter>("Automatic atlas export completed without faults.");
        }
        else
        {
            autoFaulted = true;
            ModHelper.Error<AtlasExporter>(fault);
            ShowStatus(
                $"Automatic export stopped: {fault.GetType().Name}. " +
                "Restart BTD6 before retrying; completed maps are kept.");
        }
    }

    private static IEnumerator RunAllMaps()
    {
        var catalog = GameData.Instance;
        if (catalog?.mapSet?.Maps?.items is null)
            throw new InvalidOperationException("Game data is not ready");
        var allIds = catalog.mapSet.Maps.items
            .Where(detail => detail is not null && !string.IsNullOrWhiteSpace(detail.id))
            .Select(detail => detail.id)
            .Distinct()
            .ToArray();
        var skipped = allIds.Where(id => SkippedMapIds.Contains(id)).ToArray();
        var mapIds = allIds.Where(id => !SkippedMapIds.Contains(id)).ToArray();
        ModHelper.Msg<AtlasExporter>($"Automatic atlas export: {mapIds.Length} maps queued.");
        foreach (var skippedId in skipped)
            ModHelper.Msg<AtlasExporter>($"Automatic atlas export: skipping {skippedId} (not loadable via the normal game loader).");
        // Resume: keep maps that already have an export on disk so a stopped
        // run continues where it left off. Delete Btd6AtlasExports to force a
        // full re-export.
        var exportDir = Path.Combine(MelonEnvironment.ModsDirectory, "Btd6AtlasExports");
        if (Directory.Exists(exportDir))
        {
            foreach (var mapId in mapIds)
            {
                if (ExportExists(exportDir, mapId))
                    ModHelper.Msg<AtlasExporter>($"Automatic atlas export: skipping {mapId} (already exported).");
            }
            mapIds = mapIds.Where(id => !ExportExists(exportDir, id)).ToArray();
        }
        foreach (var mapId in mapIds)
        {
            var menuDeadline = DateTimeOffset.UtcNow + InitialMenuTimeout;
            var lastMenuLog = DateTimeOffset.MinValue;
            while (!MainMenuReady())
            {
                if (DateTimeOffset.UtcNow > menuDeadline)
                    throw new TimeoutException(
                        "The main menu did not become ready: " + MenuBlocker() +
                        ". Close Mod settings to a clean main menu with no popups, then retry.");
                if (DateTimeOffset.UtcNow - lastMenuLog > TimeSpan.FromSeconds(5))
                {
                    lastMenuLog = DateTimeOffset.UtcNow;
                    ModHelper.Msg<AtlasExporter>("Waiting for clean main menu: " + MenuBlocker());
                }
                yield return null;
            }
            AssertEnvironment();
            ModHelper.Msg<AtlasExporter>($"Automatic atlas export: loading {mapId}");

            InGameData.CreateNewInstance();
            var gameData = InGameData.Editable;
            gameData.SetupNormalGame(mapId);
            gameData.selectedDifficulty = "Easy";
            gameData.selectedMode = "Sandbox";
            gameData.selectedCoopMode = false;
            gameData.selectedCouchMode = false;
            gameData.goldenBloonActive = false;
            gameData.monkeyTeamsActive = false;
            gameData.collectionEventBonusActive = false;

            var loader = UI.instance.LoadGameEnumerator();
            if (loader is null) throw new InvalidOperationException("The normal game loader was unavailable");
            var loadDeadline = DateTimeOffset.UtcNow + LoadTimeout;
            try
            {
                while (loader.MoveNext())
                {
                    if (DateTimeOffset.UtcNow > loadDeadline)
                        throw new TimeoutException($"Loading {mapId} exceeded {LoadTimeout.TotalSeconds:F0} seconds");
                    yield return loader.Current;
                }
            }
            finally
            {
                (loader as IDisposable)?.Dispose();
            }
            while (!MapReady(mapId))
            {
                var observed = InGame.instance?.GetGameModel()?.map?.mapName;
                if (!string.IsNullOrWhiteSpace(observed) && observed != mapId)
                    throw new InvalidOperationException($"Loaded map is {observed}; expected {mapId}");
                if (DateTimeOffset.UtcNow > loadDeadline)
                    throw new TimeoutException($"Map {mapId} did not become ready");
                yield return null;
            }
            var currentGame = InGameData.CurrentGame;
            if (currentGame == null ||
                currentGame.selectedDifficulty != "Easy" ||
                currentGame.selectedMode != "Sandbox" ||
                !currentGame.IsSandbox)
                throw new InvalidOperationException($"Loaded {mapId} outside Easy Sandbox configuration");
            yield return null;

            AssertEnvironment();
            // The Sandbox intro dialog ("Dr. Monkey's Bloon simulator is ready")
            // appears after every map load. It is info-only, so hide it on
            // first sight instead of waiting. Hiding invokes no dialog
            // buttons, so it cannot claim rewards or advance flows. The
            // pre-run main menu gate stays strict and is never auto-dismissed.
            for (var attempt = 1;
                 attempt <= 3 &&
                 (PopupScreen.instance == null || PopupScreen.instance.IsPopupActiveOrLoading());
                 attempt++)
            {
                ModHelper.Msg<AtlasExporter>(
                    $"Automatic atlas export: hiding blocking dialog after loading {mapId} (attempt {attempt}/3).");
                PopupScreen.instance?.HideAllPopups();
                var attemptDeadline = DateTimeOffset.UtcNow + TimeSpan.FromSeconds(2);
                while (PopupScreen.instance != null &&
                       PopupScreen.instance.IsPopupActiveOrLoading() &&
                       DateTimeOffset.UtcNow <= attemptDeadline)
                    yield return null;
            }
            if (PopupScreen.instance == null || PopupScreen.instance.IsPopupActiveOrLoading())
                throw new InvalidOperationException(
                    $"A dialog is still active after loading {mapId} and 3 hide attempts; it was not clicked automatically");
            var written = WriteAtlasMap(mapId, InGame.instance.GetGameModel().map, mapId);
            ModHelper.Msg<AtlasExporter>($"Automatic atlas export: {mapId} -> {written.FileName}");

            var inGame = InGame.instance;
            if (inGame == null)
                throw new InvalidOperationException("The loaded game disappeared before returning to the menu");
            var returnToMenu = inGame.ReturnToMainMenu();
            if (returnToMenu is null)
                throw new InvalidOperationException("The normal return-to-menu flow was unavailable");
            var returnDeadline = DateTimeOffset.UtcNow + MenuTimeout;
            try
            {
                while (returnToMenu.MoveNext())
                {
                    if (DateTimeOffset.UtcNow > returnDeadline)
                        throw new TimeoutException($"Returning from {mapId} exceeded {MenuTimeout.TotalSeconds:F0} seconds");
                    yield return returnToMenu.Current;
                }
            }
            finally
            {
                (returnToMenu as IDisposable)?.Dispose();
            }
            while (!MainMenuReady())
            {
                if (DateTimeOffset.UtcNow > returnDeadline)
                    throw new TimeoutException(
                        $"Main menu did not recover after {mapId}: " + MenuBlocker());
                yield return null;
            }
        }
    }

    private static bool ExportExists(string exportDir, string mapId)
    {
        var prefix = "atlas-" + SafeFile(mapId) + "-";
        foreach (var file in Directory.GetFiles(exportDir, prefix + "*.json"))
        {
            if (Path.GetFileName(file).StartsWith(prefix, StringComparison.Ordinal))
                return true;
        }
        return false;
    }

    private sealed record WrittenAtlas(string FileName, string Sha256);
    private static WrittenAtlas WriteAtlasMap(string mapId, MapModel mapModel, string expectedMapId = null)
    {
        if (expectedMapId is not null && mapModel?.mapName != expectedMapId)
            throw new InvalidOperationException(
                $"Active map is {mapModel?.mapName ?? "none"}; expected {expectedMapId}");
        var unsupported = new List<string>();
        var map = ProjectMap(mapId, mapModel, unsupported);
        var envelope = new AtlasEnvelope(
            Format,
            FormatVersion,
            ModVersion,
            DateTimeOffset.UtcNow.ToString("O"),
            mapId,
            map,
            unsupported.ToArray());
        var bytes = JsonSerializer.SerializeToUtf8Bytes(envelope, AtlasJson.Options);
        var directory = Path.Combine(MelonEnvironment.ModsDirectory, "Btd6AtlasExports");
        Directory.CreateDirectory(directory);
        var fileName = $"atlas-{SafeFile(mapId)}-{DateTimeOffset.UtcNow:yyyyMMddTHHmmssZ}.json";
        var path = Path.Combine(directory, fileName);
        var tempPath = path + ".tmp";
        File.WriteAllBytes(tempPath, bytes);
        File.Move(tempPath, path);
        var persisted = File.ReadAllBytes(path);
        var hash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        if (persisted.Length != bytes.Length ||
            Convert.ToHexString(SHA256.HashData(persisted)).ToLowerInvariant() != hash)
            throw new IOException($"Export verification failed for {fileName}");
        ModHelper.Msg<AtlasExporter>($"Atlas export complete: {path} (sha256 {hash})");
        return new WrittenAtlas(fileName, hash);
    }

    private static void AssertEnvironment()
    {
        var loaded = MelonBase.RegisteredMelons
            .Select(melon => melon.Info.Name)
            .Where(name => !string.IsNullOrWhiteSpace(name))
            .Distinct(StringComparer.Ordinal)
            .ToArray();
        var unexpected = loaded.Where(name => !AllowedMelons.Contains(name)).ToArray();
        if (unexpected.Length > 0)
            throw new InvalidOperationException($"Unexpected loaded mod: {unexpected[0]}");
    }

    private static bool MainMenuReady()
    {
        var inGame = InGame.instance;
        var ui = UI.instance;
        var menu = MenuManager.instance;
        var popup = PopupScreen.instance;
        var currentMenu = menu != null ? menu.GetCurrentMenu() : null;
        return inGame == null &&
               ui != null &&
               !ui.isLoadingGame &&
               menu != null &&
               currentMenu != null &&
               currentMenu.Is<MainMenu>() &&
               popup != null &&
               !popup.IsPopupActiveOrLoading();
    }

    private static string MenuBlocker()
    {
        if (InGame.instance != null) return "still in a match (InGame active)";
        var ui = UI.instance;
        if (ui == null) return "UI instance missing";
        if (ui.isLoadingGame) return "game loader busy";
        var menu = MenuManager.instance;
        if (menu == null) return "menu manager missing";
        var currentMenu = menu.GetCurrentMenu();
        if (currentMenu == null) return "no current menu";
        if (!currentMenu.Is<MainMenu>())
            return "current menu is " + currentMenu.GetType().Name + ", not MainMenu (close Mod settings)";
        var popup = PopupScreen.instance;
        if (popup == null) return "popup manager missing";
        if (popup.IsPopupActiveOrLoading()) return "a popup is open or loading (dismiss it)";
        return "unknown";
    }

    private static bool MapReady(string mapId)
    {
        var inGame = InGame.instance;
        var ui = UI.instance;
        return inGame != null &&
               inGame.initialised &&
               ui != null &&
               !ui.isLoadingGame &&
               inGame.GetGameModel()?.map?.mapName == mapId;
    }

    private static void ShowStatus(string message)
    {
        if (PopupScreen.instance != null)
            PopupScreen.instance.SafelyQueue(screen => screen.ShowOkPopup(message));
    }

    private static AtlasMapDto ProjectMap(string mapId, MapModel model, List<string> unsupported)
    {
        var boundsPoints = new List<PointDto>();
        var routes = new List<RouteDto>();
        var entrances = new List<AnchorDto>();
        var exits = new List<AnchorDto>();
        var areas = new List<AreaDto>();
        var blockers = new List<BlockerDto>();

        for (var index = 0; index < (model.paths?.Length ?? 0); index++)
        {
            var path = model.paths[index];
            if (path is null) continue;
            var routeId = SafeId(path.pathId, $"route-{index}");
            var points = new List<PointDto>();
            for (var i = 0; i < (path.points?.Length ?? 0); i++)
            {
                var dto = Point(path.points[i].point);
                points.Add(dto);
                boundsPoints.Add(dto);
            }
            // BTD6 uses (-1000,-1000) as the unset spawn/leak sentinel: never let
            // it expand the bounds or leak into anchors.
            if (UsableEndpoint(path.spawnPoint)) boundsPoints.Add(Point(path.spawnPoint));
            if (UsableEndpoint(path.leakPoint)) boundsPoints.Add(Point(path.leakPoint));
            var entranceId = path.entryModel is null ? "entrance-" + routeId : "splitter-entry-" + routeId;
            var exitId = path.exitModel is null ? "exit-" + routeId : "splitter-exit-" + routeId;
            if (path.entryModel is not null || path.exitModel is not null)
                unsupported.Add("Splitter junction topology retained as route metadata only.");
            routes.Add(new RouteDto(routeId, points.ToArray(), entranceId, exitId));
            if (path.entryModel is null && points.Count > 0)
                entrances.Add(new AnchorDto(entranceId, points[0], new[] { routeId }));
            if (path.exitModel is null && points.Count > 0)
                exits.Add(new AnchorDto(exitId, points[^1], new[] { routeId }));
        }

        for (var index = 0; index < (model.areas?.Length ?? 0); index++)
        {
            var area = model.areas[index];
            if (area is null) continue;
            var rings = Rings(area.polygon, area.holes);
            foreach (var ring in rings) boundsPoints.AddRange(ring.Points);
            var id = SafeId(area.id.ToString(), $"area-{index}");
            areas.Add(new AreaDto(id, AreaKind(area.type), rings));
            if (area.isBlocker) blockers.Add(new BlockerDto("area-blocker-" + id, "both", rings));
        }

        for (var index = 0; index < (model.blockers?.Length ?? 0); index++)
        {
            var blocker = model.blockers[index];
            if (blocker?.circle is null) continue;
            var ring = CircleRing(blocker.circle, 24);
            boundsPoints.AddRange(ring.Points);
            blockers.Add(new BlockerDto($"circle-blocker-{index}", "both", new[] { ring }));
            unsupported.Add("BlockerModel.circle approximated as a 24-point polygon.");
        }

        if ((model.mapEvents?.Length ?? 0) > 0)
            unsupported.Add("Map events inventoried, not projected; Unity-only actions unsupported.");
        if ((model.coopAreaLayouts?.Length ?? 0) > 0)
            unsupported.Add("Co-op area layouts not projected in this version.");

        return new AtlasMapDto(
            mapId,
            routes.ToArray(),
            entrances.ToArray(),
            exits.ToArray(),
            areas.ToArray(),
            blockers.ToArray(),
            Bounds(boundsPoints));
    }

    private static RingDto[] Rings(Polygon polygon, Il2CppReferenceArray<Polygon> holes)
    {
        var rings = new List<RingDto>();
        AddRing(rings, polygon);
        for (var index = 0; index < (holes?.Length ?? 0); index++) AddRing(rings, holes![index]);
        return rings.ToArray();
    }

    private static void AddRing(ICollection<RingDto> rings, Polygon polygon)
    {
        if (polygon?.points is null || polygon.points.Length < 3) return;
        rings.Add(new RingDto(polygon.points.ToArray().Select(Point).ToArray()));
    }

    private static RingDto CircleRing(Circle circle, int segments)
    {
        var points = new PointDto[segments];
        for (var index = 0; index < segments; index++)
        {
            var angle = 2 * System.Math.PI * index / segments;
            points[index] = new PointDto(
                circle.position.x + circle.radius * (float)System.Math.Cos(angle),
                circle.position.y + circle.radius * (float)System.Math.Sin(angle));
        }
        return new RingDto(points);
    }

    private static PointDto Point(Vector2 point) => new(point.x, point.y);
    private static PointDto Point(Vector3 point) => new(point.x, point.y);

    private static bool UsableEndpoint(Vector3 point) =>
        float.IsFinite(point.x) &&
        float.IsFinite(point.y) &&
        !(MathF.Abs(point.x + 1000f) < 0.01f &&
          MathF.Abs(point.y + 1000f) < 0.01f);

    private static string AreaKind(AreaType type) => type switch
    {
        AreaType.land => "land",
        AreaType.water or AreaType.waterMermonkey or AreaType.shallowWater => "water",
        AreaType.track => "track",
        AreaType.unplaceable => "unplaceable",
        _ => "other"
    };

    private static BoundsDto Bounds(List<PointDto> points)
    {
        if (points.Count == 0)
            return new BoundsDto(new PointDto(0, 0), new PointDto(0, 0));
        return new BoundsDto(
            new PointDto(points.Min(point => point.X), points.Min(point => point.Y)),
            new PointDto(points.Max(point => point.X), points.Max(point => point.Y)));
    }

    private static string SafeId(string value, string fallback)
    {
        var safe = Regex.Replace(value ?? string.Empty, "[^A-Za-z0-9._-]", "_").TrimStart('_');
        return string.IsNullOrEmpty(safe) ? fallback : safe[..System.Math.Min(128, safe.Length)];
    }

    private static string SafeFile(string value) => SafeId(value, "active-map");
}
