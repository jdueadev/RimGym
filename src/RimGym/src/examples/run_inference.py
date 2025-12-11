"""
Run Inference Example

Example of running trained RL agent in inference mode.
Demonstrates using the SpectatorClient with a trained policy.
"""

import argparse
import logging
import time
from pathlib import Path

from client import ClientConfig, SpectatorClient
from gym_env import ActionSpace, ObservationSpace
from policies import Policy
from stable_baselines3 import PPO

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


class SB3Policy(Policy):
    """
    Wrapper for Stable-Baselines3 model as a Policy.

    Allows using trained SB3 models with SpectatorClient.
    """

    def __init__(self, model_path: str, config: dict = None):
        """
        Initialize SB3 policy.

        Args:
            model_path: Path to saved SB3 model
            config: Policy configuration
        """
        super().__init__(name="SB3Policy", config=config or {})
        self.model = PPO.load(model_path)
        logger.info(f"Loaded model from: {model_path}")

    def decide(self, state: dict) -> list:
        """
        Generate actions using trained model.

        Args:
            state: Current game state

        Returns:
            List of actions
        """
        try:
            # Extract observation
            obs = ObservationSpace.extract_observation(state)

            # Get action from model
            action, _states = self.model.predict(obs, deterministic=True)

            # Decode action
            decoded_action = ActionSpace.decode_action(action, state)

            self._record_decision(state, [decoded_action])

            return [decoded_action]

        except Exception as e:
            logger.error(f"Error in SB3 policy decision: {e}")
            self._record_error(state, str(e))
            return []


def main():
    """Main inference script."""
    parser = argparse.ArgumentParser(description="Run RL agent inference on RimWorld")
    parser.add_argument("model", help="Path to trained model")
    parser.add_argument("--host", default="localhost", help="RimWorld server host")
    parser.add_argument("--port", type=int, default=50051, help="RimWorld server port")
    parser.add_argument(
        "--duration", type=int, default=300, help="Run duration in seconds (0=infinite)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load trained model
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Model not found: {model_path}")
        return

    logger.info("Loading trained model...")
    policy = SB3Policy(str(model_path))

    # Create client configuration
    config = ClientConfig(
        host=args.host,
        port=args.port,
        training_mode=False,  # Inference mode
        inference_mode=True,
        executive_policy=policy,
        poll_interval_ms=100,
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

        logger.info("Client ready! Running inference...")

        # Run for specified duration
        start_time = time.time()
        action_count = 0

        while True:
            # Check duration
            if args.duration > 0:
                elapsed = time.time() - start_time
                if elapsed >= args.duration:
                    logger.info(f"Duration reached: {elapsed:.1f} seconds")
                    break

            # Process actions
            action = client.action_queue.get(timeout=1.0)
            if action:
                action_count += 1
                logger.info(
                    f"Action {action_count}: {action.get('type')} "
                    f"(colonist: {action.get('colonist_id')})"
                )

            # Print stats every 30 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 30 == 0 and elapsed > 0:
                stats = policy.get_stats()
                logger.info(f"Statistics after {elapsed:.0f}s: {stats}")

    except KeyboardInterrupt:
        logger.info("Inference interrupted by user")

    finally:
        # Get final statistics
        stats = policy.get_stats()
        logger.info(f"Final statistics: {stats}")

        # Stop client
        client.stop(timeout=5.0)
        logger.info("Inference complete!")


if __name__ == "__main__":
    main()
