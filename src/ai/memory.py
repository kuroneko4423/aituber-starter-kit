"""Conversation memory management for context retention."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """A single message in conversation history.

    Attributes:
        role: The role of the message sender ("user" or "assistant").
        content: The message content.
        timestamp: When the message was created.
        user_name: Optional name of the user (for user messages).
    """

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    user_name: Optional[str] = None


class ConversationMemory:
    """Manages conversation history with a sliding window.

    This class maintains a limited history of conversation messages
    for providing context to the LLM.

    Args:
        max_messages: Maximum number of messages to retain.

    Example:
        ```python
        memory = ConversationMemory(max_messages=20)
        memory.add_user_message("Hello!", user_name="Viewer123")
        memory.add_assistant_message("Hi there!")

        context = memory.get_context()
        # [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]
        ```
    """

    def __init__(self, max_messages: int = 20) -> None:
        """Initialize conversation memory.

        Args:
            max_messages: Maximum messages to keep in history.
        """
        self._messages: list[Message] = []
        self._max_messages = max_messages

    def add_user_message(
        self, content: str, user_name: Optional[str] = None
    ) -> None:
        """Add a user message to history.

        Args:
            content: The message content.
            user_name: Optional name of the user.
        """
        self._messages.append(
            Message(
                role="user",
                content=content,
                user_name=user_name,
            )
        )
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant (AI) message to history.

        Args:
            content: The message content.
        """
        self._messages.append(
            Message(
                role="assistant",
                content=content,
            )
        )
        self._trim()

    def _trim(self) -> None:
        """Trim messages to max size, keeping most recent."""
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages :]

    def get_context(self) -> list[dict[str, str]]:
        """Get conversation context for LLM.

        Returns:
            List of message dictionaries with "role" and "content" keys.
        """
        return [{"role": msg.role, "content": msg.content} for msg in self._messages]

    def get_context_with_names(self) -> list[dict[str, str]]:
        """Get conversation context with user names included.

        For user messages, the content will be prefixed with the user name
        if available.

        Returns:
            List of message dictionaries.
        """
        result = []
        for msg in self._messages:
            if msg.role == "user" and msg.user_name:
                content = f"{msg.user_name}さん: {msg.content}"
            else:
                content = msg.content
            result.append({"role": msg.role, "content": content})
        return result

    def get_recent_messages(self, n: int) -> list[Message]:
        """Get the n most recent messages.

        Args:
            n: Number of messages to retrieve.

        Returns:
            List of recent Message objects.
        """
        return self._messages[-n:] if n > 0 else []

    def clear(self) -> None:
        """Clear all conversation history."""
        self._messages.clear()

    def __len__(self) -> int:
        """Get the number of messages in memory.

        Returns:
            Number of messages.
        """
        return len(self._messages)

    @property
    def is_empty(self) -> bool:
        """Check if memory is empty.

        Returns:
            True if no messages in memory.
        """
        return len(self._messages) == 0

    def get_summary(self) -> str:
        """Get a brief summary of the conversation.

        Returns:
            Summary string with message count and recent topics.
        """
        if not self._messages:
            return "No conversation history."

        user_msgs = [m for m in self._messages if m.role == "user"]
        return f"Conversation history: {len(self._messages)} messages, {len(user_msgs)} from users."
