"""Priority queue for managing incoming comments."""

import asyncio
import heapq
import logging
import re
from pathlib import Path
from typing import Optional

from .models import Comment

logger = logging.getLogger(__name__)


class CommentQueue:
    """Priority queue for managing and filtering incoming comments.

    Comments are ordered by priority (higher priority first), with support
    for NG word filtering and duplicate detection.

    Args:
        max_size: Maximum number of comments to keep in queue.
        ng_words: Set of words to filter out.

    Example:
        ```python
        queue = CommentQueue(max_size=100)
        queue.set_ng_words({"spam", "badword"})

        await queue.push(comment)
        next_comment = await queue.pop()
        ```
    """

    def __init__(
        self,
        max_size: int = 100,
        ng_words: Optional[set[str]] = None,
    ) -> None:
        """Initialize the comment queue.

        Args:
            max_size: Maximum queue size.
            ng_words: Initial set of NG words to filter.
        """
        self._queue: list[Comment] = []
        self._max_size = max_size
        self._ng_words: set[str] = ng_words or set()
        self._ng_pattern: Optional[re.Pattern[str]] = None
        self._seen_ids: set[str] = set()
        self._lock = asyncio.Lock()

        if self._ng_words:
            self._compile_ng_pattern()

    def _compile_ng_pattern(self) -> None:
        """Compile NG words into a regex pattern."""
        if not self._ng_words:
            self._ng_pattern = None
            return

        # Escape special regex characters and join with OR
        escaped = [re.escape(word) for word in self._ng_words]
        self._ng_pattern = re.compile("|".join(escaped), re.IGNORECASE)

    def set_ng_words(self, words: set[str]) -> None:
        """Update the NG words list.

        Args:
            words: New set of NG words.
        """
        self._ng_words = words
        self._compile_ng_pattern()
        logger.info(f"Updated NG words: {len(words)} words")

    def load_ng_words_from_file(self, file_path: Path) -> None:
        """Load NG words from a file (one word per line).

        Args:
            file_path: Path to the NG words file.
        """
        if not file_path.exists():
            logger.warning(f"NG words file not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            words = {line.strip() for line in f if line.strip()}

        self.set_ng_words(words)
        logger.info(f"Loaded {len(words)} NG words from {file_path}")

    def _is_valid(self, comment: Comment) -> bool:
        """Check if a comment passes all filters.

        Args:
            comment: Comment to validate.

        Returns:
            True if comment is valid, False if it should be filtered.
        """
        # Duplicate check
        if comment.id in self._seen_ids:
            logger.debug(f"Duplicate comment filtered: {comment.id}")
            return False

        # Empty message check
        if not comment.message.strip():
            logger.debug("Empty comment filtered")
            return False

        # NG word check
        if self._ng_pattern and self._ng_pattern.search(comment.message):
            logger.debug(f"NG word found in comment: {comment.message[:30]}...")
            return False

        return True

    async def push(self, comment: Comment) -> bool:
        """Add a comment to the queue.

        Args:
            comment: Comment to add.

        Returns:
            True if the comment was added, False if filtered.
        """
        async with self._lock:
            if not self._is_valid(comment):
                return False

            # Track seen IDs (limit size to prevent memory issues)
            self._seen_ids.add(comment.id)
            if len(self._seen_ids) > self._max_size * 2:
                # Remove oldest half
                self._seen_ids = set(list(self._seen_ids)[self._max_size :])

            # Add to priority queue
            if len(self._queue) >= self._max_size:
                # Replace lowest priority if new comment has higher priority
                heapq.heappushpop(self._queue, comment)
            else:
                heapq.heappush(self._queue, comment)

            logger.debug(
                f"Queued comment from {comment.user_name} "
                f"(priority={comment.priority}, queue_size={len(self._queue)})"
            )
            return True

    async def pop(self) -> Optional[Comment]:
        """Get and remove the highest priority comment.

        Returns:
            The highest priority comment, or None if queue is empty.
        """
        async with self._lock:
            if self._queue:
                return heapq.heappop(self._queue)
            return None

    async def peek(self) -> Optional[Comment]:
        """View the highest priority comment without removing it.

        Returns:
            The highest priority comment, or None if queue is empty.
        """
        async with self._lock:
            if self._queue:
                return self._queue[0]
            return None

    def __len__(self) -> int:
        """Get the current queue size.

        Returns:
            Number of comments in queue.
        """
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if queue has no comments.
        """
        return len(self._queue) == 0

    def clear(self) -> None:
        """Clear all comments from the queue."""
        self._queue.clear()
        logger.info("Comment queue cleared")
