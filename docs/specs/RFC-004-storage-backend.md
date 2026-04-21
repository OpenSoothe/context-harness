# RFC-004: Storage Backend Interface

**Status**: Draft
**Authors**: Xiaming Chen
**Created**: 2026-04-21
**Last Updated**: 2026-04-21
**Depends on**: [RFC-001-world-view](RFC-001-world-view.md), [RFC-002-core-architecture](RFC-002-core-architecture.md), [RFC-003-domain-models](RFC-003-domain-models.md)
**Supersedes**: ---
**Kind**: Implementation Interface Design

---

## 1. Abstract

This RFC defines the StorageBackend abstract interface and FileBackend default implementation for the context-harness library. The backend abstracts all persistence operations with a checkpointer-inspired config-based pattern. Thread, message, memory, and spilled content operations have consistent signatures. FileBackend uses JSON/JSONL storage with efficient append for messages and indexing for search. The interface enables pluggable backends without affecting core logic.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This RFC defines:

* StorageBackend abstract interface contract
* Method signatures for thread, message, memory, and spilled content operations
* Error types and handling contracts
* FileBackend implementation structure and storage format
* Config-based routing pattern (LangGraph checkpointer-inspired)
* Caching and indexing strategies for FileBackend
* Backend initialization and configuration parameters

### 2.2 Non-Goals

This RFC does **not** define:

* Additional backend implementations (SQLite, VectorDB - future work)
* Internal optimization algorithms (beyond basic caching/indexing)
* Concurrency handling patterns (thread-safe access)
* Migration or backup/restore strategies
* Performance benchmarks or tuning parameters

---

## 3. Background & Motivation

**Why abstract backend:** Different deployment contexts require different storage:
- Local/prototyping: FileBackend (no external dependencies)
- Production single-file: SQLiteBackend (structured queries, embedded)
- Semantic search: VectorBackend (Chroma, Pinecone integration)

Abstract interface isolates persistence from core logic, enabling pluggable backends without refactoring components.

**Why checkpointer pattern:** LangGraph uses config-based routing for thread persistence (config contains thread_id and filters). This pattern provides:
- Flexible routing (thread_id, user_id, session filters)
- Consistent parameter structure across methods
- Compatible with LangChain ecosystem patterns

**Why JSON/JSONL for FileBackend:**
- JSON for threads/memories: Human-readable, easy debugging, structured metadata
- JSONL for messages: Efficient append (no full file rewrite), streaming support
- No external dependencies: Works with standard Python libraries

---

## 4. Naming Conventions

| Pattern | Purpose | Example |
|---------|---------|---------|
| `{verb}_{entity}` | Backend operation naming | `get_thread`, `put_memory`, `append_message` |
| `config: Dict[str, Any]` | Config parameter naming | All methods use config dict for routing |
| `{entity}_id` | Identifier naming | `thread_id`, `memory_id`, `spill_id` |
| `StorageBackend` | Abstract interface naming | Base class for all backends |
| `FileBackend` | Implementation naming | Concrete file-based implementation |
| `BackendError` | Error type hierarchy | Base exception for backend failures |

---

## 5. Data Structures

### 5.1 StorageBackend Abstract Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from .models import Thread, ThreadMessage, Memory, SpilledContentReference

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
            ValidationError: If thread structure invalid
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
            ValidationError: If message structure invalid
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
            ValidationError: If memory structure invalid
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
```

### 5.2 Backend Error Types

```python
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
```

---

## 6. Interface Contracts

### 6.1 FileBackend Implementation

**Storage structure:**

```
.context_harness/
  threads/
    {thread_id}.json           # Thread metadata
    {thread_id}/
      messages.jsonl           # Message history (append-efficient)
  memories/
    {memory_id}.json           # Individual memories
    index.json                 # Searchable metadata index
  spilled/
    {spill_id}.jsonl           # Large content files
    metadata.json              # Spill metadata registry
