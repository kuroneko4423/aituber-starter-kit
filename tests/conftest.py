"""Pytest configuration and fixtures."""

import asyncio
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    characters_dir = config_dir / "characters"
    characters_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_character_yaml() -> str:
    """Sample character YAML for testing."""
    return """
name: "テストキャラ"
age: 18
gender: "女性"

personality: |
  テスト用のキャラクターです。
  明るく元気な性格。

speaking_style:
  first_person: "私"
  second_person: "あなた"
  sentence_endings:
    - "〜だよ！"
    - "〜なの！"
  expressions:
    happy:
      - "やったー！"
      - "嬉しい！"

background: |
  テスト用の背景設定です。

restrictions:
  - テスト用の禁止事項

example_dialogues:
  - user: "こんにちは"
    assistant: "こんにちは！テストだよ！"
"""


@pytest.fixture
def sample_config_yaml() -> str:
    """Sample config YAML for testing."""
    return """
platform:
  name: youtube
  video_id: "test_video_id"

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 150

tts:
  engine: voicevox
  host: localhost
  port: 50021
  speaker_id: 1
  speed: 1.0

avatar:
  enabled: false

comment:
  response_interval: 5.0
  priority_donation: true
  max_queue_size: 100

character_file: config/characters/default.yaml
"""
