using System.Collections.Generic;

namespace RimworldMLBridge.DTOs
{
    /// <summary>
    /// Summary of quests - both active and historical
    /// </summary>
    public class QuestsDTO
    {
        public List<QuestDTO> ActiveQuests { get; set; } = new List<QuestDTO>();
        public List<QuestDTO> HistoricalQuests { get; set; } = new List<QuestDTO>();
    }

    /// <summary>
    /// Individual quest data
    /// </summary>
    public class QuestDTO
    {
        public int Id { get; set; }
        public string QuestDef { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string State { get; set; }
        public float ExpiryHours { get; set; }
        public List<string> Rewards { get; set; } = new List<string>();
    }

    /// <summary>
    /// Summary of incidents that have occurred on the map
    /// </summary>
    public class IncidentsDTO
    {
        public List<IncidentDTO> Incidents { get; set; } = new List<IncidentDTO>();
    }

    /// <summary>
    /// Individual incident (event) data from the story state
    /// </summary>
    public class IncidentDTO
    {
        public string IncidentDef { get; set; }
        public string Label { get; set; }
        public string Category { get; set; }
        public float IncidentHour { get; set; }
        public float DaysSinceOccurred { get; set; }
    }

    /// <summary>
    /// Lord (AI group controller) data - manages raids, caravans, etc.
    /// </summary>
    public class LordDTO
    {
        public int LoadId { get; set; }
        public string FactionName { get; set; }
        public string FactionDefName { get; set; }
        public string LordJobType { get; set; }
        public string CurrentToilName { get; set; }
        public int TicksInToil { get; set; }
        public int NumPawnsLostViolently { get; set; }
        public int NumPawnsEverGained { get; set; }
        public List<string> OwnedPawnIds { get; set; } = new List<string>();
        public List<string> OwnedBuildingIds { get; set; } = new List<string>();
        public List<string> QuestTags { get; set; } = new List<string>();
        public string InSignalLeave { get; set; }
        public bool AnyActivePawn { get; set; }
    }

    /// <summary>
    /// Game condition (weather events, toxic fallout, etc.)
    /// </summary>
    public class GameConditionDTO
    {
        public string DefName { get; set; }
        public string Label { get; set; }
        public int TicksPassed { get; set; }
        public int TicksLeft { get; set; }
        public bool Permanent { get; set; }
    }

    /// <summary>
    /// Active threat summary for ML agent decision-making
    /// </summary>
    public class ThreatSummaryDTO
    {
        public int ActiveRaidCount { get; set; }
        public int HostilePawnCount { get; set; }
        public int ActiveFireCount { get; set; }
        public bool HasMechCluster { get; set; }
        public bool HasInfestation { get; set; }
        public List<LordDTO> ActiveLords { get; set; } = new List<LordDTO>();
        public List<GameConditionDTO> ActiveConditions { get; set; } = new List<GameConditionDTO>();
    }

    /// <summary>
    /// Aggregate incident state for the game
    /// </summary>
    public class IncidentStateDTO
    {
        public QuestsDTO Quests { get; set; }
        public IncidentsDTO RecentIncidents { get; set; }
        public ThreatSummaryDTO ThreatSummary { get; set; }
    }
}
