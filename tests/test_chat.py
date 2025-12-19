"""Tests for chat module."""

from datetime import datetime

import pytest

from src.chat.models import Comment, Platform
from src.chat.comment_queue import CommentQueue


class TestComment:
    """Tests for Comment model."""

    def test_create_comment(self) -> None:
        """Test creating a basic comment."""
        comment = Comment(
            id="123",
            platform=Platform.YOUTUBE,
            user_id="user123",
            user_name="TestUser",
            message="Hello World",
        )
        assert comment.id == "123"
        assert comment.platform == Platform.YOUTUBE
        assert comment.user_name == "TestUser"
        assert comment.message == "Hello World"
        assert comment.is_member is False
        assert comment.donation_amount == 0

    def test_priority_calculation_normal(self) -> None:
        """Test priority for normal comment."""
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Normal comment",
        )
        assert comment.priority == 0

    def test_priority_calculation_member(self) -> None:
        """Test priority for member comment."""
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Member comment",
            is_member=True,
        )
        assert comment.priority == 20

    def test_priority_calculation_moderator(self) -> None:
        """Test priority for moderator comment."""
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Mod comment",
            is_moderator=True,
        )
        assert comment.priority == 10

    def test_priority_calculation_donation(self) -> None:
        """Test priority for donation comment."""
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Super chat!",
            donation_amount=500,
        )
        # 100 (base) + 5 (500/100)
        assert comment.priority == 105

    def test_priority_calculation_combined(self) -> None:
        """Test priority for member with donation."""
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Member super chat",
            is_member=True,
            donation_amount=1000,
        )
        # 100 + 10 (1000/100) + 20 (member)
        assert comment.priority == 130

    def test_comment_comparison(self) -> None:
        """Test comment comparison for priority queue."""
        low_priority = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User1",
            message="Normal",
        )
        high_priority = Comment(
            id="2",
            platform=Platform.YOUTUBE,
            user_id="user2",
            user_name="User2",
            message="Super chat",
            donation_amount=1000,
        )
        # Higher priority should be "less than" for min-heap
        assert high_priority < low_priority


class TestCommentQueue:
    """Tests for CommentQueue."""

    @pytest.mark.asyncio
    async def test_push_and_pop(self) -> None:
        """Test basic push and pop operations."""
        queue = CommentQueue()
        comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Hello",
        )

        await queue.push(comment)
        assert len(queue) == 1

        popped = await queue.pop()
        assert popped is not None
        assert popped.id == "1"
        assert len(queue) == 0

    @pytest.mark.asyncio
    async def test_priority_ordering(self) -> None:
        """Test that higher priority comments come first."""
        queue = CommentQueue()

        normal = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="Normal",
            message="Normal comment",
        )
        donation = Comment(
            id="2",
            platform=Platform.YOUTUBE,
            user_id="user2",
            user_name="Donor",
            message="Super chat",
            donation_amount=500,
        )

        await queue.push(normal)
        await queue.push(donation)

        # Donation should come first
        first = await queue.pop()
        assert first is not None
        assert first.id == "2"

    @pytest.mark.asyncio
    async def test_duplicate_filtering(self) -> None:
        """Test that duplicate comments are filtered."""
        queue = CommentQueue()
        comment = Comment(
            id="same_id",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Hello",
        )

        result1 = await queue.push(comment)
        result2 = await queue.push(comment)

        assert result1 is True
        assert result2 is False
        assert len(queue) == 1

    @pytest.mark.asyncio
    async def test_ng_word_filtering(self) -> None:
        """Test NG word filtering."""
        queue = CommentQueue()
        queue.set_ng_words({"spam", "badword"})

        good_comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="Hello World",
        )
        bad_comment = Comment(
            id="2",
            platform=Platform.YOUTUBE,
            user_id="user2",
            user_name="Spammer",
            message="This is spam content",
        )

        result1 = await queue.push(good_comment)
        result2 = await queue.push(bad_comment)

        assert result1 is True
        assert result2 is False
        assert len(queue) == 1

    @pytest.mark.asyncio
    async def test_empty_message_filtering(self) -> None:
        """Test that empty messages are filtered."""
        queue = CommentQueue()
        empty_comment = Comment(
            id="1",
            platform=Platform.YOUTUBE,
            user_id="user1",
            user_name="User",
            message="   ",  # Whitespace only
        )

        result = await queue.push(empty_comment)
        assert result is False
        assert len(queue) == 0

    @pytest.mark.asyncio
    async def test_max_size(self) -> None:
        """Test max queue size enforcement."""
        queue = CommentQueue(max_size=3)

        for i in range(5):
            comment = Comment(
                id=str(i),
                platform=Platform.YOUTUBE,
                user_id=f"user{i}",
                user_name=f"User{i}",
                message=f"Message {i}",
            )
            await queue.push(comment)

        assert len(queue) == 3
