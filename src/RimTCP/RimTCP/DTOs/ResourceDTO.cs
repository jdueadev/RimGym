using System.Collections.Generic;

namespace RimTCP.DTOs
{
    /// <summary>
    /// Summary of all resources on a map.
    /// Ported from RIMAPI - stripped of HTTP/JSON dependencies.
    /// </summary>
    public class ResourcesSummaryDTO
    {
        public int TotalItems { get; set; }
        public double TotalMarketValue { get; set; }
        public string LastUpdated { get; set; }
        public List<ResourceCategoryDTO> Categories { get; set; } = new List<ResourceCategoryDTO>();
        public CriticalResourcesDTO CriticalResources { get; set; }
    }

    /// <summary>
    /// Resource category with count and value.
    /// </summary>
    public class ResourceCategoryDTO
    {
        public string Category { get; set; }
        public int Count { get; set; }
        public double MarketValue { get; set; }
    }

    /// <summary>
    /// Critical resources analysis (food, medicine, weapons).
    /// </summary>
    public class CriticalResourcesDTO
    {
        public ResourcesFoodSummaryDTO FoodSummary { get; set; }
        public int MedicineTotal { get; set; }
        public int WeaponCount { get; set; }
        public float WeaponValue { get; set; }
    }

    /// <summary>
    /// Detailed food resources summary.
    /// </summary>
    public class ResourcesFoodSummaryDTO
    {
        public int FoodTotal { get; set; }
        public float TotalNutrition { get; set; }
        public int MealsCount { get; set; }
        public int RawFoodCount { get; set; }
    }

    /// <summary>
    /// Storage utilization summary.
    /// </summary>
    public class StoragesSummaryDTO
    {
        public int TotalStockpiles { get; set; }
        public int TotalCells { get; set; }
        public int UsedCells { get; set; }
        public int UtilizationPercent { get; set; }
    }
}
