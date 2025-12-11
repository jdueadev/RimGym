using System;
using System.Linq;
using RimworldMLBridge.DTOs;
using RimworldMLBridge.Protos;
using Google.Protobuf.Collections;

namespace RimworldMLBridge.Adapters
{
    /// <summary>
    /// Phase V: Adapter for converting Map DTOs to Protobuf messages
    /// Handles terrain, buildings, items, zones, and rooms
    /// Target: <1ms conversion time
    /// </summary>
    public class MapAdapter
    {
        /// <summary>
        /// Convert MapDTO to Protobuf MapState
        /// </summary>
        public static MapState ToProtobuf(MapDTO mapDto)
        {
            if (mapDto == null)
                return null;

            var mapState = new MapState
            {
                MapId = mapDto.Id,
                SizeX = mapDto.SizeX,
                SizeY = mapDto.SizeY,
                SizeZ = mapDto.SizeZ,
                Biome = mapDto.Biome ?? "Unknown",
                AverageTemperature = mapDto.AverageTemperature,
                AverageCleanliness = mapDto.AverageCleanliness,
                WildlifeCount = mapDto.WildlifeCount,
                HostileCount = mapDto.HostileCount,
                TerrainIsDelta = false, // Full state by default
                TotalItemCount = mapDto.TotalItemCount
            };

            // Convert terrain cells
            if (mapDto.TerrainCells != null)
            {
                foreach (var cell in mapDto.TerrainCells)
                {
                    mapState.TerrainCells.Add(ToProtobuf(cell));
                }
            }

            // Convert buildings
            if (mapDto.Buildings != null)
            {
                foreach (var building in mapDto.Buildings)
                {
                    mapState.Buildings.Add(ToProtobufBuildingState(building));
                }
            }

            // Convert items
            if (mapDto.Items != null)
            {
                foreach (var item in mapDto.Items)
                {
                    mapState.Items.Add(ToProtobuf(item));
                }
            }

            // Convert zones
            if (mapDto.Zones != null)
            {
                foreach (var zone in mapDto.Zones)
                {
                    mapState.Zones.Add(ToProtobuf(zone));
                }
            }

            // Convert rooms
            if (mapDto.Rooms != null)
            {
                foreach (var room in mapDto.Rooms)
                {
                    mapState.Rooms.Add(ToProtobuf(room));
                }
            }

            return mapState;
        }

        /// <summary>
        /// Convert TerrainCellDTO to Protobuf TerrainCell
        /// </summary>
        private static TerrainCell ToProtobuf(TerrainCellDTO cellDto)
        {
            return new TerrainCell
            {
                X = cellDto.X,
                Y = cellDto.Y,
                Type = ParseTerrainType(cellDto.Type),
                DefName = cellDto.DefName ?? "Unknown",
                Walkable = cellDto.Walkable,
                Fertility = cellDto.Fertility,
                Beauty = cellDto.Beauty
            };
        }

        /// <summary>
        /// Convert BuildingDTO to Protobuf BuildingState
        /// </summary>
        private static BuildingState ToProtobufBuildingState(BuildingDTO buildingDto)
        {
            var buildingState = new BuildingState
            {
                ThingId = buildingDto.ThingId,
                DefName = buildingDto.DefName ?? "Unknown",
                Label = buildingDto.Label ?? buildingDto.DefName ?? "Building",
                Type = ParseBuildingType(buildingDto.Type),
                Rotation = buildingDto.Rotation,
                HealthPercent = buildingDto.HealthPercent,
                FactionId = buildingDto.FactionId,
                IsPowered = buildingDto.IsPowered,
                IsConstructed = buildingDto.IsConstructed
            };

            // Set position
            if (buildingDto.Position != null)
            {
                buildingState.Position = new Vector3
                {
                    X = buildingDto.Position.X,
                    Y = buildingDto.Position.Y,
                    Z = buildingDto.Position.Z
                };
            }

            // Set size
            if (buildingDto.Size != null)
            {
                buildingState.Size = new Vector3
                {
                    X = buildingDto.Size.X,
                    Y = buildingDto.Size.Y,
                    Z = buildingDto.Size.Z
                };
            }

            // Add stats
            if (buildingDto.Stats != null)
            {
                foreach (var kvp in buildingDto.Stats)
                {
                    buildingState.Stats[kvp.Key] = kvp.Value;
                }
            }

            return buildingState;
        }

        /// <summary>
        /// Convert ItemDTO to Protobuf ItemState
        /// </summary>
        private static ItemState ToProtobuf(ItemDTO itemDto)
        {
            var itemState = new ItemState
            {
                ThingId = itemDto.ThingId,
                DefName = itemDto.DefName ?? "Unknown",
                Label = itemDto.Label ?? itemDto.DefName ?? "Item",
                StackCount = itemDto.StackCount,
                HitPoints = itemDto.HitPoints,
                FactionId = itemDto.FactionId,
                Category = itemDto.Category ?? "Unknown",
                Forbidden = itemDto.Forbidden
            };

            // Set position
            if (itemDto.Position != null)
            {
                itemState.Position = new Vector3
                {
                    X = itemDto.Position.X,
                    Y = itemDto.Position.Y,
                    Z = itemDto.Position.Z
                };
            }

            return itemState;
        }

