using HarmonyLib;
using Verse;

namespace RimworldMLBridge
{
    [HarmonyPatch(typeof(TickManager), "DoSingleTick")]
    public static class TickManagerPatch
    {
        private static int tickCount = 0;
        private static int reportEveryNTicks = 250; // ~1 in-game hour at normal speed

        public static void Postfix(TickManager __instance)
        {
            if (!MlBridgeMod.Connected) return;

            tickCount++;
            // not time to report yet
            if (tickCount % reportEveryNTicks != 0) return;
            // Send current tick to Python
            MlBridgeMod.SendMessage($"TICK:{tickCount}");
            // Wait for pytrhon to acknowledge (blocking!)
            var response = MlBridgeMod.ReceiveMessage();

            if (response != null)
            {
                Log.Message($"[MLBridge] Python said: {response}");
            }
        }

    }
}