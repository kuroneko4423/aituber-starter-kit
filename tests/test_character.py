"""Tests for character module."""

from pathlib import Path

import pytest

from src.ai.character import Character, SpeakingStyle, ExampleDialogue


class TestSpeakingStyle:
    """Tests for SpeakingStyle."""

    def test_default_values(self) -> None:
        """Test default speaking style values."""
        style = SpeakingStyle()
        assert style.first_person == "私"
        assert style.second_person == "あなた"
        assert style.sentence_endings == []
        assert style.expressions == {}

    def test_custom_values(self) -> None:
        """Test custom speaking style values."""
        style = SpeakingStyle(
            first_person="僕",
            second_person="君",
            sentence_endings=["〜だよ", "〜なんだ"],
            expressions={"happy": ["やった！"]},
        )
        assert style.first_person == "僕"
        assert style.second_person == "君"
        assert len(style.sentence_endings) == 2


class TestCharacter:
    """Tests for Character."""

    def test_create_character(self) -> None:
        """Test creating a character."""
        char = Character(
            name="テストキャラ",
            age=17,
            gender="女性",
            personality="明るい性格",
        )
        assert char.name == "テストキャラ"
        assert char.age == 17
        assert char.gender == "女性"

    def test_to_system_prompt(self) -> None:
        """Test system prompt generation."""
        char = Character(
            name="アイちゃん",
            age=17,
            gender="女性",
            personality="明るく元気な性格",
            speaking_style=SpeakingStyle(
                first_person="私",
                sentence_endings=["〜だよ！"],
            ),
            restrictions=["政治的な話題に触れない"],
        )

        prompt = char.to_system_prompt()

        assert "アイちゃん" in prompt
        assert "17歳" in prompt
        assert "女性" in prompt
        assert "明るく元気な性格" in prompt
        assert "私" in prompt
        assert "〜だよ！" in prompt
        assert "政治的な話題に触れない" in prompt

    def test_from_yaml(
        self,
        test_config_dir: Path,
        sample_character_yaml: str,
    ) -> None:
        """Test loading character from YAML."""
        char_file = test_config_dir / "characters" / "test.yaml"
        char_file.write_text(sample_character_yaml)

        char = Character.from_yaml(char_file)

        assert char.name == "テストキャラ"
        assert char.age == 18
        assert char.speaking_style.first_person == "私"
        assert len(char.example_dialogues) == 1
        assert char.example_dialogues[0].user == "こんにちは"

    def test_from_dict(self) -> None:
        """Test creating character from dictionary."""
        data = {
            "name": "テスト",
            "age": 20,
            "personality": "テスト性格",
            "speaking_style": {
                "first_person": "俺",
            },
            "example_dialogues": [
                {"user": "Hi", "assistant": "Hello!"}
            ],
        }

        char = Character.from_dict(data)

        assert char.name == "テスト"
        assert char.age == 20
        assert char.speaking_style.first_person == "俺"
        assert len(char.example_dialogues) == 1


class TestExampleDialogue:
    """Tests for ExampleDialogue."""

    def test_create_dialogue(self) -> None:
        """Test creating example dialogue."""
        dialogue = ExampleDialogue(
            user="こんにちは",
            assistant="こんにちは！元気？",
        )
        assert dialogue.user == "こんにちは"
        assert dialogue.assistant == "こんにちは！元気？"
