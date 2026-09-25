using System.Text.Json;
using System.Text.Json.Serialization;

namespace Btd6Atlas;

// Slim map-geometry DTOs. Field names mirror the retired reference exporter so
// accepted captures stay comparable; anything not captured is simply absent.

internal sealed record AtlasEnvelope(
    string Format,
    string FormatVersion,
    string ExporterVersion,
    string ExportedAtUtc,
    string MapId,
    AtlasMapDto Map,
    string[] Unsupported);

internal sealed record AtlasMapDto(
    string Id,
    RouteDto[] Routes,
    AnchorDto[] Entrances,
    AnchorDto[] Exits,
    AreaDto[] Areas,
    BlockerDto[] Blockers,
    BoundsDto Bounds);

internal sealed record PointDto(float X, float Y);

internal sealed record BoundsDto(PointDto Min, PointDto Max);

internal sealed record RingDto(PointDto[] Points);

internal sealed record AnchorDto(string Id, PointDto Point, string[] RouteIds);

internal sealed record RouteDto(
    string Id,
    PointDto[] Points,
    string EntranceId,
    string ExitId);

internal sealed record AreaDto(string Id, string Kind, RingDto[] Rings);

internal sealed record BlockerDto(string Id, string Kind, RingDto[] Rings);

internal static class AtlasJson
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        WriteIndented = true
    };
}
