using System;
using RimTCP.DTOs;
using Verse;

namespace RimTCP.Services
{
    /// <summary>
    /// Central registry for managing service instances.
    /// Provides singleton access to all data extraction services.
    /// Thread-safe for main thread access during game state queries.
    /// </summary>
    public static class ServiceRegistry
    {
        private static ColonistService _colonistService;
        private static MapService _mapService;
        private static ResourceService _resourceService;
        private static IncidentService _incidentService;
        private static readonly object _lock = new object();
        private static bool _initialized = false;

        /// <summary>
        /// Initialize all services. Call from main thread during mod startup.
        /// </summary>
        public static void Initialize()
        {
            lock (_lock)
            {
                if (_initialized)
                    return;

                try
                {
                    _colonistService = new ColonistService();
                    _mapService = new MapService();
                    _resourceService = new ResourceService();
                    _incidentService = new IncidentService();
                    _initialized = true;

                    Log.Message($"{Constants.LogPrefix} ServiceRegistry initialized successfully");
                }
                catch (Exception ex)
                {
                    Log.Error(
                        $"{Constants.LogPrefix} Failed to initialize ServiceRegistry: {ex.Message}"
                    );
                }
            }
        }

        /// <summary>
        /// Get the ColonistService instance.
        /// </summary>
        public static ColonistService Colonists
        {
            get
            {
                EnsureInitialized();
                return _colonistService;
            }
        }

        /// <summary>
        /// Get the MapService instance.
        /// </summary>
        public static MapService Maps
        {
            get
            {
                EnsureInitialized();
                return _mapService;
            }
        }

        /// <summary>
        /// Get the ResourceService instance.
        /// </summary>
        public static ResourceService Resources
        {
            get
            {
                EnsureInitialized();
                return _resourceService;
            }
        }

        /// <summary>
        /// Get the IncidentService instance.
        /// </summary>
        public static IncidentService Incidents
        {
            get
            {
                EnsureInitialized();
                return _incidentService;
            }
        }

        /// <summary>
        /// Ensure services are initialized before access.
        /// </summary>
        private static void EnsureInitialized()
        {
            if (!_initialized)
            {
                Initialize();
            }
        }

        /// <summary>
        /// Check if the game is in a valid state for data extraction.
        /// </summary>
        public static bool IsGameReady()
        {
            return Current.Game != null && Find.CurrentMap != null;
        }

        /// <summary>
        /// Get the current map ID, or -1 if no map is loaded.
        /// </summary>
        public static int GetCurrentMapId()
        {
            return Find.CurrentMap?.uniqueID ?? -1;
        }

        /// <summary>
        /// Extract comprehensive game state using all services.
        /// This is the main entry point for RimTCP to query game state.
        /// MUST be called from the main thread.
        /// </summary>
        public static GameStateDTO GetFullGameState()
        {
            var state = new GameStateDTO();

            if (!IsGameReady())
            {
                state.IsReady = false;
                state.StatusMessage = "Game not loaded";
                return state;
            }

            try
            {
                var mapId = GetCurrentMapId();

                // Populate colonists
                state.Colonists = Colonists.GetColonists();
                state.ColonistsDetailed = Colonists.GetColonistsDetailed();

                // Populate map info
                state.Maps = Maps.GetMaps();
                state.CurrentMapId = mapId;
                state.Weather = Maps.GetWeather(mapId);
                state.CreaturesSummary = Maps.GetMapCreaturesSummary(mapId);

                // Populate resources
                state.ResourcesSummary = Resources.GetResourcesSummary(mapId);
                state.StoragesSummary = Resources.GetStoragesSummary(mapId);

                // Populate incidents and threats
                state.IncidentState = Incidents.GetIncidentState(mapId);
                state.ThreatSummary = Incidents.GetThreatSummary(mapId);

                state.IsReady = true;
                state.StatusMessage = "State extracted successfully";
                state.Timestamp = DateTime.Now;
                state.TickCount = Find.TickManager?.TicksAbs ?? 0;
            }
            catch (Exception ex)
            {
                Log.Warning($"{Constants.LogPrefix} Error extracting game state: {ex.Message}");
                state.IsReady = false;
                state.StatusMessage = $"Error: {ex.Message}";
            }

            return state;
        }

        /// <summary>
        /// Reset services (e.g., when loading a new game).
        /// </summary>
        public static void Reset()
        {
            lock (_lock)
            {
                _initialized = false;
                _colonistService = null;
                _mapService = null;
                _resourceService = null;
                _incidentService = null;
            }
        }
    }

    /// <summary>
    /// Comprehensive game state DTO containing all extracted data.
    /// Used as the main response type for full state queries.
    /// </summary>
    public class GameStateDTO
    {
        // Status
        public bool IsReady { get; set; }
        public string StatusMessage { get; set; }
        public DateTime Timestamp { get; set; }
        public long TickCount { get; set; }

        // Map info
        public int CurrentMapId { get; set; }
        public System.Collections.Generic.List<MapDTO> Maps { get; set; } =
            new System.Collections.Generic.List<MapDTO>();
        public MapWeatherDTO Weather { get; set; }
        public MapCreaturesSummaryDTO CreaturesSummary { get; set; }

        // Colonists
        public System.Collections.Generic.List<ColonistDTO> Colonists { get; set; } =
            new System.Collections.Generic.List<ColonistDTO>();
        public System.Collections.Generic.List<ColonistDetailedDTO> ColonistsDetailed { get; set; } =
            new System.Collections.Generic.List<ColonistDetailedDTO>();

        // Resources
        public ResourcesSummaryDTO ResourcesSummary { get; set; }
        public StoragesSummaryDTO StoragesSummary { get; set; }

        // Incidents and Threats
        public IncidentStateDTO IncidentState { get; set; }
        public ThreatSummaryDTO ThreatSummary { get; set; }
    }
}
