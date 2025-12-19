"""Tests for TTS engine modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.tts.coeiroink import CoeiroinkEngine
from src.tts.style_bert_vits import StyleBertVitsEngine
from src.tts.nijivoice import NijivoiceEngine
from src.tts.models import AudioData, Speaker


class TestCoeiroinkEngine:
    """Test CoeiroinkEngine class."""

    def test_init(self):
        """Test engine initialization."""
        engine = CoeiroinkEngine(
            host="localhost",
            port=50032,
            speaker_id=0,
            speed=1.0,
        )

        assert engine.host == "localhost"
        assert engine.port == 50032
        assert engine.speaker_id == 0
        assert engine.base_url == "http://localhost:50032"
        assert engine.engine_name == "coeiroink"

    def test_set_speed(self):
        """Test setting speed."""
        engine = CoeiroinkEngine()

        engine.set_speed(1.5)
        assert engine.speed == 1.5

        # Test clamping
        engine.set_speed(3.0)
        assert engine.speed == 2.0

        engine.set_speed(0.1)
        assert engine.speed == 0.5

    def test_set_pitch(self):
        """Test setting pitch."""
        engine = CoeiroinkEngine()

        engine.set_pitch(0.1)
        assert engine.pitch == 0.1

        # Test clamping
        engine.set_pitch(0.5)
        assert engine.pitch == 0.15

        engine.set_pitch(-0.5)
        assert engine.pitch == -0.15

    def test_set_intonation(self):
        """Test setting intonation."""
        engine = CoeiroinkEngine()

        engine.set_intonation(1.5)
        assert engine.intonation == 1.5

        # Test clamping
        engine.set_intonation(3.0)
        assert engine.intonation == 2.0

    def test_set_volume(self):
        """Test setting volume."""
        engine = CoeiroinkEngine()

        engine.set_volume(0.5)
        assert engine.volume == 0.5

        # Test clamping
        engine.set_volume(-1.0)
        assert engine.volume == 0.0

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Test synthesizing empty text."""
        engine = CoeiroinkEngine()

        result = await engine.synthesize("")
        assert result == b""

        result = await engine.synthesize("   ")
        assert result == b""

        await engine.close()

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """Test connection check when server is not available."""
        engine = CoeiroinkEngine(host="nonexistent-host", port=50032)

        result = await engine.check_connection()
        assert result is False

        await engine.close()


class TestStyleBertVitsEngine:
    """Test StyleBertVitsEngine class."""

    def test_init(self):
        """Test engine initialization."""
        engine = StyleBertVitsEngine(
            host="localhost",
            port=5000,
            model_name="my_model",
            speaker_id=0,
        )

        assert engine.host == "localhost"
        assert engine.port == 5000
        assert engine.model_name == "my_model"
        assert engine.base_url == "http://localhost:5000"
        assert engine.engine_name == "style_bert_vits"

    def test_set_speed(self):
        """Test setting speed."""
        engine = StyleBertVitsEngine()

        engine.set_speed(1.5)
        assert engine.speed == 1.5

        # Test clamping
        engine.set_speed(3.0)
        assert engine.speed == 2.0

    def test_set_style(self):
        """Test setting style."""
        engine = StyleBertVitsEngine()

        engine.set_style("Happy", 1.5)
        assert engine.style == "Happy"
        assert engine.style_weight == 1.5

        # Test clamping weight
        engine.set_style("Sad", 3.0)
        assert engine.style_weight == 2.0

    def test_set_noise_params(self):
        """Test setting noise parameters."""
        engine = StyleBertVitsEngine()

        engine.set_noise_params(noise=0.5, noisew=0.6)
        assert engine.noise == 0.5
        assert engine.noisew == 0.6

        # Test clamping
        engine.set_noise_params(noise=1.5)
        assert engine.noise == 1.0

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Test synthesizing empty text."""
        engine = StyleBertVitsEngine()

        result = await engine.synthesize("")
        assert result == b""

        await engine.close()

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """Test connection check when server is not available."""
        engine = StyleBertVitsEngine(host="nonexistent-host", port=5000)

        result = await engine.check_connection()
        assert result is False

        await engine.close()


class TestNijivoiceEngine:
    """Test NijivoiceEngine class."""

    def test_init(self):
        """Test engine initialization."""
        engine = NijivoiceEngine(
            api_key="test-api-key",
            actor_id="test-actor",
            speed=1.0,
        )

        assert engine.api_key == "test-api-key"
        assert engine.actor_id == "test-actor"
        assert engine.speed == 1.0
        assert engine.engine_name == "nijivoice"

    def test_set_speed(self):
        """Test setting speed."""
        engine = NijivoiceEngine(api_key="test-key")

        engine.set_speed(1.5)
        assert engine.speed == 1.5

        # Test clamping
        engine.set_speed(3.0)
        assert engine.speed == 2.0

        engine.set_speed(0.1)
        assert engine.speed == 0.4

    def test_set_pitch(self):
        """Test setting pitch."""
        engine = NijivoiceEngine(api_key="test-key")

        engine.set_pitch(1.5)
        assert engine.pitch == 1.5

        # Test clamping
        engine.set_pitch(3.0)
        assert engine.pitch == 2.0

    def test_set_intonation(self):
        """Test setting intonation."""
        engine = NijivoiceEngine(api_key="test-key")

        engine.set_intonation(1.5)
        assert engine.intonation == 1.5

        # Test clamping
        engine.set_intonation(3.0)
        assert engine.intonation == 2.0

    def test_set_volume(self):
        """Test setting volume."""
        engine = NijivoiceEngine(api_key="test-key")

        engine.set_volume(0.5)
        assert engine.volume == 0.5

        # Test clamping
        engine.set_volume(0.05)
        assert engine.volume == 0.1

    def test_set_actor(self):
        """Test setting actor."""
        engine = NijivoiceEngine(api_key="test-key")

        engine.set_actor("new-actor-id")
        assert engine.actor_id == "new-actor-id"

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Test synthesizing empty text."""
        engine = NijivoiceEngine(api_key="test-key", actor_id="test")

        result = await engine.synthesize("")
        assert result == b""

        await engine.close()

    @pytest.mark.asyncio
    async def test_synthesize_without_actor_id(self):
        """Test synthesizing without actor_id raises error."""
        engine = NijivoiceEngine(api_key="test-key")

        with pytest.raises(ValueError, match="actor_id is required"):
            await engine.synthesize("Hello")

        await engine.close()

    @pytest.mark.asyncio
    async def test_check_connection_failure(self):
        """Test connection check when API is not available."""
        engine = NijivoiceEngine(api_key="invalid-key")

        # This will fail because the API key is invalid
        result = await engine.check_connection()
        assert result is False

        await engine.close()
