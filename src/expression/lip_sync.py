"""Lip sync controller for audio-driven mouth animation."""

import asyncio
import io
import logging
import wave
from typing import Optional

import numpy as np

from ..avatar.base import BaseAvatarController

logger = logging.getLogger(__name__)


class LipSyncController:
    """Controls lip sync animation based on audio volume.

    This controller analyzes audio data and animates the avatar's
    mouth movement in sync with the audio.

    Args:
        avatar_controller: The avatar controller to use for animation.
        update_interval: Time between animation updates in seconds.
        smoothing: Smoothing factor for mouth movement (0.0-1.0).

    Example:
        ```python
        controller = LipSyncController(avatar_controller)
        await controller.sync_with_audio(audio_bytes)
        ```
    """

    def __init__(
        self,
        avatar_controller: BaseAvatarController,
        update_interval: float = 0.05,  # 50ms = 20fps
        smoothing: float = 0.3,
    ) -> None:
        """Initialize the lip sync controller.

        Args:
            avatar_controller: Avatar controller for mouth animation.
            update_interval: Animation update interval in seconds.
            smoothing: Smoothing factor (higher = smoother but less responsive).
        """
        self._avatar = avatar_controller
        self._update_interval = update_interval
        self._smoothing = max(0.0, min(1.0, smoothing))
        self._current_value: float = 0.0
        self._is_syncing: bool = False
        logger.info(
            f"Initialized LipSyncController (interval={update_interval}s, "
            f"smoothing={smoothing})"
        )

    @property
    def is_syncing(self) -> bool:
        """Check if currently syncing audio."""
        return self._is_syncing

    async def sync_with_audio(self, audio_data: bytes) -> None:
        """Synchronize lip movement with audio data.

        This method analyzes the audio volume over time and animates
        the mouth movement accordingly.

        Args:
            audio_data: WAV format audio bytes.
        """
        if self._is_syncing:
            logger.warning("Already syncing, ignoring new audio")
            return

        self._is_syncing = True
        logger.debug(f"Starting lip sync for {len(audio_data)} bytes of audio")

        try:
            # Parse WAV data
            audio_info = self._parse_wav(audio_data)
            if audio_info is None:
                logger.warning("Failed to parse audio data")
                return

            samples, framerate = audio_info

            # Calculate frames for animation
            samples_per_frame = int(framerate * self._update_interval)
            total_frames = len(samples) // samples_per_frame

            logger.debug(
                f"Animating {total_frames} frames at {1/self._update_interval:.0f}fps"
            )

            # Animate lip sync
            for i in range(total_frames):
                start = i * samples_per_frame
                end = start + samples_per_frame
                frame_samples = samples[start:end]

                # Calculate volume
                volume = self._calculate_volume(frame_samples)

                # Apply smoothing
                self._current_value = (
                    self._smoothing * self._current_value
                    + (1 - self._smoothing) * volume
                )

                # Set mouth value
                await self._set_mouth_open(self._current_value)
                await asyncio.sleep(self._update_interval)

        except Exception as e:
            logger.error(f"Error during lip sync: {e}", exc_info=True)
        finally:
            # Close mouth at the end
            await self._close_mouth()
            self._is_syncing = False

    def _parse_wav(self, audio_data: bytes) -> Optional[tuple[np.ndarray, int]]:
        """Parse WAV audio data.

        Args:
            audio_data: WAV format bytes.

        Returns:
            Tuple of (samples array, sample rate) or None on error.
        """
        try:
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, "rb") as wav:
                    n_channels = wav.getnchannels()
                    sampwidth = wav.getsampwidth()
                    framerate = wav.getframerate()
                    n_frames = wav.getnframes()
                    raw_data = wav.readframes(n_frames)

            # Determine dtype based on sample width
            if sampwidth == 1:
                dtype = np.int8
            elif sampwidth == 2:
                dtype = np.int16
            elif sampwidth == 4:
                dtype = np.int32
            else:
                logger.warning(f"Unsupported sample width: {sampwidth}")
                return None

            samples = np.frombuffer(raw_data, dtype=dtype)

            # Convert to mono if stereo
            if n_channels == 2:
                samples = samples[::2]

            return samples, framerate

        except Exception as e:
            logger.error(f"Failed to parse WAV data: {e}")
            return None

    def _calculate_volume(self, samples: np.ndarray) -> float:
        """Calculate normalized volume from audio samples.

        Args:
            samples: Audio sample array.

        Returns:
            Normalized volume (0.0 to 1.0).
        """
        if len(samples) == 0:
            return 0.0

        # Calculate RMS (Root Mean Square)
        samples_float = samples.astype(np.float32)
        rms = np.sqrt(np.mean(samples_float**2))

        # Normalize to 0-1 range
        # Assuming 16-bit audio, max value is 32768
        # Use a lower threshold for better sensitivity
        normalized = rms / 8000.0

        # Clamp to 0-1
        return min(1.0, max(0.0, normalized))

    async def _set_mouth_open(self, value: float) -> None:
        """Set mouth open value on avatar.

        Args:
            value: Mouth open value (0.0 to 1.0).
        """
        try:
            await self._avatar.set_lip_sync(value)
        except Exception as e:
            logger.error(f"Failed to set mouth value: {e}")

    async def _close_mouth(self) -> None:
        """Gradually close the mouth."""
        # Smooth closing animation
        while self._current_value > 0.01:
            self._current_value *= 0.5
            await self._set_mouth_open(self._current_value)
            await asyncio.sleep(self._update_interval)

        self._current_value = 0.0
        await self._set_mouth_open(0.0)

    async def stop(self) -> None:
        """Stop any ongoing lip sync."""
        self._is_syncing = False
        await self._close_mouth()
