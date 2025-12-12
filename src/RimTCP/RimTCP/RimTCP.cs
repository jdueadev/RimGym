using System;
using HarmonyLib;
using RimTCP.Services;
using Verse;

namespace RimTCP
{
    [StaticConstructorOnStartup]
    public static class RimTcpMod
    {
        public static TcpProtobufServer Server;
        public static bool ServerRunning = false;
        public static int Port = 50051;

        // Phase III: Hybrid Valve - Execution mode control
        public static bool TrainingMode = true; // Default to training mode (synchronous)
        public static bool StepPermitted = false; // In training mode, only advance when true
        public static int TicksToRun = 0; // Number of ticks to run in current step

        static RimTcpMod()
        {
            Log.Message($"{Constants.LogPrefix} =================================");
            Log.Message($"{Constants.LogPrefix} Initializing RimTCP with TCP+Protobuf...");

            try
            {
                // Initialize ServiceRegistry for data extraction services
                ServiceRegistry.Initialize();
                Log.Message($"{Constants.LogPrefix} Service registry initialized");
            }
            catch (Exception e)
            {
                Log.Error(
                    $"{Constants.LogPrefix} ServiceRegistry initialization failed: {e.Message}"
                );
            }

            try
            {
                // Apply Harmony patches
                var harmony = new Harmony(Constants.HarmonyId);
                harmony.PatchAll();
                Log.Message($"{Constants.LogPrefix} Harmony patches applied successfully");
            }
            catch (Exception e)
            {
                Log.Error($"{Constants.LogPrefix} Harmony patch failed: {e.Message}");
                Log.Error($"{Constants.LogPrefix} Stack trace: {e.StackTrace}");
            }

            // Start TCP server
            try
            {
                Server = new TcpProtobufServer(Port);
                Server.Start();
                ServerRunning = true;
                Log.Message($"{Constants.LogPrefix} TCP+Protobuf server started successfully!");
                Log.Message($"{Constants.LogPrefix} Listening on port {Port}");
                Log.Message($"{Constants.LogPrefix} Ready for Python client connections");
            }
            catch (Exception e)
            {
                Log.Error($"{Constants.LogPrefix} Failed to start TCP server: {e.Message}");
                Log.Error($"{Constants.LogPrefix} Stack trace: {e.StackTrace}");
            }

            Log.Message($"{Constants.LogPrefix} =================================");
        }

        public static void StopServer()
        {
            if (Server != null && ServerRunning)
            {
                try
                {
                    Log.Message($"{Constants.LogPrefix} Shutting down TCP server...");
                    Server.Stop();
                    ServerRunning = false;
                    Log.Message($"{Constants.LogPrefix} TCP server stopped");
                }
                catch (Exception e)
                {
                    Log.Error($"{Constants.LogPrefix} Error stopping server: {e.Message}");
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
            if (RimTcpMod.ServerRunning && RimTcpMod.Server != null)
            {
                try
                {
                    // Process queued commands from TCP client
                    RimTcpMod.Server.ProcessCommands();

                    // TASK-008: Heartbeat for server health monitoring
                    RimTcpMod.Server.Heartbeat();

                    // Reset error counter on successful execution
                    _consecutiveErrors = 0;
                }
                catch (Exception e)
                {
                    _consecutiveErrors++;

                    // Log error with context
                    Log.Error(
                        $"{Constants.LogPrefix} Error in main loop (count={_consecutiveErrors}): {e.Message}"
                    );

                    // If too many consecutive errors, disable to prevent game instability
                    if (_consecutiveErrors >= MaxConsecutiveErrors)
                    {
                        Log.Error(
                            $"{Constants.LogPrefix} Too many consecutive errors ({MaxConsecutiveErrors}), disabling server to protect game stability"
                        );
                        try
                        {
                            RimTcpMod.StopServer();
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
