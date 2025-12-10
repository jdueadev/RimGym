using System;
using System.Collections.Generic;
using System.Linq;
using RimworldMLBridge.DTOs;
using RimWorld;
using UnityEngine;
using Verse;

namespace RimworldMLBridge.Services
{
    /// <summary>
    /// Service for extracting map data from RimWorld.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// Returns raw C# DTOs for efficient Protobuf serialization.
    /// </summary>
    public class MapService
    {
        /// <summary>
        /// Get a map by its unique ID.
        /// </summary>
        public static Map GetMapByID(int uniqueID)
        {
            foreach (Map map in Find.Maps)
            {
                if (map.uniqueID == uniqueID)
                {
                    return map;
                }
            }
            return null;
        }

        /// <summary>
        /// Get a Thing on a specific map by ID.
        /// </summary>
        public static Thing GetThingOnMapById(int mapId, int thingId)
        {
            Map map = GetMapByID(mapId);
            if (map == null) return null;

            return map.listerThings.AllThings
                .FirstOrDefault(s => s.thingIDNumber == thingId);
        }

        /// <summary>
        /// Get basic info for all maps in the game.
        /// </summary>
        public List<MapDTO> GetMaps()
        {
            var maps = new List<MapDTO>();

            try
            {
                if (Current.Game?.Maps == null) return maps;

                foreach (var map in Current.Game.Maps)
                {
                    maps.Add(new MapDTO
                    {
                        Id = map.uniqueID,
                        Index = map.Index,
                        Seed = map.ConstantRandSeed,
                        FactionId = map.ParentFaction?.loadID.ToString() ?? "",
                        IsPlayerHome = map.IsPlayerHome,
                        IsPocketMap = map.IsPocketMap,
                        IsTempIncidentMap = map.IsTempIncidentMap,
                        Size = map.Size.ToString()
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting maps: {ex.Message}");
            }

            return maps;
        }

        /// <summary>
        /// Get weather info for a map.
        /// </summary>
        public MapWeatherDTO GetWeather(int mapId)
        {
            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return new MapWeatherDTO();

                return new MapWeatherDTO
                {
                    Weather = map.weatherManager?.CurWeatherPerceived?.defName ?? "Unknown",
                    Temperature = map.mapTemperature?.OutdoorTemp ?? 0f
                };
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting weather: {ex.Message}");
                return new MapWeatherDTO();
            }
        }

        /// <summary>
        /// Get creatures summary for a map.
        /// </summary>
        public MapCreaturesSummaryDTO GetMapCreaturesSummary(int mapId)
        {
            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return new MapCreaturesSummaryDTO();

                return new MapCreaturesSummaryDTO
                {
                    ColonistsCount = map.mapPawns.FreeColonistsSpawnedCount,
                    PrisonersCount = map.mapPawns.PrisonersOfColonyCount,
                    EnemiesCount = map.mapPawns.AllPawnsSpawned.Count(p =>
                        p.RaceProps?.Humanlike == true && p.HostileTo(Faction.OfPlayer)),
                    AnimalsCount = map.mapPawns.AllPawnsSpawned.Count(p =>
                        p.RaceProps?.Animal == true),
                    InsectoidsCount = map.mapPawns.AllPawnsSpawned.Count(p =>
                        p?.Faction?.def == FactionDefOf.Insect),
                    MechanoidsCount = map.mapPawns.AllPawnsSpawned.Count(p =>
                        p?.RaceProps?.IsMechanoid == true)
                };
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting creatures summary: {ex.Message}");
                return new MapCreaturesSummaryDTO();
            }
        }

        /// <summary>
        /// Get all animals on a map.
        /// </summary>
        public List<AnimalDTO> GetMapAnimals(int mapId)
        {
            var animals = new List<AnimalDTO>();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return animals;

                animals = map.mapPawns.AllPawns
                    .Where(p => p.RaceProps?.Animal == true)
                    .Select(p => new AnimalDTO
                    {
                        Id = p.thingIDNumber,
                        Name = p.LabelShortCap,
                        Def = p.def?.defName,
                        Faction = p.Faction?.ToString(),
                        Position = new PositionDTO
                        {
                            X = p.Position.x,
                            Y = p.Position.z  // Use Z for 2D position
                        },
                        Trainer = p.relations?.DirectRelations?
                            .Where(r => r.def == PawnRelationDefOf.Bond)
                            .Select(r => r.otherPawn?.thingIDNumber)
                            .FirstOrDefault(),
                        Pregnant = p.health?.hediffSet?.HasHediff(HediffDefOf.Pregnant) ?? false
                    })
                    .ToList();
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map animals: {ex.Message}");
            }

            return animals;
        }

        /// <summary>
        /// Get all haulable things on a map.
        /// </summary>
        public List<ThingDTO> GetMapThings(int mapId)
        {
            var things = new List<ThingDTO>();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return things;

                things = map.listerThings
                    .ThingsInGroup(ThingRequestGroup.HaulableEver)
                    .Select(t => ThingToDTO(t))
                    .ToList();
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map things: {ex.Message}");
            }

            return things;
        }

