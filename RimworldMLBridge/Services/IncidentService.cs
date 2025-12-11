using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using RimworldMLBridge.DTOs;
using Verse;
using Verse.AI.Group;

namespace RimworldMLBridge.Services
{
    /// <summary>
    /// Service for extracting incident, quest, threat, and event data.
    /// Ported from RIMAPI IncidentService with HTTP/JSON layers stripped.
    /// </summary>
    public class IncidentService
    {
        private static readonly string LogPrefix = "[MLBridge.IncidentService]";

        /// <summary>
        /// Get recent incidents that have occurred on the specified map.
        /// </summary>
        public IncidentsDTO GetIncidents(int mapId = -1)
        {
            var result = new IncidentsDTO();

            try
            {
                Map map = mapId >= 0 ? GetMapByID(mapId) : Find.CurrentMap;
                if (map?.storyState?.lastFireTicks == null)
                    return result;

                foreach (var entry in map.storyState.lastFireTicks)
                {
                    if (entry.Key == null) continue;

                    result.Incidents.Add(new IncidentDTO
                    {
                        IncidentDef = entry.Key.defName,
                        Label = entry.Key.label ?? entry.Key.defName,
                        Category = GetIncidentCategory(entry.Key),
                        IncidentHour = TicksToDays(entry.Value) * 24f,
                        DaysSinceOccurred = (Find.TickManager.TicksGame - entry.Value) / 60000f
                    });
                }

                // Sort by most recent first
                result.Incidents.Sort((a, b) => b.IncidentHour.CompareTo(a.IncidentHour));
            }
            catch (Exception ex)
            {
                Log.Error($"{LogPrefix} GetIncidents error: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Get all Lords (AI group controllers) on the specified map.
        /// Lords manage raids, caravans, and other group behaviors.
        /// </summary>
        public List<LordDTO> GetLords(int mapId = -1)
        {
            var result = new List<LordDTO>();

            try
            {
                Map map = mapId >= 0 ? GetMapByID(mapId) : Find.CurrentMap;
                if (map?.lordManager?.lords == null)
                    return result;

                foreach (Lord lord in map.lordManager.lords)
                {
                    if (lord == null) continue;

                    result.Add(new LordDTO
                    {
                        LoadId = lord.loadID,
                        FactionName = lord.faction?.Name,
                        FactionDefName = lord.faction?.def?.defName,
                        LordJobType = lord.LordJob?.GetType().Name,
                        CurrentToilName = lord.CurLordToil?.GetType().Name,
                        TicksInToil = lord.ticksInToil,
                        NumPawnsLostViolently = lord.numPawnsLostViolently,
                        NumPawnsEverGained = lord.numPawnsEverGained,
                        OwnedPawnIds = lord.ownedPawns?.Select(p => p.ThingID).ToList() ?? new List<string>(),
                        OwnedBuildingIds = lord.ownedBuildings?.Select(b => b.ThingID).ToList() ?? new List<string>(),
                        QuestTags = lord.questTags?.ToList() ?? new List<string>(),
                        InSignalLeave = lord.inSignalLeave,
                        AnyActivePawn = lord.AnyActivePawn
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Error($"{LogPrefix} GetLords error: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Get all quests - both active and historical.
        /// </summary>
        public QuestsDTO GetQuests()
        {
            var result = new QuestsDTO();

            try
            {
                if (Find.QuestManager == null)
                    return result;

                var allQuests = Find.QuestManager.QuestsListForReading;
                if (allQuests == null)
                    return result;

                // Historical quests
                foreach (var quest in allQuests.Where(q => q != null && q.Historical))
                {
                    result.HistoricalQuests.Add(CreateQuestDTO(quest));
                }

                // Active quests
                foreach (var quest in allQuests.Where(q => q != null && !q.Historical))
                {
                    result.ActiveQuests.Add(CreateQuestDTO(quest));
                }
            }
            catch (Exception ex)
            {
                Log.Error($"{LogPrefix} GetQuests error: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Get active game conditions (toxic fallout, cold snap, etc.)
        /// </summary>
        public List<GameConditionDTO> GetGameConditions(int mapId = -1)
        {
            var result = new List<GameConditionDTO>();

            try
            {
                Map map = mapId >= 0 ? GetMapByID(mapId) : Find.CurrentMap;
                if (map?.gameConditionManager == null)
                    return result;

                foreach (var condition in map.gameConditionManager.ActiveConditions)
                {
                    if (condition == null) continue;

                    result.Add(new GameConditionDTO
                    {
                        DefName = condition.def?.defName,
                        Label = condition.LabelCap,
                        TicksPassed = condition.TicksPassed,
                        TicksLeft = condition.TicksLeft,
                        Permanent = condition.Permanent
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Error($"{LogPrefix} GetGameConditions error: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Get a comprehensive threat summary for ML agent decision-making.
        /// </summary>
        public ThreatSummaryDTO GetThreatSummary(int mapId = -1)
        {
            var result = new ThreatSummaryDTO();

            try
            {
                Map map = mapId >= 0 ? GetMapByID(mapId) : Find.CurrentMap;
                if (map == null)
                    return result;

                // Count active raids/hostile lords
                var lords = GetLords(mapId);
                result.ActiveLords = lords.Where(l => IsHostileLord(l)).ToList();
                result.ActiveRaidCount = result.ActiveLords.Count;

                // Count hostile pawns on the map
                if (map.mapPawns != null)
                {
                    result.HostilePawnCount = map.mapPawns.AllPawnsSpawned
                        ?.Count(p => p != null && p.HostileTo(Faction.OfPlayer) && !p.Downed && !p.Dead) ?? 0;
                }

                // Count active fires
                if (map.listerThings != null)
                {
                    result.ActiveFireCount = map.listerThings.ThingsOfDef(ThingDefOf.Fire)?.Count ?? 0;
                }

                // Check for mech clusters
                result.HasMechCluster = lords.Any(l =>
                    l.LordJobType != null &&
                    l.LordJobType.Contains("MechCluster"));

                // Check for infestations
                result.HasInfestation = lords.Any(l =>
                    l.LordJobType != null &&
                    (l.LordJobType.Contains("Infestation") || l.LordJobType.Contains("Hive")));

                // Get active game conditions
                result.ActiveConditions = GetGameConditions(mapId);
            }
            catch (Exception ex)
            {
                Log.Error($"{LogPrefix} GetThreatSummary error: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Get complete incident state including quests, recent incidents, and threats.
        /// </summary>
        public IncidentStateDTO GetIncidentState(int mapId = -1)
        {
            return new IncidentStateDTO
            {
                Quests = GetQuests(),
                RecentIncidents = GetIncidents(mapId),
                ThreatSummary = GetThreatSummary(mapId)
            };
        }

        #region Helper Methods

        private QuestDTO CreateQuestDTO(Quest quest)
        {
            return new QuestDTO
            {
                Id = quest.id,
                QuestDef = quest.root?.defName ?? "Unknown",
                Name = quest.name,
                Description = quest.description.ToString(),
                State = quest.State.ToString(),
                ExpiryHours = TicksToDays(quest.TicksUntilExpiry) * 24f,
                Rewards = GetQuestRewards(quest)
            };
        }

        private List<string> GetQuestRewards(Quest quest)
        {
            var rewardList = new List<string>();

            try
            {
                // In RimWorld 1.6, rewards are accessed through QuestPart_Choice
                if (quest?.PartsListForReading == null)
                    return rewardList;

                foreach (var part in quest.PartsListForReading)
                {
                    // Try to get reward description from quest parts
                    if (part is QuestPart_Choice choice && choice.choices != null)
                    {
                        foreach (var choiceOption in choice.choices)
                        {
                            if (choiceOption?.rewards != null)
                            {
                                foreach (var reward in choiceOption.rewards)
                                {
                                    // Get the string representation of the reward
                                    var label = reward?.ToString();
                                    if (!string.IsNullOrEmpty(label))
                                    {
                                        rewardList.Add(label);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"{LogPrefix} GetQuestRewards error: {ex.Message}");
            }

            return rewardList;
        }

        private string GetIncidentCategory(IncidentDef def)
        {
            if (def?.category == null)
                return "Unknown";

            if (def.category == IncidentCategoryDefOf.ThreatBig)
                return "ThreatBig";
            if (def.category == IncidentCategoryDefOf.ThreatSmall)
                return "ThreatSmall";
            if (def.category == IncidentCategoryDefOf.DeepDrillInfestation)
                return "DeepDrillInfestation";
            if (def.category == IncidentCategoryDefOf.DiseaseHuman)
                return "DiseaseHuman";
            if (def.category == IncidentCategoryDefOf.GiveQuest)
                return "GiveQuest";
            if (def.category == IncidentCategoryDefOf.Misc)
                return "Misc";
            if (def.category == IncidentCategoryDefOf.Special)
                return "Special";

            return def.category.defName ?? "Unknown";
        }

        private bool IsHostileLord(LordDTO lord)
        {
            if (lord == null || string.IsNullOrEmpty(lord.LordJobType))
                return false;

            // Check for common hostile lord job types
            var hostileTypes = new[] {
                "AssaultColony", "Raid", "Siege", "Kidnap",
                "Steal", "MechCluster", "Infestation"
            };

            return hostileTypes.Any(t =>
                lord.LordJobType.Contains(t, StringComparison.OrdinalIgnoreCase));
        }

        private Map GetMapByID(int mapId)
        {
            if (mapId < 0 || Current.Game?.Maps == null)
                return Find.CurrentMap;

            return Current.Game.Maps.FirstOrDefault(m => m?.uniqueID == mapId) ?? Find.CurrentMap;
        }

        private float TicksToDays(int ticks)
        {
            // 60000 ticks per day in RimWorld
            return ticks / 60000f;
        }

        #endregion
    }
}
