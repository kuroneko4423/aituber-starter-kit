"""Memory retrieval system for context-aware responses."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .long_term_memory import LongTermMemory
from .models import Importance, MemoryEntry, MemorySearchResult, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for memory retrieval.

    Attributes:
        max_results: Maximum number of memories to retrieve.
        relevance_threshold: Minimum relevance score (0.0 to 1.0).
        recency_weight: Weight for recency in scoring (0.0 to 1.0).
        importance_weight: Weight for importance in scoring (0.0 to 1.0).
        user_context_weight: Weight for user-specific context (0.0 to 1.0).
        include_user_profile: Whether to include user profile information.
    """

    max_results: int = 5
    relevance_threshold: float = 0.3
    recency_weight: float = 0.3
    importance_weight: float = 0.2
    user_context_weight: float = 0.3
    include_user_profile: bool = True


class MemoryRetriever:
    """Retrieves relevant memories for context-aware responses.

    This class implements a RAG-like (Retrieval-Augmented Generation) system
    that finds relevant memories to include in the LLM context.

    Args:
        memory_store: The long-term memory store.
        config: Retrieval configuration.

    Example:
        ```python
        retriever = MemoryRetriever(memory_store)

        # Retrieve relevant context
        context = await retriever.retrieve_context(
            query="What's your favorite anime?",
            user_name="Viewer123",
        )

        # Use context in LLM prompt
        full_prompt = f"{context}\n\nUser: {query}"
        ```
    """

    def __init__(
        self,
        memory_store: LongTermMemory,
        config: Optional[RetrievalConfig] = None,
    ) -> None:
        """Initialize the memory retriever.

        Args:
            memory_store: The long-term memory store.
            config: Optional retrieval configuration.
        """
        self.memory = memory_store
        self.config = config or RetrievalConfig()

    async def retrieve(
        self,
        query: str,
        user_name: Optional[str] = None,
        memory_types: Optional[list[MemoryType]] = None,
    ) -> list[MemorySearchResult]:
        """Retrieve relevant memories for a query.

        Args:
            query: The search query (usually the user's message).
            user_name: Optional user name for context.
            memory_types: Optional filter for memory types.

        Returns:
            List of relevant memory search results.
        """
        results: list[MemorySearchResult] = []

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        if not keywords:
            # No meaningful keywords, return recent memories
            recent = await self.memory.get_recent(limit=self.config.max_results)
            for entry in recent:
                results.append(
                    MemorySearchResult(
                        entry=entry,
                        relevance_score=0.3,
                        match_reason="recent",
                    )
                )
            return results

        # Search by keywords
        try:
            search_query = " OR ".join(keywords)
            for mem_type in memory_types or [None]:
                entries = await self.memory.search(
                    query=search_query,
                    limit=self.config.max_results * 2,
                    memory_type=mem_type,
                    user_name=user_name if self.config.user_context_weight > 0 else None,
                )

                for entry in entries:
                    score = self._calculate_relevance(entry, query, keywords, user_name)
                    if score >= self.config.relevance_threshold:
                        results.append(
                            MemorySearchResult(
                                entry=entry,
                                relevance_score=score,
                                match_reason="keyword_match",
                            )
                        )
        except Exception as e:
            logger.warning(f"Search failed: {e}, falling back to recent memories")
            recent = await self.memory.get_recent(limit=self.config.max_results)
            for entry in recent:
                results.append(
                    MemorySearchResult(
                        entry=entry,
                        relevance_score=0.3,
                        match_reason="fallback",
                    )
                )

        # Get user-specific memories if user is known
        if user_name and self.config.user_context_weight > 0:
            user_memories = await self.memory.search_by_user(
                user_name,
                limit=self.config.max_results,
            )
            for entry in user_memories:
                # Check if already in results
                if not any(r.entry.id == entry.id for r in results):
                    score = self._calculate_relevance(entry, query, keywords, user_name)
                    score += self.config.user_context_weight * 0.5  # Boost user-specific
                    results.append(
                        MemorySearchResult(
                            entry=entry,
                            relevance_score=min(score, 1.0),
                            match_reason="user_context",
                        )
                    )

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[: self.config.max_results]

    async def retrieve_context(
        self,
        query: str,
        user_name: Optional[str] = None,
    ) -> str:
        """Retrieve and format context for LLM prompt.

        This method retrieves relevant memories and formats them
        as a context string suitable for inclusion in an LLM prompt.

        Args:
            query: The user's message.
            user_name: Optional user name.

        Returns:
            Formatted context string.
        """
        results = await self.retrieve(query, user_name)

        if not results:
            return ""

        context_parts = []

        # Add user profile if available
        if user_name and self.config.include_user_profile:
            profile = await self.memory.get_user_profile(user_name)
            if profile:
                profile_str = self._format_user_profile(profile)
                if profile_str:
                    context_parts.append(f"[User Info: {user_name}]\n{profile_str}")

        # Add relevant memories
        if results:
            memory_strs = []
            for result in results:
                formatted = self._format_memory(result)
                if formatted:
                    memory_strs.append(formatted)

            if memory_strs:
                context_parts.append(
                    "[Relevant Memories]\n" + "\n".join(memory_strs)
                )

        if not context_parts:
            return ""

        return "\n\n".join(context_parts)

    async def store_interaction(
        self,
        user_name: str,
        user_message: str,
        ai_response: str,
        emotion: Optional[str] = None,
        extract_facts: bool = True,
    ) -> list[str]:
        """Store an interaction and extract important information.

        Args:
            user_name: The user's name.
            user_message: The user's message.
            ai_response: The AI's response.
            emotion: Detected emotion.
            extract_facts: Whether to extract and store facts.

        Returns:
            List of created memory entry IDs.
        """
        entry_ids = []

        # Store the conversation
        conv_id = await self.memory.record_interaction(
            user_name=user_name,
            user_message=user_message,
            ai_response=ai_response,
            emotion=emotion,
        )
        entry_ids.append(conv_id)

        # Extract and store facts if enabled
        if extract_facts:
            facts = self._extract_facts(user_message, user_name)
            for fact_content, importance in facts:
                fact_entry = MemoryEntry(
                    memory_type=MemoryType.FACT,
                    content=fact_content,
                    user_name=user_name,
                    importance=importance,
                    keywords=self._extract_keywords(fact_content),
                )
                fact_id = await self.memory.store(fact_entry)
                entry_ids.append(fact_id)

        return entry_ids

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text.

        Args:
            text: Input text.

        Returns:
            List of keywords.
        """
        # Remove common words and punctuation
        stopwords = {
            "の", "は", "が", "を", "に", "で", "と", "も", "や", "から",
            "まで", "より", "など", "って", "という", "です", "ます",
            "だ", "な", "ね", "よ", "か", "い", "う", "え", "お",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because",
            "until", "while", "this", "that", "these", "those", "it",
        }

        # Tokenize (simple split for now)
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter and return
        keywords = [
            word for word in words
            if word not in stopwords and len(word) > 1
        ]

        return list(set(keywords))[:10]  # Limit to 10 unique keywords

    def _calculate_relevance(
        self,
        entry: MemoryEntry,
        query: str,
        keywords: list[str],
        user_name: Optional[str],
    ) -> float:
        """Calculate relevance score for a memory entry.

        Args:
            entry: The memory entry.
            query: Original query.
            keywords: Extracted keywords.
            user_name: User name for context.

        Returns:
            Relevance score (0.0 to 1.0).
        """
        score = 0.0

        # Keyword match score
        entry_text = entry.content.lower()
        matched_keywords = sum(1 for kw in keywords if kw in entry_text)
        keyword_score = matched_keywords / max(len(keywords), 1)
        score += keyword_score * (1.0 - self.config.recency_weight - self.config.importance_weight)

        # Recency score
        age = datetime.now() - entry.timestamp
        if age < timedelta(hours=1):
            recency_score = 1.0
        elif age < timedelta(days=1):
            recency_score = 0.8
        elif age < timedelta(days=7):
            recency_score = 0.5
        elif age < timedelta(days=30):
            recency_score = 0.3
        else:
            recency_score = 0.1
        score += recency_score * self.config.recency_weight

        # Importance score
        importance_scores = {
            Importance.LOW: 0.25,
            Importance.MEDIUM: 0.5,
            Importance.HIGH: 0.75,
            Importance.CRITICAL: 1.0,
        }
        importance_score = importance_scores.get(entry.importance, 0.5)
        score += importance_score * self.config.importance_weight

        # User context bonus
        if user_name and entry.user_name == user_name:
            score += self.config.user_context_weight * 0.3

        return min(score, 1.0)

    def _extract_facts(
        self,
        text: str,
        user_name: str,
    ) -> list[tuple[str, Importance]]:
        """Extract facts from user message.

        Args:
            text: User's message.
            user_name: User's name.

        Returns:
            List of (fact_content, importance) tuples.
        """
        facts = []

        # Pattern matching for common fact expressions
        patterns = [
            # Japanese patterns
            (r"(?:私|僕|俺)(?:は|の)(.+?)(?:が好き|が嫌い|です)", Importance.MEDIUM),
            (r"(.+?)(?:が好き|が嫌い)", Importance.MEDIUM),
            (r"(?:私|僕|俺)(?:は|の)(.+?)(?:をしている|をやっている)", Importance.MEDIUM),
            (r"(?:誕生日|たんじょうび)(?:は|が)(.+)", Importance.HIGH),
            # English patterns
            (r"(?:I|my)\s+(?:like|love|enjoy)\s+(.+)", Importance.MEDIUM),
            (r"(?:I|my)\s+(?:hate|dislike)\s+(.+)", Importance.MEDIUM),
            (r"(?:I am|I'm)\s+(.+)", Importance.MEDIUM),
            (r"my\s+(?:birthday|name)\s+is\s+(.+)", Importance.HIGH),
        ]

        for pattern, importance in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                fact = f"{user_name}: {match.strip()}"
                if len(fact) > 10:  # Minimum length check
                    facts.append((fact, importance))

        return facts[:3]  # Limit to 3 facts per message

    def _format_memory(self, result: MemorySearchResult) -> str:
        """Format a memory search result for context.

        Args:
            result: The search result.

        Returns:
            Formatted string.
        """
        entry = result.entry
        time_ago = self._time_ago(entry.timestamp)

        # Truncate content if too long
        content = entry.content
        if len(content) > 200:
            content = content[:197] + "..."

        return f"- [{time_ago}] {content}"

    def _format_user_profile(self, profile) -> str:
        """Format user profile for context.

        Args:
            profile: UserProfile instance.

        Returns:
            Formatted string.
        """
        parts = []

        parts.append(f"Interactions: {profile.interaction_count}")

        if profile.topics:
            parts.append(f"Topics: {', '.join(profile.topics[:5])}")

        if profile.preferences:
            prefs = [f"{k}: {v}" for k, v in list(profile.preferences.items())[:3]]
            parts.append(f"Preferences: {', '.join(prefs)}")

        if profile.notes:
            parts.append(f"Notes: {profile.notes[-1]}")  # Most recent note

        return "\n".join(parts)

    def _time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as relative time.

        Args:
            timestamp: The timestamp.

        Returns:
            Human-readable relative time.
        """
        delta = datetime.now() - timestamp

        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days}d ago"
        else:
            return timestamp.strftime("%m/%d")