        /// <summary>
        /// Get all buildings on a map.
        /// </summary>
        public List<BuildingDTO> GetMapBuildings(int mapId)
        {
            var buildings = new List<BuildingDTO>();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return buildings;

                foreach (Building building in map.listerBuildings.allBuildingsColonist)
                {
                    buildings.Add(new BuildingDTO
                    {
                        Id = building.thingIDNumber,
                        Def = building.def?.defName,
                        Label = building.Label,
                        Position = new PositionDTO
                        {
                            X = building.Position.x,
                            Y = building.Position.y,
                            Z = building.Position.z
                        },
                        Type = building.GetType().Name
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map buildings: {ex.Message}");
            }

            return buildings;
        }

        /// <summary>
        /// Get all zones on a map.
        /// </summary>
        public List<ZoneDTO> GetMapZones(int mapId)
        {
            var zones = new List<ZoneDTO>();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return zones;

                foreach (Zone zone in map.zoneManager.AllZones)
                {
                    zones.Add(new ZoneDTO
                    {
                        Id = zone.ID,
                        CellsCount = zone.CellCount,
                        Label = zone.label,
                        BaseLabel = zone.BaseLabel,
                        Type = zone.GetType().Name
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map zones: {ex.Message}");
            }

            return zones;
        }

        /// <summary>
        /// Get all areas on a map.
        /// </summary>
        public List<ZoneDTO> GetMapAreas(int mapId)
        {
            var areas = new List<ZoneDTO>();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return areas;

                foreach (Area area in map.areaManager.AllAreas)
                {
                    areas.Add(new ZoneDTO
                    {
                        Id = area.ID,
                        CellsCount = area.ActiveCells.Count(),
                        Label = area.Label,
                        BaseLabel = area.Label,
                        Type = area.GetType().Name
                    });
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map areas: {ex.Message}");
            }

            return areas;
        }

        /// <summary>
        /// Get zones and areas combined for a map.
        /// </summary>
        public MapZonesDTO GetMapZonesAndAreas(int mapId)
        {
            return new MapZonesDTO
            {
                Zones = GetMapZones(mapId),
                Areas = GetMapAreas(mapId)
            };
        }

        /// <summary>
        /// Get all rooms on a map.
        /// </summary>
        public MapRoomsDTO GetMapRooms(int mapId)
        {
            var mapRooms = new MapRoomsDTO();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return mapRooms;

                // Access rooms through region grid
                var allRooms = map.regionGrid.AllRooms;

                mapRooms.Rooms = allRooms
                    .Select(r => new RoomDTO
                    {
                        Id = r.ID,
                        RoleLabel = r.GetRoomRoleLabel(),
                        Temperature = r.Temperature,
                        CellsCount = r.CellCount,
                        TouchesMapEdge = r.TouchesMapEdge,
                        IsPrisonCell = r.IsPrisonCell,
                        IsDoorway = r.IsDoorway,
                        ContainedBedsIds = r.ContainedBeds?.Select(b => b.thingIDNumber).ToList() ?? new List<int>(),
                        OpenRoofCount = r.OpenRoofCount
                    })
                    .ToList();
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting map rooms: {ex.Message}");
            }

            return mapRooms;
        }

        /// <summary>
        /// Get power grid information for a map.
        /// </summary>
        public MapPowerInfoDTO GetMapPowerInfo(int mapId)
        {
            var powerInfo = new MapPowerInfoDTO();

            try
            {
                var map = GetMapByID(mapId);
                if (map == null) return powerInfo;

                foreach (Building building in map.listerBuildings.allBuildingsColonist)
                {
                    // Check if building is a Power Generator
                    CompPowerPlant powerPlant = building.TryGetComp<CompPowerPlant>();
                    if (powerPlant != null)
                    {
                        powerInfo.TotalPossiblePower += Mathf.RoundToInt(
                            Mathf.Abs(powerPlant.Props.PowerConsumption));
                        powerInfo.CurrentPower += Mathf.RoundToInt(powerPlant.PowerOutput);
                        powerInfo.ProducePowerBuildings.Add(building.thingIDNumber);
                        continue;
                    }

                    // Check if building is a Battery
                    CompPowerBattery powerBattery = building.TryGetComp<CompPowerBattery>();
                    if (powerBattery != null)
                    {
                        powerInfo.CurrentlyStoredPower += Mathf.RoundToInt(powerBattery.StoredEnergy);
                        powerInfo.TotalPowerStorage += Mathf.RoundToInt(powerBattery.Props.storedEnergyMax);
                        powerInfo.StorePowerBuildings.Add(building.thingIDNumber);
                    }
                }

                // Calculate power consumption
                foreach (PowerNet net in map.powerNetManager.AllNetsListForReading)
                {
                    foreach (CompPowerTrader comp in net.powerComps)
                    {
                        if (comp.Props.PowerConsumption > 0f)
                        {
                            powerInfo.TotalConsumption += Mathf.RoundToInt(comp.Props.PowerConsumption);
                        }
                        if (comp.PowerOn && comp.PowerOutput < 0f)
                        {
                            powerInfo.ConsumptionPowerOn += Mathf.RoundToInt(Mathf.Abs(comp.PowerOutput));
                        }

                        Building building = comp.parent as Building;
                        if (building != null)
                        {
                            powerInfo.ConsumePowerBuildings.Add(building.thingIDNumber);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting power info: {ex.Message}");
            }

            return powerInfo;
        }

        /// <summary>
        /// Convert a Thing to DTO.
        /// </summary>
        private ThingDTO ThingToDTO(Thing thing)
        {
            var dto = new ThingDTO
            {
                ThingId = thing.thingIDNumber,
                DefName = thing.def?.defName,
                Label = thing.Label,
                Categories = thing.def?.thingCategories?.Select(c => c.defName).ToList() ?? new List<string>(),
                Position = new PositionDTO
                {
                    X = thing.Position.x,
                    Y = thing.Position.y,
                    Z = thing.Position.z
                },
                StackCount = thing.stackCount,
                MarketValue = thing.MarketValue,
                IsForbidden = thing.IsForbidden(Faction.OfPlayer),
                Quality = -1
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
