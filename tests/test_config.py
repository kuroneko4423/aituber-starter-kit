"""Tests for configuration module."""

from pathlib import Path

import pytest
import yaml

from src.config import (
    AppConfig,
    LLMConfig,
    TTSConfig,
    AvatarConfig,
    CommentConfig,
    PlatformConfig,
    load_config,
)


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 150

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet",
            temperature=0.9,
            max_tokens=200,
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.temperature == 0.9
        assert config.max_tokens == 200

    def test_temperature_bounds(self) -> None:
        """Test temperature value bounds."""
        # Valid values
        config = LLMConfig(temperature=0.0)
        assert config.temperature == 0.0

        config = LLMConfig(temperature=2.0)
        assert config.temperature == 2.0


class TestTTSConfig:
    """Tests for TTSConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TTSConfig()
        assert config.engine == "voicevox"
        assert config.host == "localhost"
        assert config.port == 50021
        assert config.speaker_id == 1
        assert config.speed == 1.0

    def test_speed_bounds(self) -> None:
        """Test speed value bounds."""
        config = TTSConfig(speed=0.5)
        assert config.speed == 0.5

        config = TTSConfig(speed=2.0)
        assert config.speed == 2.0


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = AppConfig()
        assert config.platform.name == "youtube"
        assert config.llm.provider == "openai"
        assert config.tts.engine == "voicevox"
        assert config.avatar.enabled is True


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_file(self) -> None:
        """Test loading config when file doesn't exist."""
        config = load_config(Path("nonexistent.yaml"))
        assert isinstance(config, AppConfig)
        # Should return default config
        assert config.platform.name == "youtube"

    def test_load_valid_config(
        self,
        test_config_dir: Path,
        sample_config_yaml: str,
    ) -> None:
        """Test loading valid config file."""
        config_file = test_config_dir / "config.yaml"
        config_file.write_text(sample_config_yaml)

        config = load_config(config_file)
        assert config.platform.video_id == "test_video_id"
        assert config.llm.model == "gpt-4o-mini"
        assert config.avatar.enabled is False