```

**Implementation signature:**

```python
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

    def get_thread(self, config: Dict[str, Any]) -> Optional[Thread]:
        """
        Implementation: Read threads/{thread_id}.json.
        
        Cache hit: Return cached Thread.
        Cache miss: Read JSON, deserialize, cache, return.
        """
        thread_id = config.get("thread_id")
        if not thread_id:
            raise BackendConfigurationError("thread_id required in config")

        # File path: threads/{thread_id}.json
        # Deserialize JSON → Thread object
        # Cache if enabled
        # Return Thread or None if file doesn't exist

    def put_thread(self, config: Dict[str, Any], thread: Thread) -> None:
        """
        Implementation: Write threads/{thread_id}.json.
        
        Serialize Thread → JSON.
        Write to file.
        Update cache.
        """
        thread_id = config.get("thread_id")
        # Serialize Thread → JSON
        # Write to threads/{thread_id}.json
        # Update cache if enabled

    def append_message(self, config: Dict[str, Any], message: ThreadMessage) -> None:
        """
        Implementation: Append to threads/{thread_id}/messages.jsonl.
        
        Serialize ThreadMessage → JSON line.
        Append to JSONL file (no full rewrite).
        Update thread metadata (message_count, updated_at).
        """
        thread_id = config.get("thread_id")
        # Serialize message → JSON line
        # Append to threads/{thread_id}/messages.jsonl
        # Update threads/{thread_id}.json metadata

    def get_messages(
        self,
        config: Dict[str, Any],
        limit: Optional[int] = None,
        before_timestamp: Optional[float] = None
    ) -> List[ThreadMessage]:
        """
        Implementation: Read threads/{thread_id}/messages.jsonl.
        
        Stream JSONL lines.
        Deserialize each → ThreadMessage.
        Apply filters (limit, timestamp).
        Return list.
        """
        # Stream messages.jsonl
        # Deserialize each line
        # Filter by timestamp if provided
        # Apply limit if provided
        # Return list

    def put_memory(self, memory: Memory, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Implementation: Write memories/{memory_id}.json and update index.
        
        Serialize Memory → JSON.
        Write to file.
        Update memories/index.json (searchable metadata).
        """
        # Serialize memory → JSON
        # Write to memories/{memory.memory_id}.json
        # Update index: thread_id, memory_type, relevance_score, timestamp

    def search_memories(
        self,
        query: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Implementation: Query memories/index.json, load matching memories.
        
        Read index.json.
        Filter by config (thread_id, user_id), memory_type.
        Keyword search if query provided (simple matching).
        Rank by relevance_score.
        Load Memory objects from files.
        Return list.
        """
        # Query index.json
        # Apply filters
        # Keyword search on content/metadata (future: semantic search)
        # Rank by relevance_score
        # Load matching memories
        # Return list

    def spill_content(
        self,
        content: Any,
        spill_metadata: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> SpilledContentReference:
        """
        Implementation: Write spilled/{spill_id}.jsonl, update metadata.
        
        Generate spill_id.
        Serialize content → JSONL.
        Write to file.
        Create SpilledContentReference.
        Update spilled/metadata.json registry.
        Return reference.
        """
        # Generate spill_id
        # Write content to spilled/{spill_id}.jsonl
        # Create SpilledContentReference
        # Update metadata registry
        # Return reference
```

| Method | File Path | Format | Behavior |
|--------|-----------|--------|----------|
| get_thread | threads/{thread_id}.json | JSON | Read, deserialize, cache |
| put_thread | threads/{thread_id}.json | JSON | Serialize, write, cache |
| append_message | threads/{thread_id}/messages.jsonl | JSONL | Append line, no rewrite |
| get_messages | threads/{thread_id}/messages.jsonl | JSONL | Stream, filter, deserialize |
| put_memory | memories/{memory_id}.json + index.json | JSON | Write memory + update index |
| search_memories | memories/index.json + {memory_id}.json | JSON | Query index, load matching |
| spill_content | spilled/{spill_id}.jsonl + metadata.json | JSONL | Write content + update registry |

---

## 7. Implementation Patterns

### 7.1 Config Routing Pattern

```python
# Config dict provides routing information
config = {"thread_id": "thread_abc", "user_id": "user_123"}

# Backend extracts thread_id for routing
thread_id = config["thread_id"]

# Additional filters optional
user_id = config.get("user_id")  # Optional filter
```

**Pattern contract:**
- config MUST contain thread_id for thread/message operations
- Additional fields (user_id, date_range) are optional filters
- Backend validates required fields, raises BackendConfigurationError if missing

### 7.2 JSONL Append Pattern

```python
import json

# Append message to thread history
def append_message(self, config: Dict[str, Any], message: ThreadMessage) -> None:
    thread_id = config["thread_id"]
    file_path = f"threads/{thread_id}/messages.jsonl"

    # Serialize message to JSON line
    message_json = json.dumps({
        "message_id": message.message_id,
        "thread_id": message.thread_id,
        "timestamp": message.timestamp,
        "is_spilled": message.is_spilled,
        "spill_reference": message.spill_reference,
        "metadata": message.metadata,
        "content": message.content if isinstance(message.content, str) else message.content.dict()
    })

    # Append line (efficient, no rewrite)
    with open(file_path, "a") as f:
        f.write(message_json + "\n")

    # Update thread metadata
    thread = self.get_thread(config)
    thread.metadata["message_count"] += 1
    self.put_thread(config, thread)
```

### 7.3 Memory Indexing Pattern

```python
# Index structure for fast search
# memories/index.json
{
    "memories": [
        {
            "memory_id": "mem_abc",
            "thread_id": "thread_123",
            "memory_type": "summary",
            "relevance_score": 0.85,
            "timestamp": 1640000000,
            "content_preview": "User prefers concise responses..."
        },
        ...
    ]
}

# Search implementation
def search_memories(self, query: str, config: Dict, limit: int) -> List[Memory]:
    # Read index
    index = self._read_index()

    # Filter
    candidates = index["memories"]
    if config.get("thread_id"):
        candidates = [m for m in candidates if m["thread_id"] == config["thread_id"]]
    if memory_type:
        candidates = [m for m in candidates if m["memory_type"] == memory_type]

    # Keyword search (simple matching)
    if query:
        candidates = [m for m in candidates if query.lower() in m["content_preview"].lower()]

    # Rank by relevance
    candidates.sort(key=lambda m: m["relevance_score"], reverse=True)

    # Limit
    candidates = candidates[:limit]

    # Load full Memory objects
    memories = [self.get_memory(m["memory_id"]) for m in candidates]

    return memories
```

### 7.4 Caching Pattern

```python
from functools import lru_cache
import time

class FileBackend(StorageBackend):
    def __init__(self, cache_ttl: int = 300):
        self.cache = {}  # {key: (value, timestamp)}
        self.cache_ttl = cache_ttl

    def _cache_get(self, key: str) -> Optional[Any]:
        """Get from cache if not expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return value
            else:
                # Expired, remove
                del self.cache[key]
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        """Set cache with current timestamp."""
        self.cache[key] = (value, time.time())

    def get_thread(self, config: Dict[str, Any]) -> Optional[Thread]:
        thread_id = config["thread_id"]
        cache_key = f"thread:{thread_id}"

        # Check cache
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        # Read from file
        thread = self._read_thread_file(thread_id)

        # Cache if exists
        if thread:
            self._cache_set(cache_key, thread)

        return thread
```

---

## 8. Examples

### 8.1 Basic Backend Usage

```python
backend = FileBackend(base_path=".context_harness")

# Create thread
thread = Thread(thread_id="thread_abc", metadata={"user_id": "user1"})
backend.put_thread({"thread_id": "thread_abc"}, thread)

# Add messages
msg1 = ThreadMessage.create_from_langchain("thread_abc", HumanMessage("Hello"))
backend.append_message({"thread_id": "thread_abc"}, msg1)

msg2 = ThreadMessage.create_from_langchain("thread_abc", AIMessage("Hi! How can I help?"))
backend.append_message({"thread_id": "thread_abc"}, msg2)

# Retrieve thread
thread = backend.get_thread({"thread_id": "thread_abc"})
print(thread.metadata["message_count"])  # 2

# Get messages
messages = backend.get_messages({"thread_id": "thread_abc"}, limit=10)
print(len(messages))  # 2
```

### 8.2 Memory Storage and Search

```python
# Create memory
memory = Memory(
    memory_type=MemoryType.SUMMARY,
    content="User discussed pricing tiers",
    thread_id="thread_abc",
    related_message_ids=["msg_1", "msg_2"],
    relevance_score=0.9
)

backend.put_memory(memory)

# Search memories
results = backend.search_memories(
    query="pricing",
    config={"thread_id": "thread_abc"},
    limit=5
)

print(len(results))  # 1
print(results[0].content)  # "User discussed pricing tiers"
```

### 8.3 Content Spilling

```python
# Spill large content
large_content = "API response with 50000 records..."
spill_ref = backend.spill_content(
    content=large_content,
    spill_metadata={
        "content_type": "tool_response",
        "preview": "API returned 50000 records...",
        "size": len(large_content)
    }
)

print(spill_ref.spill_id)  # UUID
print(spill_ref.content_location)  # "spilled/{spill_id}.jsonl"

# Retrieve spilled content
retrieved = backend.retrieve_spilled_content(spill_ref.spill_id)
print(retrieved == large_content)  # True
```

---

## 9. Relationship to Other RFCs

This implementation interface depends on:

* **[RFC-001-world-view](RFC-001-world-view.md)**: Backend abstraction invariant - backend abstracts persistence, core never accesses storage format.

* **[RFC-002-core-architecture](RFC-002-core-architecture.md)**: Data layer structure - backend resides in Data layer, depends on nothing upward.

* **[RFC-003-domain-models](RFC-003-domain-models.md)**: Domain model types - backend operations use Thread, ThreadMessage, Memory, SpilledContentReference as parameters and return types.

Enables:

* **[RFC-005-facade-interface](RFC-005-facade-interface.md)**: Facade injects backend into core components. Backend provides persistence for facade operations.

---

## 10. Open Questions

1. **JSONL line size limit:** If a single message or spilled content is extremely large (multi-MB), should JSONL split into multiple lines or use alternative storage (binary files)? JSONL line splitting breaks streaming semantics.

2. **Index update frequency:** Should memory index.json update on every put_memory (immediate) or periodically (batch)? Immediate ensures fresh search; batch reduces write overhead.

3. **Cache invalidation strategy:** When thread is updated via put_thread, should cache invalidate immediately or rely on TTL expiration? Immediate invalidation prevents stale reads; TTL reduces cache churn.

4. **Config validation scope:** Should backend validate all optional config fields (user_id, date_range) or only required thread_id? Full validation prevents invalid filters; minimal validation reduces coupling.

5. **Spilled content garbage collection:** Should backend automatically delete spilled content when referencing message deleted, or require manual cleanup? Automatic GC prevents orphaned files; manual gives user control.

---

## 11. Conclusion

This RFC defines the StorageBackend abstract interface with config-based routing (checkpointer pattern) and FileBackend default implementation using JSON/JSONL storage. The interface provides consistent methods for thread, message, memory, and spilled content operations with clear error handling. FileBackend implements efficient message append (JSONL), searchable memory indexing, and optional caching.

Backend abstraction isolates persistence from core logic, enabling pluggable implementations (FileBackend, SQLiteBackend, VectorBackend) without refactoring components. Config-based routing provides flexible filtering compatible with LangGraph patterns. FileBackend's zero-dependency JSON/JSONL approach works for local/prototyping contexts while maintaining searchability and efficiency.

> **Abstraction principle:** Backend defines the persistence contract—config routing, domain model parameters, error handling—enabling pluggable implementations without affecting core layer.