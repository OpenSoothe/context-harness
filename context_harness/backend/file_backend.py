"""FileBackend implementation with JSON/JSONL storage."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from context_harness.models import Thread, ThreadMessage, Memory, SpilledContentReference, SpillType
from context_harness.backend.base import (
    StorageBackend,
    BackendError,
    BackendConfigurationError,
    SpillContentNotFoundError,
)
from context_harness.backend.cache import SimpleCache
from context_harness.backend.serialization import (
    serialize_thread,
    deserialize_thread,
    serialize_thread_message,
    deserialize_thread_message,
    serialize_memory,
    deserialize_memory,
    serialize_spill_reference,
    deserialize_spill_reference,
    to_json,
    from_json,
)


class FileBackend(StorageBackend):
    """
    File-based storage backend using JSON/JSONL.

    Features:
    - JSON for threads/memories (structured, readable)
    - JSONL for messages (efficient append, streaming)
    - In-memory cache for frequent access (configurable TTL)
    - Metadata indexing for search
    """

    def __init__(
        self,
        base_path: str = ".context_harness",
        cache_ttl: int = 300,  # 5 minutes
        cache_enabled: bool = True
    ):
        """
        Initialize FileBackend.

        Args:
            base_path: Root directory for storage
            cache_ttl: Cache TTL in seconds
            cache_enabled: Enable/disable caching

        Raises:
            BackendConfigurationError: If base_path invalid or cannot create
        """
        self.base_path = Path(base_path)
        self.cache_enabled = cache_enabled
        self.cache = SimpleCache(ttl_seconds=cache_ttl) if cache_enabled else None

        # Create base directory structure
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._threads_dir().mkdir(exist_ok=True)
            self._memories_dir().mkdir(exist_ok=True)
            self._spilled_dir().mkdir(exist_ok=True)
        except OSError as e:
            raise BackendConfigurationError(f"Failed to create storage directories: {e}")

    # === Directory Helpers ===

    def _threads_dir(self) -> Path:
        """Get threads directory."""
        return self.base_path / "threads"

    def _memories_dir(self) -> Path:
        """Get memories directory."""
        return self.base_path / "memories"

    def _spilled_dir(self) -> Path:
        """Get spilled directory."""
        return self.base_path / "spilled"

    def _thread_file(self, thread_id: str) -> Path:
        """Get thread metadata file path."""
        return self._threads_dir() / f"{thread_id}.json"

    def _thread_messages_file(self, thread_id: str) -> Path:
        """Get thread messages JSONL file path."""
        return self._threads_dir() / thread_id / "messages.jsonl"

    def _memory_file(self, memory_id: str) -> Path:
        """Get memory file path."""
        return self._memories_dir() / f"{memory_id}.json"

    def _memory_index_file(self) -> Path:
        """Get memory index file path."""
        return self._memories_dir() / "index.json"

    def _spill_file(self, spill_id: str) -> Path:
        """Get spill content file path."""
        return self._spilled_dir() / f"{spill_id}.jsonl"

    def _spill_metadata_file(self) -> Path:
        """Get spill metadata registry file path."""
        return self._spilled_dir() / "metadata.json"

    # === Thread Operations ===

    def get_thread(self, config: Dict[str, Any]) -> Optional[Thread]:
        """
        Retrieve thread by config (contains thread_id).

        Implementation: Read threads/{thread_id}.json.
        """
        thread_id = config.get("thread_id")
        if not thread_id:
            raise BackendConfigurationError("thread_id required in config")

        # Check cache first
        cache_key = f"thread:{thread_id}"
        if self.cache_enabled and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Read from file
        thread_file = self._thread_file(thread_id)
        if not thread_file.exists():
            return None

        try:
            with open(thread_file, 'r') as f:
                data = from_json(f.read())
            thread = deserialize_thread(data)

            # Cache if enabled
            if self.cache_enabled and self.cache:
                self.cache.set(cache_key, thread)

            return thread
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to read thread {thread_id}: {e}")

    def put_thread(self, config: Dict[str, Any], thread: Thread) -> None:
        """
        Save/update thread state.

        Implementation: Write threads/{thread_id}.json.
        """
        thread_id = config.get("thread_id") or thread.thread_id

        # Ensure thread directory exists
        thread_dir = self._threads_dir() / thread_id
        thread_dir.mkdir(exist_ok=True)

        # Serialize and write
        thread_file = self._thread_file(thread_id)
        try:
            data = serialize_thread(thread)
            with open(thread_file, 'w') as f:
                f.write(to_json(data))

            # Update cache
            if self.cache_enabled and self.cache:
                cache_key = f"thread:{thread_id}"
                self.cache.set(cache_key, thread)
        except OSError as e:
            raise BackendError(f"Failed to write thread {thread_id}: {e}")

    def list_threads(self, config: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        List thread metadata with optional filters.

        Implementation: List thread files, apply filters.
        """
        threads_dir = self._threads_dir()
        thread_files = list(threads_dir.glob("*.json"))

        threads = []
        for thread_file in thread_files:
            try:
                with open(thread_file, 'r') as f:
                    data = from_json(f.read())

                # Apply filters
                if config:
                    # Filter by user_id
                    if "user_id" in config:
                        if data.get("metadata", {}).get("user_id") != config["user_id"]:
                            continue

                threads.append({
                    "thread_id": data["thread_id"],
                    "metadata": data["metadata"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                })
            except (OSError, json.JSONDecodeError) as e:
                # Skip invalid files
                continue

        # Sort by created_at descending
        threads.sort(key=lambda t: t["created_at"], reverse=True)

        return threads

    # === Message Operations ===

    def append_message(self, config: Dict[str, Any], message: ThreadMessage) -> None:
        """
        Append message to thread (efficient, no full rewrite).

        Implementation: Append to threads/{thread_id}/messages.jsonl.
        """
        thread_id = config.get("thread_id")
        if not thread_id:
            raise BackendConfigurationError("thread_id required in config")

        # Ensure thread directory exists
        thread_dir = self._threads_dir() / thread_id
        thread_dir.mkdir(exist_ok=True)

        # Serialize message to JSON line
        messages_file = self._thread_messages_file(thread_id)
        try:
            data = serialize_thread_message(message)
            json_line = json.dumps(data)

            # Append to JSONL file
            with open(messages_file, 'a') as f:
                f.write(json_line + '\n')

            # Update thread metadata (update timestamp)
            thread = self.get_thread(config)
            if thread:
                thread.update_timestamp()
                self.put_thread(config, thread)
        except OSError as e:
            raise BackendError(f"Failed to append message to thread {thread_id}: {e}")

    def get_messages(
        self,
        config: Dict[str, Any],
        limit: Optional[int] = None,
        before_timestamp: Optional[float] = None
    ) -> List[ThreadMessage]:
        """
        Retrieve messages from thread with pagination.

        Implementation: Read threads/{thread_id}/messages.jsonl, filter, deserialize.
        """
        thread_id = config.get("thread_id")
        if not thread_id:
            raise BackendConfigurationError("thread_id required in config")

        messages_file = self._thread_messages_file(thread_id)
        if not messages_file.exists():
            return []

        messages = []
        try:
            with open(messages_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = from_json(line)
                    message = deserialize_thread_message(data)

                    # Apply timestamp filter
                    if before_timestamp and message.timestamp >= before_timestamp:
                        continue

                    messages.append(message)

            # Messages are in chronological order (append order)
            # Apply limit (get most recent N messages)
            if limit and len(messages) > limit:
                messages = messages[-limit:]

            return messages
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to read messages from thread {thread_id}: {e}")

    # === Memory Operations ===

    def put_memory(self, memory: Memory, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Store memory (thread-linked or cross-thread).

        Implementation: Write memories/{memory_id}.json and update index.
        """
        # Write memory file
        memory_file = self._memory_file(memory.memory_id)
        try:
            data = serialize_memory(memory)
            with open(memory_file, 'w') as f:
                f.write(to_json(data))

            # Update index
            self._update_memory_index(memory)
        except OSError as e:
            raise BackendError(f"Failed to write memory {memory.memory_id}: {e}")

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve specific memory by ID.

        Implementation: Read memories/{memory_id}.json.
        """
        memory_file = self._memory_file(memory_id)
        if not memory_file.exists():
            return None

        try:
            with open(memory_file, 'r') as f:
                data = from_json(f.read())
            memory = deserialize_memory(data)
            return memory
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to read memory {memory_id}: {e}")

    def search_memories(
        self,
        query: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Search memories with semantic query and filters.

        Implementation: Query memories/index.json, load matching memories.
        """
        index_file = self._memory_index_file()
        if not index_file.exists():
            return []

        try:
            with open(index_file, 'r') as f:
                index_data = from_json(f.read())

            memories_index = index_data.get("memories", [])

            # Apply filters
            candidates = []
            for entry in memories_index:
                # Filter by thread_id
                if config and "thread_id" in config:
                    if entry.get("thread_id") != config["thread_id"]:
                        continue

                # Filter by memory_type
                if memory_type:
                    if entry.get("memory_type") != memory_type:
                        continue

                # Keyword search on content_preview
                if query:
                    preview = entry.get("content_preview", "")
                    if query.lower() not in preview.lower():
                        continue

                candidates.append(entry)

            # Rank by relevance_score descending
            candidates.sort(key=lambda e: e.get("relevance_score", 0.0), reverse=True)

            # Apply limit
            if limit:
                candidates = candidates[:limit]

            # Load Memory objects
            memories = []
            for entry in candidates:
                memory_id = entry["memory_id"]
                memory = self.get_memory(memory_id)
                if memory:
                    memories.append(memory)

            return memories
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to search memories: {e}")

    def _update_memory_index(self, memory: Memory) -> None:
        """Update memory index with new/updated memory metadata."""
        index_file = self._memory_index_file()

        # Load existing index
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index_data = from_json(f.read())
            except (OSError, json.JSONDecodeError):
                index_data = {"memories": []}
        else:
            index_data = {"memories": []}

        memories_index = index_data.get("memories", [])

        # Remove existing entry for this memory_id
        memories_index = [e for e in memories_index if e.get("memory_id") != memory.memory_id]

        # Add new entry
        entry = {
            "memory_id": memory.memory_id,
            "thread_id": memory.thread_id,
            "memory_type": memory.memory_type.value,
            "relevance_score": memory.relevance_score,
            "timestamp": memory.metadata.get("timestamp", time.time()),
            "content_preview": memory.content[:100],  # First 100 chars
        }
        memories_index.append(entry)

        # Write updated index
        try:
            with open(index_file, 'w') as f:
                f.write(to_json({"memories": memories_index}))
        except OSError as e:
            raise BackendError(f"Failed to update memory index: {e}")

    # === Spilled Content Operations ===

    def spill_content(
        self,
        content: Any,
        spill_metadata: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> SpilledContentReference:
        """
        Offload large content to storage and return reference.

        Implementation: Write spilled/{spill_id}.jsonl, update metadata.
        """
        import uuid

        # Generate spill_id
        spill_id = str(uuid.uuid4())

        # Write content to file
        spill_file = self._spill_file(spill_id)
        try:
            # Serialize content (assuming string or JSON-serializable)
            if isinstance(content, str):
                content_data = {"content": content}
            else:
                content_data = content

            with open(spill_file, 'w') as f:
                f.write(json.dumps(content_data) + '\n')

            # Create SpilledContentReference
            spill_ref = SpilledContentReference(
                spill_type=SpillType.MESSAGE_SPILL,
                content_location=str(spill_file),
                content_size=spill_metadata.get("size", len(str(content))),
                content_type=spill_metadata.get("content_type", "unknown"),
                content_preview=spill_metadata.get("preview"),
                spill_id=spill_id,
            )

            # Update spill metadata registry
            self._update_spill_metadata(spill_ref)

            return spill_ref
        except OSError as e:
            raise BackendError(f"Failed to spill content: {e}")

    def retrieve_spilled_content(self, spill_id: str) -> Optional[Any]:
        """
        Retrieve spilled content by ID.

        Implementation: Read spilled/{spill_id}.jsonl.
        """
        spill_file = self._spill_file(spill_id)
        if not spill_file.exists():
            raise SpillContentNotFoundError(f"Spilled content {spill_id} not found")

        try:
            with open(spill_file, 'r') as f:
                content_data = from_json(f.read())

            # Return content
            if isinstance(content_data, dict) and "content" in content_data:
                return content_data["content"]
            else:
                return content_data
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to retrieve spilled content {spill_id}: {e}")

    def delete_spilled_content(self, spill_id: str) -> None:
        """
        Delete spilled content.

        Implementation: Delete spilled/{spill_id}.jsonl, update metadata.
        """
        spill_file = self._spill_file(spill_id)
        if not spill_file.exists():
            raise SpillContentNotFoundError(f"Spilled content {spill_id} not found")

        try:
            # Delete file
            spill_file.unlink()

            # Update metadata registry
            self._remove_spill_metadata(spill_id)
        except OSError as e:
            raise BackendError(f"Failed to delete spilled content {spill_id}: {e}")

    def _update_spill_metadata(self, spill_ref: SpilledContentReference) -> None:
        """Update spill metadata registry."""
        metadata_file = self._spill_metadata_file()

        # Load existing metadata
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata_data = from_json(f.read())
            except (OSError, json.JSONDecodeError):
                metadata_data = {"spills": []}
        else:
            metadata_data = {"spills": []}

        spills = metadata_data.get("spills", [])

        # Add entry
        entry = {
            "spill_id": spill_ref.spill_id,
            "spill_type": spill_ref.spill_type.value,
            "content_location": spill_ref.content_location,
            "content_size": spill_ref.content_size,
            "content_type": spill_ref.content_type,
            "timestamp": time.time(),
        }
        spills.append(entry)

        # Write updated metadata
        try:
            with open(metadata_file, 'w') as f:
                f.write(to_json({"spills": spills}))
        except OSError as e:
            raise BackendError(f"Failed to update spill metadata: {e}")

    def _remove_spill_metadata(self, spill_id: str) -> None:
        """Remove spill metadata entry."""
        metadata_file = self._spill_metadata_file()

        if not metadata_file.exists():
            return

        try:
            with open(metadata_file, 'r') as f:
                metadata_data = from_json(f.read())

            spills = metadata_data.get("spills", [])
            spills = [s for s in spills if s.get("spill_id") != spill_id]

            with open(metadata_file, 'w') as f:
                f.write(to_json({"spills": spills}))
        except (OSError, json.JSONDecodeError) as e:
            raise BackendError(f"Failed to remove spill metadata: {e}")