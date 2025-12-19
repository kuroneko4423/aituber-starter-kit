"""
COEIROINK TTS Engine

COEIROINKを使用して音声合成を行います。
VOICEVOXと互換性のあるAPIを提供しています。
"""

import logging
from typing import Optional

import httpx

from .base import BaseTTSEngine
from .models import AudioData, Speaker

logger = logging.getLogger(__name__)


class CoeiroinkEngine(BaseTTSEngine):
    """COEIROINK 音声合成エンジン"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50032,  # COEIROINKのデフォルトポート
        speaker_id: int = 0,
        speed: float = 1.0,
        pitch: float = 0.0,
        intonation: float = 1.0,
        volume: float = 1.0,
    ):
        """
        COEIROINK エンジンを初期化

        Args:
            host: COEIROINKサーバーのホスト
            port: COEIROINKサーバーのポート
            speaker_id: 話者ID
            speed: 話速（0.5-2.0）
            pitch: ピッチ（-0.15-0.15）
            intonation: 抑揚（0.0-2.0）
            volume: 音量（0.0-2.0）
        """
        self.host = host
        self.port = port
        self.speaker_id = speaker_id
        self.speed = speed
        self.pitch = pitch
        self.intonation = intonation
        self.volume = volume

        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(timeout=30.0)

    async def synthesize(
        self,
        text: str,
        speaker_id: Optional[int] = None,
    ) -> bytes:
        """
        テキストを音声に変換

        Args:
            text: 合成するテキスト
            speaker_id: 話者ID（Noneの場合はデフォルトを使用）

        Returns:
            WAV形式の音声データ
        """
        if not text.strip():
            logger.warning("Empty text provided for synthesis")
            return b""

        speaker = speaker_id if speaker_id is not None else self.speaker_id

        try:
            # 1. 音声合成用のクエリを作成
            query_response = await self._client.post(
                f"{self.base_url}/audio_query",
                params={
                    "text": text,
                    "speaker": speaker,
                },
            )
            query_response.raise_for_status()
            query = query_response.json()

            # パラメータを設定
            query["speedScale"] = self.speed
            query["pitchScale"] = self.pitch
            query["intonationScale"] = self.intonation
            query["volumeScale"] = self.volume

            # 2. 音声を合成
            synthesis_response = await self._client.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker},
                json=query,
            )
            synthesis_response.raise_for_status()

            return synthesis_response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from COEIROINK: {e}")
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
        return AudioData(
            data=audio_bytes,
            sample_rate=24000,  # COEIROINKのデフォルトサンプルレート
            channels=1,
            sample_width=2,  # 16bit
        )

    async def get_speakers(self) -> list[Speaker]:
        """
        利用可能な話者一覧を取得

        Returns:
            話者のリスト
        """
        try:
            response = await self._client.get(f"{self.base_url}/speakers")
            response.raise_for_status()

            speakers_data = response.json()
            speakers = []

            for speaker_info in speakers_data:
                name = speaker_info.get("name", "Unknown")
                styles = speaker_info.get("styles", [])

                for style in styles:
                    speakers.append(Speaker(
                        id=style.get("id", 0),
                        name=f"{name} ({style.get('name', 'default')})",
                        style=style.get("name", "default"),
                    ))

            return speakers

        except Exception as e:
            logger.error(f"Error getting speakers: {e}")
            return []

    def set_speed(self, speed: float) -> None:
        """
        話速を設定

        Args:
            speed: 話速（0.5-2.0）
        """
        self.speed = max(0.5, min(2.0, speed))

    def set_pitch(self, pitch: float) -> None:
        """
        ピッチを設定

        Args:
            pitch: ピッチ（-0.15-0.15）
        """
        self.pitch = max(-0.15, min(0.15, pitch))

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
            volume: 音量（0.0-2.0）
        """
        self.volume = max(0.0, min(2.0, volume))

    async def check_connection(self) -> bool:
        """
        COEIROINKサーバーへの接続を確認

        Returns:
            接続成功の場合True
        """
        try:
            response = await self._client.get(f"{self.base_url}/speakers")
            return response.status_code == 200
        except Exception:
            return False

    async def get_version(self) -> Optional[str]:
        """
        COEIROINKのバージョンを取得

        Returns:
            バージョン文字列またはNone
        """
        try:
            response = await self._client.get(f"{self.base_url}/version")
            if response.status_code == 200:
                return response.text.strip('"')
            return None
        except Exception:
            return None

    async def close(self) -> None:
        """クライアントをクローズ"""
        await self._client.aclose()

    @property
    def engine_name(self) -> str:
        """エンジン名を返す"""
        return "coeiroink"
