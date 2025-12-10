using HarmonyLib;
using Verse;
using System;
using System.Threading.Tasks;
using Grpc.Core;
using RimworldMLBridge.Protos;

namespace RimworldMLBridge
{
    [StaticConstructorOnStartup]
    public static class MlBridgeMod
    {
        public static Server GrpcServer;
        public static bool ServerRunning = false;
        public static int Port = 50051; // Standard gRPC port
        
        static MlBridgeMod()
        {
            Log.Message("[MLBridge] =================================");
            Log.Message("[MLBridge] Initializing ML Bridge with gRPC...");
            
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
                return;
            }
            
            // Start gRPC server
            try
            {
                StartGrpcServer();
            }
            catch (Exception e)
            {
                Log.Error("[MLBridge] Failed to start gRPC server: " + e.Message);
                Log.Error("[MLBridge] Stack trace: " + e.StackTrace);
            }
            
            Log.Message("[MLBridge] =================================");
        }
        
        static void StartGrpcServer()
        {
            Log.Message("[MLBridge] Starting gRPC server on port " + Port);
            
            GrpcServer = new Server
            {
                Services = { MLBridge.BindService(new MLBridgeService()) },
                Ports = { new ServerPort("localhost", Port, ServerCredentials.Insecure) }
            };
            
            GrpcServer.Start();
            ServerRunning = true;
            
            Log.Message("[MLBridge] gRPC server started successfully!");
            Log.Message("[MLBridge] Listening on localhost:" + Port);
            Log.Message("[MLBridge] Ready for Python gRPC client connections");
        }
        
        public static void StopServer()
        {
            if (GrpcServer != null && ServerRunning)
            {
                try
                {
                    Log.Message("[MLBridge] Shutting down gRPC server...");
                    GrpcServer.ShutdownAsync().Wait();
                    ServerRunning = false;
                    Log.Message("[MLBridge] gRPC server stopped");
                }
                catch (Exception e)
                {
                    Log.Error("[MLBridge] Error stopping server: " + e.Message);
                }
            }
        }
    }
}