"""YouTube Live chat client implementation."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from .base import BaseChatClient
from .models import Comment, Platform

logger = logging.getLogger(__name__)


class YouTubeChatClient(BaseChatClient):
    """YouTube Live chat client using pytchat.

    This client connects to YouTube Live chat and retrieves comments
    in real-time using the pytchat library.

    Args:
        video_id: The YouTube video ID (from the URL).
                 e.g., for "https://youtube.com/watch?v=XXXXX", use "XXXXX"

    Example:
        ```python
        client = YouTubeChatClient("dQw4w9WgXcQ")
        await client.connect()
        client.on_comment(lambda c: print(c.message))
        await client.start_listening()
        ```
    """

    def __init__(self, video_id: str) -> None:
        """Initialize the YouTube chat client.

        Args:
            video_id: YouTube video ID to connect to.
        """
        super().__init__()
        self.video_id = video_id
        self._chat: Optional[object] = None
        self._comment_buffer: asyncio.Queue[Comment] = asyncio.Queue()

    async def connect(self) -> None:
        """Connect to YouTube Live chat.

        Raises:
            ImportError: If pytchat is not installed.
            ConnectionError: If connection to the chat fails.
        """
        if self._is_connected:
            logger.warning("Already connected to YouTube chat")
            return

        try:
            import pytchat
        except ImportError as e:
            raise ImportError(
                "pytchat is required for YouTube chat. "
                "Install with: pip install pytchat"
            ) from e

        try:
            self._chat = pytchat.create(video_id=self.video_id)
            self._is_connected = True
            logger.info(f"Connected to YouTube chat for video: {self.video_id}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to YouTube chat: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from YouTube Live chat."""
        if self._chat is not None:
            try:
                self._chat.terminate()  # type: ignore
            except Exception as e:
                logger.warning(f"Error terminating YouTube chat: {e}")
            self._chat = None

        self._is_connected = False
        logger.info("Disconnected from YouTube chat")

    async def fetch_comments(self) -> AsyncGenerator[Comment, None]:
        """Fetch comments from YouTube Live chat.

        Yields:
            Comment objects as they arrive.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._chat:
            raise RuntimeError("Not connected. Call connect() first.")

        while self._chat.is_alive():  # type: ignore
            try:
                # pytchat is synchronous, run in thread pool
                chat_data = await asyncio.get_event_loop().run_in_executor(
                    None, self._get_chat_items
                )

                for item in chat_data:
                    comment = self._parse_chat_item(item)
                    yield comment

            except Exception as e:
                logger.error(f"Error fetching YouTube comments: {e}")

            # Small delay to prevent tight loop
            await asyncio.sleep(0.5)

    def _get_chat_items(self) -> list:
        """Get chat items from pytchat (synchronous).

        Returns:
            List of chat items.
        """
        if not self._chat:
            return []

        items = []
        chat_data = self._chat.get()  # type: ignore
        for item in chat_data.items:
            items.append(item)
        return items

    def _parse_chat_item(self, item: object) -> Comment:
        """Parse a pytchat item into a Comment model.

        Args:
            item: Raw pytchat chat item.

        Returns:
            Parsed Comment object.
        """
        # Extract donation information
        donation_amount = 0
        donation_currency = None

        # Check for super chat
        if hasattr(item, "amountValue") and item.amountValue:  # type: ignore
            try:
                donation_amount = int(float(item.amountValue))  # type: ignore
            except (ValueError, TypeError):
                donation_amount = 0

            if hasattr(item, "currency"):
                donation_currency = str(item.currency)  # type: ignore

        # Parse timestamp
        timestamp = datetime.now()
        if hasattr(item, "datetime"):
            try:
                timestamp = datetime.fromisoformat(str(item.datetime))  # type: ignore
            except (ValueError, TypeError):
                pass

        # Check membership/moderator status
        is_member = False
        is_moderator = False

        if hasattr(item, "author"):
            author = item.author  # type: ignore
            if hasattr(author, "isChatSponsor"):
                is_member = bool(author.isChatSponsor)
            if hasattr(author, "isChatModerator"):
                is_moderator = bool(author.isChatModerator)
            if hasattr(author, "isChatOwner") and author.isChatOwner:
                is_moderator = True

        # Build Comment object
        return Comment(
            id=str(item.id) if hasattr(item, "id") else str(hash(item)),  # type: ignore
            platform=Platform.YOUTUBE,
            user_id=(
                str(item.author.channelId)  # type: ignore
                if hasattr(item, "author") and hasattr(item.author, "channelId")  # type: ignore
                else "unknown"
            ),
            user_name=(
                str(item.author.name)  # type: ignore
                if hasattr(item, "author") and hasattr(item.author, "name")  # type: ignore
                else "Anonymous"
            ),
            message=str(item.message) if hasattr(item, "message") else "",  # type: ignore
            timestamp=timestamp,
            is_member=is_member,
            is_moderator=is_moderator,
            donation_amount=donation_amount,
            donation_currency=donation_currency,
        )
