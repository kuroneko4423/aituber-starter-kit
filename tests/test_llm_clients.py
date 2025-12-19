"""Tests for LLM client modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.anthropic_client import AnthropicClient, ANTHROPIC_AVAILABLE
from src.ai.google_client import GoogleClient, GOOGLE_AI_AVAILABLE
from src.ai.ollama_client import OllamaClient
from src.ai.character import Character


class TestAnthropicClient:
    """Test AnthropicClient class."""

    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client."""
        with patch("src.ai.anthropic_client.AsyncAnthropic") as mock:
            yield mock

    @pytest.mark.skipif(
        not ANTHROPIC_AVAILABLE,
        reason="anthropic not installed",
    )
    def test_init(self, mock_anthropic):
        """Test client initialization."""
        client = AnthropicClient(
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=150,
        )

        assert client.model == "claude-3-5-sonnet-20241022"
        assert client.temperature == 0.7
        assert client.max_tokens == 150
        assert client.provider_name == "anthropic"

    @pytest.mark.skipif(
        not ANTHROPIC_AVAILABLE,
        reason="anthropic not installed",
    )
    def test_set_character(self, mock_anthropic):
        """Test setting character."""
        client = AnthropicClient(api_key="test-key")

        character = Character(
            name="TestChar",
            personality="Test personality",
        )
        client.set_character(character)

        assert client._character == character

    @pytest.mark.skipif(
        not ANTHROPIC_AVAILABLE,
        reason="anthropic not installed",
    )
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_anthropic):
        """Test generating response."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello! Nice to meet you!")]
        mock_anthropic.return_value.messages.create = AsyncMock(
            return_value=mock_response
        )

        client = AnthropicClient(api_key="test-key")
        response = await client.generate_response("Hello!")

        assert response == "Hello! Nice to meet you!"


class TestGoogleClient:
    """Test GoogleClient class."""

    @pytest.fixture
    def mock_genai(self):
        """Mock Google Generative AI."""
        with patch("src.ai.google_client.genai") as mock:
            yield mock

    @pytest.mark.skipif(
        not GOOGLE_AI_AVAILABLE,
        reason="google-generativeai not installed",
    )
    def test_init(self, mock_genai):
        """Test client initialization."""
        client = GoogleClient(
            api_key="test-key",
            model="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=150,
        )

        assert client.model == "gemini-1.5-flash"
        assert client.temperature == 0.7
        assert client.max_tokens == 150
        assert client.provider_name == "google"

    @pytest.mark.skipif(
        not GOOGLE_AI_AVAILABLE,
        reason="google-generativeai not installed",
    )
    def test_set_character(self, mock_genai):
        """Test setting character."""
        client = GoogleClient(api_key="test-key")

        character = Character(
            name="TestChar",
            personality="Test personality",
        )
        client.set_character(character)

        assert client._character == character


class TestOllamaClient:
    """Test OllamaClient class."""

    def test_init(self):
        """Test client initialization."""
        client = OllamaClient(
            model="llama3.1",
            host="localhost",
            port=11434,
            temperature=0.7,
            max_tokens=150,
        )

        assert client.model == "llama3.1"
        assert client.host == "localhost"
        assert client.port == 11434
        assert client.base_url == "http://localhost:11434"
        assert client.provider_name == "ollama"

    def test_set_character(self):
        """Test setting character."""
        client = OllamaClient(model="llama3.1")

        character = Character(
            name="TestChar",
            personality="Test personality",
        )
        client.set_character(character)

        assert client._character == character

    def test_build_system_prompt_without_character(self):
        """Test building system prompt without character."""
        client = OllamaClient(model="llama3.1")
        prompt = client._build_system_prompt()

        assert prompt == "You are a helpful AI assistant."

    def test_build_system_prompt_with_character(self):
        """Test building system prompt with character."""
        client = OllamaClient(model="llama3.1")

        character = Character(
            name="TestChar",
            personality="Test personality",
        )
        client.set_character(character)

        prompt = client._build_system_prompt()
        assert "TestChar" in prompt

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """Test connection check when server is not available."""
        client = OllamaClient(
            model="llama3.1",
            host="nonexistent-host",
            port=11434,
        )

        result = await client.check_connection()
        assert result is False

        await client.close()

    def test_build_messages(self):
        """Test building messages list."""
        client = OllamaClient(model="llama3.1")

        messages = client._build_messages("Hello!", context=None)

        # Should have system prompt and user message
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"

    def test_build_messages_with_context(self):
        """Test building messages with context."""
        client = OllamaClient(model="llama3.1")

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]
        messages = client._build_messages("New message", context=context)

        # Should have system prompt + context + current message
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Previous message"
        assert messages[2]["content"] == "Previous response"
        assert messages[3]["content"] == "New message"
