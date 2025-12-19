"""Configuration management for AITuber Starter Kit."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "openai"  # openai / anthropic / google / ollama
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=150, ge=1, le=4096)

    # Ollama specific settings
    ollama_host: str = "localhost"
    ollama_port: int = 11434


class TTSConfig(BaseModel):
    """Text-to-speech configuration."""

    engine: str = "voicevox"  # voicevox / coeiroink / style_bert_vits / nijivoice
    host: str = "localhost"
    port: int = 50021
    speaker_id: int = 1
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-0.15, le=0.15)
    intonation: float = Field(default=1.0, ge=0.0, le=2.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)

    # Style-Bert-VITS2 specific settings
    style_bert_model: str = "default"
    style_bert_style: str = "Neutral"
    style_bert_style_weight: float = 1.0

    # Nijivoice specific settings
    nijivoice_actor_id: str = ""


class AvatarConfig(BaseModel):
    """Avatar control configuration."""

    enabled: bool = True
    host: str = "localhost"
    port: int = 8001
    plugin_name: str = "AITuber Starter Kit"
    plugin_developer: str = "AITuber Community"


class CommentConfig(BaseModel):
    """Comment processing configuration."""

    response_interval: float = Field(default=5.0, ge=1.0)
    priority_donation: bool = True
    max_queue_size: int = 100
    ng_words_file: Optional[Path] = None


class PlatformConfig(BaseModel):
    """Streaming platform configuration."""

    name: str = "youtube"  # youtube / twitch / niconico
    video_id: Optional[str] = None
    channel_id: Optional[str] = None

    # Twitch specific settings
    twitch_channel: Optional[str] = None


class ExpressionConfig(BaseModel):
    """Expression and emotion configuration."""

    enabled: bool = True
    analyze_emotion: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    file: Optional[Path] = None


class DashboardConfig(BaseModel):
    """Dashboard configuration."""

    enabled: bool = False
    host: str = "localhost"
    port: int = 8080


class MemoryConfig(BaseModel):
    """Long-term memory configuration."""

    enabled: bool = False
    db_path: str = "data/memory.db"
    max_results: int = 5
    relevance_threshold: float = 0.3


class AppConfig(BaseModel):
    """Main application configuration."""

    platform: PlatformConfig = Field(default_factory=PlatformConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    avatar: AvatarConfig = Field(default_factory=AvatarConfig)
    comment: CommentConfig = Field(default_factory=CommentConfig)
    expression: ExpressionConfig = Field(default_factory=ExpressionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    character_file: Path = Path("config/characters/default.yaml")


class Settings(BaseSettings):
    """Environment-based settings (secrets)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Platform API Keys
    youtube_api_key: Optional[str] = None
    twitch_access_token: Optional[str] = None
    twitch_client_id: Optional[str] = None

    # TTS API Keys
    nijivoice_api_key: Optional[str] = None


def load_config(config_path: Path = Path("config/config.yaml")) -> AppConfig:
    """Load application configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        AppConfig instance with loaded configuration.
    """
    if not config_path.exists():
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return AppConfig(**data)


# Global settings instance
settings = Settings()
