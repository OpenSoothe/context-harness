"""ContextBuilder - Construct context for new queries."""

from typing import Optional, List, Dict, Any

from context_harness.backend import StorageBackend
from context_harness.models import ThreadMessage, Memory, ContextConfig, RetrievalStrategy, MemoryType


class ContextBuilder:
    """Build context for new queries by selecting and formatting information."""

    def __init__(
        self,
        backend: StorageBackend,
        config: Optional[ContextConfig] = None
    ):
        """
        Initialize ContextBuilder.

        Args:
            backend: StorageBackend instance
            config: ContextConfig for context construction
        """
        self._backend = backend
        self._config = config or ContextConfig()

    def build_context(
        self,
        query: str,
        thread_id: Optional[str] = None,
        config: Optional[ContextConfig] = None
    ) -> str:
        """
        Build full context string for new query.

        Args:
            query: New user query
            thread_id: Optional thread for history retrieval
            config: Optional override config

        Returns:
            Formatted context string
        """
        use_config = config or self._config

        # Select messages
        messages = []
        if thread_id:
            messages = self.select_messages(query, thread_id, use_config.retrieval_strategy)

        # Select memories
        memories = []
        if thread_id:
            memories = self.select_memories(query, thread_id)

        # Format context
        context = self.format_context(messages, memories, use_config)

        return context

    def select_messages(
        self,
        query: str,
        thread_id: str,
        strategy: RetrievalStrategy
    ) -> List[ThreadMessage]:
        """
        Select relevant messages from thread.

        Args:
            query: New query
            thread_id: Thread identifier
            strategy: Retrieval strategy

        Returns:
            List of selected ThreadMessage objects
        """
        config = {"thread_id": thread_id}

        if strategy == RetrievalStrategy.RECENT_FIRST:
            # Get most recent messages
            messages = self._backend.get_messages(config, limit=10)
        elif strategy == RetrievalStrategy.SEMANTIC_SIMILARITY:
            # For now, fallback to recent-first (semantic search future work)
            messages = self._backend.get_messages(config, limit=10)
        else:
            # Hybrid: combine recency + future semantic relevance
            messages = self._backend.get_messages(config, limit=10)

        return messages

    def select_memories(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Select relevant memories.

        Args:
            query: New query
            thread_id: Optional thread filter

        Returns:
            List of relevant Memory objects
        """
        # Search memories relevant to query
        memories = self._backend.search_memories(
            query=query,
            config={"thread_id": thread_id} if thread_id else None,
            limit=5
        )

        return memories

    def format_context(
        self,
        messages: List[ThreadMessage],
        memories: List[Memory],
        config: ContextConfig
    ) -> str:
        """
        Format selected items into context string.

        Args:
            messages: Selected messages
            memories: Selected memories
            config: ContextConfig with template format

        Returns:
            Formatted context string
        """
        sections = []

        for section_name in config.sections:
            template = config.template_format.get(section_name, "{content}")
            content = ""

            if section_name == "recent_history" and messages:
                # Format messages
                msg_parts = []
                for msg in messages:
                    if msg.is_spilled:
                        # Include spill marker
                        msg_parts.append(msg.content)
                    else:
                        # Unwrap to actual content
                        msg_parts.append(str(msg.unwrap_to_langchain().content))

                content = "\n".join(msg_parts)

            elif section_name == "relevant_memories" and memories:
                # Format memories
                memory_parts = []
                for memory in memories:
                    memory_parts.append(memory.content)

                content = "\n".join(memory_parts)

            elif section_name == "experiences":
                # Extract experience patterns
                experience_parts = []
                for memory in memories:
                    if memory.memory_type == MemoryType.EXPERIENCE_PATTERN:
                        experience_parts.append(memory.content)

                content = "\n".join(experience_parts) if experience_parts else ""

            if content:
                section_text = template.format(content=content)
                sections.append(section_text)

        return "\n\n".join(sections)