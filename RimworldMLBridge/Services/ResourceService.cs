using System;
using System.Collections.Generic;
using System.Linq;
using RimworldMLBridge.DTOs;
using RimWorld;
using Verse;

namespace RimworldMLBridge.Services
{
    /// <summary>
    /// Service for extracting resource/item data from RimWorld.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// Returns raw C# DTOs for efficient Protobuf serialization.
    /// </summary>
    public class ResourceService
    {
        private readonly MapService _mapService = new MapService();

        /// <summary>
        /// Get a summary of all resources on a map.
        /// </summary>
        public ResourcesSummaryDTO GetResourcesSummary(int mapId)
        {
            try
            {
                var map = MapService.GetMapByID(mapId);
                if (map == null) return new ResourcesSummaryDTO();

                var allItems = map.listerThings.AllThings
                    .Where(t => t.def.EverStorable(false))
                    .ToList();

                var summary = new ResourcesSummaryDTO
                {
                    TotalItems = allItems.Count,
                    TotalMarketValue = allItems.Sum(t => t.MarketValue * t.stackCount),
                    LastUpdated = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    Categories = GetResourcesCategorizedList(map),
                    CriticalResources = AnalyzeCriticalResources(map, allItems)
                };

                return summary;
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting resources summary: {ex.Message}");
                return new ResourcesSummaryDTO();
            }
        }

