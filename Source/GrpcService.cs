using System;
using System.Threading.Tasks;
using Grpc.Core;
using RimworldMLBridge.Protos;
using Verse;

namespace RimworldMLBridge
{
    /// <summary>
    /// gRPC service implementation for ML Bridge
    /// </summary>
    public class MLBridgeService : MLBridge.MLBridgeBase
    {
        private static long currentTick = 0;
        private static object tickLock = new object();

        public override Task<AckMessage> SendTick(TickMessage request, ServerCallContext context)
        {
            lock (tickLock)
            {
                currentTick = request.TickCount;
            }
            
            Log.Message($"[MLBridge] Received tick: {request.TickCount}");
            
            return Task.FromResult(new AckMessage
            {
                TickCount = request.TickCount,
                Success = true,
                Message = "Tick acknowledged"
            });
        }

        public override Task<StateMessage> ExecuteCommand(CommandMessage request, ServerCallContext context)
        {
            Log.Message($"[MLBridge] Executing command: {request.Type}");
            
            // Create a basic state response
            var state = new StateMessage
            {
                FrameId = currentTick,
                IsReady = true,
                StatusMessage = $"Command {request.Type} executed"
            };

            // Add basic global state if game is running
            try
            {
                if (Current.Game != null)
                {
                    var ticksAbs = Find.TickManager.TicksAbs;
                    var longitude = Find.WorldGrid.LongLatOf(Find.CurrentMap.Tile).x;
                    
                    state.Global = new GlobalState
                    {
                        Day = GenDate.DayOfTwelfth(ticksAbs, longitude),
                        Year = GenDate.Year(ticksAbs, longitude)
                    };
                }
            }
            catch (Exception e)
            {
                Log.Warning($"[MLBridge] Could not fetch game state: {e.Message}");
                state.IsReady = false;
                state.StatusMessage = "Game not fully loaded";
            }

            return Task.FromResult(state);
        }

        public override Task<StateMessage> GetState(EmptyMessage request, ServerCallContext context)
        {
            Log.Message($"[MLBridge] Getting current state");
            
            var state = new StateMessage
            {
                FrameId = currentTick,
                IsReady = true,
                StatusMessage = "State retrieved"
            };

            // Add game state if available
            try
            {
                if (Current.Game != null && Find.CurrentMap != null)
                {
                    var ticksAbs = Find.TickManager.TicksAbs;
                    var longitude = Find.WorldGrid.LongLatOf(Find.CurrentMap.Tile).x;
                    
                    state.Global = new GlobalState
                    {
                        Day = GenDate.DayOfTwelfth(ticksAbs, longitude),
                        Year = GenDate.Year(ticksAbs, longitude),
                        Temperature = Find.CurrentMap.mapTemperature.OutdoorTemp
                    };

                    // Add pawns as entities
                    foreach (var pawn in Find.CurrentMap.mapPawns.FreeColonistsSpawned)
                    {
                        var entity = new Entity
                        {
                            Id = pawn.thingIDNumber,
                            Type = "Pawn",
                            DefName = pawn.def.defName,
                            Position = new Protos.Vector3
                            {
                                X = pawn.Position.x,
                                Y = pawn.Position.y,
                                Z = pawn.Position.z
                            },
                            State = new EntityState
                            {
                                Health = pawn.health.summaryHealth.SummaryHealthPercent,
                                IsDrafted = pawn.Drafted,
                                CurrentJob = pawn.CurJobDef?.defName ?? "None"
                            }
                        };

                        // Add needs if available
                        if (pawn.needs != null)
                        {
                            entity.State.Mood = pawn.needs.mood?.CurLevel ?? 0;
                            entity.State.Hunger = pawn.needs.food?.CurLevel ?? 0;
                            entity.State.Rest = pawn.needs.rest?.CurLevel ?? 0;
                        }

                        state.Entities.Add(entity);
                    }
                }
            }
            catch (Exception e)
            {
                Log.Warning($"[MLBridge] Error fetching detailed state: {e.Message}");
                state.IsReady = false;
                state.StatusMessage = $"Error: {e.Message}";
            }

            return Task.FromResult(state);
        }

        public static long GetCurrentTick()
        {
            lock (tickLock)
            {
                return currentTick;
            }
        }
    }
}
