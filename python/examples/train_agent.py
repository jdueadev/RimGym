"""
Train RL Agent Example

Example of training an RL agent using the RimWorld Gymnasium environment.
Demonstrates integration with Stable-Baselines3.
"""

import argparse
import logging
from pathlib import Path

from gym_env import RimWorldEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def make_env(
    host: str = "localhost",
    port: int = 50051,
    training_mode: bool = True,
    max_episode_steps: int = 1000,
):
    """
    Create RimWorld environment.

    Args:
        host: RimWorld server host
        port: RimWorld server port
        training_mode: Whether to run in training mode
        max_episode_steps: Maximum steps per episode

    Returns:
        Wrapped environment
    """

    def _init():
        env = RimWorldEnv(
            host=host,
            port=port,
            training_mode=training_mode,
            max_episode_steps=max_episode_steps,
        )
        return Monitor(env)

    return _init


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description="Train RL agent on RimWorld")
    parser.add_argument("--host", default="localhost", help="RimWorld server host")
    parser.add_argument("--port", type=int, default=50051, help="RimWorld server port")
    parser.add_argument(
        "--timesteps", type=int, default=100000, help="Total training timesteps"
    )
    parser.add_argument(
        "--save-freq", type=int, default=10000, help="Save model every N steps"
    )
    parser.add_argument(
        "--eval-freq", type=int, default=5000, help="Evaluate every N steps"
    )
    parser.add_argument(
        "--log-dir", default="./logs", help="Directory for logs and models"
    )
    parser.add_argument(
        "--episode-length", type=int, default=1000, help="Max episode length"
    )
    parser.add_argument("--check-env", action="store_true", help="Validate environment")
    parser.add_argument(
        "--num-envs", type=int, default=1, help="Number of parallel environments"
    )

    args = parser.parse_args()

    # Create log directory
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Creating RimWorld environment...")

    if args.num_envs == 1:
        # Single environment
        env = make_env(
            host=args.host,
            port=args.port,
            training_mode=True,
            max_episode_steps=args.episode_length,
        )()
    else:
        # Multiple parallel environments (requires multiple RimWorld instances)
        logger.warning(
            f"Using {args.num_envs} parallel environments requires {args.num_envs} RimWorld instances"
        )
        env = DummyVecEnv(
            [
                make_env(
                    host=args.host,
                    port=args.port + i,
                    training_mode=True,
                    max_episode_steps=args.episode_length,
                )
                for i in range(args.num_envs)
            ]
        )

    # Validate environment if requested
    if args.check_env and args.num_envs == 1:
        logger.info("Validating environment...")
        check_env(env, warn=True)
        logger.info("Environment validated successfully!")

    logger.info("Creating PPO agent...")

    # Create PPO agent
    model = PPO(
        "MultiInputPolicy",  # For Dict observation space
        env,
        verbose=1,
        tensorboard_log=str(log_dir / "tensorboard"),
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=args.save_freq,
        save_path=str(log_dir / "checkpoints"),
        name_prefix="rimworld_model",
    )

    eval_callback = EvalCallback(
        env,
        best_model_save_path=str(log_dir / "best_model"),
        log_path=str(log_dir / "eval"),
        eval_freq=args.eval_freq,
        n_eval_episodes=5,
        deterministic=True,
    )

    logger.info(f"Starting training for {args.timesteps} timesteps...")
    logger.info(f"Logs will be saved to: {log_dir}")

    try:
        # Train agent
        model.learn(
            total_timesteps=args.timesteps,
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True,
        )

        # Save final model
        final_model_path = log_dir / "final_model"
        model.save(str(final_model_path))
        logger.info(f"Final model saved to: {final_model_path}")

    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        interrupt_model_path = log_dir / "interrupted_model"
        model.save(str(interrupt_model_path))
        logger.info(f"Model saved to: {interrupt_model_path}")

    finally:
        env.close()
        logger.info("Training complete!")


if __name__ == "__main__":
    main()
