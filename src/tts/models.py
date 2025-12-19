"""Data models for TTS (Text-to-Speech) module."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Speaker:
    """TTS speaker/voice information.

    Attributes:
        id: Unique identifier for the speaker.
        name: Display name of the speaker.
        styles: Available voice styles for this speaker.
        description: Optional description of the voice.
    """

    id: int
    name: str
    styles: list[str] = field(default_factory=list)
    description: Optional[str] = None

    def __repr__(self) -> str:
        """String representation."""
        return f"Speaker(id={self.id}, name={self.name!r})"


@dataclass
class AudioData:
    """Synthesized audio data container.

    Attributes:
        data: Raw audio bytes (typically WAV format).
        sample_rate: Audio sample rate in Hz.
        channels: Number of audio channels (1=mono, 2=stereo).
        format: Audio format identifier (e.g., "wav", "mp3").
        duration: Duration in seconds (calculated if not provided).
    """

    data: bytes
    sample_rate: int = 24000
    channels: int = 1
    format: str = "wav"
    duration: Optional[float] = None

    def __post_init__(self) -> None:
        """Calculate duration if not provided."""
        if self.duration is None and self.data:
            # Estimate duration for 16-bit audio
            bytes_per_sample = 2 * self.channels
            total_samples = len(self.data) / bytes_per_sample
            self.duration = total_samples / self.sample_rate

    def __len__(self) -> int:
        """Get the size of audio data in bytes."""
        return len(self.data)

    @property
    def is_empty(self) -> bool:
        """Check if audio data is empty."""
        return len(self.data) == 0


@dataclass
class SynthesisOptions:
    """Options for speech synthesis.

    Attributes:
        speed: Speaking speed multiplier (0.5-2.0).
        pitch: Voice pitch adjustment (-0.15 to 0.15).
        intonation: Intonation scale (0.0-2.0).
        volume: Output volume multiplier (0.0-2.0).
    """

    speed: float = 1.0
    pitch: float = 0.0
    intonation: float = 1.0
    volume: float = 1.0

    def __post_init__(self) -> None:
        """Validate and clamp values."""
        self.speed = max(0.5, min(2.0, self.speed))
        self.pitch = max(-0.15, min(0.15, self.pitch))
        self.intonation = max(0.0, min(2.0, self.intonation))
        self.volume = max(0.0, min(2.0, self.volume))
