"""Tests for emotion analyzer module."""

import pytest

from src.expression.emotion_analyzer import (
    Emotion,
    EmotionResult,
    ExpressionMapping,
    EmotionAnalyzer,
)


class TestEmotion:
    """Test Emotion enum."""

    def test_emotion_values(self):
        """Test that all emotion values are defined."""
        assert Emotion.NEUTRAL.value == "neutral"
        assert Emotion.HAPPY.value == "happy"
        assert Emotion.SAD.value == "sad"
        assert Emotion.ANGRY.value == "angry"
        assert Emotion.SURPRISED.value == "surprised"
        assert Emotion.EMBARRASSED.value == "embarrassed"
        assert Emotion.THINKING.value == "thinking"


class TestEmotionResult:
    """Test EmotionResult dataclass."""

    def test_creation(self):
        """Test creating an EmotionResult."""
        result = EmotionResult(
            primary_emotion=Emotion.HAPPY,
            confidence=0.8,
            secondary_emotion=Emotion.SURPRISED,
            intensity=0.7,
        )

        assert result.primary_emotion == Emotion.HAPPY
        assert result.confidence == 0.8
        assert result.secondary_emotion == Emotion.SURPRISED
        assert result.intensity == 0.7

    def test_default_values(self):
        """Test default values."""
        result = EmotionResult(
            primary_emotion=Emotion.NEUTRAL,
            confidence=1.0,
        )

        assert result.secondary_emotion is None
        assert result.intensity == 0.5


class TestEmotionAnalyzer:
    """Test EmotionAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create an emotion analyzer."""
        return EmotionAnalyzer()

    def test_analyze_neutral(self, analyzer):
        """Test analyzing neutral text."""
        result = analyzer.analyze("今日は普通の日です")
        assert result.primary_emotion == Emotion.NEUTRAL

    def test_analyze_happy(self, analyzer):
        """Test analyzing happy text."""
        result = analyzer.analyze("わーい！嬉しい！やったー！")
        assert result.primary_emotion == Emotion.HAPPY
        assert result.confidence > 0.5

    def test_analyze_sad(self, analyzer):
        """Test analyzing sad text."""
        result = analyzer.analyze("悲しい…とても残念です")
        assert result.primary_emotion == Emotion.SAD

    def test_analyze_angry(self, analyzer):
        """Test analyzing angry text."""
        result = analyzer.analyze("むかつく！許せない！")
        assert result.primary_emotion == Emotion.ANGRY

    def test_analyze_surprised(self, analyzer):
        """Test analyzing surprised text."""
        result = analyzer.analyze("えっ！？マジで！？びっくり！")
        assert result.primary_emotion == Emotion.SURPRISED

    def test_analyze_embarrassed(self, analyzer):
        """Test analyzing embarrassed text."""
        result = analyzer.analyze("恥ずかしい…照れちゃう…えへへ")
        assert result.primary_emotion == Emotion.EMBARRASSED

    def test_analyze_thinking(self, analyzer):
        """Test analyzing thinking text."""
        result = analyzer.analyze("うーん、どうしよう…わからないな")
        assert result.primary_emotion == Emotion.THINKING

    def test_analyze_with_emoji(self, analyzer):
        """Test analyzing text with emoji."""
        result = analyzer.analyze("ありがとう！😊💕")
        assert result.primary_emotion == Emotion.HAPPY

    def test_analyze_empty_text(self, analyzer):
        """Test analyzing empty text."""
        result = analyzer.analyze("")
        assert result.primary_emotion == Emotion.NEUTRAL
        assert result.confidence == 1.0

    def test_intensity_calculation(self, analyzer):
        """Test that intensity increases with more keywords."""
        # Single keyword
        result1 = analyzer.analyze("嬉しい")
        # Multiple keywords
        result2 = analyzer.analyze("嬉しい！やったー！最高！わーい！")

        assert result2.intensity > result1.intensity

    def test_get_expression_mapping(self, analyzer):
        """Test getting expression mapping."""
        mapping = analyzer.get_expression_mapping(Emotion.HAPPY)

        assert mapping.expression_name == "happy"
        assert "ParamMouthSmile" in mapping.parameter_values
        assert mapping.parameter_values["ParamMouthSmile"] == 1.0

    def test_analyze_and_map(self, analyzer):
        """Test analyze_and_map method."""
        result, mapping = analyzer.analyze_and_map("嬉しい！やったー！")

        assert result.primary_emotion == Emotion.HAPPY
        assert mapping.expression_name == "happy"
        # Check that intensity affects parameter values
        assert mapping.parameter_values["ParamMouthSmile"] <= 1.0

    def test_custom_keywords(self):
        """Test analyzer with custom keywords."""
        custom_keywords = {
            Emotion.HAPPY: ["カスタム喜び"],
        }
        analyzer = EmotionAnalyzer(custom_keywords=custom_keywords)

        result = analyzer.analyze("カスタム喜び")
        assert result.primary_emotion == Emotion.HAPPY

    def test_custom_mappings(self):
        """Test analyzer with custom expression mappings."""
        custom_mapping = ExpressionMapping(
            expression_name="custom_happy",
            parameter_values={"CustomParam": 0.5},
        )
        custom_mappings = {Emotion.HAPPY: custom_mapping}

        analyzer = EmotionAnalyzer(custom_mappings=custom_mappings)
        mapping = analyzer.get_expression_mapping(Emotion.HAPPY)

        assert mapping.expression_name == "custom_happy"
        assert mapping.parameter_values["CustomParam"] == 0.5
