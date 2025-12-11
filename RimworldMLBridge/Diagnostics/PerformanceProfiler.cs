using System;
using System.Diagnostics;
using System.Text;
using Verse;

namespace RimworldMLBridge.Diagnostics
{
    /// <summary>
    /// Performance profiler for Phase V state extraction.
    /// Measures time taken for map, incident, and world data extraction.
    /// </summary>
    public static class PerformanceProfiler
    {
        private static readonly Stopwatch _stopwatch = new Stopwatch();
        private static PerformanceStats _lastStats = new PerformanceStats();
        
        /// <summary>
        /// Performance statistics for a single state extraction cycle.
        /// </summary>
        public class PerformanceStats
        {
            public long MapExtractionMs { get; set; }
            public long IncidentExtractionMs { get; set; }
            public long WorldExtractionMs { get; set; }
            public long TotalExtractionMs { get; set; }
            public long SerializationMs { get; set; }
            public long TotalCycleMs { get; set; }
            
            // Data complexity metrics
            public int BuildingCount { get; set; }
            public int ItemCount { get; set; }
            public int IncidentCount { get; set; }
            public int FactionCount { get; set; }
            public int SettlementCount { get; set; }
            
            // Size metrics
            public int SerializedSizeBytes { get; set; }
            
            public override string ToString()
            {
                var sb = new StringBuilder();
                sb.AppendLine("=== Phase V Performance Stats ===");
                sb.AppendLine($"Map Extraction:      {MapExtractionMs,5} ms ({BuildingCount} buildings, {ItemCount} items)");
                sb.AppendLine($"Incident Extraction: {IncidentExtractionMs,5} ms ({IncidentCount} incidents)");
                sb.AppendLine($"World Extraction:    {WorldExtractionMs,5} ms ({FactionCount} factions, {SettlementCount} settlements)");
                sb.AppendLine($"Total Extraction:    {TotalExtractionMs,5} ms");
                sb.AppendLine($"Serialization:       {SerializationMs,5} ms");
                sb.AppendLine($"Total Cycle:         {TotalCycleMs,5} ms");
                sb.AppendLine($"Serialized Size:     {SerializedSizeBytes,7} bytes ({SerializedSizeBytes / 1024.0:F1} KB)");
                
                // Performance assessment
                if (TotalExtractionMs <= 5)
                {
                    sb.AppendLine("✓ EXCELLENT: Extraction time <= 5ms target");
                }
                else if (TotalExtractionMs <= 10)
                {
                    sb.AppendLine("⚠ GOOD: Extraction time within acceptable range");
                }
                else
                {
                    sb.AppendLine("✗ NEEDS OPTIMIZATION: Extraction time exceeds 10ms");
                }
                
                return sb.ToString();
            }
        }
        
        /// <summary>
        /// Start timing for map extraction.
        /// </summary>
        public static void StartMapExtraction()
        {
            _stopwatch.Restart();
        }
        
        /// <summary>
        /// End timing for map extraction and record duration.
        /// </summary>
        public static void EndMapExtraction(int buildingCount, int itemCount)
        {
            _lastStats.MapExtractionMs = _stopwatch.ElapsedMilliseconds;
            _lastStats.BuildingCount = buildingCount;
            _lastStats.ItemCount = itemCount;
        }
        
        /// <summary>
        /// Start timing for incident extraction.
        /// </summary>
        public static void StartIncidentExtraction()
        {
            _stopwatch.Restart();
        }
        
        /// <summary>
        /// End timing for incident extraction and record duration.
        /// </summary>
        public static void EndIncidentExtraction(int incidentCount)
        {
            _lastStats.IncidentExtractionMs = _stopwatch.ElapsedMilliseconds;
            _lastStats.IncidentCount = incidentCount;
        }
        
        /// <summary>
        /// Start timing for world extraction.
        /// </summary>
        public static void StartWorldExtraction()
        {
            _stopwatch.Restart();
        }
        
        /// <summary>
        /// End timing for world extraction and record duration.
        /// </summary>
        public static void EndWorldExtraction(int factionCount, int settlementCount)
        {
            _lastStats.WorldExtractionMs = _stopwatch.ElapsedMilliseconds;
            _lastStats.FactionCount = factionCount;
            _lastStats.SettlementCount = settlementCount;
        }
        
        /// <summary>
        /// Start timing for serialization.
        /// </summary>
        public static void StartSerialization()
        {
            _stopwatch.Restart();
        }
        
        /// <summary>
        /// End timing for serialization and record duration.
        /// </summary>
        public static void EndSerialization(int serializedSizeBytes)
        {
            _lastStats.SerializationMs = _stopwatch.ElapsedMilliseconds;
            _lastStats.SerializedSizeBytes = serializedSizeBytes;
        }
        
        /// <summary>
        /// Finalize stats calculation.
        /// </summary>
        public static void FinalizeStats(long totalCycleMs)
        {
            _lastStats.TotalExtractionMs = _lastStats.MapExtractionMs 
                + _lastStats.IncidentExtractionMs 
                + _lastStats.WorldExtractionMs;
            _lastStats.TotalCycleMs = totalCycleMs;
        }
        
        /// <summary>
        /// Get the last recorded performance stats.
        /// </summary>
        public static PerformanceStats GetLastStats()
        {
            return _lastStats;
        }
        
        /// <summary>
        /// Log performance stats to RimWorld log.
        /// </summary>
        public static void LogStats()
        {
            Log.Message($"[MLBridge:Performance] {_lastStats}");
        }
        
        /// <summary>
        /// Reset profiler state.
        /// </summary>
        public static void Reset()
        {
            _lastStats = new PerformanceStats();
            _stopwatch.Reset();
        }
    }
}