        /// <summary>
        /// Convert ZoneDTO to Protobuf ZoneState
        /// </summary>
        private static ZoneState ToProtobuf(ZoneDTO zoneDto)
        {
            var zoneState = new ZoneState
            {
                Id = zoneDto.Id,
                Label = zoneDto.Label ?? $"Zone {zoneDto.Id}",
                Type = ParseZoneType(zoneDto.Type)
            };

            // Add cell positions
            if (zoneDto.Cells != null)
            {
                foreach (var cell in zoneDto.Cells)
                {
                    zoneState.Cells.Add(new Vector3
                    {
                        X = cell.X,
                        Y = cell.Y,
                        Z = cell.Z
                    });
                }
            }

            // Add settings
            if (zoneDto.Settings != null)
            {
                foreach (var kvp in zoneDto.Settings)
                {
                    zoneState.Settings[kvp.Key] = kvp.Value;
                }
            }

            return zoneState;
        }

        /// <summary>
        /// Convert RoomDTO to Protobuf RoomState
        /// </summary>
        private static RoomState ToProtobuf(RoomDTO roomDto)
        {
            var roomState = new RoomState
            {
                Id = roomDto.Id,
                CellCount = roomDto.CellCount,
                Temperature = roomDto.Temperature,
                Cleanliness = roomDto.Cleanliness,
                Beauty = roomDto.Beauty,
                Wealth = roomDto.Wealth,
                Space = roomDto.Space,
                IsOutdoors = roomDto.IsOutdoors
            };

            // Add building IDs
            if (roomDto.BuildingIds != null)
            {
                roomState.BuildingIds.AddRange(roomDto.BuildingIds);
            }

            return roomState;
        }

        #region Enum Parsers

        private static TerrainType ParseTerrainType(string type)
        {
            if (string.IsNullOrEmpty(type))
                return TerrainType.TerrainUnknown;

            switch (type.ToUpperInvariant())
            {
                case "TERRAIN_SOIL":
                    return TerrainType.TerrainSoil;
                case "TERRAIN_GRAVEL":
                    return TerrainType.TerrainGravel;
                case "TERRAIN_SAND":
                    return TerrainType.TerrainSand;
                case "TERRAIN_MARSH":
                    return TerrainType.TerrainMarsh;
                case "TERRAIN_WATER":
                    return TerrainType.TerrainWater;
                case "TERRAIN_STONE":
                    return TerrainType.TerrainStone;
                case "TERRAIN_WOOD_FLOOR":
                    return TerrainType.TerrainWoodFloor;
                case "TERRAIN_CONCRETE":
                    return TerrainType.TerrainConcrete;
                case "TERRAIN_METAL":
                    return TerrainType.TerrainMetal;
                case "TERRAIN_CARPET":
                    return TerrainType.TerrainCarpet;
                default:
                    return TerrainType.TerrainUnknown;
            }
        }

        private static BuildingType ParseBuildingType(string type)
        {
            if (string.IsNullOrEmpty(type))
                return BuildingType.BuildingUnknown;

            switch (type.ToUpperInvariant())
            {
                case "BUILDING_WALL":
                    return BuildingType.BuildingWall;
                case "BUILDING_DOOR":
                    return BuildingType.BuildingDoor;
                case "BUILDING_BED":
                    return BuildingType.BuildingBed;
                case "BUILDING_TABLE":
                    return BuildingType.BuildingTable;
                case "BUILDING_WORKBENCH":
                    return BuildingType.BuildingWorkbench;
                case "BUILDING_STORAGE":
                    return BuildingType.BuildingStorage;
                case "BUILDING_POWER":
                    return BuildingType.BuildingPower;
                case "BUILDING_PRODUCTION":
                    return BuildingType.BuildingProduction;
                case "BUILDING_DEFENSE":
                    return BuildingType.BuildingDefense;
                case "BUILDING_DECORATION":
                    return BuildingType.BuildingDecoration;
                default:
                    return BuildingType.BuildingUnknown;
            }
        }

        private static ZoneType ParseZoneType(string type)
        {
            if (string.IsNullOrEmpty(type))
                return ZoneType.ZoneStockpile;

            switch (type.ToUpperInvariant())
            {
                case "ZONE_STOCKPILE":
                    return ZoneType.ZoneStockpile;
                case "ZONE_GROWING":
                    return ZoneType.ZoneGrowing;
                case "ZONE_DUMPING":
                    return ZoneType.ZoneDumping;
                case "ZONE_ANIMAL":
                    return ZoneType.ZoneAnimal;
                default:
                    return ZoneType.ZoneStockpile;
            }
        }

        #endregion
    }
}
