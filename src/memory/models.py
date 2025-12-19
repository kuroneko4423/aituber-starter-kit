"""Data models for long-term memory system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class MemoryType(str, Enum):
    """Types of memory entries."""

    CONVERSATION = "conversation"
    USER_INFO = "user_info"
    TOPIC = "topic"
    FACT = "fact"
    PREFERENCE = "preference"


class Importance(str, Enum):
    """Importance level of memory entries."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MemoryEntry:
    """A single memory entry.

    Attributes:
        id: Unique identifier for the entry.
        memory_type: Type of memory (conversation, user_info, etc.).
        content: The main content of the memory.
        user_name: Associated user name (if applicable).
        keywords: Keywords for search/retrieval.
        importance: Importance level of the memory.
        emotion: Detected emotion (if applicable).
        timestamp: When the memory was created.
        last_accessed: When the memory was last retrieved.
        access_count: Number of times the memory was accessed.
        metadata: Additional metadata.
    """

    content: str
    memory_type: MemoryType = MemoryType.CONVERSATION
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_name: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    importance: Importance = Importance.MEDIUM
    emotion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the memory entry.
        """
        return {
            "id": self.id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "user_name": self.user_name,
            "keywords": self.keywords,
            "importance": self.importance.value,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create from dictionary.

        Args:
            data: Dictionary with memory data.

        Returns:
            MemoryEntry instance.
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            memory_type=MemoryType(data.get("memory_type", "conversation")),
            content=data["content"],
            user_name=data.get("user_name"),
            keywords=data.get("keywords", []),
            importance=Importance(data.get("importance", "medium")),
            emotion=data.get("emotion"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("timestamp"), str)
            else data.get("timestamp", datetime.now()),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if data.get("last_accessed")
            else None,
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemorySearchResult:
    """Result from a memory search.

    Attributes:
        entry: The memory entry.
        relevance_score: Relevance score (0.0 to 1.0).
        match_reason: Why this entry matched.
    """

    entry: MemoryEntry
    relevance_score: float
    match_reason: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "entry": self.entry.to_dict(),
            "relevance_score": self.relevance_score,
            "match_reason": self.match_reason,
        }


@dataclass
class UserProfile:
    """Profile information about a user.

    Attributes:
        user_name: The user's name.
        first_seen: When the user was first seen.
        last_seen: When the user was last seen.
        interaction_count: Total number of interactions.
        topics: Topics the user has discussed.
        preferences: Known user preferences.
        notes: Additional notes about the user.
    """

    user_name: str
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    topics: list[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "user_name": self.user_name,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "interaction_count": self.interaction_count,
            "topics": self.topics,
            "preferences": self.preferences,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary.

        Args:
            data: Dictionary with profile data.

        Returns:
            UserProfile instance.
        """
        return cls(
            user_name=data["user_name"],
            first_seen=datetime.fromisoformat(data["first_seen"])
            if isinstance(data.get("first_seen"), str)
            else data.get("first_seen", datetime.now()),
            last_seen=datetime.fromisoformat(data["last_seen"])
            if isinstance(data.get("last_seen"), str)
            else data.get("last_seen", datetime.now()),
            interaction_count=data.get("interaction_count", 0),
            topics=data.get("topics", []),
            preferences=data.get("preferences", {}),
            notes=data.get("notes", []),
        )
