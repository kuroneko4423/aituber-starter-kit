"""
Style-Bert-VITS2 TTS Engine

Style-Bert-VITS2を使用して感情豊かな音声合成を行います。
"""

import logging
from typing import Optional

import httpx

from .base import BaseTTSEngine
from .models import AudioData, Speaker

logger = logging.getLogger(__name__)


class StyleBertVitsEngine(BaseTTSEngine):
    """Style-Bert-VITS2 音声合成エンジン"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        model_name: str = "default",
        speaker_id: int = 0,
        speed: float = 1.0,
        noise: float = 0.667,
        noisew: float = 0.8,
        sdp_ratio: float = 0.2,
        language: str = "JP",
        style: str = "Neutral",
        style_weight: float = 1.0,
    ):
        """
        Style-Bert-VITS2 エンジンを初期化

        Args:
            host: サーバーのホスト
            port: サーバーのポート
            model_name: 使用するモデル名
            speaker_id: 話者ID
            speed: 話速
            noise: ノイズスケール
            noisew: ノイズスケールW
            sdp_ratio: SDP比率
            language: 言語（JP/EN/ZH）
            style: スタイル名
            style_weight: スタイルの強さ
        """
        self.host = host
        self.port = port
        self.model_name = model_name
        self.speaker_id = speaker_id
        self.speed = speed
        self.noise = noise
        self.noisew = noisew
        self.sdp_ratio = sdp_ratio
        self.language = language
        self.style = style
        self.style_weight = style_weight

        self.base_url = f"http://{host}:{port}"
        self._client = httpx.AsyncClient(timeout=60.0)

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
            # APIエンドポイントにリクエスト
            response = await self._client.get(
                f"{self.base_url}/voice",
                params={
                    "text": text,
                    "model_name": self.model_name,
                    "speaker_id": speaker,
                    "length": 1.0 / self.speed,  # lengthは話速の逆数
                    "noise": self.noise,
                    "noisew": self.noisew,
                    "sdp_ratio": self.sdp_ratio,
                    "language": self.language,
                    "style": self.style,
                    "style_weight": self.style_weight,
                },
            )
            response.raise_for_status()

            return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Style-Bert-VITS2: {e}")
            raise
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise

    async def synthesize_with_emotion(
        self,
        text: str,
        emotion: str,
        emotion_weight: float = 1.0,
        speaker_id: Optional[int] = None,
    ) -> bytes:
        """
        感情を指定して音声合成

        Args:
            text: 合成するテキスト
            emotion: 感情スタイル名
            emotion_weight: 感情の強さ（0.0-2.0）
            speaker_id: 話者ID

        Returns:
            WAV形式の音声データ
        """
        # 一時的にスタイルを変更
        original_style = self.style
        original_weight = self.style_weight

        self.style = emotion
        self.style_weight = emotion_weight

        try:
            return await self.synthesize(text, speaker_id)
        finally:
            # スタイルを元に戻す
            self.style = original_style
            self.style_weight = original_weight

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
            sample_rate=44100,  # Style-Bert-VITS2のデフォルト
            channels=1,
            sample_width=2,
        )

    async def get_speakers(self) -> list[Speaker]:
        """
        利用可能な話者一覧を取得

        Returns:
            話者のリスト
        """
        try:
            response = await self._client.get(f"{self.base_url}/models/info")
            response.raise_for_status()

            models_info = response.json()
            speakers = []

            for model_name, model_info in models_info.items():
                spk2id = model_info.get("spk2id", {})
                styles = model_info.get("style2id", {})

                for speaker_name, speaker_id in spk2id.items():
                    for style_name in styles.keys():
                        speakers.append(Speaker(
                            id=speaker_id,
                            name=f"{model_name}/{speaker_name}",
                            style=style_name,
                        ))

            return speakers

        except Exception as e:
            logger.error(f"Error getting speakers: {e}")
            return []

    async def get_models(self) -> list[str]:
        """
        利用可能なモデル一覧を取得

        Returns:
            モデル名のリスト
        """
        try:
            response = await self._client.get(f"{self.base_url}/models/info")
            response.raise_for_status()

            models_info = response.json()
            return list(models_info.keys())

        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []

    async def get_styles(self, model_name: Optional[str] = None) -> list[str]:
        """
        利用可能なスタイル一覧を取得

        Args:
            model_name: モデル名（Noneの場合はデフォルトモデル）

        Returns:
            スタイル名のリスト
        """
        try:
            response = await self._client.get(f"{self.base_url}/models/info")
            response.raise_for_status()

            models_info = response.json()
            target_model = model_name or self.model_name

            if target_model in models_info:
                return list(models_info[target_model].get("style2id", {}).keys())

            return []

        except Exception as e:
            logger.error(f"Error getting styles: {e}")
            return []

    def set_speed(self, speed: float) -> None:
        """
        話速を設定

        Args:
            speed: 話速（0.5-2.0）
        """
        self.speed = max(0.5, min(2.0, speed))

    def set_style(self, style: str, weight: float = 1.0) -> None:
        """
        スタイルを設定

        Args:
            style: スタイル名
            weight: スタイルの強さ
        """
        self.style = style
        self.style_weight = max(0.0, min(2.0, weight))

    def set_noise_params(
        self,
        noise: Optional[float] = None,
        noisew: Optional[float] = None,
    ) -> None:
        """
        ノイズパラメータを設定

        Args:
            noise: ノイズスケール
            noisew: ノイズスケールW
        """
        if noise is not None:
            self.noise = max(0.0, min(1.0, noise))
        if noisew is not None:
            self.noisew = max(0.0, min(1.0, noisew))

    async def check_connection(self) -> bool:
        """
        サーバーへの接続を確認

        Returns:
            接続成功の場合True
        """
        try:
            response = await self._client.get(f"{self.base_url}/models/info")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """クライアントをクローズ"""
        await self._client.aclose()

    @property
    def engine_name(self) -> str:
        """エンジン名を返す"""
        return "style_bert_vits"
