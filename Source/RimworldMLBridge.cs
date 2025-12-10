using HarmonyLib;
using Verse;
using System;
using System. Net;
using System.Net.Sockets;
using System.Text;
using System. Threading;
using JetBrains.Annotations;

namespace RimworldMLBridge
{
    [StaticConstructorOnStartup]
    public static class MlBridgeMod
    {
        public static TcpListener Server;
        public static TcpClient Client;
        public static NetworkStream Stream;
        public static bool Connected = false;
        public static bool ServerRunning = false;
        public static int Port = 9876;
        
        static MlBridgeMod()
        {
            Log.Message("[MLBridge] =================================");
            Log.Message("[MLBridge] Initializing ML Bridge.. .");
            
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
            
            // Start TCP server in background thread
            var serverThread = new Thread(StartServer);
            serverThread.IsBackground = true;
            serverThread.Start();
            
            Log.Message("[MLBridge] Server thread started");
            Log.Message("[MLBridge] Waiting for Python connection on port " + Port);
            Log.Message("[MLBridge] =================================");
        }
        
        static void StartServer()
        {
            try
            {
                Log.Message("[MLBridge] Starting TCP listener on port " + Port);
                Server = new TcpListener(IPAddress. Loopback, Port);
                Server. Start();
                ServerRunning = true;
                Log.Message("[MLBridge] TCP listener started, waiting for client.. .");
                
                Client = Server.AcceptTcpClient(); // Blocks until Python connects
                Stream = Client.GetStream();
                Connected = true;
                Log.Message("[MLBridge] Python agent connected successfully!");
            }
            catch (SocketException se)
            {
                Log.Error("[MLBridge] Socket error: " + se. SocketErrorCode + " - " + se.Message);
            }
            catch (Exception e)
            {
                Log. Error("[MLBridge] Server error: " + e.GetType().Name + " - " + e. Message);
                Log.Error("[MLBridge] Stack trace:  " + e. StackTrace);
            }
        }
        
        public static void SendMessage(string message)
        {
            if (! Connected) return;
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message + "\n");
                Stream.Write(data, 0, data.Length);
            }
            catch (Exception e)
            {
                Log. Error("[MLBridge] Send error: " + e.Message);
                Connected = false;
            }
        }
        
        public static string ReceiveMessage()
        {
            if (!Connected) return null;
            try
            {
                byte[] buffer = new byte[1024];
                int bytesRead = Stream.Read(buffer, 0, buffer. Length);
                return Encoding.UTF8.GetString(buffer, 0, bytesRead).Trim();
            }
            catch (Exception e)
            {
                Log.Error("[MLBridge] Receive error: " + e.Message);
                Connected = false;
                return null;
            }
        }
    }
}