"""Tests for memory module."""

import pytest

from src.ai.memory import ConversationMemory, Message


class TestMessage:
    """Tests for Message."""

    def test_create_message(self) -> None:
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_message_with_user_name(self) -> None:
        """Test message with user name."""
        msg = Message(role="user", content="Hello", user_name="TestUser")
        assert msg.user_name == "TestUser"


class TestConversationMemory:
    """Tests for ConversationMemory."""

    def test_add_user_message(self) -> None:
        """Test adding user message."""
        memory = ConversationMemory()
        memory.add_user_message("Hello", user_name="User1")

        assert len(memory) == 1
        context = memory.get_context()
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello"

    def test_add_assistant_message(self) -> None:
        """Test adding assistant message."""
        memory = ConversationMemory()
        memory.add_assistant_message("Hi there!")

        assert len(memory) == 1
        context = memory.get_context()
        assert context[0]["role"] == "assistant"
        assert context[0]["content"] == "Hi there!"

    def test_conversation_flow(self) -> None:
        """Test typical conversation flow."""
        memory = ConversationMemory()
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi!")
        memory.add_user_message("How are you?")
        memory.add_assistant_message("I'm good!")

        assert len(memory) == 4
        context = memory.get_context()
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"
        assert context[2]["role"] == "user"
        assert context[3]["role"] == "assistant"

    def test_max_messages(self) -> None:
        """Test max messages limit."""
        memory = ConversationMemory(max_messages=3)

        for i in range(5):
            memory.add_user_message(f"Message {i}")

        assert len(memory) == 3
        context = memory.get_context()
        # Should keep most recent
        assert context[0]["content"] == "Message 2"
        assert context[2]["content"] == "Message 4"

    def test_get_context_with_names(self) -> None:
        """Test getting context with user names."""
        memory = ConversationMemory()
        memory.add_user_message("Hello", user_name="TestUser")
        memory.add_assistant_message("Hi!")

        context = memory.get_context_with_names()
        assert "TestUserさん: Hello" in context[0]["content"]

    def test_clear(self) -> None:
        """Test clearing memory."""
        memory = ConversationMemory()
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi")

        memory.clear()

        assert len(memory) == 0
        assert memory.is_empty

    def test_get_recent_messages(self) -> None:
        """Test getting recent messages."""
        memory = ConversationMemory()
        for i in range(5):
            memory.add_user_message(f"Message {i}")

        recent = memory.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[2].content == "Message 4"

    def test_is_empty(self) -> None:
        """Test is_empty property."""
        memory = ConversationMemory()
        assert memory.is_empty

        memory.add_user_message("Hello")
        assert not memory.is_empty
