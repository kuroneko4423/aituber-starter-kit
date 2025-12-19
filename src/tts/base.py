"""Abstract base class for TTS (Text-to-Speech) engines."""

from abc import ABC, abstractmethod

from .models import AudioData, Speaker


class BaseTTSEngine(ABC):
    """Abstract base class for TTS engines.

    This class defines the interface for all TTS implementations.
    Subclasses must implement synthesize() and get_speakers().

    Example:
        ```python
        class MyTTSEngine(BaseTTSEngine):
            async def synthesize(self, text: str, speaker_id: int) -> AudioData:
                # Convert text to audio
                return AudioData(data=audio_bytes)

            async def get_speakers(self) -> list[Speaker]:
                return [Speaker(id=1, name="Default")]
        ```
    """

    def __init__(self) -> None:
        """Initialize the TTS engine."""
        self._speed: float = 1.0
        self._pitch: float = 0.0
        self._intonation: float = 1.0
        self._volume: float = 1.0

    @property
    def speed(self) -> float:
        """Get current speaking speed."""
        return self._speed

    @property
    def pitch(self) -> float:
        """Get current voice pitch."""
        return self._pitch

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        speaker_id: int,
    ) -> AudioData:
        """Synthesize text to audio.

        Args:
            text: The text to convert to speech.
            speaker_id: ID of the speaker/voice to use.

        Returns:
            AudioData containing the synthesized audio.

        Raises:
            Exception: If synthesis fails.
        """
        pass

    @abstractmethod
    async def get_speakers(self) -> list[Speaker]:
        """Get available speakers/voices.

        Returns:
            List of available Speaker objects.

        Raises:
            Exception: If fetching speakers fails.
        """
        pass

    def set_speed(self, speed: float) -> None:
        """Set speaking speed.

        Args:
            speed: Speed multiplier (0.5 to 2.0).
        """
        self._speed = max(0.5, min(2.0, speed))

    def set_pitch(self, pitch: float) -> None:
        """Set voice pitch.

        Args:
            pitch: Pitch adjustment (-0.15 to 0.15).
        """
        self._pitch = max(-0.15, min(0.15, pitch))

    def set_intonation(self, intonation: float) -> None:
        """Set intonation scale.

        Args:
            intonation: Intonation scale (0.0 to 2.0).
        """
        self._intonation = max(0.0, min(2.0, intonation))

    def set_volume(self, volume: float) -> None:
        """Set output volume.

        Args:
            volume: Volume multiplier (0.0 to 2.0).
        """
        self._volume = max(0.0, min(2.0, volume))

    async def is_available(self) -> bool:
        """Check if the TTS engine is available and running.

        Returns:
            True if engine is available, False otherwise.
        """
        try:
            await self.get_speakers()
            return True
        except Exception:
            return False
