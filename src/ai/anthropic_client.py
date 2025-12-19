"""
Anthropic Claude API Client

Claude APIを使用してAI応答を生成します。
"""

import logging
from typing import AsyncGenerator, Optional

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

from .base import BaseLLMClient
from .character import Character
from .memory import ConversationMemory

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude APIクライアント"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):
        """
        Anthropic Clientを初期化

        Args:
            api_key: Anthropic APIキー
            model: 使用するモデル名
            temperature: 生成時の温度パラメータ
            max_tokens: 最大トークン数
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic is not installed. "
                "Please install it with: pip install anthropic"
            )

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._client = AsyncAnthropic(api_key=api_key)
        self._character: Optional[Character] = None
        self._memory: Optional[ConversationMemory] = None

    def set_character(self, character: Character) -> None:
        """
        キャラクター設定を適用

        Args:
            character: キャラクター設定
        """
        self._character = character
        logger.info(f"Character set: {character.name}")

    def set_memory(self, memory: ConversationMemory) -> None:
        """
        会話メモリを設定

        Args:
            memory: 会話メモリ
        """
        self._memory = memory

    async def generate_response(
        self,
        message: str,
        context: Optional[list[dict]] = None,
    ) -> str:
        """
        応答テキストを生成

        Args:
            message: ユーザーメッセージ
            context: 追加のコンテキスト（オプション）

        Returns:
            生成された応答テキスト
        """
        # システムプロンプトを構築
        system_prompt = self._build_system_prompt()

        # メッセージ履歴を構築
        messages = self._build_messages(message, context)

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            )

            # 応答テキストを取得
            response_text = response.content[0].text

            # メモリに保存
            if self._memory:
                self._memory.add_message("user", message)
                self._memory.add_message("assistant", response_text)

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def stream_response(
        self,
        message: str,
        context: Optional[list[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミング応答を生成

        Args:
            message: ユーザーメッセージ
            context: 追加のコンテキスト（オプション）

        Yields:
            生成されたテキストの断片
        """
        # システムプロンプトを構築
        system_prompt = self._build_system_prompt()

        # メッセージ履歴を構築
        messages = self._build_messages(message, context)

        try:
            full_response = ""

            async with self._client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield text

            # メモリに保存
            if self._memory:
                self._memory.add_message("user", message)
                self._memory.add_message("assistant", full_response)

        except Exception as e:
            logger.error(f"Error in stream response: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """
        システムプロンプトを構築

        Returns:
            システムプロンプト文字列
        """
        if self._character:
            return self._character.to_system_prompt()
        return "You are a helpful AI assistant."

    def _build_messages(
        self,
        message: str,
        context: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        メッセージリストを構築

        Args:
            message: 現在のユーザーメッセージ
            context: 追加のコンテキスト

        Returns:
            Anthropic API用のメッセージリスト
        """
        messages = []

        # メモリからの履歴を追加
        if self._memory:
            for msg in self._memory.get_context():
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # 追加コンテキストを追加
        if context:
            for ctx in context:
                messages.append({
                    "role": ctx.get("role", "user"),
                    "content": ctx.get("content", ""),
                })

        # 現在のメッセージを追加
        messages.append({
            "role": "user",
            "content": message,
        })

        return messages

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        return "anthropic"

    @property
    def model_name(self) -> str:
        """モデル名を返す"""
        return self.model
