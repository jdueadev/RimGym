namespace RimTCP
{
    /// <summary>
    /// Centralized constants for RimWorld ML Bridge configuration.
    /// </summary>
    public static class Constants
    {
        // Network Configuration
        /// <summary>
        /// Default TCP port for the ML Bridge server.
        /// </summary>
        public const int DefaultPort = 50051;

        /// <summary>
        /// Default host address for the server.
        /// </summary>
        public const string DefaultHost = "0.0.0.0";

        // Connection Settings
        /// <summary>
        /// Heartbeat interval in seconds for client connection monitoring.
        /// </summary>
        public const int HeartbeatIntervalSeconds = 30;

        /// <summary>
        /// Maximum connection errors before client is disconnected.
        /// </summary>
        public const int MaxConnectionErrors = 10;

        /// <summary>
        /// Read timeout for socket operations in milliseconds.
        /// </summary>
        public const int SocketReadTimeoutMs = 1000;

        // Protocol Settings
        /// <summary>
        /// Size of the message length prefix in bytes (big-endian int32).
        /// </summary>
        public const int LengthPrefixSize = 4;

        /// <summary>
        /// Maximum message size in bytes (10 MB).
        /// </summary>
        public const int MaxMessageSize = 10 * 1024 * 1024;

        // Game Tick Settings
        /// <summary>
        /// Default number of ticks per second at normal game speed.
        /// </summary>
        public const int TicksPerSecond = 60;

        /// <summary>
        /// Default ticks to run per STEP command.
        /// </summary>
        public const int DefaultTicksPerStep = 60;

        // Logging
        /// <summary>
        /// Log prefix for all ML Bridge messages.
        /// </summary>
        public const string LogPrefix = "[MLBridge]";

        // Mod Identity
        /// <summary>
        /// Harmony ID for this mod.
        /// </summary>
        public const string HarmonyId = "com.jmduea.rimworldmlbridge";

        /// <summary>
        /// Current mod version.
        /// </summary>
        public const string Version = "0.5.0";
    }
}
