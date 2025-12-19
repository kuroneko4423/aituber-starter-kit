"""Character configuration and system prompt generation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SpeakingStyle:
    """Character speaking style configuration.

    Attributes:
        first_person: How the character refers to themselves (e.g., "私", "僕").
        second_person: How the character refers to the listener.
        sentence_endings: Common sentence endings the character uses.
        expressions: Emotional expressions mapped by emotion type.
    """

    first_person: str = "私"
    second_person: str = "あなた"
    sentence_endings: list[str] = field(default_factory=list)
    expressions: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ExampleDialogue:
    """Example dialogue for few-shot prompting.

    Attributes:
        user: What the viewer/user says.
        assistant: How the character responds.
    """

    user: str
    assistant: str


@dataclass
class Character:
    """AITuber character configuration.

    This class holds all character settings and can generate a system prompt
    for the LLM to follow.

    Attributes:
        name: Character's name.
        age: Character's age (optional).
        gender: Character's gender (optional).
        personality: Description of personality traits.
        speaking_style: How the character speaks.
        background: Character's backstory.
        restrictions: Things the character should NOT do.
        example_dialogues: Example conversations for few-shot learning.
    """

    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    personality: str = ""
    speaking_style: SpeakingStyle = field(default_factory=SpeakingStyle)
    background: str = ""
    restrictions: list[str] = field(default_factory=list)
    example_dialogues: list[ExampleDialogue] = field(default_factory=list)

    def to_system_prompt(self) -> str:
        """Convert character configuration to a system prompt for LLM.

        Returns:
            A formatted system prompt string.
        """
        parts: list[str] = [
            f"あなたは「{self.name}」というAITuberとして振る舞ってください。",
            "視聴者からのコメントに対して、キャラクターになりきって応答してください。",
            "",
            "【基本情報】",
            f"名前: {self.name}",
        ]

        if self.age is not None:
            parts.append(f"年齢: {self.age}歳")
        if self.gender:
            parts.append(f"性別: {self.gender}")

        if self.personality:
            parts.extend(
                [
                    "",
                    "【性格】",
                    self.personality.strip(),
                ]
            )

        # Speaking style
        parts.extend(
            [
                "",
                "【話し方】",
                f"一人称: {self.speaking_style.first_person}",
                f"二人称: {self.speaking_style.second_person}",
            ]
        )

        if self.speaking_style.sentence_endings:
            endings = ", ".join(self.speaking_style.sentence_endings)
            parts.append(f"語尾の例: {endings}")

        if self.speaking_style.expressions:
            parts.append("")
            parts.append("【感情表現の例】")
            for emotion, exprs in self.speaking_style.expressions.items():
                parts.append(f"- {emotion}: {', '.join(exprs)}")

        if self.background:
            parts.extend(
                [
                    "",
                    "【背景設定】",
                    self.background.strip(),
                ]
            )

        if self.restrictions:
            parts.extend(
                [
                    "",
                    "【禁止事項】",
                    *[f"- {r}" for r in self.restrictions],
                ]
            )

        if self.example_dialogues:
            parts.extend(
                [
                    "",
                    "【会話例】",
                ]
            )
            for ex in self.example_dialogues:
                parts.append(f"視聴者: {ex.user}")
                parts.append(f"{self.name}: {ex.assistant}")
                parts.append("")

        parts.extend(
            [
                "",
                "【応答ルール】",
                "- 視聴者からのコメントに対して自然に応答してください",
                "- 応答は簡潔に（1-3文程度）してください",
                "- キャラクターの設定を守り、一貫性のある応答をしてください",
                "- 視聴者の名前が分かる場合は呼びかけてください",
            ]
        )

        return "\n".join(parts)

    @classmethod
    def from_yaml(cls, path: Path) -> "Character":
        """Load character configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            Character instance with loaded configuration.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            yaml.YAMLError: If the YAML is invalid.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Parse speaking style
        speaking_style_data = data.get("speaking_style", {})
        speaking_style = SpeakingStyle(
            first_person=speaking_style_data.get("first_person", "私"),
            second_person=speaking_style_data.get("second_person", "あなた"),
            sentence_endings=speaking_style_data.get("sentence_endings", []),
            expressions=speaking_style_data.get("expressions", {}),
        )

        # Parse example dialogues
        example_dialogues = [
            ExampleDialogue(user=ex["user"], assistant=ex["assistant"])
            for ex in data.get("example_dialogues", [])
        ]

        return cls(
            name=data.get("name", "AITuber"),
            age=data.get("age"),
            gender=data.get("gender"),
            personality=data.get("personality", ""),
            speaking_style=speaking_style,
            background=data.get("background", ""),
            restrictions=data.get("restrictions", []),
            example_dialogues=example_dialogues,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """Create a Character from a dictionary.

        Args:
            data: Dictionary with character configuration.

        Returns:
            Character instance.
        """
        speaking_style_data = data.get("speaking_style", {})
        speaking_style = SpeakingStyle(
            first_person=speaking_style_data.get("first_person", "私"),
            second_person=speaking_style_data.get("second_person", "あなた"),
            sentence_endings=speaking_style_data.get("sentence_endings", []),
            expressions=speaking_style_data.get("expressions", {}),
        )

        example_dialogues = [
            ExampleDialogue(user=ex["user"], assistant=ex["assistant"])
            for ex in data.get("example_dialogues", [])
        ]

        return cls(
            name=data.get("name", "AITuber"),
            age=data.get("age"),
            gender=data.get("gender"),
            personality=data.get("personality", ""),
            speaking_style=speaking_style,
            background=data.get("background", ""),
            restrictions=data.get("restrictions", []),
            example_dialogues=example_dialogues,
        )
