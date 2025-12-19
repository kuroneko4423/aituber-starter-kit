"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from .character import Character


class BaseLLMClient(ABC):
    """Abstract base class for LLM (Large Language Model) clients.

    This class defines the interface for all LLM implementations.
    Subclasses must implement generate_response() and stream_response().

    Example:
        ```python
        class MyLLMClient(BaseLLMClient):
            async def generate_response(
                self, message: str, context: list[dict[str, str]]
            ) -> str:
                # Call LLM API and return response
                return "Hello!"

            async def stream_response(
                self, message: str, context: list[dict[str, str]]
            ) -> AsyncGenerator[str, None]:
                # Stream response tokens
                yield "Hello"
                yield "!"
        ```
    """

    def __init__(self) -> None:
        """Initialize the LLM client."""
        self._character: Optional[Character] = None

    @property
    def character(self) -> Optional[Character]:
        """Get the current character configuration.

        Returns:
            Current Character or None if not set.
        """
        return self._character

    def set_character(self, character: Character) -> None:
        """Set the character for response generation.

        The character's system prompt will be used in all subsequent
        API calls.

        Args:
            character: Character configuration to use.
        """
        self._character = character

    @abstractmethod
    async def generate_response(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> str:
        """Generate a response to the given message.

        Args:
            message: The user message to respond to.
            context: Previous conversation history as list of
                    {"role": "user"|"assistant", "content": "..."} dicts.

        Returns:
            The generated response text.

        Raises:
            Exception: If API call fails.
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Stream a response token by token.

        This is useful for real-time display of responses as they
        are generated.

        Args:
            message: The user message to respond to.
            context: Previous conversation history.

        Yields:
            Response tokens as they are generated.

        Raises:
            Exception: If API call fails.
        """
        # This is a generator, must use yield
        yield  # type: ignore

    def _build_system_prompt(self) -> str:
        """Build the system prompt from character settings.

        Returns:
            System prompt string, or default if no character set.
        """
        if self._character is None:
            return (
                "あなたは親しみやすいAITuberです。"
                "視聴者からのコメントに対して、フレンドリーに応答してください。"
                "応答は簡潔に（1-3文程度）してください。"
            )
        return self._character.to_system_prompt()

    def _build_messages(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Build the full messages list for API call.

        Args:
            message: The current user message.
            context: Previous conversation history.

        Returns:
            Complete messages list including system prompt.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        messages.extend(context)
        messages.append({"role": "user", "content": message})
        return messages
