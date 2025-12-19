"""
Google Gemini API Client

Google Generative AI (Gemini)を使用してAI応答を生成します。
"""

import logging
from typing import AsyncGenerator, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    genai = None
    GenerationConfig = None

from .base import BaseLLMClient
from .character import Character
from .memory import ConversationMemory

logger = logging.getLogger(__name__)


class GoogleClient(BaseLLMClient):
    """Google Gemini APIクライアント"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):
        """
        Google Clientを初期化

        Args:
            api_key: Google AI APIキー
            model: 使用するモデル名
            temperature: 生成時の温度パラメータ
            max_tokens: 最大トークン数
        """
        if not GOOGLE_AI_AVAILABLE:
            raise ImportError(
                "google-generativeai is not installed. "
                "Please install it with: pip install google-generativeai"
            )

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # APIキーを設定
        genai.configure(api_key=api_key)

        # モデルインスタンスを作成
        self._model = genai.GenerativeModel(model)
        self._character: Optional[Character] = None
        self._memory: Optional[ConversationMemory] = None
        self._chat: Optional[genai.ChatSession] = None

    def set_character(self, character: Character) -> None:
        """
        キャラクター設定を適用

        Args:
            character: キャラクター設定
        """
        self._character = character
        self._reset_chat()
        logger.info(f"Character set: {character.name}")

    def set_memory(self, memory: ConversationMemory) -> None:
        """
        会話メモリを設定

        Args:
            memory: 会話メモリ
        """
        self._memory = memory

    def _reset_chat(self) -> None:
        """チャットセッションをリセット"""
        system_instruction = self._build_system_prompt()

        # システム指示付きでモデルを再作成
        self._model = genai.GenerativeModel(
            self.model,
            system_instruction=system_instruction,
        )
        self._chat = None

    def _get_chat(self) -> 'genai.ChatSession':
        """
        チャットセッションを取得または作成

        Returns:
            チャットセッション
        """
        if self._chat is None:
            # 履歴を構築
            history = self._build_history()
            self._chat = self._model.start_chat(history=history)
        return self._chat

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
        try:
            # Generation設定
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )

            # コンテキストを含むメッセージを構築
            full_message = self._build_message_with_context(message, context)

            # チャットセッションを取得
            chat = self._get_chat()

            # 応答を生成（同期APIを非同期で実行）
            import asyncio
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat.send_message(
                    full_message,
                    generation_config=generation_config,
                ),
            )

            response_text = response.text

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
        try:
            # Generation設定
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )

            # コンテキストを含むメッセージを構築
            full_message = self._build_message_with_context(message, context)

            # チャットセッションを取得
            chat = self._get_chat()

            # ストリーミング応答を生成
            import asyncio
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat.send_message(
                    full_message,
                    generation_config=generation_config,
                    stream=True,
                ),
            )

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

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

    def _build_history(self) -> list[dict]:
        """
        Gemini用の履歴を構築

        Returns:
            履歴のリスト
        """
        history = []

        if self._memory:
            for msg in self._memory.get_context():
                role = "user" if msg["role"] == "user" else "model"
                history.append({
                    "role": role,
                    "parts": [msg["content"]],
                })

        return history

    def _build_message_with_context(
        self,
        message: str,
        context: Optional[list[dict]] = None,
    ) -> str:
        """
        コンテキストを含むメッセージを構築

        Args:
            message: ユーザーメッセージ
            context: 追加のコンテキスト

        Returns:
            構築されたメッセージ
        """
        if not context:
            return message

        # コンテキストをメッセージに含める
        context_text = "\n".join([
            f"{ctx.get('role', 'user')}: {ctx.get('content', '')}"
            for ctx in context
        ])

        return f"{context_text}\n\nuser: {message}"

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        return "google"

    @property
    def model_name(self) -> str:
        """モデル名を返す"""
        return self.model
