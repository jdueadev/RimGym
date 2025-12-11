using System.Collections.Generic;

namespace RimworldMLBridge.DTOs
{
    /// <summary>
    /// Generic thing/item data transfer object.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// </summary>
    public class ThingDTO
    {
        public int ThingId { get; set; }
        public string DefName { get; set; }
        public string Label { get; set; }
        public List<string> Categories { get; set; } = new List<string>();
        public PositionDTO Position { get; set; }
        public int StackCount { get; set; }
        public float MarketValue { get; set; }
        public bool IsForbidden { get; set; }
        public int Quality { get; set; } = -1;  // -1 means no quality
        public int HitPoints { get; set; }
        public int MaxHitPoints { get; set; }
    }

    /// <summary>
    /// Building data transfer object.
    /// </summary>
    public class BuildingDTO
    {
        public int Id { get; set; }
        public string Def { get; set; }
        public string Label { get; set; }
        public PositionDTO Position { get; set; }
        public string Type { get; set; }
    }

    /// <summary>
    /// Animal data transfer object.
    /// </summary>
    public class AnimalDTO
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Def { get; set; }
        public string Faction { get; set; }
        public PositionDTO Position { get; set; }
        public int? Trainer { get; set; }
        public bool Pregnant { get; set; }
    }
}
