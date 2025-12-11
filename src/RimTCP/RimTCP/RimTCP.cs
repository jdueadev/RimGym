using System;
using HarmonyLib;
using RimTCP.Services;
using Verse;

namespace RimTCP
{
    [StaticConstructorOnStartup]
    public static class MlBridgeMod
    {
        public static TcpProtobufServer Server;
        public static bool ServerRunning = false;
        public static int Port = 50051;

        // Phase III: Hybrid Valve - Execution mode control
        public static bool TrainingMode = true; // Default to training mode (synchronous)
        public static bool StepPermitted = false; // In training mode, only advance when true
        public static int TicksToRun = 0; // Number of ticks to run in current step

        static MlBridgeMod()
        {
            Log.Message("[MLBridge] =================================");
            Log.Message("[MLBridge] Initializing ML Bridge with TCP+Protobuf...");

            try
            {
                // Initialize ServiceRegistry for data extraction services
                ServiceRegistry.Initialize();
                Log.Message("[MLBridge] Service registry initialized");
            }
            catch (Exception e)
            {
                Log.Error("[MLBridge] ServiceRegistry initialization failed: " + e.Message);
            }

            try
            {
                // Apply Harmony patches
                var harmony = new Harmony("com.jmduea.rimworldmlbridge");
                harmony.PatchAll();
                Log.Message("[MLBridge] Harmony patches applied successfully");
            }
            catch (Exception e)
            {
                Log.Error("[MLBridge] Harmony patch failed: " + e.Message);
                Log.Error("[MLBridge] Stack trace: " + e.StackTrace);
            }

            // Start TCP server
            try
            {
                Server = new TcpProtobufServer(Port);
                Server.Start();
                ServerRunning = true;
                Log.Message("[MLBridge] TCP+Protobuf server started successfully!");
                Log.Message("[MLBridge] Listening on localhost:" + Port);
                Log.Message("[MLBridge] Ready for Python client connections");
            }
            catch (Exception e)
            {
                Log.Error("[MLBridge] Failed to start TCP server: " + e.Message);
                Log.Error("[MLBridge] Stack trace: " + e.StackTrace);
            }

            Log.Message("[MLBridge] =================================");
        }

        public static void StopServer()
        {
            if (Server != null && ServerRunning)
            {
                try
                {
                    Log.Message("[MLBridge] Shutting down TCP server...");
                    Server.Stop();
                    ServerRunning = false;
                    Log.Message("[MLBridge] TCP server stopped");
                }
                catch (Exception e)
                {
                    Log.Error("[MLBridge] Error stopping server: " + e.Message);
                }
            }
        }
    }

    /// <summary>
    /// Harmony patch to process TCP commands on the main Unity thread.
    /// Commands are queued from the TCP background thread and processed here to avoid threading issues.
    /// TASK-013: Error boundary prevents mod exceptions from crashing RimWorld main loop.
    /// </summary>
    [HarmonyPatch(typeof(Root))]
    [HarmonyPatch("Update")]
    public static class Root_Update_Patch
    {
        private static int _consecutiveErrors = 0;
        private const int MaxConsecutiveErrors = 10;

        static void Postfix()
        {
            if (MlBridgeMod.ServerRunning && MlBridgeMod.Server != null)
            {
                try
                {
                    // Process queued commands from TCP client
                    MlBridgeMod.Server.ProcessCommands();

                    // TASK-008: Heartbeat for server health monitoring
                    MlBridgeMod.Server.Heartbeat();

                    // Reset error counter on successful execution
                    _consecutiveErrors = 0;
                }
                catch (Exception e)
                {
                    _consecutiveErrors++;

                    // Log error with context
                    Log.Error(
                        $"[MLBridge] Error in main loop (count={_consecutiveErrors}): {e.Message}"
                    );

                    // If too many consecutive errors, disable to prevent game instability
                    if (_consecutiveErrors >= MaxConsecutiveErrors)
                    {
                        Log.Error(
                            $"[MLBridge] Too many consecutive errors ({MaxConsecutiveErrors}), disabling server to protect game stability"
                        );
                        try
                        {
                            MlBridgeMod.StopServer();
                        }
                        catch
                        {
                            // Swallow any shutdown errors
                        }
                    }
                }
            }
        }
    }
}
