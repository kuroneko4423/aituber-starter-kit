"""Main entry point for AITuber Starter Kit."""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from .config import load_config, settings, AppConfig
from .ai.character import Character
from .ai.openai_client import OpenAIClient
from .avatar.vtube_studio import VTubeStudioController
from .chat.youtube_chat import YouTubeChatClient
from .pipeline import AITuberPipeline
from .tts.voicevox import VoicevoxEngine
from .dashboard import DashboardServer
from .memory import LongTermMemory, MemoryRetriever


def setup_logging(config: AppConfig) -> None:
    """Configure logging based on settings.

    Args:
        config: Application configuration.
    """
    level = getattr(logging, config.logging.level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if config.logging.file:
        # Ensure log directory exists
        config.logging.file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(config.logging.file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


async def create_pipeline(config: AppConfig) -> AITuberPipeline:
    """Create and configure the AITuber pipeline.

    Args:
        config: Application configuration.

    Returns:
        Configured AITuberPipeline instance.

    Raises:
        ValueError: If configuration is invalid.
    """
    logger = logging.getLogger(__name__)

    # Initialize chat client
    logger.info(f"Initializing chat client for platform: {config.platform.name}")

    if config.platform.name == "youtube":
        if not config.platform.video_id:
            raise ValueError(
                "YouTube video_id is required. "
                "Set it in config/config.yaml or via command line."
            )
        chat_client = YouTubeChatClient(config.platform.video_id)
    else:
        raise ValueError(f"Unsupported platform: {config.platform.name}")

    # Initialize LLM client
    logger.info(f"Initializing LLM client: {config.llm.provider}")

    if config.llm.provider == "openai":
        llm_client = OpenAIClient(
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm.provider}")

    # Load character
    logger.info(f"Loading character from: {config.character_file}")

    if config.character_file.exists():
        character = Character.from_yaml(config.character_file)
        llm_client.set_character(character)
        logger.info(f"Loaded character: {character.name}")
    else:
        logger.warning(
            f"Character file not found: {config.character_file}. "
            "Using default character."
        )

    # Initialize TTS engine
    logger.info(f"Initializing TTS engine: {config.tts.engine}")

    if config.tts.engine == "voicevox":
        tts_engine = VoicevoxEngine(
            host=config.tts.host,
            port=config.tts.port,
        )
        tts_engine.set_speed(config.tts.speed)
        tts_engine.set_pitch(config.tts.pitch)
    else:
        raise ValueError(f"Unsupported TTS engine: {config.tts.engine}")

    # Initialize avatar controller (optional)
    avatar_controller: Optional[VTubeStudioController] = None

    if config.avatar.enabled:
        logger.info("Initializing avatar controller")
        avatar_controller = VTubeStudioController(
            host=config.avatar.host,
            port=config.avatar.port,
            plugin_name=config.avatar.plugin_name,
            plugin_developer=config.avatar.plugin_developer,
        )

    # Load NG words if configured
    comment_queue_ng_words = None
    if config.comment.ng_words_file and config.comment.ng_words_file.exists():
        logger.info(f"Loading NG words from: {config.comment.ng_words_file}")

    # Create pipeline
    pipeline = AITuberPipeline(
        chat_client=chat_client,
        llm_client=llm_client,
        tts_engine=tts_engine,
        avatar_controller=avatar_controller,
        response_interval=config.comment.response_interval,
        speaker_id=config.tts.speaker_id,
    )

    return pipeline


async def main_async(config_path: Optional[Path] = None) -> None:
    """Async main entry point.

    Args:
        config_path: Optional path to config file.
    """
    # Load configuration
    config = load_config(config_path or Path("config/config.yaml"))

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("AITuber Starter Kit")
    logger.info("=" * 50)
    logger.info(f"Platform: {config.platform.name}")
    logger.info(f"LLM: {config.llm.provider} ({config.llm.model})")
    logger.info(f"TTS: {config.tts.engine}")
    logger.info(f"Avatar: {'enabled' if config.avatar.enabled else 'disabled'}")
    logger.info(f"Dashboard: {'enabled' if config.dashboard.enabled else 'disabled'}")
    logger.info(f"Memory: {'enabled' if config.memory.enabled else 'disabled'}")
    logger.info("=" * 50)

    # Create pipeline
    pipeline = await create_pipeline(config)

    # Initialize dashboard server (if enabled)
    dashboard: Optional[DashboardServer] = None
    if config.dashboard.enabled:
        logger.info(f"Starting dashboard at http://{config.dashboard.host}:{config.dashboard.port}")
        dashboard = DashboardServer(
            host=config.dashboard.host,
            port=config.dashboard.port,
        )
        dashboard.set_pipeline(pipeline)

    # Initialize long-term memory (if enabled)
    memory_store: Optional[LongTermMemory] = None
    memory_retriever: Optional[MemoryRetriever] = None
    if config.memory.enabled:
        logger.info(f"Initializing long-term memory at {config.memory.db_path}")
        memory_store = LongTermMemory(db_path=config.memory.db_path)
        await memory_store.initialize()

        from .memory.retriever import RetrievalConfig
        retriever_config = RetrievalConfig(
            max_results=config.memory.max_results,
            relevance_threshold=config.memory.relevance_threshold,
        )
        memory_retriever = MemoryRetriever(memory_store, retriever_config)

        # Attach memory to pipeline
        pipeline.memory_store = memory_store
        pipeline.memory_retriever = memory_retriever

        if dashboard:
            dashboard.set_memory_store(memory_store)

    # Setup shutdown handling
    shutdown_event = asyncio.Event()

    def signal_handler(sig: signal.Signals) -> None:
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        shutdown_event.set()

    # Register signal handlers (Unix only)
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # Start services
    try:
        # Start dashboard server
        if dashboard:
            await dashboard.start()
            logger.info(f"Dashboard available at {dashboard.get_url()}")

        # Run until shutdown signal
        pipeline_task = asyncio.create_task(pipeline.start())

        # Wait for either pipeline to finish or shutdown signal
        done, pending = await asyncio.wait(
            [pipeline_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await pipeline.stop()

        # Cleanup dashboard
        if dashboard:
            await dashboard.stop()

        # Cleanup memory
        if memory_store:
            await memory_store.close()

        logger.info("Goodbye!")


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AITuber Starter Kit - AI-powered VTuber streaming toolkit"
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to configuration file",
    )
    parser.add_argument(
        "-v", "--video-id",
        type=str,
        help="YouTube video ID (overrides config)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Load and modify config if needed
    config = load_config(args.config)

    if args.video_id:
        config.platform.video_id = args.video_id

    if args.debug:
        config.logging.level = "DEBUG"

    # Run
    try:
        asyncio.run(main_async(args.config))
    except KeyboardInterrupt:
        pass


def run() -> None:
    """Alternative entry point (for pyproject.toml scripts)."""
    main()


if __name__ == "__main__":
    main()
