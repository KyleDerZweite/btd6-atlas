#!/usr/bin/env python3
"""Export complete gameplay Tower records from a committed Atlas capture.

Run with no arguments to process every family, or --tower DartMonkey to inspect
one family. Uses Python 3.10+, Git, and the standard library. No network access.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/KyleDerZweite/btd6-atlas"
SETS = {1: "primary", 2: "military", 4: "magic", 8: "support"}
# Confirmed against the installed 56.3 Assembly-CSharp.dll, not inferred masks.
IMMUNITIES = {1: "lead", 2: "black", 4: "white", 8: "purple", 16: "frozen",
              32: "immune", 64: "glass"}
AREAS = {0: "track", 1: "water", 2: "land", 3: "unplaceable", 4: "ice",
         5: "removable", 6: "waterMermonkey", 7: "shallowWater"}
LEGAL_TIERS = {
    tiers for tiers in itertools.product(range(6), repeat=3)
    if sum(tier > 0 for tier in tiers) <= 2
    and sum(tier > 2 for tier in tiers) <= 1
}

# Explicit types only. A behavior containing "Effect" can still affect gameplay.
PRESENTATION = set("""
SoundModel EffectModel AssetPathModel DisplayModel AudioClipReference
PrefabReference SpriteReference PlayAnimationIndexModel ShowTextOnHitModel
CreateSoundOnAttachedModel CreateSoundOnSellModel CreateSoundOnTowerPlaceModel
CreateSoundOnUpgradeModel CreateSoundOnAbilityModel CreateRandomSoundOnAbilityModel
CreateSoundOnPickupModel CreateSoundOnProjectileCollisionModel
CreateSoundOnProjectileCreatedModel CreateSoundOnProjectileExhaustModel
CreateSoundOnProjectileExpireModel CreateEffectAfterTimeModel CreateEffectOnPlaceModel
CreateEffectOnSellModel CreateEffectOnUpgradeModel CreateEffectOnAbilityModel
CreateEffectOnAbilityEndModel CreateEffectOnContactModel CreateEffectOnExpireModel
CreateEffectOnExhaustedModel CreateEffectOnExhaustFractionModel CreateEffectOnPopModel
CreateEffectFromCollisionToCollisionModel CreateEffectOnParentOnAttackModel
CreateEffectWhileAttackingModel CreateEffectProjectileAfterTimeModel
CreateLightningEffectModel CreateRopeEffectModel CreateTextEffectModel
IncreaseWorthTextEffectModel EjectEffectModel EjectEffectWithOffsetsModel
AlternateAnimationModel CycleAnimationModel EjectAnimationModel
RateBasedAnimationOffsetModel WeaponRateAnimationSpeedModel
LinkDisplayScaleToTowerRangeModel SetSpriteFromPierceModel ShowCashIconInsteadModel
SwitchDisplayModel
AnimateAirUnitOnFireModel AnimateOnBeastHandlerModel BeastHandlerPetDisplayStepModel
GreatWhiteDisplayStepModel DrawSubtowerRangeCircleModel BuffIconPerTowerInRangeModel
CreateEffectOnAirUnitDestroyModel CreateEffectOnAirUnitModel LineEffectModel PointLineEffectModel
""".split())

# Direct projections of the captured mechanisms inspected for the first pass.
# ponytail: skip unhandled mechanics; add a projection when a captured Tower needs it.
SUPPORTED = set("""
TowerModel AttackModel WeaponModel ProjectileModel AbilityModel ApplyModModel
CircleFootprintModel RectangleFootprintModel TargetType SingleEmissionModel
ArcEmissionModel SingleEmmisionTowardsTargetModel InstantDamageEmissionModel
AttackFilterModel ProjectileFilterModel FilterInvisibleModel FilterAllModel
FilterAllExceptTargetModel FilterWithTagModel FilterWithTagsModel FilterOutTagModel
FilterMoabModel FilterBloonIfDamageTypeModel FilterInBaseTowerIdModel
TargetFirstModel TargetLastModel TargetCloseModel TargetStrongModel TargetMoabModel
TargetFirstPrioCamoModel TargetLastPrioCamoModel TargetClosePrioCamoModel
TargetStrongPrioCamoModel TargetEliteTargettingModel TargetTrackModel
TargetSelectedPointModel RandomPositionBasicModel RandomTargetSpreadModel
RotateToTargetModel CheckTargetsWithoutOffsetsModel SwitchTargetSupplierOnUpgradeModel
TargetSupplierSupportModel DamageModel TravelStraitModel CritMultiplierModel
DamageModifierForTagModel KnockbackModel MonkeyFanClubModel
ProjectileBlockerCollisionReboundModel MapBorderReboundModel
ExpireProjectileAtScreenEdgeModel CreateProjectileOnExhaustFractionModel
CreateProjectileOnContactModel ActivateAttackModel AddBehaviorToBloonModel
DamageOverTimeModel AgeModel LinkProjectileRadiusToTowerRangeModel SpinModel
TrackTargetModel RandomRangeTravelStraitModel PushBackModel SlowModel
SlowModifierForTagModel AbilityDamageAllModel AlternateProjectileModel
ActivateAbilitiesOnAbilityModel CashModel EmitOnDamageModel InstantModel
LeakDangerAttackSpeedModel OffsetModel PickupModel RateSupportModel
RetargetOnContactModel SlowMaimMoabModel TurboModel WeaponRateMinModel
Curve Vector3 ArriveAtTargetModel ScaleProjectileModel HeightOffsetProjectileModel
EmissionsPerRoundFilterModel BananaCentralBuffModel BankModel BonusLivesPerRoundModel
CentralMarketBuffModel CollectCashZoneModel ImfLoanCollectionModel ImfLoanModel
PerRoundCashBonusTowerModel SendToBankModel
RandomEmissionModel EmissionWithOffsetsModel ThrowMarkerOffsetModel
EmissionRotationOffTowerDirectionModel EmissionRotationOffProjectileDirectionModel
FilterGlueLevelModel FilterOveridingMutatedTargetModel FilterMutatedTargetModel
SlowOnPopModel SlowForBloonModel RangeSupportModel EndOfRoundClearBypassModel
SyncTargetPriorityWithSubTowersModel PlacementAreaTypeRangeBuffModel
BurstWeaponBehaviorModel TowerRadiusModel
AbilityCooldownScaleSupportModel AbilityCreateTowerModel AccelerateModel
AcidPoolEmissionModel AcidPoolModel AcidicMixtureCheckModel AcidicMixtureModel
ActivateAbilityAfterIntervalModel ActivateDamageBypassSupportZoneModel
ActivateDamageModifierSupportZoneModel ActivateLightningRodZapModel
ActivateProjectileSpeedSupportZoneModel ActivateRangeSupportZoneModel
ActivateRateSupportZoneModel ActivateRicochetSupportZoneModel
AddAcidicMixtureToProjectileModel AddAttackTowerMutatorModel
AddBehaviorModifierForTagModel AddBehaviorToBloonInZoneModel
AddBehaviorToTowerMutatorModel AddBehaviorToTowerSupportModel
AddBerserkerBrewToProjectileModel AddBonusDamagePerHitToBloonModel AddHeatToBloonModel
AddMakeshiftAreaModel AddTagToBloonModel AdoraTrackTargetModel AgeRandomModel
AgeingDestroyModel AirUnitModel AngleToMapCenterModel AttackAirUnitModel
AttackMinimumRangeModel AutoTargetTrackModel BeastHandlerLeashModel BeastHandlerPetModel
BeastHandlerUpgradeLockModel BerserkerBrewCheckModel BerserkerBrewModel
BloonDistanceRateBonusModel BloonTagDamageOverrideModel BonusCashZoneModel
BonusLivesOnAbilityModel BountyHunterZoneModel BrewTargettingModel
BurstWeaponIncreasingArcBehaviorModel CallToArmsModel CamoBlockZoneModel
CanBuffIndicatorModel CantBeReflectedModel CarryProjectileModel CashIncreaseModel
CashPerTowerInRangeModel CashbackZoneModel CenterElipsePatternModel
CheckAirUnitOverTrackModel CheckTempleCanFireModel CheckTempleUnderLevelModel ChilledModel
ChipMapBasedObjectModel CirclePatternModel ClearHitBloonsModel CloseTargetTrackModel
CollectCreatedProjectileModel CollideExtraPierceReductionModel CollideOnlyWithTargetModel
CollideReducePierceForBloonStateModel ComancheDefenceModel
CreateDistanceProjectileOnExhaustFractionModel CreateGreatWhiteEffectModel
CreateNearbyWaterModel CreateProjectileOnBlockerCollideModel
CreateProjectileOnExhaustPierceModel CreateProjectileOnExpireModel
CreateProjectileOnIntervalModel CreateProjectileOnTowerDestroyModel CreateTowerModel
CreateTypedTowerCurrentIndexModel CreateTypedTowerModel CreditPopsToParentTowerModel
CritRollWithDistanceModel DamageBasedAttackSpeedModel DamageImmunityBypassModel
DamageInRingRadiusModel DamageModifierForBloonStateAndTypeModel
DamageModifierForBloonStateModel DamageModifierForBloonTypeModel
DamageModifierForCashAmountModel DamageModifierSupportModel
DamageModifierUnstableConcoctionModel DamageModifierWrathModel DamageOverTimeCustomModel
DamageOverTimeZoneModel DamagePercentOfMaxModel DamageSupportModel DamageTowerMutatorModel
DamageTypeSupportModel DamageUpModel DarkshiftModel DartlingMaintainLastPosModel
DesperadoMarkModel DestroyIfTargetLostModel DestroyProjectileIfTowerDestroyedModel
DiscountZoneModel DistributeToChildrenBloonModifierModel DontDestroyOnContinueModel
DruidVengeanceEffectModel EatBloonModel EmissionArcRotationOffDisplayDirectionModel
EmissionArcRotationOffTowerDirectionModel EmissionAtClosestPathSegmentModel
EmissionCamoIfTargetIsCamoModel EmissionOverTimeModel
EmissionRotationOffBloonDirectionModel EmissionRotationOffDisplayModel
EmissionRotationOffDisplayOnEmitModel EmitOnDamageWithStateModel EmitOnDestroyModel
EmitOnPopModel ExpireProjectileOnBossSpawnedModel FadeProjectileModel FallToGroundModel
FighterMovementModel FighterPilotPatternCloseModel FighterPilotPatternFirstModel
FighterPilotPatternLastModel FighterPilotPatternStrongModel FigureEightPatternModel
FilterBadImmunityModel FilterFrozenBloonsModel FilterIfAttackHasTargetModel
FilterInSetModel FilterInTowerTiersModel FilterInvisibleSubIntelModel
FilterMarkedToPopModel FilterOfftrackModel FilterOnlyCamoInModel FilterOutBloonModel
FilterOutOffscreenModel FilterTargetAngleFilterModel FilterTargetAngleModel
FilterTowerParentModel FindDeploymentLocationModel FireAlternateWeaponModel
FireFromAirUnitModel FireWhenAlternateWeaponIsReadyModel FlagshipAttackSpeedIncreaseModel
FlipFollowPathModel FollowPathModel FollowTouchSettingModel FreeUpgradeSupportModel
FreezeModel FreezeModifierForTagsModel FreezeNearbyWaterModel FrozenRemainsExplosionModel
GalvanizedModel GrappleEmissionModel GreatWhiteLimitProjectileModel
GroundZeroBombBuffModel GrowBlockModel GyrfalconPatternModel HeliMovementModel
IgnoreInsufficientPierceModel IgnoreThrowMarkerModel IgnoreTowersBlockerModel
ImmunityModel IncreaseBloonWorthModel IncreaseRangeModel JungleVineEffectModel
JungleVineLimitProjectileModel KeepInBoundsModel KeepTowerZAtTerrainHeightModel
LatchToBloonModel LifeBasedAttackSpeedModel LightningModel LightningRodEmitModel
LightningRodManagerModel LightningRodModel LimitProjectileModel
LineProjectileEmissionModel LinearTravelModel LivesModel LoadAlchemistBrewInfoModel
LockInPlaceSettingModel MarkedToPopModel MarkedToPopProjectileBehaviorModel
MerchantShipModel MoabShoveZoneModel MoabTakedownModel MonkeyCityIncomeSupportModel
MonkeyCityModel MonkeyTempleModel MonkeyopolisModel MonkeyopolisUpgradeCostModel
MorphBloonModel MorphTowerModel MultiEmissionModel MultiInstantEmissionModel
MutateRemoveAllAttacksOnAbilityActivateModel NecroEmissionFilterModel
NecromancerEmissionModel NecromancerTargetTrackWithinRangeModel NecromancerZoneModel
OrbitModel OverclockModel OverclockPermanentModel OverrideCamoDetectionModel
ParallelEmissionModel PathMovementFromScreenCenterModel
PathMovementFromScreenCenterPatternModel PathMovementModel PatrolPointsSettingModel
PauseOtherAttacksModel PierceFromLivesGainedModel PiercePercentageSupportModel
PierceSupportModel PierceTowerMutatorModel PoplustSupportModel
PreEmptiveStrikeLauncherModel PrinceOfDarknessEmissionModel
PrinceOfDarknessZombieBuffModel PrioritiseRotationModel ProjectileOverTimeModel
ProjectileSizeTowerMutatorModel ProjectileSpeedSupportModel
ProjectileSpeedTowerMutatorModel ProjectileZeroRotationModel PursuitSettingModel
RandomAngleOffsetModel RandomArcEmissionModel RandomPositionModel
RandomRotationWeaponBehaviorModel RangeTowerMutatorModel RedeployModel RefreshPierceModel
ReloadTimeTowerMutatorModel RemoveBloonModifiersModel RemoveDamageTypeModifierModel
RemoveMutatorOnUpgradeModel RemoveMutatorsFromBloonModel RemovePermaBrewModel
ResetRateOnInitialiseModel RotateModel RotateToDefaultPositionTowerModel
RotateToMiddleOfTargetsModel RotateToParentModel RotateToPointerModel
RotateToTargetAirUnitModel RotateToTargetAttackOffsetModel SavedSubTowerModel
ScaleDamageWithTimeModel ScaleProjectileOverTimeModel SelectParentOnSelectedModel
SetTriggerOnAirUnitFireModel SlowBloonsZoneModel SlowMinusAbilityDurationModel
SmartTargetTrackModel SpiritOfTheForestModel StandoffModel StartOfRoundRateBuffModel
StatePoppedBasedPierceModel SubCommanderSupportModel SubTowerFilterModel
SubmergeEffectModel SubmergeModel SubmergedTargetModel SupportRemoveFilterOutTagModel
SupportShinobiTacticsModel SupportStackingRangeModel TakeAimModel TargetCloseAirUnitModel
TargetCloseSharedRangeModel TargetDesperadoCloseModel TargetDesperadoFirstModel
TargetDesperadoLastModel TargetDesperadoStrongModel TargetFirstAirUnitModel
TargetFirstSharedRangeModel TargetFriendlyModel TargetGrapplableModel
TargetInFrontOfAirUnitModel TargetIndependantModel TargetLastAirUnitModel
TargetLastSharedRangeModel TargetLeftHandModel TargetPointerModel TargetRightHandModel
TargetSelectedPointOrDefaultModel TargetStrongAirUnitModel TargetStrongSharedRangeModel
TargetTrackOrDefaultAcidPoolModel TargetTrackOrDefaultModel
TempleTowerMutatorGroupTierOneModel TempleTowerMutatorGroupTierTwoModel TheBlazingSunModel
ToggleFocusStanceModel TowerCreateTowerModel TowerExpireModel
TowerExpireOnParentDestroyedModel TowerExpireOnParentUpgradedModel
TowerRangeDamageBuffModel TrackTargetWithinTimeModel TradeEmpireBuffModel TranceBloonModel
TranceTotemSpawnerModel TravelAlongPathModel TravelCurvyModel TravelStraitSlowdownModel
TravelTowardsEmitTowerModel UnstableConcoctionSplashModel UseAttackRotationModel
UseParentEjectModel UsePresetTargetModel UseTowerRangeModel VagrantWeaponBehaviorModel
VigilanteTowerBehaviorModel VisibilitySupportModel WindChanceTowerMutatorModel WindModel
WindlashModel WintersMercyTowerBuffModel ZephyrSenseToggleModel ZeroRotationModel
ZeroRotationOnAbilityModel UpgradePathModel
""".split())
KINDS = {
    "TravelStraitModel": "travelStraight",
    "SingleEmmisionTowardsTargetModel": "emitTowardTarget",
    "CritMultiplierModel": "criticalHit",
    "MonkeyFanClubModel": "fanClubTransformation",
    "CreateProjectileOnExhaustFractionModel": "spawnAtExhaustionThresholds",
    "CreateProjectileOnContactModel": "spawnOnContact",
    "ProjectileBlockerCollisionReboundModel": "reboundFromBlockers",
    "MapBorderReboundModel": "reboundFromMapBorder",
    "ExpireProjectileAtScreenEdgeModel": "expireAtScreenEdge",
    "FilterInvisibleModel": "excludeCamo",
    "ApplyModModel": "externalModifier",
    "AgeModel": "expireAfterDuration",
}
FIELD_NAMES = {
    "lifespan": "durationSeconds",
    "Lifespan": "durationSeconds", "speed": "speedUnitsPerSecond",
    "Speed": "speedUnitsPerSecond", "cooldown": "cooldownSeconds",
    "interval": "intervalSeconds", "delay": "delaySeconds",
    "initialDelay": "initialDelaySeconds", "customStartCooldown": "initialCooldownSeconds",
    "animationOffset": "animationOffsetSeconds", "radius": "radius",
    "damageAddative": "bonusDamage", "damageMultiplier": "damageMultiplier",
    "collisionPass": "processingPhase", "collisionPasses": "processingPhases",
    "CappedDamage": "effectiveDamage", "CappedPierce": "effectivePierce",
    "maxDamage": "damageCap", "maxPierce": "pierceCap",
    "displayName": "name", "mod": "reference", "mutatorId": "modifierId",
    "mutationId": "modifierId", "ignoreWithMutatorsList": "excludedModifierIds",
    "behaviors": "effects",
}
TYPE_FIELDS = {
    "CritMultiplierModel": {"damage": "criticalDamage", "lower": "minShotInterval",
                            "upper": "maxShotInterval"},
    "MonkeyFanClubModel": {"towerCount": "maxTargets", "maxTier": "targetTierLimit",
                           "reloadModifier": "attackIntervalMultiplier"},
    "CreateProjectileOnExhaustFractionModel": {
        "fraction": "pierceExhaustionFraction", "durationfraction": "durationFraction"},
    "TargetType": {"id": "priority"},
    "DamageModel": {"damage": "amount"},
    "AlternateProjectileModel": {"interval": "shotInterval"},
    "WeaponModel": {"rate": "intervalSeconds", "rateFrames": "intervalFrames",
                    "modelName": "id"},
    "AbilityModel": {"modelName": "id"},
    "UpgradePathModel": {"tower": "towerId", "upgrade": "upgradeId"},
    "SingleEmissionModel": {},
}
OMIT_FIELDS = {
    "TowerModel": set("""
        towerTheme icon icon3D portrait instaIcon emoteSpriteSmall emoteSpriteLarge
        secondarySelectionMenu display animationSpeed displayScale DisplayScale
        towerSelectionMenuThemeId ignoreTowerForSelection dontDisplayUpgrades hideInfoButton
        bonusSelectionRadius showPowerTowerBuffs showBuffs loadedFromSave isBakable
        cachedThrowMarkerHeight RadiusSquared paragonUpgrade isParagon IsBaseTower
        tier powerName geraldoItemName skinName _powerProTowerModel
        powerProTowerModel frontierId isStunned isPrimedForRedeploy
    """.split()),
    "AttackModel": {"drawRangeCircle", "addsToSharedGrid"},
    "WeaponModel": {"animation", "animateOnMainAttack", "isStunned"},
    "ProjectileModel": {"display", "displayModel", "saveId", "hasDamageModifiers"},
    "DamageModel": {"createPopEffect", "immuneBloonPropertiesOriginal"},
    "DamageOverTimeModel": {"immuneBloonPropertiesOriginal", "displayLifetime",
                            "displayPath", "rotateEffectWithBloon"},
    "AbilityModel": set("""
        description icon animation dontShowStacked animateOnMainAttackDisplay
        hideAbilityIfInCooldown alwaysSetAnimationState isHidden
    """.split()),
    "RateSupportModel": {"buffLocsName", "buffIconName", "showBuffIcon",
                         "onlyShowBuffIfMutated"},
    "BananaCentralBuffModel": {"buffLocsName", "buffIconName"},
    "CentralMarketBuffModel": {"buffLocsName", "buffIconName"},
    "BankModel": {"collectAnimation"},
    "CollectCashZoneModel": {"animateTower"},
    "AlternateProjectileModel": {"alternateAnimation"},
    "LinkProjectileRadiusToTowerRangeModel": {"displayRadius"},
    "TargetType": {"intID"},
}
PRESENTATION_FIELDS = {
    "buffLocsName", "buffIconName", "buffLocsFullName", "showBuffIcon",
    "onlyShowBuffIfMutated", "displayScale", "displayFullscreen",
    "animationState", "animationStateOpen", "animationStateClosed",
    "animationStateOnSetTarget", "animationStateOnTowerOnDestroy",
    "animationStateSecond", "animationIndexDuringMorphDelay",
}
FAMILY_MARKERS = set("""
baseId isSubTower isSubEntity isPowerTower isPowerProTower isGeraldoItem
isBeastHandlerPet selectParentOnSelected beastHandlerLeashMutationId towerSize
""".split())
OMIT = object()


def git(*args, binary=False):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode().strip())
    return result.stdout if binary else result.stdout.decode()


def model_type(model):
    return model.get("$type", "").split("[", 1)[0].split(",", 1)[0].rsplit(".", 1)[-1]


def code(tiers):
    return "".join(map(str, tiers))


def project(value, location, referenced_ids=frozenset()):
    """Translate supported captured mechanisms without guessing missing values."""
    if isinstance(value, list):
        return [item for index, raw in enumerate(value)
                if (item := project(raw, f"{location}/{index}", referenced_ids)) is not OMIT]
    if not isinstance(value, dict):
        return value
    kind = model_type(value)
    if not kind or value.get("$type", "").startswith("Il2CppSystem.Collections.Generic.Dictionary`2["):
        return {field: item for field, raw in value.items() if field != "$type"
                and (item := project(raw, f"{location}/{field}", referenced_ids)) is not OMIT}
    if kind in PRESENTATION:
        return OMIT
    if kind and kind not in SUPPORTED:
        raise ValueError(f"unsupported gameplay model {kind} at {location}")
    result = {}
    if kind:
        name = kind.removesuffix("Model")
        result["kind"] = KINDS.get(kind, name[0].lower() + name[1:])
    for field, raw in value.items():
        if (field == "$type" or field in OMIT_FIELDS.get(kind, set())
                or field in PRESENTATION_FIELDS):
            continue
        if field == "name":
            # Preserve semantic IDs such as Fire:Dot, but discard generated names.
            if raw and not raw.startswith(kind):
                result["id"] = raw
            elif raw in referenced_ids:
                result["sourceModelId"] = raw
            continue
        lower = field[0].lower() + field[1:] if field else field
        if field != lower and lower in value:
            if field == "TargetTypes" and raw != value[lower]:
                field = "resolvedTargetTypes"
            elif value[lower] is None:
                field = lower  # Nullable backing fields have resolved public getters.
            elif raw != value[lower]:
                raise ValueError(f"conflicting {field}/{lower} values at {location}")
            else:
                continue
        if raw is None:
            continue
        if field.endswith("Frames") and raw == 0:
            continue  # Uninitialized derived caches in this static export.
        if field.endswith("Squared") and field.removesuffix("Squared") in value:
            continue  # The distance or radius itself already supplies this value.
        if field == "immuneBloonProperties":
            if type(raw) is not int or raw & ~sum(IMMUNITIES):
                raise ValueError(f"unknown immunity flags {raw!r} at {location}")
            result["immuneTo"] = [name for flag, name in IMMUNITIES.items() if raw & flag]
            continue
        if field == "areaTypes":
            if any(area not in AREAS for area in raw):
                raise ValueError(f"unknown placement area at {location}")
            result["allowedAreas"] = [AREAS[area] for area in raw]
            continue
        if field == "tag" and value.get("tags") == [raw]:
            continue
        if field == "ignoreWithMutators" and value.get("ignoreWithMutatorsList") == raw.split(","):
            continue
        item = project(raw, f"{location}/{field}", referenced_ids)
        if item is not OMIT:
            target = TYPE_FIELDS.get(kind, {}).get(field, FIELD_NAMES.get(field, field[0].lower() + field[1:]))
            if target in result:
                if result[target] == item:
                    continue
                raise ValueError(f"duplicate projected field {target} at {location}")
            result[target] = item
    if kind == "SingleEmissionModel":
        result["count"] = 1
    return result


def eligibility(base):
    if base.get("towerSet") == 16:
        return "hero"
    if base.get("isParagon") or base.get("towerSet") == 32:
        return "paragon"
    if base.get("isBeastHandlerPet") or base.get("IsBeastHandlerPet"):
        return "pet"
    if base.get("isSubTower") or base.get("IsSubEntity"):
        return "subentity"
    if base.get("isPowerTower") or base.get("isPowerProTower") or base.get("towerSet") == 64:
        return "power or item"
    if base.get("towerSet") not in SETS:
        return "not an ordinary Tower"
    if base.get("tiers") != [0, 0, 0]:
        return "missing ordinary 000 base"
    return None


def build_tower(family, paths, read, upgrades_by_name, capture, manifest, revision, converter_hash):
    inputs = {}

    def load(path):
        raw = read(path)
        inputs[path] = hashlib.sha256(raw).hexdigest()
        datum = json.loads(raw)
        if not isinstance(datum, dict):
            raise ValueError(f"expected a model object in {path}")
        return datum

    prefix = f"{capture}/game-data/Towers/{family}/"
    base_path = f"{prefix}{family}.json"
    if base_path not in paths:
        return None, "missing ordinary 000 base"
    base = load(base_path)
    if reason := eligibility(base):
        return None, reason
    states = {}
    additional = {}
    for path in sorted(paths):
        stem = Path(path).stem
        if stem.endswith("-Paragon"):
            continue
        if stem != family and not re.fullmatch(re.escape(family) + r"-[0-9]{3}", stem):
            model = load(path)
            if not model.get("isParagon"):
                name = model.get("name", stem)
                if name in additional:
                    raise ValueError(f"duplicate additional model {name!r}")
                additional[name] = (model, path)
            continue
        model = base if path == base_path else load(path)
        tiers = model.get("tiers")
        if (not isinstance(tiers, list) or len(tiers) != 3
                or any(type(tier) is not int for tier in tiers)
                or tuple(tiers) not in LEGAL_TIERS):
            raise ValueError(f"invalid ordinary state tiers in {path}")
        expected_name = family if tiers == [0, 0, 0] else f"{family}-{code(tiers)}"
        if model.get("name") != expected_name or model.get("baseId") != family or model.get("isParagon"):
            raise ValueError(f"state identity disagrees with its filename in {path}")
        key = code(tiers)
        if key in states:
            raise ValueError(f"duplicate state {key}")
        states[key] = (model, path)
    missing = sorted(code(tiers) for tiers in LEGAL_TIERS if code(tiers) not in states)
    if missing:
        raise ValueError(f"incomplete ordinary states: missing {', '.join(missing)}")

    definitions = {}
    links = {}
    repeated_links = 0
    for key, (model, path) in sorted(states.items()):
        links[key] = []
        expected_targets = {
            code(target) for index in range(3)
            if (target := tuple(tier + (index == j) for j, tier in enumerate(model["tiers"]))) in LEGAL_TIERS
        }
        targets = set()
        purchases = set()
        for link in model.get("upgrades") or []:
            target_name, name = link["tower"], link["upgrade"]
            if (target_name, name) in purchases:
                repeated_links += 1
                continue
            purchases.add((target_name, name))
            target = "000" if target_name == family else target_name.removeprefix(family + "-")
            if target not in states or target in targets or target not in expected_targets:
                raise ValueError(f"invalid purchase link to {target_name} in {path}")
            targets.add(target)
            if name not in upgrades_by_name:
                raise ValueError(f"missing upgrade definition {name!r} referenced by {path}")
            upgrade_path = upgrades_by_name[name]
            upgrade = load(upgrade_path)
            old, new = model["tiers"], states[target][0]["tiers"]
            index = next(i for i in range(3) if old[i] != new[i])
            if (upgrade.get("name") != name or upgrade.get("IsParagon")
                    or upgrade.get("path") != index or upgrade.get("tier") != new[index] - 1):
                raise ValueError(f"upgrade definition disagrees with purchase link in {upgrade_path}")
            definitions[name] = {
                "path": index + 1, "tier": new[index], "cost": upgrade["cost"],
                "xpCost": upgrade["xpCost"], "sourcePath": upgrade_path,
            }
            links[key].append({"upgrade": name, "state": target})
        if targets != expected_targets:
            raise ValueError(f"missing purchase links in {path}")
    if len(definitions) != 15 or len({(d["path"], d["tier"]) for d in definitions.values()}) != 15:
        raise ValueError("expected three paths with five unique purchases each")
    if repeated_links:
        print(f"{family}: collapsed {repeated_links} identical repeated purchase links", flush=True)

    exported = {}
    names, references = set(), set()

    def collect_ids(value):
        if isinstance(value, dict):
            for field, item in value.items():
                if field == "name" and isinstance(item, str):
                    names.add(item)
                elif field != "$type":
                    collect_ids(item)
        elif isinstance(value, list):
            for item in value:
                collect_ids(item)
        elif isinstance(value, str):
            references.add(value)

    for model, _ in itertools.chain(states.values(), additional.values()):
        collect_ids(model)
    referenced_ids = names & references - {""}
    for key, (model, path) in sorted(states.items()):
        applied = model.get("appliedUpgrades") or []
        expected_applied = {name for name, d in definitions.items() if d["tier"] <= model["tiers"][d["path"] - 1]}
        if len(applied) != len(set(applied)) or set(applied) != expected_applied:
            raise ValueError(f"applied upgrades disagree with tiers in {path}")
        state = project(model, path + "#", referenced_ids)
        behaviors = state.pop("effects", [])
        state.pop("kind")
        state.pop("id", None)
        state.pop("upgrades", None)
        state.pop("towerSet", None)
        for field in FAMILY_MARKERS:
            state.pop(field, None)
        state["baseCost"] = state.pop("cost")
        state["totalCost"] = state["baseCost"] + sum(definitions[name]["cost"] for name in applied)
        state["sourcePath"] = path
        state["nextPurchases"] = links[key]
        state["externalModifiers"] = state.pop("mods", [])
        state["placement"] = {field: state.pop(field) for field in (
            "allowedAreas", "footprint", "ignoreCoopAreas", "ignoreAreaChanges",
            "isExclusivelyWaterBased") if field in state}
        state["targeting"] = {field: state.pop(field) for field in (
            "targetTypes", "resolvedTargetTypes", "isGlobalRange", "ignoreBlockers") if field in state}
        state["attacks"] = [b for b in behaviors if b["kind"] == "attack"]
        state["abilities"] = [b for b in behaviors if b["kind"] == "ability"]
        state["effects"] = [b for b in behaviors if b["kind"] not in {"attack", "ability"}]
        exported[key] = state

    manifest_path = f"{capture}/manifest.json"
    inputs[manifest_path] = hashlib.sha256(read(manifest_path)).hexdigest()
    return {
        "formatVersion": 1,
        "source": {
            "repository": REPOSITORY, "atlasCommit": revision, "capture": capture,
            "gameVersion": str(manifest["gameVersion"]), "steamBuildId": str(manifest["steamBuildId"]),
            "captureDateUtc": manifest["captureDateUtc"],
            "modHelperVersion": manifest["modHelperVersion"],
            "atlasExporterVersion": manifest["atlasExporterVersion"],
            "converterPath": "scripts/export-gameplay-towers.py", "converterSha256": converter_hash,
            "files": [{"path": path, "sha256": digest} for path, digest in sorted(inputs.items())],
            "license": "CC BY-NC 4.0", "attribution": "Bloons TD 6 is by Ninja Kiwi.",
        },
        "tower": {"id": family, "category": SETS[base["towerSet"]], "baseCost": base["cost"]},
        "upgrades": dict(sorted(definitions.items(), key=lambda item: (item[1]["path"], item[1]["tier"]))),
        "states": exported,
        "additionalModels": {
            name: {"sourcePath": path, **project(model, path + "#", referenced_ids)}
            for name, (model, path) in sorted(additional.items())
        },
    }, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tower", help="process one family instead of every family")
    args = parser.parse_args()
    try:
        revision = git("rev-parse", "HEAD").strip()
        paths = git("ls-tree", "-r", "--name-only", "-z", revision, "--", "data").split("\0")
        cache = {}

        def read(path):
            if path not in cache:
                cache[path] = git("show", f"{revision}:{path}", binary=True)
            return cache[path]

        manifests = [(path, json.loads(read(path))) for path in paths
                     if re.fullmatch(r"data/[^/]+-build-[^/]+/manifest\.json", path)]
        if not manifests:
            raise ValueError("no committed capture manifest under data/")
        manifest_path, manifest = max(manifests, key=lambda item: (
            item[1]["captureDateUtc"], int(item[1]["steamBuildId"])))
        capture = str(Path(manifest_path).parent)
        upgrades_by_name = {}
        for path in paths:
            if path.startswith(f"{capture}/game-data/Upgrades/") and path.endswith(".json"):
                name = json.loads(read(path)).get("name")
                if name in upgrades_by_name:
                    raise ValueError(f"duplicate upgrade definition {name!r}")
                upgrades_by_name[name] = path
        prefix = f"{capture}/game-data/Towers/"
        families = {}
        for path in paths:
            if path.startswith(prefix) and path.endswith(".json"):
                families.setdefault(path[len(prefix):].split("/")[0], []).append(path)
        if args.tower and args.tower not in families:
            raise ValueError(f"unknown Tower family {args.tower}")
        destination = ROOT / capture / "gameplay-towers"
        converter_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        print(f"Capture {capture}; Atlas {revision}", flush=True)
        written = ineligible = unsupported = 0
        for family in sorted(families):
            if args.tower and family != args.tower:
                continue
            try:
                result, reason = build_tower(family, families[family], read, upgrades_by_name, capture,
                                             manifest, revision, converter_hash)
                if reason:
                    ineligible += 1
                    print(f"{family}: skipped ({reason})", flush=True)
                    continue
                filename = re.sub(r"(?<!^)(?=[A-Z])", "-", family).lower() + ".json"
                destination.mkdir(parents=True, exist_ok=True)
                output = destination / filename
                temporary = output.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
                temporary.replace(output)
                written += 1
                print(f"{family}: wrote {output.relative_to(ROOT)} (64 states, 15 upgrades)", flush=True)
            except (ValueError, KeyError, TypeError) as error:
                unsupported += 1
                print(f"{family}: skipped ({error})", flush=True)
        print(f"Exported {written}; skipped {ineligible} ineligible and {unsupported} unsupported or incomplete families.")
        return 0 if written else 1
    except (OSError, ValueError, KeyError) as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
