using System;
using System.Linq;
using RimworldMLBridge.DTOs;
using RimworldMLBridge.Protos;

namespace RimworldMLBridge.Adapters
{
    /// <summary>
    /// Phase V: Adapter for converting World DTOs to Protobuf messages
    /// Handles factions, settlements, caravans, and world events
    /// Target: <1ms conversion time
    /// </summary>
    public class WorldAdapter
    {
        /// <summary>
        /// Convert WorldStateDTO to Protobuf WorldState
        /// </summary>
        public static WorldState ToProtobuf(WorldStateDTO worldDto)
        {
            if (worldDto == null)
                return null;

            var worldState = new WorldState
            {
                TileCount = worldDto.TileCount,
                CoveragePercent = worldDto.CoveragePercent,
                SeedString = worldDto.SeedString ?? "",
                PlanetName = worldDto.PlanetName ?? "Unknown"
            };

            // Convert factions
            if (worldDto.Factions != null)
            {
                foreach (var faction in worldDto.Factions)
                {
                    worldState.Factions.Add(ToProtobuf(faction));
                }
            }

            // Convert settlements
            if (worldDto.Settlements != null)
            {
                foreach (var settlement in worldDto.Settlements)
                {
                    worldState.Settlements.Add(ToProtobuf(settlement));
                }
            }

            // Convert caravans
            if (worldDto.Caravans != null)
            {
                foreach (var caravan in worldDto.Caravans)
                {
                    worldState.Caravans.Add(ToProtobuf(caravan));
                }
            }

            // Convert world events
            if (worldDto.Events != null)
            {
                foreach (var worldEvent in worldDto.Events)
                {
                    worldState.Events.Add(ToProtobuf(worldEvent));
                }
            }

            return worldState;
        }

        /// <summary>
        /// Convert FactionDTO to Protobuf FactionState
        /// </summary>
        private static FactionState ToProtobuf(FactionDTO factionDto)
        {
            return new FactionState
            {
                FactionId = factionDto.FactionId,
                DefName = factionDto.DefName ?? "Unknown",
                Name = factionDto.Name ?? factionDto.DefName ?? "Faction",
                Relation = ParseFactionRelation(factionDto.Relation),
                Goodwill = factionDto.Goodwill,
                IsPlayer = factionDto.IsPlayer,
                Defeated = factionDto.Defeated,
                SettlementCount = factionDto.SettlementCount
            };
        }

        /// <summary>
        /// Convert SettlementDTO to Protobuf SettlementState
        /// </summary>
        private static SettlementState ToProtobuf(SettlementDTO settlementDto)
        {
            var settlementState = new SettlementState
            {
                Id = settlementDto.Id,
                Name = settlementDto.Name ?? $"Settlement {settlementDto.Id}",
                FactionId = settlementDto.FactionId,
                Type = settlementDto.Type ?? "Base",
                IsPlayerHome = settlementDto.IsPlayerHome
            };

            // Set tile position
            if (settlementDto.TilePosition != null)
            {
                settlementState.TilePosition = new Vector3
                {
                    X = settlementDto.TilePosition.X,
                    Y = settlementDto.TilePosition.Y,
                    Z = settlementDto.TilePosition.Z
                };
            }

            return settlementState;
        }

        /// <summary>
        /// Convert CaravanDTO to Protobuf CaravanState
        /// </summary>
        private static CaravanState ToProtobuf(CaravanDTO caravanDto)
        {
            var caravanState = new CaravanState
            {
                ThingId = caravanDto.ThingId,
                Name = caravanDto.Name ?? $"Caravan {caravanDto.ThingId}",
                FactionId = caravanDto.FactionId,
                PawnCount = caravanDto.PawnCount,
                IsPlayerCaravan = caravanDto.IsPlayerCaravan
            };

            // Set tile position
            if (caravanDto.TilePosition != null)
            {
                caravanState.TilePosition = new Vector3
                {
                    X = caravanDto.TilePosition.X,
                    Y = caravanDto.TilePosition.Y,
                    Z = caravanDto.TilePosition.Z
                };
            }

            // Set tile destination
            if (caravanDto.TileDestination != null)
            {
                caravanState.TileDestination = new Vector3
                {
                    X = caravanDto.TileDestination.X,
                    Y = caravanDto.TileDestination.Y,
                    Z = caravanDto.TileDestination.Z
                };
            }

            return caravanState;
        }

        /// <summary>
        /// Convert WorldEventDTO to Protobuf WorldEvent
        /// </summary>
        private static WorldEvent ToProtobuf(WorldEventDTO eventDto)
        {
            var worldEvent = new WorldEvent
            {
                Id = eventDto.Id,
                DefName = eventDto.DefName ?? "Unknown",
                Label = eventDto.Label ?? eventDto.DefName ?? "Event",
                Description = eventDto.Description ?? "",
                StartTick = eventDto.StartTick,
                ExpiryTick = eventDto.ExpiryTick,
                IsActive = eventDto.IsActive
            };

            // Set tile position
            if (eventDto.TilePosition != null)
            {
                worldEvent.TilePosition = new Vector3
                {
                    X = eventDto.TilePosition.X,
                    Y = eventDto.TilePosition.Y,
                    Z = eventDto.TilePosition.Z
                };
            }

            return worldEvent;
        }

        #region Enum Parsers

        private static FactionRelation ParseFactionRelation(string relation)
        {
            if (string.IsNullOrEmpty(relation))
                return FactionRelation.RelationNeutral;

            switch (relation.ToLowerInvariant())
            {
                case "hostile":
                case "enemy":
                    return FactionRelation.RelationHostile;
                case "ally":
                case "allied":
                case "friendly":
                    return FactionRelation.RelationAlly;
                case "neutral":
                default:
                    return FactionRelation.RelationNeutral;
            }
        }

        #endregion
    }
}
