using System.Collections.Generic;

namespace RimTCP.DTOs
{
    /// <summary>
    /// Map data transfer object.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// Phase V: Extended with terrain, buildings, items, zones, rooms
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

        // Phase V additions
        public int SizeX { get; set; }
        public int SizeY { get; set; }
        public int SizeZ { get; set; }
        public string Biome { get; set; }
        public float AverageTemperature { get; set; }
        public float AverageCleanliness { get; set; }
        public int WildlifeCount { get; set; }
        public int HostileCount { get; set; }
        public int TotalItemCount { get; set; }

        public List<TerrainCellDTO> TerrainCells { get; set; } = new List<TerrainCellDTO>();
        public List<BuildingDTO> Buildings { get; set; } = new List<BuildingDTO>();
        public List<ItemDTO> Items { get; set; } = new List<ItemDTO>();
        public List<ZoneDTO> Zones { get; set; } = new List<ZoneDTO>();
        public List<RoomDTO> Rooms { get; set; } = new List<RoomDTO>();
    }

    /// <summary>
    /// Terrain cell data for map visualization.
    /// </summary>
    public class TerrainCellDTO
    {
        public int X { get; set; }
        public int Y { get; set; }
        public string Type { get; set; } // Enum as string: TERRAIN_SOIL, TERRAIN_WATER, etc.
        public string DefName { get; set; }
        public bool Walkable { get; set; }
        public float Fertility { get; set; }
        public float Beauty { get; set; }
    }

    /// <summary>
    /// Item/Thing data for map.
    /// </summary>
    public class ItemDTO
    {
        public int ThingId { get; set; }
        public string DefName { get; set; }
        public string Label { get; set; }
        public PositionDTO Position { get; set; }
        public int StackCount { get; set; }
        public float HitPoints { get; set; }
        public int FactionId { get; set; }
        public string Category { get; set; }
        public bool Forbidden { get; set; }
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
        public string Type { get; set; } // ZONE_STOCKPILE, ZONE_GROWING, etc.
        
        // Phase V additions
        public List<Vector3DTO> Cells { get; set; } = new List<Vector3DTO>();
        public Dictionary<string, string> Settings { get; set; } = new Dictionary<string, string>();
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

        // Phase V additions
        public int CellCount { get; set; }
        public float Cleanliness { get; set; }
        public float Beauty { get; set; }
        public float Wealth { get; set; }
        public float Space { get; set; }
        public bool IsOutdoors { get; set; }
        public List<int> BuildingIds { get; set; } = new List<int>();
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
