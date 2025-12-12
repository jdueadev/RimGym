using HarmonyLib;
using Verse;

namespace RimTCP
{
    /// <summary>
    /// Phase III: Hybrid Valve Tick Control
    ///
    /// Training Mode (Synchronous):
    ///   - Prefix returns false to block tick unless StepPermitted is true
    ///   - Game pauses between steps, only advances on explicit STEP command
    ///
    /// Inference Mode (Asynchronous):
    ///   - Prefix returns true to allow normal game flow
    ///   - Agent queries state without blocking game
    /// </summary>
    [HarmonyPatch(typeof(TickManager), "DoSingleTick")]
    public static class TickManagerPatch
    {
        private static int tickCount = 0;
        private static int _reportEveryNTicks = 250; // ~1 in-game hour at normal speed

        /// <summary>
        /// Prefix: Controls whether the tick should execute
        /// </summary>
        public static bool Prefix(TickManager __instance)
        {
            if (!RimTcpMod.ServerRunning)
                return true; // Let game run normally if server not active

            // Inference Mode (Asynchronous): Always allow ticks
            if (!RimTcpMod.TrainingMode)
            {
                return true;
            }

            // Training Mode (Synchronous): Only allow tick if step permitted
            if (RimTcpMod.StepPermitted && RimTcpMod.TicksToRun > 0)
            {
                RimTcpMod.TicksToRun--;

                // If this was the last tick in the step, revoke permission
                if (RimTcpMod.TicksToRun == 0)
                {
                    RimTcpMod.StepPermitted = false;
                }

                return true; // Execute the tick
            }

            // Training mode, no permission: Block the tick
            return false;
        }

        /// <summary>
        /// Postfix: Logging and state tracking after tick executes
        /// </summary>
        public static void Postfix(TickManager __instance)
        {
            if (!RimTcpMod.ServerRunning)
                return;

            tickCount++;

            // Log periodically (not every tick to avoid spam)
            if (tickCount % _reportEveryNTicks == 0)
            {
                string modeStr = RimTcpMod.TrainingMode ? "TRAINING" : "INFERENCE";
                Log.Message(
                    $"{Constants.LogPrefix} [{modeStr}] Tick: {tickCount} (Frame: {Find.TickManager.TicksAbs})"
                );
            }
        }
    }
}
