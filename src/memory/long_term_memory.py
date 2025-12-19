"""SQLite-based long-term memory storage."""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Importance, MemoryEntry, MemoryType, UserProfile

logger = logging.getLogger(__name__)


class LongTermMemory:
    """SQLite-based long-term memory storage.

    This class provides persistent storage for conversation history,
    user information, and other memories that should persist across sessions.

    Args:
        db_path: Path to the SQLite database file.

    Example:
        ```python
        memory = LongTermMemory("data/memory.db")
        await memory.initialize()

        # Store a memory
        entry = MemoryEntry(
            content="User likes anime",
            memory_type=MemoryType.USER_INFO,
            user_name="Viewer123",
        )
        await memory.store(entry)

        # Search memories
        results = await memory.search("anime", limit=5)
        ```
    """

    def __init__(self, db_path: str = "data/memory.db") -> None:
        """Initialize the long-term memory store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the database and create tables."""
        async with self._lock:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row

            # Create tables
            self._connection.executescript(
                """
                -- Memory entries table
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    user_name TEXT,
                    keywords TEXT,
                    importance TEXT DEFAULT 'medium',
                    emotion TEXT,
                    timestamp TEXT NOT NULL,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT
                );

                -- Index for faster searches
                CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_name);
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp);

                -- User profiles table
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_name TEXT PRIMARY KEY,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    interaction_count INTEGER DEFAULT 0,
                    topics TEXT,
                    preferences TEXT,
                    notes TEXT
                );

                -- Full-text search table
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content,
                    keywords,
                    content='memories',
                    content_rowid='rowid'
                );

                -- Triggers to keep FTS in sync
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content, keywords)
                    VALUES (new.rowid, new.content, new.keywords);
                END;

                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, keywords)
                    VALUES ('delete', old.rowid, old.content, old.keywords);
                END;

                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, keywords)
                    VALUES ('delete', old.rowid, old.content, old.keywords);
                    INSERT INTO memories_fts(rowid, content, keywords)
                    VALUES (new.rowid, new.content, new.keywords);
                END;
                """
            )
            self._connection.commit()
            logger.info(f"Long-term memory initialized at {self.db_path}")

    async def close(self) -> None:
        """Close the database connection."""
        async with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                logger.info("Long-term memory closed")

    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry.

        Args:
            entry: The memory entry to store.

        Returns:
            The ID of the stored entry.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            self._connection.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, memory_type, content, user_name, keywords, importance,
                 emotion, timestamp, last_accessed, access_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.memory_type.value,
                    entry.content,
                    entry.user_name,
                    json.dumps(entry.keywords),
                    entry.importance.value,
                    entry.emotion,
                    entry.timestamp.isoformat(),
                    entry.last_accessed.isoformat() if entry.last_accessed else None,
                    entry.access_count,
                    json.dumps(entry.metadata),
                ),
            )
            self._connection.commit()

            logger.debug(f"Stored memory: {entry.id[:8]}...")
            return entry.id

    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID.

        Args:
            entry_id: The ID of the entry to retrieve.

        Returns:
            The memory entry, or None if not found.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            cursor = self._connection.execute(
                "SELECT * FROM memories WHERE id = ?",
                (entry_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Update access tracking
            self._connection.execute(
                """
                UPDATE memories
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ?
                """,
                (datetime.now().isoformat(), entry_id),
            )
            self._connection.commit()

            return self._row_to_entry(row)

    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        user_name: Optional[str] = None,
        min_importance: Optional[Importance] = None,
    ) -> list[MemoryEntry]:
        """Search for memories using full-text search.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            memory_type: Filter by memory type.
            user_name: Filter by user name.
            min_importance: Minimum importance level.

        Returns:
            List of matching memory entries.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            # Build query
            sql = """
                SELECT m.* FROM memories m
                JOIN memories_fts ON m.rowid = memories_fts.rowid
                WHERE memories_fts MATCH ?
            """
            params: list = [query]

            if memory_type:
                sql += " AND m.memory_type = ?"
                params.append(memory_type.value)

            if user_name:
                sql += " AND m.user_name = ?"
                params.append(user_name)

            if min_importance:
                importance_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                min_level = importance_order.get(min_importance.value, 0)
                sql += f" AND m.importance IN ({','.join('?' * (4 - min_level))})"
                params.extend(
                    [i.value for i in Importance][min_level:]
                )

            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)

            cursor = self._connection.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_entry(row) for row in rows]

    async def search_by_user(
        self,
        user_name: str,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Get memories associated with a specific user.

        Args:
            user_name: The user to search for.
            limit: Maximum number of results.

        Returns:
            List of memory entries for the user.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            cursor = self._connection.execute(
                """
                SELECT * FROM memories
                WHERE user_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_name, limit),
            )
            rows = cursor.fetchall()

            return [self._row_to_entry(row) for row in rows]

    async def get_recent(
        self,
        limit: int = 50,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Get recent memory entries.

        Args:
            limit: Maximum number of results.
            memory_type: Filter by memory type.

        Returns:
            List of recent memory entries.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            if memory_type:
                cursor = self._connection.execute(
                    """
                    SELECT * FROM memories
                    WHERE memory_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (memory_type.value, limit),
                )
            else:
                cursor = self._connection.execute(
                    """
                    SELECT * FROM memories
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry.

        Args:
            entry_id: The ID of the entry to delete.

        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            cursor = self._connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (entry_id,),
            )
            self._connection.commit()

            return cursor.rowcount > 0

    async def get_user_profile(self, user_name: str) -> Optional[UserProfile]:
        """Get a user's profile.

        Args:
            user_name: The user's name.

        Returns:
            The user profile, or None if not found.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            cursor = self._connection.execute(
                "SELECT * FROM user_profiles WHERE user_name = ?",
                (user_name,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return UserProfile(
                user_name=row["user_name"],
                first_seen=datetime.fromisoformat(row["first_seen"]),
                last_seen=datetime.fromisoformat(row["last_seen"]),
                interaction_count=row["interaction_count"],
                topics=json.loads(row["topics"] or "[]"),
                preferences=json.loads(row["preferences"] or "{}"),
                notes=json.loads(row["notes"] or "[]"),
            )

    async def update_user_profile(self, profile: UserProfile) -> None:
        """Update or create a user profile.

        Args:
            profile: The user profile to save.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            self._connection.execute(
                """
                INSERT OR REPLACE INTO user_profiles
                (user_name, first_seen, last_seen, interaction_count, topics, preferences, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.user_name,
                    profile.first_seen.isoformat(),
                    profile.last_seen.isoformat(),
                    profile.interaction_count,
                    json.dumps(profile.topics),
                    json.dumps(profile.preferences),
                    json.dumps(profile.notes),
                ),
            )
            self._connection.commit()

    async def record_interaction(
        self,
        user_name: str,
        user_message: str,
        ai_response: str,
        emotion: Optional[str] = None,
    ) -> str:
        """Record a conversation interaction.

        This is a convenience method that creates a memory entry
        and updates the user profile.

        Args:
            user_name: The user's name.
            user_message: The user's message.
            ai_response: The AI's response.
            emotion: Detected emotion (optional).

        Returns:
            The ID of the created memory entry.
        """
        # Create memory entry
        entry = MemoryEntry(
            memory_type=MemoryType.CONVERSATION,
            content=f"{user_name}: {user_message}\nAI: {ai_response}",
            user_name=user_name,
            emotion=emotion,
            metadata={
                "user_message": user_message,
                "ai_response": ai_response,
            },
        )
        entry_id = await self.store(entry)

        # Update user profile
        profile = await self.get_user_profile(user_name)
        if profile:
            profile.last_seen = datetime.now()
            profile.interaction_count += 1
        else:
            profile = UserProfile(
                user_name=user_name,
                interaction_count=1,
            )
        await self.update_user_profile(profile)

        return entry_id

    async def get_stats(self) -> dict:
        """Get memory statistics.

        Returns:
            Dictionary with memory statistics.
        """
        async with self._lock:
            if not self._connection:
                raise RuntimeError("Memory not initialized")

            cursor = self._connection.execute(
                "SELECT COUNT(*) as total FROM memories"
            )
            total = cursor.fetchone()["total"]

            cursor = self._connection.execute(
                """
                SELECT memory_type, COUNT(*) as count
                FROM memories
                GROUP BY memory_type
                """
            )
            by_type = {row["memory_type"]: row["count"] for row in cursor.fetchall()}

            cursor = self._connection.execute(
                "SELECT COUNT(*) as total FROM user_profiles"
            )
            user_count = cursor.fetchone()["total"]

            return {
                "total_entries": total,
                "by_type": by_type,
                "unique_users": user_count,
            }

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """Convert a database row to a MemoryEntry.

        Args:
            row: SQLite row object.

        Returns:
            MemoryEntry instance.
        """
        return MemoryEntry(
            id=row["id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            user_name=row["user_name"],
            keywords=json.loads(row["keywords"] or "[]"),
            importance=Importance(row["importance"]),
            emotion=row["emotion"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"])
            if row["last_accessed"]
            else None,
            access_count=row["access_count"],
            metadata=json.loads(row["metadata"] or "{}"),
        )
