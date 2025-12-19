"""Tests for factory module."""

import pytest
from unittest.mock import MagicMock, patch

from src.config import AppConfig, Settings, PlatformConfig, LLMConfig, TTSConfig
from src.factory import (
    create_chat_client,
    create_llm_client,
    create_tts_engine,
    create_avatar_controller,
)
from src.chat.youtube_chat import YouTubeChatClient
from src.ai.openai_client import OpenAIClient
from src.ai.ollama_client import OllamaClient
from src.tts.voicevox import VoicevoxEngine
from src.tts.coeiroink import CoeiroinkEngine


class TestCreateChatClient:
    """Test create_chat_client function."""

    def test_create_youtube_client(self):
        """Test creating YouTube chat client."""
        config = AppConfig(
            platform=PlatformConfig(
                name="youtube",
                video_id="test_video_id",
            )
        )
        settings = Settings()

        client = create_chat_client(config, settings)

        assert isinstance(client, YouTubeChatClient)

    def test_create_youtube_client_without_video_id(self):
        """Test error when video_id is missing."""
        config = AppConfig(
            platform=PlatformConfig(
                name="youtube",
                video_id=None,
            )
        )
        settings = Settings()

        with pytest.raises(ValueError, match="video_id is required"):
            create_chat_client(config, settings)

    def test_create_twitch_client_without_token(self):
        """Test error when Twitch token is missing."""
        config = AppConfig(
            platform=PlatformConfig(
                name="twitch",
                twitch_channel="test_channel",
            )
        )
        settings = Settings(twitch_access_token=None)

        with pytest.raises(ValueError, match="TWITCH_ACCESS_TOKEN is required"):
            create_chat_client(config, settings)

    def test_unsupported_platform(self):
        """Test error for unsupported platform."""
        config = AppConfig(
            platform=PlatformConfig(
                name="unsupported",
            )
        )
        settings = Settings()

        with pytest.raises(ValueError, match="Unsupported platform"):
            create_chat_client(config, settings)


class TestCreateLLMClient:
    """Test create_llm_client function."""

    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        config = AppConfig(
            llm=LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                temperature=0.7,
            )
        )
        settings = Settings(openai_api_key="test-key")

        client = create_llm_client(config, settings)

        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4o-mini"

    def test_create_openai_client_without_key(self):
        """Test error when OpenAI key is missing."""
        config = AppConfig(
            llm=LLMConfig(provider="openai")
        )
        settings = Settings(openai_api_key="")

        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            create_llm_client(config, settings)

    def test_create_anthropic_client_without_key(self):
        """Test error when Anthropic key is missing."""
        config = AppConfig(
            llm=LLMConfig(provider="anthropic")
        )
        settings = Settings(anthropic_api_key=None)

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            create_llm_client(config, settings)

    def test_create_google_client_without_key(self):
        """Test error when Google key is missing."""
        config = AppConfig(
            llm=LLMConfig(provider="google")
        )
        settings = Settings(google_api_key=None)

        with pytest.raises(ValueError, match="GOOGLE_API_KEY is required"):
            create_llm_client(config, settings)

    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        config = AppConfig(
            llm=LLMConfig(
                provider="ollama",
                model="llama3.1",
                ollama_host="localhost",
                ollama_port=11434,
            )
        )
        settings = Settings()

        client = create_llm_client(config, settings)

        assert isinstance(client, OllamaClient)
        assert client.model == "llama3.1"
        assert client.host == "localhost"
        assert client.port == 11434

    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        config = AppConfig(
            llm=LLMConfig(provider="unsupported")
        )
        settings = Settings()

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client(config, settings)


class TestCreateTTSEngine:
    """Test create_tts_engine function."""

    def test_create_voicevox_engine(self):
        """Test creating VOICEVOX engine."""
        config = AppConfig(
            tts=TTSConfig(
                engine="voicevox",
                host="localhost",
                port=50021,
                speaker_id=1,
            )
        )
        settings = Settings()

        engine = create_tts_engine(config, settings)

        assert isinstance(engine, VoicevoxEngine)
        assert engine.speaker_id == 1

    def test_create_coeiroink_engine(self):
        """Test creating COEIROINK engine."""
        config = AppConfig(
            tts=TTSConfig(
                engine="coeiroink",
                host="localhost",
                port=50032,
            )
        )
        settings = Settings()

        engine = create_tts_engine(config, settings)

        assert isinstance(engine, CoeiroinkEngine)
        assert engine.port == 50032

    def test_create_coeiroink_engine_default_port(self):
        """Test COEIROINK uses its default port when VOICEVOX port is specified."""
        config = AppConfig(
            tts=TTSConfig(
                engine="coeiroink",
                host="localhost",
                port=50021,  # VOICEVOX default port
            )
        )
        settings = Settings()

        engine = create_tts_engine(config, settings)

        assert isinstance(engine, CoeiroinkEngine)
        assert engine.port == 50032  # Should use COEIROINK default

    def test_create_nijivoice_without_key(self):
        """Test error when Nijivoice API key is missing."""
        config = AppConfig(
            tts=TTSConfig(
                engine="nijivoice",
                nijivoice_actor_id="test-actor",
            )
        )
        settings = Settings(nijivoice_api_key=None)

        with pytest.raises(ValueError, match="NIJIVOICE_API_KEY is required"):
            create_tts_engine(config, settings)

    def test_create_nijivoice_without_actor_id(self):
        """Test error when Nijivoice actor_id is missing."""
        config = AppConfig(
            tts=TTSConfig(
                engine="nijivoice",
                nijivoice_actor_id="",
            )
        )
        settings = Settings(nijivoice_api_key="test-key")

        with pytest.raises(ValueError, match="actor_id is required"):
            create_tts_engine(config, settings)

    def test_unsupported_engine(self):
        """Test error for unsupported engine."""
        config = AppConfig(
            tts=TTSConfig(engine="unsupported")
        )
        settings = Settings()

        with pytest.raises(ValueError, match="Unsupported TTS engine"):
            create_tts_engine(config, settings)


class TestCreateAvatarController:
    """Test create_avatar_controller function."""

    def test_create_vtube_studio_controller(self):
        """Test creating VTube Studio controller."""
        config = AppConfig()  # Uses defaults

        controller = create_avatar_controller(config)

        assert controller is not None
        assert controller.host == "localhost"
        assert controller.port == 8001

    def test_disabled_avatar(self):
        """Test that None is returned when avatar is disabled."""
        from src.config import AvatarConfig

        config = AppConfig(
            avatar=AvatarConfig(enabled=False)
        )

        controller = create_avatar_controller(config)

        assert controller is None
