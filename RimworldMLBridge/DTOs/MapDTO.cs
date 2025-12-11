using System.Collections.Generic;

namespace RimworldMLBridge.DTOs
{
    /// <summary>
    /// Map data transfer object.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// </summary>
    public class MapDTO
    {
        public int Id { get; set; }
        public int Index { get; set; }
        public int Seed { get; set; }
        public string FactionId { get; set; }
        public bool IsPlayerHome { get; set; }
        public bool IsPocketMap { get; set; }
        public bool IsTempIncidentMap { get; set; }
        public string Size { get; set; }
    }

    /// <summary>
    /// Weather data for a map.
    /// </summary>
    public class MapWeatherDTO
    {
        public string Weather { get; set; }
        public float Temperature { get; set; }
    }

    /// <summary>
    /// Power grid information for a map.
    /// </summary>
    public class MapPowerInfoDTO
    {
        public int CurrentPower { get; set; }
        public int TotalPossiblePower { get; set; }
        public int CurrentlyStoredPower { get; set; }
        public int TotalPowerStorage { get; set; }
        public int TotalConsumption { get; set; }
        public int ConsumptionPowerOn { get; set; }
        public List<int> ProducePowerBuildings { get; set; } = new List<int>();
        public List<int> ConsumePowerBuildings { get; set; } = new List<int>();
        public List<int> StorePowerBuildings { get; set; } = new List<int>();
    }

    /// <summary>
    /// Creatures summary for a map (counts of different creature types).
    /// </summary>
    public class MapCreaturesSummaryDTO
    {
        public int ColonistsCount { get; set; }
        public int PrisonersCount { get; set; }
        public int EnemiesCount { get; set; }
        public int AnimalsCount { get; set; }
        public int InsectoidsCount { get; set; }
        public int MechanoidsCount { get; set; }
    }

    /// <summary>
    /// Zone data transfer object.
    /// </summary>
    public class ZoneDTO
    {
        public int Id { get; set; }
        public int CellsCount { get; set; }
        public string Label { get; set; }
        public string BaseLabel { get; set; }
        public string Type { get; set; }
    }

    /// <summary>
    /// Room data transfer object.
    /// </summary>
    public class RoomDTO
    {
        public int Id { get; set; }
        public string RoleLabel { get; set; }
        public float Temperature { get; set; }
        public int CellsCount { get; set; }
        public bool TouchesMapEdge { get; set; }
        public bool IsPrisonCell { get; set; }
        public bool IsDoorway { get; set; }
        public int OpenRoofCount { get; set; }
        public List<int> ContainedBedsIds { get; set; } = new List<int>();
    }

    /// <summary>
    /// Combined zones and areas data for a map.
    /// </summary>
    public class MapZonesDTO
    {
        public List<ZoneDTO> Zones { get; set; } = new List<ZoneDTO>();
        public List<ZoneDTO> Areas { get; set; } = new List<ZoneDTO>();
    }

    /// <summary>
    /// All rooms on a map.
    /// </summary>
    public class MapRoomsDTO
    {
        public List<RoomDTO> Rooms { get; set; } = new List<RoomDTO>();
    }
}
