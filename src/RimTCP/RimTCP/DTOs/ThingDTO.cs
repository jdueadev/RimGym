using System.Collections.Generic;

namespace RimTCP.DTOs
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
    /// Phase V: Extended for rich map state
    /// </summary>
    public class BuildingDTO
    {
        public int Id { get; set; }
        public int ThingId { get; set; }  // Alias for Id
        public string Def { get; set; }
        public string DefName { get; set; }  // Alias for Def
        public string Label { get; set; }
        public PositionDTO Position { get; set; }
        public string Type { get; set; }

        // Phase V additions
        public int Rotation { get; set; }
        public Vector3DTO Size { get; set; }
        public float HealthPercent { get; set; }
        public int FactionId { get; set; }
        public bool IsPowered { get; set; }
        public bool IsConstructed { get; set; }
        public Dictionary<string, float> Stats { get; set; } = new Dictionary<string, float>();
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

    /// <summary>
    /// Simple 3D vector for positions and dimensions (float precision).
    /// </summary>
    public class Vector3DTO
    {
        public float X { get; set; }
        public float Y { get; set; }
        public float Z { get; set; }
    }
}
