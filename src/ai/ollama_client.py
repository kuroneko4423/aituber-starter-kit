"""
Ollama Local LLM Client

Ollamaを使用してローカルLLMで応答を生成します。
"""

import logging
from typing import AsyncGenerator, Optional

import httpx

from .base import BaseLLMClient
from .character import Character
from .memory import ConversationMemory

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Ollama ローカルLLMクライアント"""

    def __init__(
        self,
        model: str = "llama3.1",
        host: str = "localhost",
        port: int = 11434,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):
        """
        Ollama Clientを初期化

        Args:
            model: 使用するモデル名
            host: Ollamaサーバーのホスト
            port: Ollamaサーバーのポート
            temperature: 生成時の温度パラメータ
            max_tokens: 最大トークン数
        """
        self.model = model
        self.host = host
        self.port = port
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(timeout=60.0)
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
        # メッセージリストを構築
        messages = self._build_messages(message, context)

        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
            )
            response.raise_for_status()

            data = response.json()
            response_text = data.get("message", {}).get("content", "")

            # メモリに保存
            if self._memory:
                self._memory.add_message("user", message)
                self._memory.add_message("assistant", response_text)

            return response_text

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
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
        # メッセージリストを構築
        messages = self._build_messages(message, context)

        try:
            full_response = ""

            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
            ) as response:
                response.raise_for_status()

                import json
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                full_response += content
                                yield content

                            # 終了チェック
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

            # メモリに保存
            if self._memory:
                self._memory.add_message("user", message)
                self._memory.add_message("assistant", full_response)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in stream response: {e}")
            raise

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
            Ollama API用のメッセージリスト
        """
        messages = []

        # システムプロンプトを追加
        system_prompt = self._build_system_prompt()
        messages.append({
            "role": "system",
            "content": system_prompt,
        })

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

    def _build_system_prompt(self) -> str:
        """
        システムプロンプトを構築

        Returns:
            システムプロンプト文字列
        """
        if self._character:
            return self._character.to_system_prompt()
        return "You are a helpful AI assistant."

    async def list_models(self) -> list[str]:
        """
        利用可能なモデル一覧を取得

        Returns:
            モデル名のリスト
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return models

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def check_connection(self) -> bool:
        """
        Ollamaサーバーへの接続を確認

        Returns:
            接続成功の場合True
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """クライアントをクローズ"""
        await self._client.aclose()

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        return "ollama"

    @property
    def model_name(self) -> str:
        """モデル名を返す"""
        return self.model
