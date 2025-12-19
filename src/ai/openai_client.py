"""OpenAI API client implementation."""

import logging
import os
from typing import AsyncGenerator

from openai import AsyncOpenAI

from .base import BaseLLMClient
from ..config import settings

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client for response generation.

    This client uses the OpenAI API (GPT models) to generate
    character-appropriate responses.

    Args:
        model: The model to use (e.g., "gpt-4o-mini", "gpt-4o").
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens in response.
        api_key: Optional API key (uses env var if not provided).

    Example:
        ```python
        client = OpenAIClient(model="gpt-4o-mini", temperature=0.7)
        client.set_character(character)

        response = await client.generate_response(
            "Hello!",
            context=[{"role": "user", "content": "Hi"}]
        )
        ```
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 150,
        api_key: str | None = None,
    ) -> None:
        """Initialize the OpenAI client.

        Args:
            model: OpenAI model name.
            temperature: Response randomness (0.0-2.0).
            max_tokens: Maximum response length.
            api_key: API key (falls back to env var).
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Get API key from parameter, settings, or environment
        resolved_api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")

        if not resolved_api_key:
            logger.warning(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )

        self._client = AsyncOpenAI(api_key=resolved_api_key)
        logger.info(f"Initialized OpenAI client with model: {model}")

    async def generate_response(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> str:
        """Generate a response using the OpenAI API.

        Args:
            message: User message to respond to.
            context: Previous conversation history.

        Returns:
            Generated response text.

        Raises:
            openai.OpenAIError: If API call fails.
        """
        messages = self._build_messages(message, context)

        logger.debug(f"Generating response for: {message[:50]}...")

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        result = response.choices[0].message.content or ""
        logger.debug(f"Generated response: {result[:50]}...")

        return result

    async def stream_response(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Stream a response token by token.

        Args:
            message: User message to respond to.
            context: Previous conversation history.

        Yields:
            Response tokens as they are generated.

        Raises:
            openai.OpenAIError: If API call fails.
        """
        messages = self._build_messages(message, context)

        logger.debug(f"Streaming response for: {message[:50]}...")

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_with_emotion(
        self,
        message: str,
        context: list[dict[str, str]],
    ) -> tuple[str, str]:
        """Generate a response with emotion detection.

        This method asks the model to also identify the emotion
        of the response for expression control.

        Args:
            message: User message to respond to.
            context: Previous conversation history.

        Returns:
            Tuple of (response_text, detected_emotion).
        """
        # Add instruction to include emotion
        emotion_instruction = (
            "\n\n応答の最後に、あなたの感情を [emotion:感情名] の形式で追加してください。"
            "感情は happy, sad, surprised, angry, thinking のいずれかです。"
        )

        messages = self._build_messages(message, context)
        messages[0]["content"] += emotion_instruction

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            temperature=self.temperature,
            max_tokens=self.max_tokens + 20,  # Extra tokens for emotion tag
        )

        result = response.choices[0].message.content or ""

        # Parse emotion from response
        import re

        emotion_match = re.search(r"\[emotion:(\w+)\]", result)
        if emotion_match:
            emotion = emotion_match.group(1)
            # Remove emotion tag from response
            result = re.sub(r"\s*\[emotion:\w+\]\s*", "", result)
        else:
            emotion = "neutral"

        return result, emotion
