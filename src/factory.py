"""Factory functions for creating components from configuration."""

import logging
from typing import Optional

from .config import AppConfig, Settings

# Chat clients
from .chat.base import BaseChatClient
from .chat.youtube_chat import YouTubeChatClient
from .chat.twitch_chat import TwitchChatClient

# LLM clients
from .ai.base import BaseLLMClient
from .ai.openai_client import OpenAIClient
from .ai.anthropic_client import AnthropicClient
from .ai.google_client import GoogleClient
from .ai.ollama_client import OllamaClient
from .ai.character import Character

# TTS engines
from .tts.base import BaseTTSEngine
from .tts.voicevox import VoicevoxEngine
from .tts.coeiroink import CoeiroinkEngine
from .tts.style_bert_vits import StyleBertVitsEngine
from .tts.nijivoice import NijivoiceEngine

# Avatar
from .avatar.base import BaseAvatarController
from .avatar.vtube_studio import VTubeStudioController

logger = logging.getLogger(__name__)


def create_chat_client(config: AppConfig, settings: Settings) -> BaseChatClient:
    """
    設定からチャットクライアントを作成

    Args:
        config: アプリケーション設定
        settings: 環境変数設定

    Returns:
        チャットクライアント

    Raises:
        ValueError: 未対応のプラットフォームの場合
    """
    platform = config.platform.name.lower()

    if platform == "youtube":
        if not config.platform.video_id:
            raise ValueError("YouTube video_id is required")
        return YouTubeChatClient(video_id=config.platform.video_id)

    elif platform == "twitch":
        if not settings.twitch_access_token:
            raise ValueError("TWITCH_ACCESS_TOKEN is required")
        if not config.platform.twitch_channel:
            raise ValueError("Twitch channel name is required")

        return TwitchChatClient(
            access_token=settings.twitch_access_token,
            channel_name=config.platform.twitch_channel,
            client_id=settings.twitch_client_id,
        )

    else:
        raise ValueError(f"Unsupported platform: {platform}")


def create_llm_client(
    config: AppConfig,
    settings: Settings,
    character: Optional[Character] = None,
) -> BaseLLMClient:
    """
    設定からLLMクライアントを作成

    Args:
        config: アプリケーション設定
        settings: 環境変数設定
        character: キャラクター設定（オプション）

    Returns:
        LLMクライアント

    Raises:
        ValueError: 未対応のプロバイダーまたはAPIキー未設定の場合
    """
    provider = config.llm.provider.lower()

    client: BaseLLMClient

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")

        client = OpenAIClient(
            api_key=settings.openai_api_key,
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        client = AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

    elif provider == "google":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")

        client = GoogleClient(
            api_key=settings.google_api_key,
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

    elif provider == "ollama":
        client = OllamaClient(
            model=config.llm.model,
            host=config.llm.ollama_host,
            port=config.llm.ollama_port,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    # キャラクター設定を適用
    if character:
        client.set_character(character)

    logger.info(f"Created LLM client: {provider}/{config.llm.model}")
    return client


def create_tts_engine(config: AppConfig, settings: Settings) -> BaseTTSEngine:
    """
    設定からTTSエンジンを作成

    Args:
        config: アプリケーション設定
        settings: 環境変数設定

    Returns:
        TTSエンジン

    Raises:
        ValueError: 未対応のエンジンまたはAPIキー未設定の場合
    """
    engine = config.tts.engine.lower()

    if engine == "voicevox":
        return VoicevoxEngine(
            host=config.tts.host,
            port=config.tts.port,
            speaker_id=config.tts.speaker_id,
            speed=config.tts.speed,
            pitch=config.tts.pitch,
            intonation=config.tts.intonation,
            volume=config.tts.volume,
        )

    elif engine == "coeiroink":
        # COEIROINKのデフォルトポートは50032
        port = config.tts.port if config.tts.port != 50021 else 50032
        return CoeiroinkEngine(
            host=config.tts.host,
            port=port,
            speaker_id=config.tts.speaker_id,
            speed=config.tts.speed,
            pitch=config.tts.pitch,
            intonation=config.tts.intonation,
            volume=config.tts.volume,
        )

    elif engine == "style_bert_vits":
        # Style-Bert-VITS2のデフォルトポートは5000
        port = config.tts.port if config.tts.port != 50021 else 5000
        return StyleBertVitsEngine(
            host=config.tts.host,
            port=port,
            model_name=config.tts.style_bert_model,
            speaker_id=config.tts.speaker_id,
            speed=config.tts.speed,
            style=config.tts.style_bert_style,
            style_weight=config.tts.style_bert_style_weight,
        )

    elif engine == "nijivoice":
        if not settings.nijivoice_api_key:
            raise ValueError("NIJIVOICE_API_KEY is required")
        if not config.tts.nijivoice_actor_id:
            raise ValueError("Nijivoice actor_id is required")

        return NijivoiceEngine(
            api_key=settings.nijivoice_api_key,
            actor_id=config.tts.nijivoice_actor_id,
            speed=config.tts.speed,
            pitch=config.tts.pitch,
            intonation=config.tts.intonation,
            volume=config.tts.volume,
        )

    else:
        raise ValueError(f"Unsupported TTS engine: {engine}")


def create_avatar_controller(
    config: AppConfig,
) -> Optional[BaseAvatarController]:
    """
    設定からアバターコントローラーを作成

    Args:
        config: アプリケーション設定

    Returns:
        アバターコントローラー（無効の場合はNone）
    """
    if not config.avatar.enabled:
        logger.info("Avatar control is disabled")
        return None

    controller = VTubeStudioController(
        host=config.avatar.host,
        port=config.avatar.port,
        plugin_name=config.avatar.plugin_name,
        plugin_developer=config.avatar.plugin_developer,
    )

    logger.info(
        f"Created VTube Studio controller: {config.avatar.host}:{config.avatar.port}"
    )
    return controller
