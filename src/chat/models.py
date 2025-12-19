"""Data models for chat comments."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class Platform(Enum):
    """Supported streaming platforms."""

    YOUTUBE = auto()
    TWITCH = auto()
    NICONICO = auto()


@dataclass
class Comment:
    """Represents a chat comment from any platform.

    Attributes:
        id: Unique identifier for the comment.
        platform: Source platform of the comment.
        user_id: Unique identifier of the user.
        user_name: Display name of the user.
        message: The comment text content.
        timestamp: When the comment was posted.
        is_member: Whether the user is a member/subscriber.
        is_moderator: Whether the user is a moderator.
        donation_amount: Super chat/donation amount (0 for regular comments).
        donation_currency: Currency of the donation (e.g., "JPY", "USD").
        priority: Calculated priority for queue ordering.
    """

    id: str
    platform: Platform
    user_id: str
    user_name: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_member: bool = False
    is_moderator: bool = False
    donation_amount: int = 0
    donation_currency: Optional[str] = None
    priority: int = 0

    def __post_init__(self) -> None:
        """Calculate priority based on comment attributes."""
        if self.priority == 0:
            self.priority = self._calculate_priority()

    def _calculate_priority(self) -> int:
        """Calculate comment priority (higher = more important).

        Priority factors:
        - Donations: Base 100 + amount-based bonus (up to 100)
        - Members: +20
        - Moderators: +10

        Returns:
            Calculated priority value.
        """
        priority = 0

        # Donations get highest priority
        if self.donation_amount > 0:
            # Base priority + bonus based on amount (capped at 100)
            priority += 100 + min(self.donation_amount // 100, 100)

        # Members get moderate priority boost
        if self.is_member:
            priority += 20

        # Moderators get small priority boost
        if self.is_moderator:
            priority += 10

        return priority

    def __lt__(self, other: "Comment") -> bool:
        """Compare for priority queue ordering (higher priority first).

        Args:
            other: Another Comment to compare with.

        Returns:
            True if this comment has higher priority.
        """
        if not isinstance(other, Comment):
            return NotImplemented
        return self.priority > other.priority

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Comment(user={self.user_name!r}, "
            f"message={self.message[:30]!r}..., "
            f"priority={self.priority})"
        )
