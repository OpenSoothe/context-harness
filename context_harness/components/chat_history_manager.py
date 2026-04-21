"""ChatHistoryManager - Thread lifecycle and message management."""

from typing import Optional, Dict, Any, List
import uuid

from langchain_core.messages import BaseMessage

from context_harness.backend import StorageBackend
from context_harness.models import Thread, ThreadMessage, SpilledContentReference, SpillType
from context_harness.models.insertion_syntax import build_insertion_syntax


class ChatHistoryManager:
    """Manage conversation thread lifecycle and message history."""

    def __init__(self, backend: StorageBackend, spill_threshold: int = 10000):
        """
        Initialize ChatHistoryManager.

        Args:
            backend: StorageBackend instance
            spill_threshold: Message content size threshold for spilling (bytes)
        """
        self._backend = backend
        self._spill_threshold = spill_threshold

    def create_thread(self, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """
        Create new conversation thread.

        Args:
            metadata: Optional thread metadata

        Returns:
            Thread object
        """
        thread = Thread(metadata=metadata or {})
        config = {"thread_id": thread.thread_id}
        self._backend.put_thread(config, thread)
        return thread

    def add_message(
        self,
        thread_id: str,
        message: BaseMessage,
        auto_spill: bool = True
    ) -> ThreadMessage:
        """
        Add message to thread with automatic spill detection.

        Args:
            thread_id: Thread identifier
            message: LangChain BaseMessage
            auto_spill: Enable automatic spill for large content

        Returns:
            ThreadMessage (may be spilled if large)
        """
        # Wrap LangChain message
        wrapped_msg = ThreadMessage.create_from_langchain(thread_id, message)

        # Check spill threshold
        if auto_spill:
            content_size = len(str(message.content))
            if content_size > self._spill_threshold:
                wrapped_msg = self.spill_message_content(wrapped_msg)

        # Append message
        config = {"thread_id": thread_id}
        self._backend.append_message(config, wrapped_msg)

        return wrapped_msg

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Load thread state.

        Args:
            thread_id: Thread identifier

        Returns:
            Thread object if exists, None otherwise
        """
        config = {"thread_id": thread_id}
        return self._backend.get_thread(config)

    def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        include_spilled_markers: bool = True
    ) -> List[ThreadMessage]:
        """
        Retrieve messages from thread.

        Args:
            thread_id: Thread identifier
            limit: Optional max number of messages
            include_spilled_markers: Include spilled messages with markers

        Returns:
            List of ThreadMessage objects
        """
        config = {"thread_id": thread_id}
        messages = self._backend.get_messages(config, limit=limit)

        if not include_spilled_markers:
            messages = [msg for msg in messages if not msg.is_spilled]

        return messages

    def check_spill_needed(self, message: ThreadMessage) -> bool:
        """
        Check if message exceeds spill threshold.

        Args:
            message: ThreadMessage to check

        Returns:
            True if spill needed, False otherwise
        """
        if message.is_spilled:
            return False

        content = message.unwrap_to_langchain().content
        return len(str(content)) > self._spill_threshold

    def spill_message_content(self, message: ThreadMessage) -> ThreadMessage:
        """
        Spill large message content and return ThreadMessage with marker.

        Args:
            message: ThreadMessage to spill

        Returns:
            ThreadMessage with insertion syntax marker
        """
        # Extract content
        content = message.unwrap_to_langchain().content

        # Spill content via backend
        spill_ref = self._backend.spill_content(
            content=content,
            spill_metadata={
                "content_type": "ai_report",
                "size": len(str(content)),
                "preview": str(content)[:100]
            }
        )

        # Build insertion syntax marker
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str=SpillType.MESSAGE_SPILL.value,
            metadata={
                "content_type": spill_ref.content_type,
                "preview": spill_ref.content_preview,
                "size": spill_ref.content_size
            },
            reference=f"spill_id={spill_ref.spill_id}"
        )

        # Create spilled ThreadMessage
        spilled_message = ThreadMessage(
            thread_id=message.thread_id,
            content=marker,
            message_id=message.message_id,
            timestamp=message.timestamp,
            is_spilled=True,
            spill_reference=spill_ref,
            metadata=message.metadata
        )

        return spilled_message