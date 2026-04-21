"""ExperienceDistiller - Extract summaries and patterns from conversations."""

from typing import List

from context_harness.backend import StorageBackend
from context_harness.models import ThreadMessage, Memory, MemoryType


class ExperienceDistiller:
    """Extract summaries and reusable experience patterns from threads."""

    def __init__(self, backend: StorageBackend):
        """
        Initialize ExperienceDistiller.

        Args:
            backend: StorageBackend instance
        """
        self._backend = backend

    def distill_thread(self, thread_id: str) -> List[Memory]:
        """
        Distill a thread into memories (summaries + patterns).

        Args:
            thread_id: Thread to distill

        Returns:
            List of distilled Memory objects
        """
        # Get messages from thread
        config = {"thread_id": thread_id}
        messages = self._backend.get_messages(config)

        if not messages:
            return []

        # Distill messages
        return self.distill_messages(messages)

    def distill_messages(self, messages: List[ThreadMessage]) -> List[Memory]:
        """
        Distill raw message list.

        Args:
            messages: List of ThreadMessage objects

        Returns:
            List of Memory objects
        """
        memories = []

        # Extract summary
        summary = self.extract_summary(messages)
        if summary:
            memories.append(summary)

        # Extract patterns (user preferences, effective responses)
        patterns = self.extract_patterns(messages)
        memories.extend(patterns)

        return memories

    def extract_summary(self, messages: List[ThreadMessage]) -> Memory:
        """
        Create conversation summary.

        Default strategy: Use last N messages as summary basis.

        Args:
            messages: List of ThreadMessage objects

        Returns:
            Memory object with summary
        """
        if not messages:
            return None

        # Simple strategy: summarize last 5 messages
        recent_messages = messages[-5:] if len(messages) > 5 else messages

        # Build summary content from message content
        summary_parts = []
        for msg in recent_messages:
            if msg.is_spilled:
                # Skip spilled messages for summary
                continue

            # Extract content preview
            content = msg.unwrap_to_langchain().content
            if isinstance(content, str):
                summary_parts.append(content[:100])

        summary_content = f"Conversation summary: {len(messages)} messages discussing {summary_parts[0] if summary_parts else 'various topics'}"

        # Create Memory
        thread_id = messages[0].thread_id
        message_ids = [msg.message_id for msg in messages]

        memory = Memory(
            memory_type=MemoryType.SUMMARY,
            content=summary_content,
            thread_id=thread_id,
            related_message_ids=message_ids
        )

        return memory

    def extract_patterns(self, messages: List[ThreadMessage]) -> List[Memory]:
        """
        Extract reusable experience patterns.

        Default strategy: Keyword-based pattern extraction.

        Args:
            messages: List of ThreadMessage objects

        Returns:
            List of Memory objects with patterns
        """
        patterns = []

        # Simple pattern extraction: look for keywords like "prefer", "want", "need"
        keywords = ["prefer", "want", "need", "always", "never", "like"]

        thread_id = messages[0].thread_id if messages else ""

        for keyword in keywords:
            # Search messages for keyword
            matching_msgs = []
            for msg in messages:
                if msg.is_spilled:
                    continue

                content = str(msg.unwrap_to_langchain().content)
                if keyword.lower() in content.lower():
                    matching_msgs.append(msg)

            if matching_msgs:
                # Create pattern memory
                pattern_content = f"User {keyword}: {matching_msgs[0].unwrap_to_langchain().content[:50]}"

                memory = Memory(
                    memory_type=MemoryType.USER_PREFERENCE,
                    content=pattern_content,
                    thread_id=thread_id,
                    related_message_ids=[msg.message_id for msg in matching_msgs]
                )
                patterns.append(memory)

        return patterns

    def link_memory_to_messages(
        self,
        memory: Memory,
        message_ids: List[str]
    ) -> Memory:
        """
        Connect memory to source messages for traceability.

        Args:
            memory: Memory object
            message_ids: List of message IDs

        Returns:
            Memory with updated related_message_ids
        """
        # Update related_message_ids
        memory.related_message_ids = message_ids
        return memory