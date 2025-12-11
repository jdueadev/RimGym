"""
Spectator Demo

Simple demonstration of using SpectatorClient to observe RimWorld.
Shows how to monitor game state and events without taking actions.
"""

import argparse
import logging
import time

from client import ClientConfig, SpectatorClient

# Display limit for colonist output
MAX_DISPLAYED_COLONISTS = 3

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Main demo script."""
    parser = argparse.ArgumentParser(description="Watch RimWorld game state")
    parser.add_argument("--host", default="localhost", help="RimWorld server host")
    parser.add_argument("--port", type=int, default=50051, help="RimWorld server port")
    parser.add_argument(
        "--duration", type=int, default=60, help="Watch duration in seconds"
    )

    args = parser.parse_args()

    # Create client with no policies (observation only)
    config = ClientConfig(
        host=args.host,
        port=args.port,
        training_mode=False,
        inference_mode=True,
        poll_interval_ms=500,  # Poll every 500ms
    )

    logger.info("Starting SpectatorClient...")
    client = SpectatorClient(config)

    try:
        # Start client
        client.start()

        # Wait for ready
        if not client.wait_ready(timeout=30.0):
            logger.error("Client failed to become ready")
            return

        logger.info(f"Watching RimWorld for {args.duration} seconds...")

        # Watch for specified duration
        start_time = time.time()
        state_count = 0
        event_count = 0

        while time.time() - start_time < args.duration:
            # Get latest state
            state = client.state_queue.get_latest()
            if state:
                state_count += 1
                frame_id = state.get("frame_id", 0)
                colonist_count = len(state.get("colonists", []))

                logger.info(
                    f"Frame {frame_id}: {colonist_count} colonists, "
                    f"wealth: {state.get('global_state', {}).get('wealth', 0)}"
                )

                # Show colonist details
                for colonist in state.get("colonists", [])[:MAX_DISPLAYED_COLONISTS]:
                    health = colonist.get("health", 0)
                    mood = colonist.get("mood", 0)
                    job = colonist.get("current_job", "Unknown")
                    logger.info(
                        f"  - {colonist.get('id')}: health={health:.2f}, "
                        f"mood={mood:.2f}, job={job}"
                    )

            # Check for events
            while not client.event_queue.empty():
                event = client.event_queue.get(timeout=0.1)
                if event:
                    event_count += 1
                    logger.info(
                        f"EVENT: {event.get('type')} "
                        f"(priority: {event.get('priority')})"
                    )

            time.sleep(2.0)  # Update every 2 seconds

        elapsed = time.time() - start_time
        logger.info(f"Watched for {elapsed:.1f} seconds")
        logger.info(f"States received: {state_count}")
        logger.info(f"Events detected: {event_count}")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")

    finally:
        client.stop(timeout=5.0)
        logger.info("Demo complete!")


if __name__ == "__main__":
    main()
