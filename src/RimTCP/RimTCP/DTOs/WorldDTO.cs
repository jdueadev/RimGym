using System.Collections.Generic;

namespace RimTCP.DTOs
{
    /// <summary>
    /// Phase V: Storyteller data transfer object
    /// </summary>
    public class StorytellerDTO
    {
        public string DefName { get; set; }
        public string Label { get; set; }
        public float Difficulty { get; set; }
        public float ThreatScale { get; set; }
        public int TicksSinceLastThreat { get; set; }
        public float AdaptationDays { get; set; }
    }

    /// <summary>
    /// Phase V: Faction data transfer object
    /// </summary>
    public class FactionDTO
    {
        public int FactionId { get; set; }
        public string DefName { get; set; }
        public string Name { get; set; }
        public string Relation { get; set; } // "Hostile", "Neutral", "Ally"
        public float Goodwill { get; set; } // -100 to 100
        public bool IsPlayer { get; set; }
        public bool Defeated { get; set; }
        public int SettlementCount { get; set; }
    }

    /// <summary>
    /// Phase V: Settlement data transfer object
    /// </summary>
    public class SettlementDTO
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int FactionId { get; set; }
        public PositionDTO TilePosition { get; set; }
        public string Type { get; set; } // "City", "Town", "Base", etc.
        public bool IsPlayerHome { get; set; }
    }

    /// <summary>
    /// Phase V: Caravan data transfer object
    /// </summary>
    public class CaravanDTO
    {
        public int ThingId { get; set; }
        public string Name { get; set; }
        public int FactionId { get; set; }
        public PositionDTO TilePosition { get; set; }
        public PositionDTO TileDestination { get; set; }
        public int PawnCount { get; set; }
        public bool IsPlayerCaravan { get; set; }
    }

    /// <summary>
    /// Phase V: World event data transfer object
    /// </summary>
    public class WorldEventDTO
    {
        public int Id { get; set; }
        public string DefName { get; set; }
        public string Label { get; set; }
        public string Description { get; set; }
        public int StartTick { get; set; }
        public int ExpiryTick { get; set; }
        public bool IsActive { get; set; }
        public PositionDTO TilePosition { get; set; }
    }

    /// <summary>
    /// Phase V: Complete world state data
    /// </summary>
    public class WorldStateDTO
    {
        public List<FactionDTO> Factions { get; set; } = new List<FactionDTO>();
        public List<SettlementDTO> Settlements { get; set; } = new List<SettlementDTO>();
        public List<CaravanDTO> Caravans { get; set; } = new List<CaravanDTO>();
        public List<WorldEventDTO> Events { get; set; } = new List<WorldEventDTO>();
        public int TileCount { get; set; }
        public float CoveragePercent { get; set; }
        public string SeedString { get; set; }
        public string PlanetName { get; set; }
    }
}