        /// <summary>
        /// Get storage utilization summary for a map.
        /// </summary>
        public StoragesSummaryDTO GetStoragesSummary(int mapId)
        {
            var analysis = new StoragesSummaryDTO();

            try
            {
                var map = MapService.GetMapByID(mapId);
                if (map == null) return analysis;

                var stockpiles = map.zoneManager.AllZones.OfType<Zone_Stockpile>().ToList();
                analysis.TotalStockpiles = stockpiles.Count;
                analysis.TotalCells = stockpiles.Sum(z => z.CellCount);
                analysis.UsedCells = stockpiles.Sum(z =>
                    z.Cells.Count(c => c.GetItemCount(map) > 0));

                if (analysis.TotalCells > 0)
                {
                    analysis.UtilizationPercent = (int)(
                        (double)analysis.UsedCells / analysis.TotalCells * 100);
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting storage summary: {ex.Message}");
            }

            return analysis;
        }

        /// <summary>
        /// Get all stored resources grouped by category.
        /// </summary>
        public Dictionary<string, List<ThingDTO>> GetAllStoredResources(int mapId)
        {
            var itemsByCategory = new Dictionary<string, List<ThingDTO>>();

            try
            {
                var map = MapService.GetMapByID(mapId);
                if (map == null) return itemsByCategory;

                var items = GetItemsFromStorageLocations(map);

                foreach (var thing in items)
                {
                    var category = GetPrimaryCategoryForThing(thing.def);
                    if (category == null) continue;

                    var categoryLabel = category.defName;

                    if (!itemsByCategory.TryGetValue(categoryLabel, out var categoryList))
                    {
                        categoryList = new List<ThingDTO>();
                        itemsByCategory[categoryLabel] = categoryList;
                    }

                    categoryList.Add(ThingToDTO(thing));
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting stored resources: {ex.Message}");
            }

            return itemsByCategory;
        }

        /// <summary>
        /// Get stored resources by a specific category.
        /// </summary>
        public List<ThingDTO> GetStoredResourcesByCategory(int mapId, string categoryDef)
        {
            var items = new List<ThingDTO>();

            try
            {
                var map = MapService.GetMapByID(mapId);
                if (map == null) return items;

                var allItems = GetItemsFromStorageLocations(map);

                foreach (var thing in allItems)
                {
                    if (!IsThingInCategory(thing, categoryDef)) continue;
                    items.Add(ThingToDTO(thing));
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting resources by category: {ex.Message}");
            }

            return items;
        }

        /// <summary>
        /// Analyze critical resources (food, medicine, weapons).
        /// </summary>
        private CriticalResourcesDTO AnalyzeCriticalResources(Map map, List<Thing> allItems)
        {
            var critical = new CriticalResourcesDTO();

            try
            {
                // Food analysis
                critical.FoodSummary = GetResourcesFoodSummary(map, allItems);

                // Medicine analysis
                var medicineItems = allItems.Where(t => t.def.IsMedicine).ToList();
                critical.MedicineTotal = medicineItems.Sum(t => t.stackCount);

                // Weapon analysis
                var weapons = allItems.Where(t => t.def.IsWeapon).ToList();
                critical.WeaponCount = weapons.Count;
                critical.WeaponValue = weapons.Sum(t => t.MarketValue);
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error analyzing critical resources: {ex.Message}");
            }

            return critical;
        }

        /// <summary>
        /// Get food resources summary.
        /// </summary>
        private ResourcesFoodSummaryDTO GetResourcesFoodSummary(Map map, List<Thing> allItems)
        {
            try
            {
                var foodItems = allItems.Where(t => t.def.IsNutritionGivingIngestible).ToList();

                return new ResourcesFoodSummaryDTO
                {
                    FoodTotal = foodItems.Sum(t => t.stackCount),
                    TotalNutrition = map.resourceCounter.TotalHumanEdibleNutrition,
                    MealsCount = allItems.Count(t =>
                        t.def.IsNutritionGivingIngestible && t.def.ingestible?.IsMeal == true),
                    RawFoodCount = allItems.Count(t =>
                        t.def.IsNutritionGivingIngestible && t.def.ingestible?.IsMeal != true)
                };
            }
            catch
            {
                return new ResourcesFoodSummaryDTO();
            }
        }

        /// <summary>
        /// Get resources categorized list.
        /// </summary>
        private List<ResourceCategoryDTO> GetResourcesCategorizedList(Map map)
        {
            var categories = new List<ResourceCategoryDTO>();

            try
            {
                var categoryData = new Dictionary<ThingCategoryDef, (int count, double value)>();

                var rootCategories = DefDatabase<ThingCategoryDef>.AllDefs
                    .Where(cat => cat.resourceReadoutRoot);

                foreach (var category in rootCategories)
                {
                    int count = map.resourceCounter.GetCountIn(category);
                    double marketValue = 0.0;

                    foreach (var kvp in map.resourceCounter.AllCountedAmounts)
                    {
                        ThingDef thingDef = kvp.Key;
                        int thingCount = kvp.Value;

                        if (thingCount > 0 && category.ContainedInThisOrDescendant(thingDef))
                        {
                            marketValue += thingDef.BaseMarketValue * thingCount;
                        }
                    }

                    if (count > 0)
                    {
                        categoryData[category] = (count, marketValue);
                    }
                }

                categories = categoryData
                    .Select(kvp => new ResourceCategoryDTO
                    {
                        Category = kvp.Key.LabelCap,
                        Count = kvp.Value.count,
                        MarketValue = kvp.Value.value
                    })
                    .ToList();
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error categorizing resources: {ex.Message}");
            }

            return categories;
        }

        /// <summary>
        /// Get items from all storage locations (stockpiles, shelves, etc).
        /// </summary>
        private List<Thing> GetItemsFromStorageLocations(Map map)
        {
            var things = new List<Thing>();

            try
            {
                // Items from buildings (shelves, bookcases, etc)
                foreach (var building in map.listerBuildings.allBuildingsColonist)
                {
                    // ISlotGroupParent buildings (shelves, hoppers)
                    ISlotGroupParent storage = building as ISlotGroupParent;
                    if (storage != null)
                    {
                        var slotGroup = storage.GetSlotGroup();
                        if (slotGroup != null)
                        {
                            things.AddRange(slotGroup.HeldThings);
                        }
                        continue;
                    }

                    // IThingHolder buildings (bookcases)
                    IThingHolder holder = building as IThingHolder;
                    if (holder != null)
                    {
                        things.AddRange(holder.GetDirectlyHeldThings());
                    }
                }

                // Items from stockpile zones
                foreach (var zone in map.zoneManager.AllZones)
                {
                    Zone_Stockpile stockpile = zone as Zone_Stockpile;
                    if (stockpile != null)
                    {
                        things.AddRange(stockpile.AllContainedThings);
                    }
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[MLBridge] Error getting items from storage: {ex.Message}");
            }

            return things;
        }

        /// <summary>
        /// Get the primary category for a thing definition.
        /// </summary>
        private ThingCategoryDef GetPrimaryCategoryForThing(ThingDef thingDef)
        {
            if (thingDef?.thingCategories != null && thingDef.thingCategories.Count > 0)
            {
                return thingDef.thingCategories[0];
            }
            return null;
        }

        /// <summary>
        /// Check if a thing belongs to a specific category.
        /// </summary>
        private bool IsThingInCategory(Thing thing, string categoryDef)
        {
            var categories = thing.def.thingCategories;
            return categories != null && categories.Any(c => 
                c.defName.Equals(categoryDef, StringComparison.OrdinalIgnoreCase));
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
