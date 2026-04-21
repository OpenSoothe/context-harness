"""StorageBackend abstract interface and error types."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from context_harness.models import Thread, ThreadMessage, Memory, SpilledContentReference


class BackendError(Exception):
    """Base exception for all backend failures."""
    pass


class ThreadNotFoundError(BackendError):
    """Thread doesn't exist for given config."""
    pass


class MemoryNotFoundError(BackendError):
    """Memory ID invalid or doesn't exist."""
    pass


class SpillContentNotFoundError(BackendError):
    """Spilled content deleted or missing."""
    pass


class BackendConfigurationError(BackendError):
    """Invalid backend configuration or initialization failure."""
    pass


class StorageBackend(ABC):
    """
    Abstract storage backend interface.

    Inspired by LangGraph checkpointer: config-based routing for threads.
    All methods use config dict for flexible filtering and routing.
    """

    # === Thread Operations ===

    @abstractmethod
    def get_thread(self, config: Dict[str, Any]) -> Optional[Thread]:
        """
        Retrieve thread by config (contains thread_id).

        Args:
            config: Dict with thread_id and optional filters
                    e.g., {"thread_id": "abc", "user_id": "user1"}

        Returns:
            Thread object if exists, None otherwise

        Raises:
            BackendError: If storage read fails
        """

    @abstractmethod
    def put_thread(self, config: Dict[str, Any], thread: Thread) -> None:
        """
        Save/update thread state.

        Args:
            config: Dict with thread_id
            thread: Thread object to persist

        Raises:
            BackendError: If storage write fails
        """

    @abstractmethod
    def list_threads(self, config: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        List thread metadata with optional filters.

        Args:
            config: Optional filters (user_id, date_range, status)

        Returns:
            List of thread config/metadata dicts (not full Thread objects)

        Raises:
            BackendError: If storage read fails
        """

    # === Message Operations ===

    @abstractmethod
    def append_message(self, config: Dict[str, Any], message: ThreadMessage) -> None:
        """
        Append message to thread (efficient, no full rewrite).

        Args:
            config: Dict with thread_id
            message: ThreadMessage to append

        Raises:
            BackendError: If storage write fails
        """

    @abstractmethod
    def get_messages(
        self,
        config: Dict[str, Any],
        limit: Optional[int] = None,
        before_timestamp: Optional[float] = None
    ) -> List[ThreadMessage]:
        """
        Retrieve messages from thread with pagination.

        Args:
            config: Dict with thread_id
            limit: Optional max number of messages
            before_timestamp: Optional timestamp filter (messages before this time)

        Returns:
            List of ThreadMessage objects (ordered chronologically)

        Raises:
            BackendError: If storage read fails
        """

    # === Memory Operations ===

    @abstractmethod
    def put_memory(self, memory: Memory, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Store memory (thread-linked or cross-thread).

        Args:
            memory: Memory object to store
            config: Optional context (thread_id, user_id for scoping)

        Raises:
            BackendError: If storage write fails
        """

    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Unique memory identifier

        Returns:
            Memory object if exists, None otherwise

        Raises:
            BackendError: If storage read fails
        """

    @abstractmethod
    def search_memories(
        self,
        query: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Search memories with semantic query and filters.

        Args:
            query: Optional semantic search query string
            config: Optional filters (thread_id, user_id, date_range)
            memory_type: Optional type filter (summary, experience_pattern)
            limit: Optional result limit

        Returns:
            List of matching Memory objects (ranked by relevance)

        Raises:
            BackendError: If storage read fails
        """

    # === Spilled Content Operations ===

    @abstractmethod
    def spill_content(
        self,
        content: Any,
        spill_metadata: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> SpilledContentReference:
        """
        Offload large content to storage and return reference.

        Args:
            content: Content to spill (text, data, etc.)
            spill_metadata: Metadata dict (content_type, preview, size)
            config: Optional context (thread_id)

        Returns:
            SpilledContentReference with spill_id and location

        Raises:
            BackendError: If storage write fails
        """

    @abstractmethod
    def retrieve_spilled_content(self, spill_id: str) -> Optional[Any]:
        """
        Retrieve spilled content by ID.

        Args:
            spill_id: Unique spill identifier

        Returns:
            Original content if exists, None otherwise

        Raises:
            BackendError: If storage read fails
            SpillContentNotFoundError: If spill_id invalid
        """

    @abstractmethod
    def delete_spilled_content(self, spill_id: str) -> None:
        """
        Delete spilled content.

        Args:
            spill_id: Unique spill identifier

        Raises:
            BackendError: If storage delete fails
            SpillContentNotFoundError: If spill_id invalid
        """