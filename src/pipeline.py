"""Main orchestrator for the AITuber system."""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from .ai.base import BaseLLMClient
from .ai.memory import ConversationMemory
from .avatar.base import BaseAvatarController
from .chat.base import BaseChatClient
from .chat.comment_queue import CommentQueue
from .chat.models import Comment
from .expression.lip_sync import LipSyncController
from .expression.emotion_analyzer import EmotionAnalyzer, EmotionExpressionController
from .tts.base import BaseTTSEngine
from .utils.audio import AudioPlayer

if TYPE_CHECKING:
    from .memory import LongTermMemory, MemoryRetriever

logger = logging.getLogger(__name__)


class AITuberPipeline:
    """Main orchestrator for the AITuber system.

    This class coordinates all components:
    - Comment retrieval from streaming platforms
    - AI response generation
    - Text-to-speech synthesis
    - Avatar lip sync control
    - Audio playback

    Args:
        chat_client: Client for retrieving comments.
        llm_client: LLM client for generating responses.
        tts_engine: TTS engine for voice synthesis.
        avatar_controller: Optional avatar controller for lip sync.
        response_interval: Minimum time between responses in seconds.
        speaker_id: TTS speaker/voice ID to use.

    Example:
        ```python
        pipeline = AITuberPipeline(
            chat_client=youtube_client,
            llm_client=openai_client,
            tts_engine=voicevox_engine,
            avatar_controller=vtube_controller,
        )
        await pipeline.start()
        ```
    """

    def __init__(
        self,
        chat_client: BaseChatClient,
        llm_client: BaseLLMClient,
        tts_engine: BaseTTSEngine,
        avatar_controller: Optional[BaseAvatarController] = None,
        response_interval: float = 5.0,
        speaker_id: int = 1,
        enable_emotion_analysis: bool = True,
    ) -> None:
        """Initialize the AITuber pipeline.

        Args:
            chat_client: Chat platform client.
            llm_client: LLM client for responses.
            tts_engine: TTS engine for voice.
            avatar_controller: Optional avatar controller.
            response_interval: Seconds between responses.
            speaker_id: Voice ID for TTS.
            enable_emotion_analysis: Whether to analyze emotions and update expressions.
        """
        self.chat_client = chat_client
        self.llm_client = llm_client
        self.tts_engine = tts_engine
        self.avatar_controller = avatar_controller
        self.response_interval = response_interval
        self.speaker_id = speaker_id
        self.enable_emotion_analysis = enable_emotion_analysis

        # Internal components
        self.comment_queue = CommentQueue()
        self.memory = ConversationMemory()
        self.audio_player = AudioPlayer()

        # Lip sync controller (if avatar is available)
        self._lip_sync: Optional[LipSyncController] = None
        if avatar_controller:
            self._lip_sync = LipSyncController(avatar_controller)

        # Emotion analyzer and expression controller
        self._emotion_analyzer: Optional[EmotionAnalyzer] = None
        self._expression_controller: Optional[EmotionExpressionController] = None
        if enable_emotion_analysis and avatar_controller:
            self._emotion_analyzer = EmotionAnalyzer()
            self._expression_controller = EmotionExpressionController(
                analyzer=self._emotion_analyzer,
                avatar_controller=avatar_controller,
            )

        # State
        self._running = False
        self._tasks: list[asyncio.Task] = []

        # Long-term memory (set externally if enabled)
        self.memory_store: Optional["LongTermMemory"] = None
        self.memory_retriever: Optional["MemoryRetriever"] = None

        logger.info(
            f"Initialized AITuberPipeline (interval={response_interval}s, "
            f"speaker={speaker_id}, avatar={'enabled' if avatar_controller else 'disabled'}, "
            f"emotion={'enabled' if enable_emotion_analysis else 'disabled'})"
        )

    @property
    def is_running(self) -> bool:
        """Check if pipeline is running."""
        return self._running

    async def start(self) -> None:
        """Start the AITuber pipeline.

        This connects to all services and begins processing comments.
        """
        if self._running:
            logger.warning("Pipeline already running")
            return

        logger.info("Starting AITuber pipeline...")
        self._running = True

        try:
            # Connect to chat platform
            await self.chat_client.connect()
            logger.info("Connected to chat platform")

            # Connect to avatar (optional)
            if self.avatar_controller:
                try:
                    await self.avatar_controller.connect()
                    logger.info("Connected to avatar controller")
                except Exception as e:
                    logger.warning(f"Avatar connection failed: {e}")
                    self.avatar_controller = None
                    self._lip_sync = None

            # Check TTS availability
            if await self.tts_engine.is_available():
                logger.info("TTS engine is available")
            else:
                logger.warning("TTS engine not available")

            # Register comment callback
            self.chat_client.on_comment(self._on_comment)

            # Start background tasks
            self._tasks = [
                asyncio.create_task(
                    self._safe_task(self.chat_client.start_listening()),
                    name="chat_listener",
                ),
                asyncio.create_task(
                    self._safe_task(self._process_comments()),
                    name="comment_processor",
                ),
            ]

            logger.info("AITuber pipeline started successfully!")

            # Wait for tasks (they run indefinitely)
            await asyncio.gather(*self._tasks, return_exceptions=True)

        except asyncio.CancelledError:
            logger.info("Pipeline cancelled")
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            raise
        finally:
            await self.stop()

    async def _safe_task(self, coro) -> None:
        """Wrap a coroutine to catch and log exceptions."""
        try:
            await coro
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Task error: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the AITuber pipeline."""
        if not self._running:
            return

        logger.info("Stopping AITuber pipeline...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellation
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Disconnect from services
        try:
            await self.chat_client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting chat: {e}")

        if self.avatar_controller:
            try:
                await self.avatar_controller.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting avatar: {e}")

        # Close TTS session if needed
        if hasattr(self.tts_engine, "close"):
            try:
                await self.tts_engine.close()  # type: ignore
            except Exception as e:
                logger.warning(f"Error closing TTS: {e}")

        logger.info("AITuber pipeline stopped")

    async def _on_comment(self, comment: Comment) -> None:
        """Handle incoming comment from chat.

        Args:
            comment: The received comment.
        """
        added = await self.comment_queue.push(comment)
        if added:
            logger.debug(
                f"Queued comment from {comment.user_name}: "
                f"{comment.message[:50]}... (priority={comment.priority})"
            )

    async def _process_comments(self) -> None:
        """Process comments from queue continuously."""
        logger.info("Comment processor started")

        while self._running:
            try:
                # Get next comment
                comment = await self.comment_queue.pop()

                if comment:
                    await self._handle_comment(comment)

                # Wait before processing next comment
                await asyncio.sleep(self.response_interval)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error processing comment: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error

    async def _handle_comment(self, comment: Comment) -> None:
        """Process a single comment through the full pipeline.

        Args:
            comment: The comment to process.
        """
        logger.info(
            "Processing comment from %s: %s",
            comment.user_name,
            comment.message,
        )

        try:
            # Step 1: Get context (short-term + long-term memory)
            formatted_message = f"{comment.user_name}さん: {comment.message}"
            context = self.memory.get_context()

            # Retrieve relevant long-term memories if available
            memory_context = ""
            if self.memory_retriever:
                try:
                    memory_context = await self.memory_retriever.retrieve_context(
                        comment.message,
                        user_name=comment.user_name,
                    )
                except Exception as e:
                    logger.warning("Long-term memory retrieval failed: %s", e)

            # Step 2: Generate AI response
            response = await self.llm_client.generate_response(
                formatted_message,
                context,
                additional_context=memory_context if memory_context else None,
            )

            logger.info("AI response: %s", response)

            # Update short-term memory
            self.memory.add_user_message(comment.message, comment.user_name)
            self.memory.add_assistant_message(response)

            # Step 3: Analyze emotion and update expression
            emotion_str = None
            if self._expression_controller:
                try:
                    emotion_result = await self._expression_controller.process_text(
                        response
                    )
                    emotion_str = emotion_result.primary_emotion.value
                    logger.debug("Detected emotion: %s", emotion_str)
                except Exception as e:
                    logger.warning("Emotion analysis failed: %s", e)

            # Step 4: Store in long-term memory if available
            if self.memory_retriever:
                try:
                    await self.memory_retriever.store_interaction(
                        user_name=comment.user_name,
                        user_message=comment.message,
                        ai_response=response,
                        emotion=emotion_str,
                    )
                except Exception as e:
                    logger.warning("Long-term memory storage failed: %s", e)

            # Step 5: Synthesize speech
            audio = await self.tts_engine.synthesize(
                response,
                speaker_id=self.speaker_id,
            )

            logger.debug("Synthesized %d bytes of audio", len(audio.data))

            # Step 6: Play audio with lip sync
            if self._lip_sync and self.avatar_controller:
                # Run lip sync and audio playback concurrently
                await asyncio.gather(
                    self._lip_sync.sync_with_audio(audio.data),
                    self.audio_player.play(audio.data),
                )
            else:
                # Just play audio
                await self.audio_player.play(audio.data)

            logger.info("Response delivered successfully")

        except Exception as e:
            logger.error("Error handling comment: %s", e, exc_info=True)

    async def respond_to_text(self, text: str, user_name: str = "User") -> str:
        """Manually respond to a text input.

        This is useful for testing or direct interaction.

        Args:
            text: The text to respond to.
            user_name: Name to use for the user.

        Returns:
            The generated response text.
        """
        logger.info(f"Manual response request: {text}")

        formatted_message = f"{user_name}さん: {text}"
        context = self.memory.get_context()

        response = await self.llm_client.generate_response(
            formatted_message,
            context,
        )

        self.memory.add_user_message(text, user_name)
        self.memory.add_assistant_message(response)

        # Synthesize and play
        audio = await self.tts_engine.synthesize(
            response,
            speaker_id=self.speaker_id,
        )

        if self._lip_sync and self.avatar_controller:
            await asyncio.gather(
                self._lip_sync.sync_with_audio(audio.data),
                self.audio_player.play(audio.data),
            )
        else:
            await self.audio_player.play(audio.data)

        return response
