"""Audio playback utilities."""

import asyncio
import io
import logging
import wave
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Async audio player for WAV data.

    This player handles audio playback asynchronously, allowing
    other tasks to continue while audio is playing.

    Example:
        ```python
        player = AudioPlayer()
        await player.play(audio_bytes)
        player.stop()
        ```
    """

    def __init__(self, device: Optional[int] = None) -> None:
        """Initialize the audio player.

        Args:
            device: Output device index. None for default device.
        """
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._device = device
        self._is_playing = False
        logger.info(
            f"Initialized AudioPlayer (device={device or 'default'})"
        )

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_playing

    async def play(self, audio_data: bytes) -> None:
        """Play WAV audio data asynchronously.

        Args:
            audio_data: WAV format audio bytes.
        """
        if self._is_playing:
            logger.warning("Already playing audio, stopping current playback")
            self.stop()

        self._is_playing = True
        logger.debug(f"Playing {len(audio_data)} bytes of audio")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._play_sync,
                audio_data,
            )
        except Exception as e:
            logger.error(f"Error playing audio: {e}", exc_info=True)
        finally:
            self._is_playing = False

    def _play_sync(self, audio_data: bytes) -> None:
        """Synchronous audio playback (runs in thread pool).

        Args:
            audio_data: WAV format audio bytes.
        """
        try:
            # Parse WAV data
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, "rb") as wav:
                    framerate = wav.getframerate()
                    n_frames = wav.getnframes()
                    n_channels = wav.getnchannels()
                    sampwidth = wav.getsampwidth()
                    raw_data = wav.readframes(n_frames)

            # Convert to numpy array
            if sampwidth == 1:
                dtype = np.int8
            elif sampwidth == 2:
                dtype = np.int16
            elif sampwidth == 4:
                dtype = np.int32
            else:
                logger.warning(f"Unsupported sample width: {sampwidth}")
                return

            samples = np.frombuffer(raw_data, dtype=dtype)

            # Reshape for stereo
            if n_channels == 2:
                samples = samples.reshape(-1, 2)

            # Normalize to float32 for sounddevice
            max_val = float(2 ** (sampwidth * 8 - 1))
            samples_float = samples.astype(np.float32) / max_val

            # Play audio
            sd.play(samples_float, samplerate=framerate, device=self._device)
            sd.wait()

            logger.debug("Audio playback completed")

        except Exception as e:
            logger.error(f"Error in sync playback: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop current audio playback."""
        sd.stop()
        self._is_playing = False
        logger.debug("Audio playback stopped")

    def set_device(self, device: Optional[int]) -> None:
        """Set the output device.

        Args:
            device: Device index or None for default.
        """
        self._device = device
        logger.info(f"Audio device set to: {device or 'default'}")

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio devices.

        Returns:
            List of device info dictionaries.
        """
        devices = sd.query_devices()
        return [
            {
                "index": i,
                "name": d["name"],
                "channels": d["max_output_channels"],
                "sample_rate": d["default_samplerate"],
            }
            for i, d in enumerate(devices)
            if d["max_output_channels"] > 0
        ]

    @staticmethod
    def get_default_device() -> Optional[dict]:
        """Get the default output device info.

        Returns:
            Device info dict or None.
        """
        try:
            device_id = sd.default.device[1]  # Output device
            if device_id is not None:
                device = sd.query_devices(device_id)
                return {
                    "index": device_id,
                    "name": device["name"],
                    "channels": device["max_output_channels"],
                    "sample_rate": device["default_samplerate"],
                }
        except Exception:
            pass
        return None
