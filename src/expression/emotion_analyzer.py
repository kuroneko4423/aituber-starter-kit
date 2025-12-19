"""
Emotion Analyzer

テキストから感情を分析し、アバターの表情にマッピングします。
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Emotion(Enum):
    """感情の種類"""
    NEUTRAL = "neutral"      # 中立
    HAPPY = "happy"          # 喜び
    SAD = "sad"              # 悲しみ
    ANGRY = "angry"          # 怒り
    SURPRISED = "surprised"  # 驚き
    FEARFUL = "fearful"      # 恐れ
    DISGUSTED = "disgusted"  # 嫌悪
    EMBARRASSED = "embarrassed"  # 照れ・恥ずかしい
    THINKING = "thinking"    # 考え中


@dataclass
class EmotionResult:
    """感情分析の結果"""
    primary_emotion: Emotion
    confidence: float
    secondary_emotion: Optional[Emotion] = None
    intensity: float = 0.5  # 0.0-1.0


@dataclass
class ExpressionMapping:
    """表情マッピング設定"""
    # VTube Studioの表情パラメータ名
    expression_name: str
    # パラメータ値（0.0-1.0）
    parameter_values: dict[str, float]


class EmotionAnalyzer:
    """テキストから感情を分析するクラス"""

    # 感情キーワード辞書（日本語）
    EMOTION_KEYWORDS: dict[Emotion, list[str]] = {
        Emotion.HAPPY: [
            "嬉しい", "うれしい", "楽しい", "たのしい", "幸せ", "しあわせ",
            "やった", "わーい", "最高", "さいこう", "素敵", "すてき",
            "ありがとう", "感謝", "好き", "すき", "大好き", "だいすき",
            "笑", "わらう", "ウキウキ", "ワクワク", "ルンルン",
            "😊", "😄", "😆", "🎉", "❤️", "💕", "✨", "🥰",
        ],
        Emotion.SAD: [
            "悲しい", "かなしい", "寂しい", "さびしい", "つらい", "辛い",
            "残念", "ざんねん", "泣く", "なく", "涙", "なみだ",
            "しょんぼり", "がっかり", "切ない", "せつない",
            "😢", "😭", "😿", "💔",
        ],
        Emotion.ANGRY: [
            "怒", "おこる", "いかる", "むかつく", "ムカつく", "イライラ",
            "許せない", "ゆるせない", "ふざけるな", "うざい", "ウザい",
            "くそ", "クソ", "最悪", "さいあく",
            "😠", "😡", "💢",
        ],
        Emotion.SURPRISED: [
            "驚", "おどろく", "びっくり", "ビックリ", "えっ", "ええ",
            "マジ", "まじ", "本当", "ほんとう", "ほんと", "すごい", "凄い",
            "やば", "ヤバ", "信じられない",
            "😲", "😮", "😯", "😱", "🤯",
        ],
        Emotion.FEARFUL: [
            "怖い", "こわい", "恐い", "恐ろしい", "おそろしい",
            "不安", "ふあん", "心配", "しんぱい", "ドキドキ",
            "ビビる", "びびる",
            "😨", "😰", "😥",
        ],
        Emotion.DISGUSTED: [
            "気持ち悪い", "きもちわるい", "きもい", "キモい",
            "嫌", "いや", "イヤ", "やだ", "ヤダ",
            "無理", "むり", "ムリ",
            "🤢", "🤮",
        ],
        Emotion.EMBARRASSED: [
            "恥ずかしい", "はずかしい", "照れ", "てれる",
            "赤面", "せきめん", "きゃー", "キャー",
            "えへへ", "てへ",
            "😳", "🙈", "😅",
        ],
        Emotion.THINKING: [
            "うーん", "ん〜", "んー", "考え", "かんがえ",
            "どう", "なぜ", "なんで", "どうして",
            "わからない", "分からない", "わかんない",
            "難しい", "むずかしい",
            "🤔", "💭",
        ],
    }

    # 感情と表情パラメータのマッピング
    DEFAULT_EXPRESSION_MAPPINGS: dict[Emotion, ExpressionMapping] = {
        Emotion.NEUTRAL: ExpressionMapping(
            expression_name="neutral",
            parameter_values={
                "ParamMouthSmile": 0.0,
                "ParamEyeSmile": 0.0,
                "ParamBrowLY": 0.0,
                "ParamBrowRY": 0.0,
            },
        ),
        Emotion.HAPPY: ExpressionMapping(
            expression_name="happy",
            parameter_values={
                "ParamMouthSmile": 1.0,
                "ParamEyeSmile": 1.0,
                "ParamBrowLY": 0.3,
                "ParamBrowRY": 0.3,
            },
        ),
        Emotion.SAD: ExpressionMapping(
            expression_name="sad",
            parameter_values={
                "ParamMouthSmile": -0.5,
                "ParamEyeSmile": 0.0,
                "ParamBrowLY": -0.5,
                "ParamBrowRY": -0.5,
            },
        ),
        Emotion.ANGRY: ExpressionMapping(
            expression_name="angry",
            parameter_values={
                "ParamMouthSmile": -0.3,
                "ParamEyeSmile": 0.0,
                "ParamBrowLY": -0.8,
                "ParamBrowRY": -0.8,
                "ParamBrowAngle": -0.5,
            },
        ),
        Emotion.SURPRISED: ExpressionMapping(
            expression_name="surprised",
            parameter_values={
                "ParamMouthOpenY": 0.7,
                "ParamEyeLOpen": 1.2,
                "ParamEyeROpen": 1.2,
                "ParamBrowLY": 0.8,
                "ParamBrowRY": 0.8,
            },
        ),
        Emotion.FEARFUL: ExpressionMapping(
            expression_name="fearful",
            parameter_values={
                "ParamMouthOpenY": 0.3,
                "ParamEyeLOpen": 1.1,
                "ParamEyeROpen": 1.1,
                "ParamBrowLY": 0.5,
                "ParamBrowRY": 0.5,
            },
        ),
        Emotion.DISGUSTED: ExpressionMapping(
            expression_name="disgusted",
            parameter_values={
                "ParamMouthSmile": -0.7,
                "ParamEyeSmile": 0.3,
                "ParamBrowLY": -0.3,
                "ParamBrowRY": -0.3,
            },
        ),
        Emotion.EMBARRASSED: ExpressionMapping(
            expression_name="embarrassed",
            parameter_values={
                "ParamMouthSmile": 0.3,
                "ParamEyeSmile": 0.5,
                "ParamCheek": 1.0,  # 頬紅
            },
        ),
        Emotion.THINKING: ExpressionMapping(
            expression_name="thinking",
            parameter_values={
                "ParamMouthSmile": 0.0,
                "ParamEyeBallX": 0.5,  # 目線を横に
                "ParamBrowLY": 0.2,
                "ParamBrowRY": -0.2,
            },
        ),
    }

    def __init__(
        self,
        custom_keywords: Optional[dict[Emotion, list[str]]] = None,
        custom_mappings: Optional[dict[Emotion, ExpressionMapping]] = None,
    ):
        """
        EmotionAnalyzerを初期化

        Args:
            custom_keywords: カスタム感情キーワード辞書
            custom_mappings: カスタム表情マッピング
        """
        # キーワード辞書を構築
        self.keywords = dict(self.EMOTION_KEYWORDS)
        if custom_keywords:
            for emotion, words in custom_keywords.items():
                if emotion in self.keywords:
                    self.keywords[emotion].extend(words)
                else:
                    self.keywords[emotion] = words

        # 表情マッピングを構築
        self.expression_mappings = dict(self.DEFAULT_EXPRESSION_MAPPINGS)
        if custom_mappings:
            self.expression_mappings.update(custom_mappings)

    def analyze(self, text: str) -> EmotionResult:
        """
        テキストから感情を分析

        Args:
            text: 分析対象のテキスト

        Returns:
            感情分析結果
        """
        # テキストを正規化
        normalized_text = text.lower()

        # 各感情のスコアを計算
        scores: dict[Emotion, float] = {}
        total_matches = 0

        for emotion, keywords in self.keywords.items():
            score = 0.0
            for keyword in keywords:
                # キーワードの出現回数をカウント
                count = normalized_text.count(keyword.lower())
                if count > 0:
                    score += count
                    total_matches += count

            scores[emotion] = score

        # スコアが0の場合はNEUTRALを返す
        if total_matches == 0:
            return EmotionResult(
                primary_emotion=Emotion.NEUTRAL,
                confidence=1.0,
                intensity=0.3,
            )

        # 最高スコアの感情を取得
        sorted_emotions = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        primary_emotion = sorted_emotions[0][0]
        primary_score = sorted_emotions[0][1]

        # 信頼度を計算（最高スコア / 総マッチ数）
        confidence = primary_score / total_matches if total_matches > 0 else 0.0

        # 強度を計算（マッチ数に基づく、最大1.0）
        intensity = min(1.0, primary_score / 3.0)

        # セカンダリ感情を取得
        secondary_emotion = None
        if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0:
            secondary_emotion = sorted_emotions[1][0]

        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            secondary_emotion=secondary_emotion,
            intensity=intensity,
        )

    def get_expression_mapping(self, emotion: Emotion) -> ExpressionMapping:
        """
        感情に対応する表情マッピングを取得

        Args:
            emotion: 感情

        Returns:
            表情マッピング
        """
        return self.expression_mappings.get(
            emotion,
            self.expression_mappings[Emotion.NEUTRAL],
        )

    def analyze_and_map(self, text: str) -> tuple[EmotionResult, ExpressionMapping]:
        """
        テキストを分析し、表情マッピングも返す

        Args:
            text: 分析対象のテキスト

        Returns:
            (感情分析結果, 表情マッピング)のタプル
        """
        result = self.analyze(text)
        mapping = self.get_expression_mapping(result.primary_emotion)

        # 強度に応じてパラメータ値を調整
        adjusted_mapping = ExpressionMapping(
            expression_name=mapping.expression_name,
            parameter_values={
                key: value * result.intensity
                for key, value in mapping.parameter_values.items()
            },
        )

        return result, adjusted_mapping


class EmotionExpressionController:
    """感情に基づいて表情を制御するコントローラー"""

    def __init__(
        self,
        analyzer: Optional[EmotionAnalyzer] = None,
        avatar_controller=None,
    ):
        """
        EmotionExpressionControllerを初期化

        Args:
            analyzer: 感情分析器
            avatar_controller: アバターコントローラー
        """
        self.analyzer = analyzer or EmotionAnalyzer()
        self.avatar_controller = avatar_controller
        self._current_emotion: Emotion = Emotion.NEUTRAL

    async def process_text(self, text: str) -> EmotionResult:
        """
        テキストを処理し、感情に応じた表情を設定

        Args:
            text: 処理対象のテキスト

        Returns:
            感情分析結果
        """
        result, mapping = self.analyzer.analyze_and_map(text)

        # 感情が変わった場合のみ表情を更新
        if result.primary_emotion != self._current_emotion:
            self._current_emotion = result.primary_emotion

            if self.avatar_controller:
                try:
                    await self.avatar_controller.set_expression(
                        mapping.expression_name
                    )
                    logger.debug(
                        f"Expression changed to: {mapping.expression_name}"
                    )
                except Exception as e:
                    logger.error(f"Failed to set expression: {e}")

        return result

    @property
    def current_emotion(self) -> Emotion:
        """現在の感情を取得"""
        return self._current_emotion
