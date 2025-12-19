"""Abstract base class for chat platform clients."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable, Optional, Union
import asyncio

from .models import Comment


# Type alias for comment callbacks
CommentCallback = Callable[[Comment], Union[None, "asyncio.Future[None]"]]


class BaseChatClient(ABC):
    """Abstract base class for chat platform clients.

    This class defines the interface for all chat platform implementations.
    Subclasses must implement connect(), disconnect(), and fetch_comments().

    Example:
        ```python
        class MyChatClient(BaseChatClient):
            async def connect(self) -> None:
                # Connect to platform
                pass

            async def disconnect(self) -> None:
                # Disconnect from platform
                pass

            async def fetch_comments(self) -> AsyncGenerator[Comment, None]:
                # Yield comments as they arrive
                yield comment
        ```
    """

    def __init__(self) -> None:
        """Initialize the chat client."""
        self._callbacks: list[CommentCallback] = []
        self._is_connected: bool = False
        self._task: Optional[asyncio.Task[None]] = None

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._is_connected

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the chat platform.

        This method should establish the connection to the streaming platform
        and prepare for receiving comments.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the chat platform.

        This method should cleanly close all connections and release resources.
        """
        pass

    @abstractmethod
    async def fetch_comments(self) -> AsyncGenerator[Comment, None]:
        """Fetch comments as an async generator.

        This method should continuously yield Comment objects as they arrive
        from the platform.

        Yields:
            Comment objects from the chat.
        """
        # This is a generator, must use yield
        yield  # type: ignore

    def on_comment(self, callback: CommentCallback) -> None:
        """Register a callback for new comments.

        The callback will be called with each new Comment received.

        Args:
            callback: Function to call when a comment is received.
                     Can be sync or async.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: CommentCallback) -> None:
        """Remove a previously registered callback.

        Args:
            callback: The callback to remove.
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _notify_callbacks(self, comment: Comment) -> None:
        """Notify all registered callbacks of a new comment.

        Args:
            comment: The comment to pass to callbacks.
        """
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(comment)
                else:
                    callback(comment)
            except Exception as e:
                # Log but don't propagate callback errors
                import logging

                logging.getLogger(__name__).error(
                    f"Error in comment callback: {e}", exc_info=True
                )

    async def start_listening(self) -> None:
        """Start the comment listening loop.

        This method will continuously fetch comments and notify callbacks.
        It runs until disconnect() is called or an error occurs.
        """
        if not self._is_connected:
            raise RuntimeError("Not connected. Call connect() first.")

        async for comment in self.fetch_comments():
            await self._notify_callbacks(comment)
