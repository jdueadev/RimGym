"""
Phase V Full Observability Demo

Demonstrates access to complete game state including:
- Map data (terrain, buildings, items, zones, rooms)
- Incident history and storyteller state
- World data (factions, settlements, caravans)

This example shows how to query and use the rich data from RIMAPI integration.
"""

import logging
import time

from client import ClientConfig, RichGameState, SpectatorClient

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """Print a section separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def demo_phase_v_observability():
    """Demonstrate Phase V full game observability."""

    # Configure client for inference mode (async queries)
    config = ClientConfig(
        host="localhost",
        port=50051,
        inference_mode=True,  # Async mode - game runs freely
        training_mode=False,
        poll_interval_ms=100,  # Poll state every 100ms
        log_level="INFO",
    )

    print_separator("Phase V Full Observability Demo")
    print("Connecting to RimWorld server...")

    with SpectatorClient(config) as client:
        if not client.wait_ready(timeout=10.0):
            logger.error("Failed to connect to server")
            return

        print("✓ Connected successfully!\n")

        # Wait a moment for initial state
        time.sleep(0.5)

        # Get current game state
        state = client.get_state(timeout=1.0)

        if not state:
            logger.error("No state received from server")
            return

        # Check if Phase V data is available
        if not isinstance(state, RichGameState):
            logger.warning("Server does not support Phase V (using legacy state)")
            return

        if not state.is_phase_v:
            logger.warning("Phase V data not present in state message")
            logger.info("Ensure RimWorld mod is Phase V compatible")
            return

        # Display comprehensive state summary
        print_separator("GAME STATE SUMMARY")
        print(state.summary())

        # Display colonist information
        print_separator("COLONIST DATA")
        print(f"Total Colonists: {state.colonist_count}\n")

        for colonist in state.colonists[:5]:  # Show first 5
            print(f"  {colonist.name} (ID: {colonist.pawn_id})")
            print(f"    Health: {colonist.health * 100:.1f}%")
            print(f"    Position: ({colonist.x:.1f}, {colonist.y:.1f})")
            print(f"    Current Job: {colonist.current_job}")
            print()

        if state.colonist_count > 5:
            print(f"  ... and {state.colonist_count - 5} more colonists\n")

        # Display map data
        if state.has_map_data:
            print_separator("MAP DATA")
            map_state = state.map_state

            print(f"Map Size: {map_state.map_size_x} x {map_state.map_size_z}")
            print(f"Total Terrain Cells: {len(map_state.terrain)}")
            print(f"Total Buildings: {map_state.building_count}")
            print(f"Total Items: {map_state.item_count}")
            print(f"Total Zones: {len(map_state.zones)}")
            print(f"Total Rooms: {len(map_state.rooms)}\n")

            # Show building types breakdown
            if map_state.buildings:
                building_types = {}
                for building in map_state.buildings:
                    building_types[building.building_type] = (
                        building_types.get(building.building_type, 0) + 1
                    )

                print("Building Types:")
                for btype, count in sorted(
                    building_types.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    print(f"  {btype}: {count}")
                print()

            # Show item types breakdown
            if map_state.items:
                item_types = {}
                for item in map_state.items:
                    item_types[item.item_type] = (
                        item_types.get(item.item_type, 0) + item.stack_count
                    )

                print("Item Stockpiles (Top 10):")
                for itype, count in sorted(
                    item_types.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    print(f"  {itype}: {count}")
                print()

            # Show room types
            if map_state.rooms:
                room_types = {}
                for room in map_state.rooms:
                    room_types[room.role] = room_types.get(room.role, 0) + 1

                print("Room Types:")
                for rtype, count in room_types.items():
                    print(f"  {rtype}: {count}")
                print()

        # Display incident data
        if state.has_incident_data:
            print_separator("INCIDENT & THREAT DATA")
            incident_state = state.incident_state

            print(f"Recent Incidents: {incident_state.incident_count}\n")

            # Show storyteller info
            if incident_state.storyteller:
                storyteller = incident_state.storyteller
                print(f"Storyteller: {storyteller.storyteller_name}")
                print(f"Difficulty: {storyteller.difficulty}\n")

            # Show threat status
            if incident_state.threats:
                threats = incident_state.threats
                print("Current Threats:")
                print(f"  Active Raids: {threats.active_raids}")
                print(f"  Active Fires: {threats.active_fires}")
                print(f"  Mental Breaks: {threats.active_mental_breaks}")
                print(f"  Threat Points: {threats.total_threat_points:.1f}\n")

            # Show recent incidents
            if incident_state.recent_incidents:
                print("Recent Events (Last 10):")
                for incident in incident_state.recent_incidents[-10:]:
                    print(
                        f"  Frame {incident.frame_id}: {incident.incident_type} (severity: {incident.severity:.2f})"
                    )
                    if incident.faction_involved:
                        print(f"    Faction: {incident.faction_involved}")
                print()

        # Display world data
        if state.has_world_data:
            print_separator("WORLD DATA")
            world_state = state.world_state

            print(f"Total Factions: {world_state.faction_count}")
            print(f"Total Settlements: {world_state.settlement_count}")
            print(f"Player Caravans: {len(world_state.caravans)}\n")

            # Show faction relations
            if world_state.factions:
                print("Faction Relations:")

                allied = world_state.get_allied_factions()
                if allied:
                    print(f"  Allies ({len(allied)}):")
                    for faction in allied[:5]:
                        print(f"    {faction.name} (Goodwill: {faction.goodwill:.0f})")

                hostile = world_state.get_hostile_factions()
                if hostile:
                    print(f"  Hostiles ({len(hostile)}):")
                    for faction in hostile[:5]:
                        print(f"    {faction.name} (Goodwill: {faction.goodwill:.0f})")

                print()

            # Show nearby settlements
            if world_state.settlements:
                print(
                    f"Settlements (showing first 5 of {world_state.settlement_count}):"
                )
                for settlement in world_state.settlements[:5]:
                    faction = world_state.get_faction_by_id(settlement.faction_id)
                    faction_name = faction.name if faction else "Unknown"
                    print(f"  {settlement.name} ({faction_name})")
                    print(
                        f"    Tile: {settlement.tile_id}, Coords: ({settlement.x:.1f}, {settlement.y:.1f})"
                    )
                print()

        # Continuous monitoring example
        print_separator("CONTINUOUS MONITORING")
        print("Monitoring game state for 10 seconds...")
        print("(Press Ctrl+C to stop)\n")

        try:
            start_time = time.time()
            frame_count = 0
            last_tick = state.tick

            while time.time() - start_time < 10.0:
                time.sleep(0.5)  # Update every 500ms

                state = client.get_state(timeout=0.5)
                if state:
                    frame_count += 1
                    ticks_elapsed = state.tick - last_tick
                    last_tick = state.tick

                    print(
                        f"[{frame_count:3d}] Frame {state.frame_id}, Tick {state.tick} (+{ticks_elapsed})"
                    )

                    if state.has_map_data:
                        print(
                            f"      Map: {state.map_state.building_count} buildings, {state.map_state.item_count} items"
                        )

                    if state.has_incident_data and state.incident_state.threats:
                        threats = state.incident_state.threats
                        if threats.active_raids > 0 or threats.active_fires > 0:
                            print(
                                f"      ⚠ THREATS: {threats.active_raids} raids, {threats.active_fires} fires"
                            )

            print(f"\n✓ Monitored {frame_count} frames in 10 seconds")
            print(f"  Average: {frame_count / 10.0:.1f} frames/second")

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")

        print_separator("DEMO COMPLETE")
        print("Phase V provides complete game observability for advanced RL agents!")
        print("All game data is now accessible through typed Python models.")


if __name__ == "__main__":
    demo_phase_v_observability()
