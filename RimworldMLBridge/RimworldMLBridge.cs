using HarmonyLib;
using Verse;
using System;
using RimworldMLBridge.Services;

namespace RimworldMLBridge
{
    [StaticConstructorOnStartup]
    public static class MlBridgeMod
    {
        public static TcpProtobufServer Server;
        public static bool ServerRunning = false;
        public static int Port = 50051;

        // Phase III: Hybrid Valve - Execution mode control
        public static bool TrainingMode = true;  // Default to training mode (synchronous)
        public static bool StepPermitted = false; // In training mode, only advance when true
        public static int TicksToRun = 0;        // Number of ticks to run in current step

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
                var harmony = new Harmony("com.yourname.rimworldmlbridge");
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
    /// </summary>
    [HarmonyPatch(typeof(Root))]
    [HarmonyPatch("Update")]
    public static class Root_Update_Patch
    {
        static void Postfix()
        {
            if (MlBridgeMod.ServerRunning && MlBridgeMod.Server != null)
            {
                try
                {
                    MlBridgeMod.Server.ProcessCommands();
                }
                catch (Exception e)
                {
                    Log.Error("[MLBridge] Error processing commands: " + e.Message);
                }
            }
        }
    }
}