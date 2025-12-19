"""
Nijivoice TTS Engine

にじボイス APIを使用して音声合成を行います。
"""

import logging
from typing import Optional

import httpx

from .base import BaseTTSEngine
from .models import AudioData, Speaker

logger = logging.getLogger(__name__)


class NijivoiceEngine(BaseTTSEngine):
    """にじボイス 音声合成エンジン"""

    BASE_URL = "https://api.nijivoice.com/api/platform/v1"

    def __init__(
        self,
        api_key: str,
        actor_id: str = "",
        speed: float = 1.0,
        pitch: float = 1.0,
        intonation: float = 1.0,
        volume: float = 1.0,
        format: str = "wav",
    ):
        """
        Nijivoice エンジンを初期化

        Args:
            api_key: にじボイス APIキー
            actor_id: デフォルトの声優ID
            speed: 話速（0.4-2.0）
            pitch: ピッチ（0.5-2.0）
            intonation: 抑揚（0.0-2.0）
            volume: 音量（0.1-2.0）
            format: 出力フォーマット（wav/mp3）
        """
        self.api_key = api_key
        self.actor_id = actor_id
        self.speed = speed
        self.pitch = pitch
        self.intonation = intonation
        self.volume = volume
        self.format = format

        self._client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
            },
        )

    async def synthesize(
        self,
        text: str,
        speaker_id: Optional[int] = None,
    ) -> bytes:
        """
        テキストを音声に変換

        Args:
            text: 合成するテキスト
            speaker_id: 話者ID（にじボイスでは使用せず、actor_idを使用）

        Returns:
            音声データ（WAVまたはMP3）
        """
        if not text.strip():
            logger.warning("Empty text provided for synthesis")
            return b""

        actor = self.actor_id
        if not actor:
            logger.error("No actor_id specified")
            raise ValueError("actor_id is required for Nijivoice synthesis")

        try:
            # 音声生成リクエスト
            response = await self._client.post(
                f"{self.BASE_URL}/voice-actors/{actor}/generate-voice",
                json={
                    "script": text,
                    "speed": str(self.speed),
                    "pitch": str(self.pitch),
                    "intonation": str(self.intonation),
                    "volume": str(self.volume),
                    "format": self.format,
                },
            )
            response.raise_for_status()

            result = response.json()

            # generatedVoiceにURLが含まれる場合
            if "generatedVoice" in result:
                voice_info = result["generatedVoice"]
                audio_url = voice_info.get("audioFileUrl")

                if audio_url:
                    # 音声ファイルをダウンロード
                    audio_response = await self._client.get(audio_url)
                    audio_response.raise_for_status()
                    return audio_response.content

            logger.error("Unexpected response format from Nijivoice")
            raise ValueError("Failed to get audio data from Nijivoice")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Nijivoice: {e}")
            raise
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise

    async def synthesize_to_audio_data(
        self,
        text: str,
        speaker_id: Optional[int] = None,
    ) -> AudioData:
        """
        テキストを音声データに変換

        Args:
            text: 合成するテキスト
            speaker_id: 話者ID

        Returns:
            AudioDataオブジェクト
        """
        audio_bytes = await self.synthesize(text, speaker_id)

        # フォーマットに応じたサンプルレート
        sample_rate = 44100 if self.format == "wav" else 44100

        return AudioData(
            data=audio_bytes,
            sample_rate=sample_rate,
            channels=1,
            sample_width=2,
        )

    async def get_speakers(self) -> list[Speaker]:
        """
        利用可能な声優一覧を取得

        Returns:
            声優のリスト
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/voice-actors",
            )
            response.raise_for_status()

            data = response.json()
            voice_actors = data.get("voiceActors", [])

            speakers = []
            for idx, actor in enumerate(voice_actors):
                speakers.append(Speaker(
                    id=idx,  # インデックスをIDとして使用
                    name=actor.get("name", "Unknown"),
                    style=actor.get("id", ""),  # actor_idをスタイルとして保存
                ))

            return speakers

        except Exception as e:
            logger.error(f"Error getting voice actors: {e}")
            return []

    async def get_voice_actor_info(self, actor_id: str) -> Optional[dict]:
        """
        声優の詳細情報を取得

        Args:
            actor_id: 声優ID

        Returns:
            声優情報の辞書またはNone
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/voice-actors/{actor_id}",
            )
            response.raise_for_status()

            return response.json().get("voiceActor")

        except Exception as e:
            logger.error(f"Error getting voice actor info: {e}")
            return None

    def set_speed(self, speed: float) -> None:
        """
        話速を設定

        Args:
            speed: 話速（0.4-2.0）
        """
        self.speed = max(0.4, min(2.0, speed))

    def set_pitch(self, pitch: float) -> None:
        """
        ピッチを設定

        Args:
            pitch: ピッチ（0.5-2.0）
        """
        self.pitch = max(0.5, min(2.0, pitch))

    def set_intonation(self, intonation: float) -> None:
        """
        抑揚を設定

        Args:
            intonation: 抑揚（0.0-2.0）
        """
        self.intonation = max(0.0, min(2.0, intonation))

    def set_volume(self, volume: float) -> None:
        """
        音量を設定

        Args:
            volume: 音量（0.1-2.0）
        """
        self.volume = max(0.1, min(2.0, volume))

    def set_actor(self, actor_id: str) -> None:
        """
        声優を設定

        Args:
            actor_id: 声優ID
        """
        self.actor_id = actor_id

    async def check_connection(self) -> bool:
        """
        APIへの接続を確認

        Returns:
            接続成功の場合True
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/voice-actors",
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """クライアントをクローズ"""
        await self._client.aclose()

    @property
    def engine_name(self) -> str:
        """エンジン名を返す"""
        return "nijivoice"
