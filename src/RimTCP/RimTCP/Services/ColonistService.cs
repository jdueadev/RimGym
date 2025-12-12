using System;
using System.Collections.Generic;
using System.Linq;
using RimTCP.DTOs;
using RimWorld;
using Verse;

namespace RimTCP.Services
{
    /// <summary>
    /// Service for extracting colonist/pawn data from RimWorld.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// Returns raw C# DTOs for efficient Protobuf serialization.
    /// </summary>
    public class ColonistService
    {
        /// <summary>
        /// Get a pawn by its ThingID.
        /// </summary>
        public static Pawn GetPawnById(int id)
        {
            try
            {
                var map = Find.CurrentMap;
                if (map == null)
                    return null;

                return map.mapPawns.AllPawns.FirstOrDefault(p => p.thingIDNumber == id);
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error finding pawn {id}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get basic colonist data for all free colonists on the current map.
        /// </summary>
        public List<ColonistDTO> GetColonists()
        {
            var colonists = new List<ColonistDTO>();

            try
            {
                var map = Find.CurrentMap;
                if (map == null)
                    return colonists;

                var freeColonists = map.mapPawns?.FreeColonists;
                if (freeColonists == null)
                    return colonists;

                foreach (var pawn in freeColonists)
                {
                    if (pawn == null)
                        continue;
                    colonists.Add(CreateColonistDTO(pawn));
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error getting colonists: {ex.Message}");
            }

            return colonists;
        }

        /// <summary>
        /// Get a single colonist by ID.
        /// </summary>
        public ColonistDTO GetColonist(int pawnId)
        {
            return GetColonists().FirstOrDefault(c => c.Id == pawnId);
        }

        /// <summary>
        /// Get detailed colonist data for all free colonists.
        /// </summary>
        public List<ColonistDetailedDTO> GetColonistsDetailed()
        {
            var colonists = new List<ColonistDetailedDTO>();

            try
            {
                var map = Find.CurrentMap;
                if (map == null)
                    return colonists;

                var freeColonists = map.mapPawns?.FreeColonists;
                if (freeColonists == null)
                    return colonists;

                foreach (var pawn in freeColonists)
                {
                    if (pawn == null)
                        continue;
                    colonists.Add(PawnToDetailedDTO(pawn));
                }
            }
            catch (Exception ex)
            {
                Log.Warning(
                    $"{Constants.LogPrefix} Error getting detailed colonists: {ex.Message}"
                );
            }

            return colonists;
        }

        /// <summary>
        /// Get detailed data for a single colonist.
        /// </summary>
        public ColonistDetailedDTO GetColonistDetailed(int pawnId)
        {
            return GetColonistsDetailed().FirstOrDefault(c => c.Colonist?.Id == pawnId);
        }

        /// <summary>
        /// Create basic colonist DTO from a Pawn.
        /// </summary>
        public static ColonistDTO CreateColonistDTO(Pawn pawn)
        {
            return new ColonistDTO
            {
                Id = pawn.thingIDNumber,
                Name = pawn.Name?.ToStringShort ?? "Unknown",
                Gender = pawn.gender.ToString(),
                Age = pawn.ageTracker?.AgeBiologicalYears ?? 0,
                Health = pawn.health?.summaryHealth?.SummaryHealthPercent ?? 1f,
                Mood = pawn.needs?.mood?.CurLevelPercentage ?? 0.5f,
                Hunger = pawn.needs?.food?.CurLevel ?? 0f,
                Position = new PositionDTO
                {
                    X = pawn.Position.x,
                    Y = pawn.Position.y,
                    Z = pawn.Position.z,
                },
                // Status flags - extracted from pawn state
                IsDrafted = pawn.Drafted,
                IsDowned = pawn.Downed,
                IsDead = pawn.Dead,
            };
        }

        /// <summary>
        /// Create detailed colonist DTO from a Pawn.
        /// </summary>
        public static ColonistDetailedDTO PawnToDetailedDTO(Pawn pawn)
        {
            try
            {
                return new ColonistDetailedDTO
                {
                    Sleep = pawn.needs?.rest?.CurLevel ?? 0f,
                    Comfort = pawn.needs?.comfort?.CurLevel ?? 0f,
                    SurroundingBeauty = pawn.needs?.beauty?.CurLevel ?? 0f,
                    FreshAir = pawn.needs?.outdoors?.CurLevel ?? 0f,
                    Colonist = CreateColonistDTO(pawn),
                    ColonistWorkInfo = new ColonistWorkInfoDTO
                    {
                        Skills = GetSkills(pawn),
                        CurrentJob = pawn.CurJob?.def?.defName ?? "",
                        Traits = GetTraits(pawn),
                        WorkPriorities = GetWorkPriorities(pawn),
                    },
                    ColonistMedicalInfo = new ColonistMedicalInfoDTO
                    {
                        Health = pawn.health?.summaryHealth?.SummaryHealthPercent ?? 1f,
                        Hediffs = GetHediffs(pawn),
                        MedicalPolicyId = (int)(
                            pawn.playerSettings?.medCare ?? MedicalCareCategory.NoCare
                        ),
                        IsSelfTendAllowed = pawn.playerSettings?.selfTend ?? false,
                    },
                    ColonistSocialInfo = CreatePawnSocialInfoDTO(pawn),
                };
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error converting pawn to DTO: {ex.Message}");
                return new ColonistDetailedDTO
                {
                    Colonist = new ColonistDTO { Id = pawn.thingIDNumber, Name = "Error" },
                };
            }
        }

        /// <summary>
        /// Extract skills from a pawn.
        /// </summary>
        public static List<SkillDTO> GetSkills(Pawn pawn)
        {
            try
            {
                if (pawn.skills?.skills == null)
                    return new List<SkillDTO>();

                return pawn
                    .skills.skills.Where(skill => skill?.def != null)
                    .Select(skill => new SkillDTO
                    {
                        Name = skill.def.defName,
                        Level = skill.Level,
                        Description = skill.def.description ?? "",
                        MinLevel = SkillRecord.MinLevel,
                        MaxLevel = SkillRecord.MaxLevel,
                        LevelDescriptor = skill.LevelDescriptor,
                        PermanentlyDisabled = skill.PermanentlyDisabled,
                        TotallyDisabled = skill.TotallyDisabled,
                        XpTotalEarned = skill.XpTotalEarned,
                        XpProgressPercent = skill.XpProgressPercent,
                        XpRequiredForLevelUp = skill.XpRequiredForLevelUp,
                        XpSinceLastLevel = skill.xpSinceLastLevel,
                        Aptitude = skill.Aptitude,
                        Passion = (int)skill.passion,
                        DisabledWorkTags = (int)skill.def.disablingWorkTags,
                    })
                    .ToList();
            }
            catch
            {
                return new List<SkillDTO>();
            }
        }

        /// <summary>
        /// Extract traits from a pawn.
        /// </summary>
        public static List<TraitDTO> GetTraits(Pawn pawn)
        {
            try
            {
                if (pawn.story?.traits?.allTraits == null)
                    return new List<TraitDTO>();

                return pawn
                    .story.traits.allTraits.Where(t => t != null)
                    .Select(t => new TraitDTO
                    {
                        Name = t.def.defName,
                        Label = t.Label,
                        Description = t.def.description ?? "",
                        DisabledWorkTags = (int)t.def.disabledWorkTags,
                        Suppressed = t.Suppressed,
                    })
                    .ToList();
            }
            catch
            {
                return new List<TraitDTO>();
            }
        }

        /// <summary>
        /// Extract work priorities from a pawn.
        /// </summary>
        public static List<WorkPriorityDTO> GetWorkPriorities(Pawn pawn)
        {
            var priorities = new List<WorkPriorityDTO>();

            try
            {
                if (pawn.workSettings == null)
                    return priorities;

                foreach (WorkTypeDef workType in DefDatabase<WorkTypeDef>.AllDefs)
                {
                    if (workType == null)
                        continue;

                    var priority = pawn.workSettings.GetPriority(workType);
                    if (priority > 0)
                    {
                        priorities.Add(
                            new WorkPriorityDTO
                            {
                                WorkType = workType.defName,
                                Priority = priority,
                                IsTotallyDisabled = pawn.WorkTypeIsDisabled(workType),
                            }
                        );
                    }
                }

                return priorities.OrderBy(p => p.Priority).ToList();
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error getting work priorities: {ex.Message}");
                return priorities;
            }
        }

        /// <summary>
        /// Extract health conditions (hediffs) from a pawn.
        /// </summary>
        public static List<HediffDTO> GetHediffs(Pawn pawn)
        {
            try
            {
                if (pawn.health?.hediffSet?.hediffs == null)
                    return new List<HediffDTO>();

                return pawn
                    .health.hediffSet.hediffs.Where(h => h != null)
                    .Select(h => HediffToDTO(h))
                    .ToList();
            }
            catch
            {
                return new List<HediffDTO>();
            }
        }

        /// <summary>
        /// Convert a single Hediff to DTO.
        /// </summary>
        public static HediffDTO HediffToDTO(Hediff hediff)
        {
            if (hediff == null)
                return null;

            return new HediffDTO
            {
                LoadId = hediff.loadID,
                DefName = hediff.def?.defName,
                Label = hediff.Label,
                LabelCap = hediff.LabelCap,
                Severity = hediff.Severity,
                SeverityLabel = hediff.SeverityLabel,
                CurStageIndex = hediff.CurStageIndex,
                CurStageLabel = hediff.CurStage?.label,
                PartLabel = hediff.Part?.Label,
                PartDefName = hediff.Part?.def?.defName,
                AgeTicks = hediff.ageTicks,
                Visible = hediff.Visible,
                IsPermanent = hediff.IsPermanent(),
                IsTended = hediff.IsTended(),
                TendableNow = hediff.TendableNow(),
                Bleeding = hediff.Bleeding,
                BleedRate = hediff.BleedRate,
                IsLethal = hediff.IsLethal,
                PainFactor = hediff.PainFactor,
                PainOffset = hediff.PainOffset,
            };
        }

        /// <summary>
        /// Create social info DTO from a pawn.
        /// </summary>
        public static ColonistSocialInfoDTO CreatePawnSocialInfoDTO(Pawn pawn)
        {
            var dto = new ColonistSocialInfoDTO
            {
                Id = pawn.ThingID,
                Name = pawn.Name?.ToString(),
                DirectRelations = new List<RelationDTO>(),
                ChildrenCount = pawn.relations?.ChildrenCount ?? 0,
            };

            try
            {
                if (pawn.relations?.DirectRelations != null)
                {
                    foreach (var relation in pawn.relations.DirectRelations)
                    {
                        if (relation?.otherPawn == null)
                            continue;

                        dto.DirectRelations.Add(
                            new RelationDTO
                            {
                                RelationDefName = relation.def?.defName,
                                OtherPawnId = relation.otherPawn.ThingID,
                                OtherPawnName = relation.otherPawn.Name?.ToString(),
                            }
                        );
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error getting social info: {ex.Message}");
            }

            return dto;
        }

        /// <summary>
        /// Get colonist inventory.
        /// </summary>
        public ColonistInventoryDTO GetColonistInventory(int pawnId)
        {
            var inventory = new ColonistInventoryDTO();

            try
            {
                var pawn = GetPawnById(pawnId);
                if (pawn == null)
                    return inventory;

                // Inventory items
                if (pawn.inventory?.innerContainer != null)
                {
                    foreach (var item in pawn.inventory.innerContainer)
                    {
                        inventory.Items.Add(ThingToDTO(item));
                    }
                }

                // Worn apparel
                if (pawn.apparel?.WornApparel != null)
                {
                    foreach (var apparel in pawn.apparel.WornApparel)
                    {
                        inventory.Apparels.Add(ThingToDTO(apparel));
                    }
                }

                // Equipment
                if (pawn.equipment?.AllEquipmentListForReading != null)
                {
                    foreach (var equipment in pawn.equipment.AllEquipmentListForReading)
                    {
                        inventory.Equipment.Add(ThingToDTO(equipment));
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error getting inventory: {ex.Message}");
            }

            return inventory;
        }

        /// <summary>
        /// Convert a Thing to DTO.
        /// </summary>
        private static ThingDTO ThingToDTO(Thing thing)
        {
            var dto = new ThingDTO
            {
                ThingId = thing.thingIDNumber,
                DefName = thing.def?.defName,
                Label = thing.Label,
                Categories =
                    thing.def?.thingCategories?.Select(c => c.defName).ToList()
                    ?? new List<string>(),
                Position = new PositionDTO
                {
                    X = thing.Position.x,
                    Y = thing.Position.y,
                    Z = thing.Position.z,
                },
                StackCount = thing.stackCount,
                MarketValue = thing.MarketValue,
                IsForbidden = thing.IsForbidden(Faction.OfPlayer),
                Quality = -1,
            };

            if (thing.TryGetQuality(out QualityCategory quality))
            {
                dto.Quality = (int)quality;
            }

            if (thing.def?.useHitPoints == true)
            {
                dto.HitPoints = thing.HitPoints;
                dto.MaxHitPoints = thing.MaxHitPoints;
            }

            return dto;
        }
    }
}
