using HarmonyLib;
using Verse;

namespace RimworldMLBridge
{
    [HarmonyPatch(typeof(TickManager), "DoSingleTick")]
    public static class TickManagerPatch
    {
        private static int tickCount = 0;
        private static int _reportEveryNTicks = 250; // ~1 in-game hour at normal speed

        public static void Postfix(TickManager __instance)
        {
            if (!MlBridgeMod.ServerRunning) return;

            tickCount++;
            // not time to report yet
            if (tickCount % _reportEveryNTicks != 0) return;

            // Log tick update (gRPC clients will poll via GetState or use streaming in future)
            Log.Message($"[MLBridge] Tick: {tickCount} (Frame: {Find.TickManager.TicksAbs})");
        }
    }
}