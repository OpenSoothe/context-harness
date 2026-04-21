"""MemoryManager - Memory storage and search."""

from typing import Optional, List, Dict, Any

from context_harness.backend import StorageBackend
from context_harness.models import Memory


class MemoryManager:
    """Manage memory storage, retrieval, and search."""

    def __init__(self, backend: StorageBackend):
        """
        Initialize MemoryManager.

        Args:
            backend: StorageBackend instance
        """
        self._backend = backend

    def store_memory(self, memory: Memory) -> None:
        """
        Save memory to backend.

        Args:
            memory: Memory object to store
        """
        self._backend.put_memory(memory)

    def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Unique memory identifier

        Returns:
            Memory object if exists, None otherwise
        """
        return self._backend.get_memory(memory_id)

    def search_memories(
        self,
        query: Optional[str] = None,
        thread_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Search memories with filters.

        Args:
            query: Optional search query string
            thread_id: Optional filter by thread
            memory_type: Optional filter by type

        Returns:
            List of matching Memory objects (ranked by relevance)
        """
        config = {"thread_id": thread_id} if thread_id else None
        return self._backend.search_memories(
            query=query,
            config=config,
            memory_type=memory_type,
            limit=limit
        )

    def get_thread_memories(self, thread_id: str) -> List[Memory]:
        """
        Get all memories linked to a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of Memory objects
        """
        return self.search_memories(thread_id=thread_id)

    def update_memory_access(self, memory_id: str) -> None:
        """
        Increment access count for relevance scoring.

        Args:
            memory_id: Memory identifier
        """
        memory = self.retrieve_memory(memory_id)
        if memory:
            # Update access_count in metadata
            access_count = memory.metadata.get("access_count", 0)
            memory.metadata["access_count"] = access_count + 1
            self.store_memory(memory)