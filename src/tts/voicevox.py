"""VOICEVOX TTS engine implementation."""

import logging
from typing import Optional

import aiohttp

from .base import BaseTTSEngine
from .models import AudioData, Speaker

logger = logging.getLogger(__name__)


class VoicevoxEngine(BaseTTSEngine):
    """VOICEVOX TTS engine implementation.

    VOICEVOX is a free, high-quality Japanese TTS engine.
    This client communicates with the VOICEVOX engine via HTTP API.

    Args:
        host: VOICEVOX server hostname.
        port: VOICEVOX server port.

    Note:
        VOICEVOX must be running before using this engine.
        Download from: https://voicevox.hiroshiba.jp/

    Example:
        ```python
        engine = VoicevoxEngine(host="localhost", port=50021)

        # Check if available
        if await engine.is_available():
            # Get speakers
            speakers = await engine.get_speakers()

            # Synthesize speech
            audio = await engine.synthesize("こんにちは", speaker_id=1)
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50021,
    ) -> None:
        """Initialize the VOICEVOX engine.

        Args:
            host: VOICEVOX server hostname.
            port: VOICEVOX server port.
        """
        super().__init__()
        self.base_url = f"http://{host}:{port}"
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info(f"Initialized VOICEVOX engine at {self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session.

        Returns:
            Active aiohttp ClientSession.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("VOICEVOX session closed")

    async def synthesize(
        self,
        text: str,
        speaker_id: int,
    ) -> AudioData:
        """Synthesize text to audio using VOICEVOX.

        Args:
            text: Japanese text to synthesize.
            speaker_id: VOICEVOX speaker ID.

        Returns:
            AudioData containing WAV audio.

        Raises:
            aiohttp.ClientError: If HTTP request fails.
        """
        session = await self._get_session()

        # Step 1: Create audio query
        logger.debug(f"Creating audio query for: {text[:30]}...")

        async with session.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker_id},
        ) as resp:
            resp.raise_for_status()
            query = await resp.json()

        # Apply synthesis options
        query["speedScale"] = self._speed
        query["pitchScale"] = self._pitch
        query["intonationScale"] = self._intonation
        query["volumeScale"] = self._volume

        # Step 2: Synthesize audio
        logger.debug("Synthesizing audio...")

        async with session.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker_id},
            json=query,
        ) as resp:
            resp.raise_for_status()
            audio_data = await resp.read()

        logger.debug(f"Synthesized {len(audio_data)} bytes of audio")

        return AudioData(
            data=audio_data,
            sample_rate=24000,
            channels=1,
            format="wav",
        )

    async def get_speakers(self) -> list[Speaker]:
        """Get available VOICEVOX speakers.

        Returns:
            List of available Speaker objects.

        Raises:
            aiohttp.ClientError: If HTTP request fails.
        """
        session = await self._get_session()

        async with session.get(f"{self.base_url}/speakers") as resp:
            resp.raise_for_status()
            speakers_data = await resp.json()

        speakers: list[Speaker] = []
        for speaker in speakers_data:
            speaker_name = speaker.get("name", "Unknown")
            for style in speaker.get("styles", []):
                speakers.append(
                    Speaker(
                        id=style["id"],
                        name=f"{speaker_name} ({style['name']})",
                        styles=[style["name"]],
                    )
                )

        logger.debug(f"Found {len(speakers)} VOICEVOX speakers")
        return speakers

    async def is_available(self) -> bool:
        """Check if VOICEVOX engine is running.

        Returns:
            True if VOICEVOX is available.
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/version",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                is_ok = resp.status == 200
                if is_ok:
                    version = await resp.text()
                    logger.info(f"VOICEVOX version: {version}")
                return is_ok
        except Exception as e:
            logger.warning(f"VOICEVOX not available: {e}")
            return False

    async def get_version(self) -> Optional[str]:
        """Get VOICEVOX engine version.

        Returns:
            Version string or None if unavailable.
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/version") as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception:
            pass
        return None

    async def get_speaker_info(self, speaker_id: int) -> Optional[dict]:
        """Get detailed information about a speaker.

        Args:
            speaker_id: The speaker ID to query.

        Returns:
            Speaker info dict or None if not found.
        """
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/speaker_info",
                params={"speaker_uuid": speaker_id},
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None
