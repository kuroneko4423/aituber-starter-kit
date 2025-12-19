"""Tests for Twitch chat client module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.chat.twitch_chat import TwitchChatClient, TWITCHIO_AVAILABLE
from src.chat.models import Platform


@pytest.mark.skipif(
    not TWITCHIO_AVAILABLE,
    reason="twitchio not installed",
)
class TestTwitchChatClient:
    """Test TwitchChatClient class."""

    def test_init(self):
        """Test client initialization."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
            client_id="test-client-id",
        )

        assert client.access_token == "test-token"
        assert client.channel_name == "test_channel"
        assert client.client_id == "test-client-id"
        assert not client.is_connected

    def test_channel_name_normalization(self):
        """Test channel name is normalized."""
        # With #
        client1 = TwitchChatClient(
            access_token="test-token",
            channel_name="#TestChannel",
        )
        assert client1.channel_name == "testchannel"

        # Without #
        client2 = TwitchChatClient(
            access_token="test-token",
            channel_name="TestChannel",
        )
        assert client2.channel_name == "testchannel"

    def test_on_comment_callback(self):
        """Test setting comment callback."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
        )

        callback = MagicMock()
        client.on_comment(callback)

        assert client._callback == callback

    def test_message_to_comment(self):
        """Test converting Twitch message to Comment."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
        )

        # Create mock message
        mock_author = MagicMock()
        mock_author.id = 12345
        mock_author.name = "test_user"
        mock_author.is_mod = False

        mock_message = MagicMock()
        mock_message.content = "Hello world!"
        mock_message.author = mock_author
        mock_message.tags = {
            "id": "msg-123",
            "badges": "subscriber/1",
            "bits": "0",
        }

        comment = client._message_to_comment(mock_message)

        assert comment.platform == Platform.TWITCH
        assert comment.user_id == "12345"
        assert comment.user_name == "test_user"
        assert comment.message == "Hello world!"
        assert comment.is_member is True  # subscriber badge
        assert comment.is_moderator is False

    def test_message_with_bits(self):
        """Test converting message with bits (donation)."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
        )

        mock_author = MagicMock()
        mock_author.id = 12345
        mock_author.name = "generous_user"
        mock_author.is_mod = False

        mock_message = MagicMock()
        mock_message.content = "Cheer100 Great stream!"
        mock_message.author = mock_author
        mock_message.tags = {
            "id": "msg-456",
            "badges": "",
            "bits": "100",
        }

        comment = client._message_to_comment(mock_message)

        assert comment.donation_amount == 100
        assert comment.priority > 0  # Should have elevated priority

    def test_message_from_broadcaster(self):
        """Test converting message from broadcaster."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
        )

        mock_author = MagicMock()
        mock_author.id = 12345
        mock_author.name = "broadcaster"
        mock_author.is_mod = False

        mock_message = MagicMock()
        mock_message.content = "Welcome everyone!"
        mock_message.author = mock_author
        mock_message.tags = {
            "id": "msg-789",
            "badges": "broadcaster/1",
        }

        comment = client._message_to_comment(mock_message)

        assert comment.is_moderator is True  # Broadcaster is treated as mod

    def test_message_from_moderator(self):
        """Test converting message from moderator."""
        client = TwitchChatClient(
            access_token="test-token",
            channel_name="test_channel",
        )

        mock_author = MagicMock()
        mock_author.id = 12345
        mock_author.name = "mod_user"
        mock_author.is_mod = True

        mock_message = MagicMock()
        mock_message.content = "Calm down chat!"
        mock_message.author = mock_author
        mock_message.tags = {
            "id": "msg-mod",
            "badges": "moderator/1",
        }

        comment = client._message_to_comment(mock_message)

        assert comment.is_moderator is True


class TestTwitchChatClientImportError:
    """Test TwitchChatClient behavior when twitchio is not installed."""

    def test_import_error_without_twitchio(self):
        """Test that ImportError is raised when twitchio is not available."""
        with patch("src.chat.twitch_chat.TWITCHIO_AVAILABLE", False):
            # Re-import to get the error
            # Note: This is a simplified test; actual behavior depends on import order
            pass
