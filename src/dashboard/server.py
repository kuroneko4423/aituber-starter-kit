"""Dashboard server management."""

import asyncio
import logging
from typing import Optional

import uvicorn

from .api import create_app

logger = logging.getLogger(__name__)


class DashboardServer:
    """Manages the dashboard web server.

    This class handles starting and stopping the FastAPI/Uvicorn server
    that provides the dashboard API.

    Args:
        host: Host address to bind to.
        port: Port number to listen on.

    Example:
        ```python
        server = DashboardServer(host="0.0.0.0", port=8080)
        server.set_pipeline(pipeline)
        await server.start()
        # ... later
        await server.stop()
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
    ) -> None:
        """Initialize the dashboard server.

        Args:
            host: Host address to bind to.
            port: Port number to listen on.
        """
        self.host = host
        self.port = port
        self.app = create_app()
        self._server: Optional[uvicorn.Server] = None
        self._server_task: Optional[asyncio.Task] = None

        logger.info(f"Dashboard server initialized (http://{host}:{port})")

    def set_pipeline(self, pipeline) -> None:
        """Set the pipeline reference for the dashboard.

        Args:
            pipeline: AITuberPipeline instance.
        """
        self.app.state.pipeline = pipeline
        logger.info("Pipeline attached to dashboard")

    def set_memory_store(self, memory_store) -> None:
        """Set the long-term memory store.

        Args:
            memory_store: LongTermMemory instance.
        """
        self.app.state.memory_store = memory_store
        logger.info("Memory store attached to dashboard")

    async def start(self) -> None:
        """Start the dashboard server."""
        if self._server_task and not self._server_task.done():
            logger.warning("Dashboard server already running")
            return

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        logger.info(f"Starting dashboard server at http://{self.host}:{self.port}")
        self._server_task = asyncio.create_task(self._server.serve())

    async def stop(self) -> None:
        """Stop the dashboard server."""
        if self._server:
            logger.info("Stopping dashboard server...")
            self._server.should_exit = True

            if self._server_task:
                try:
                    await asyncio.wait_for(self._server_task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Dashboard server stop timed out")
                except asyncio.CancelledError:
                    pass

            self._server = None
            self._server_task = None
            logger.info("Dashboard server stopped")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._server_task is not None and not self._server_task.done()

    def get_url(self) -> str:
        """Get the dashboard URL.

        Returns:
            The URL where the dashboard is accessible.
        """
        return f"http://{self.host}:{self.port}"

    def add_comment(self, comment_data: dict) -> None:
        """Add a comment to the dashboard state.

        This is called by the pipeline when a new comment is received.

        Args:
            comment_data: Comment data dictionary.
        """
        from .models import CommentData

        try:
            comment = CommentData(**comment_data)
            self.app.state.recent_comments.append(comment)

            # Keep only last 100 comments
            if len(self.app.state.recent_comments) > 100:
                self.app.state.recent_comments = self.app.state.recent_comments[-100:]

            self.app.state.stats["comments_processed"] += 1

            # Broadcast to WebSocket clients
            asyncio.create_task(self._broadcast_comment(comment))
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")

    def add_response(self, response_data: dict) -> None:
        """Add a response to the dashboard state.

        This is called by the pipeline when a new response is generated.

        Args:
            response_data: Response data dictionary.
        """
        from .models import ResponseData

        try:
            response = ResponseData(**response_data)
            self.app.state.recent_responses.append(response)

            # Keep only last 100 responses
            if len(self.app.state.recent_responses) > 100:
                self.app.state.recent_responses = self.app.state.recent_responses[-100:]

            self.app.state.stats["responses_generated"] += 1

            # Broadcast to WebSocket clients
            asyncio.create_task(self._broadcast_response(response))
        except Exception as e:
            logger.error(f"Failed to add response: {e}")

    async def _broadcast_comment(self, comment) -> None:
        """Broadcast comment to WebSocket clients."""
        from .api import _broadcast_comment

        await _broadcast_comment(self.app, comment)

    async def _broadcast_response(self, response) -> None:
        """Broadcast response to WebSocket clients."""
        from .api import _broadcast_response

        await _broadcast_response(self.app, response)
