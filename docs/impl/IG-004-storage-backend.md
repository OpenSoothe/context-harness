# IG-004: Storage Backend Implementation Guide

**Target RFC**: RFC-004-storage-backend
**Module**: context_harness/backend
**Language**: Python 3.8+
**Created**: 2026-04-21
**Status**: Complete

---

## 1. Overview

Implement StorageBackend abstract interface and FileBackend default implementation with JSON/JSONL storage, config-based routing, caching, and memory indexing. This backend provides persistence layer for all domain models.

---

## 2. Module Structure

```
context_harness/
  backend/
    __init__.py              # Export all backend types
    base.py                  # StorageBackend ABC, error types
    file_backend.py          # FileBackend implementation
    serialization.py         # JSON/JSONL serialization utilities
    cache.py                 # Simple TTL cache implementation
```

---

## 3. Implementation Details

### 3.1 base.py - Abstract Interface and Errors

**Implement:**
- `StorageBackend` ABC with all abstract methods
- `BackendError` base exception
- `ThreadNotFoundError`, `MemoryNotFoundError`, `SpillContentNotFoundError`
- `BackendConfigurationError`

**Abstract methods (13 total):**
- Thread: `get_thread`, `put_thread`, `list_threads`
- Message: `append_message`, `get_messages`
- Memory: `put_memory`, `get_memory`, `search_memories`
- Spill: `spill_content`, `retrieve_spilled_content`, `delete_spilled_content`

**Implementation notes:**
- All methods use `config: Dict[str, Any]` for routing
- Import domain models from context_harness.models
- Clear docstrings for each abstract method
- Use `@abstractmethod` decorator

### 3.2 file_backend.py - FileBackend Implementation

**Storage structure:**
```
.base_path/
  threads/
    {thread_id}.json
    {thread_id}/
      messages.jsonl
  memories/
    {memory_id}.json
    index.json
  spilled/
    {spill_id}.jsonl
    metadata.json
```

**Implement:**
- `FileBackend.__init__(base_path, cache_ttl, cache_enabled)`
- Initialize directory structure
- Create cache instance if enabled
- Implement all 13 abstract methods

**Key implementation patterns:**

**JSON serialization:**
- Use `dataclasses.asdict()` to convert domain objects
- Custom JSON encoder for LangChain BaseMessage types
- Deserialize: reconstruct domain objects from dict + imports

**JSONL append:**
- Serialize message to JSON line
- Append with newline (no full rewrite)
- Update thread metadata file

**Cache pattern:**
- Simple dict-based cache: `{key: (value, timestamp)}`
- Check TTL before returning cached value
- Update cache on writes

**Memory indexing:**
- `index.json`: List of memory metadata (thread_id, memory_type, relevance_score, timestamp)
- Update index on put_memory
- Query index for search_memories, load matching memory files

### 3.3 serialization.py - Serialization Utilities

**Implement:**
- `serialize_thread(thread) → dict`
- `deserialize_thread(data: dict) → Thread`
- `serialize_message(message) → dict`
- `deserialize_message(data: dict) → ThreadMessage`
- `serialize_memory(memory) → dict`
- `deserialize_memory(data: dict) → Memory`
- `serialize_spill_reference(ref) → dict`
- `deserialize_spill_reference(data: dict) → SpilledContentReference`

**LangChain message serialization:**
- Serialize: `{"type": msg.__class__.__name__, "content": msg.content, ...}`
- Deserialize: Reconstruct correct message type (HumanMessage, AIMessage, etc.)
- Import from `langchain_core.messages`

**Implementation notes:**
- Handle Union types (str | BaseMessage) for ThreadMessage.content
- Preserve all metadata fields
- Error handling for invalid data

### 3.4 cache.py - Simple TTL Cache

**Implement:**
- `SimpleCache.__init__(ttl_seconds)`
- `get(key) → Optional[value]`
- `set(key, value)`
- `delete(key)`
- `_is_expired(timestamp) → bool`

**Implementation:**
- Dict structure: `{key: (value, creation_timestamp)}`
- Check expiration on get
- No automatic cleanup (lazy expiration check)

---

## 4. Testing Strategy

### 4.1 Unit Tests

**test_base.py:**
- Test all error types
- Test StorageBackend is abstract (cannot instantiate)
- Test subclass without implementing all methods raises TypeError

**test_file_backend_init.py:**
- Test initialization creates directory structure
- Test invalid base_path raises BackendConfigurationError
- Test cache initialization

**test_file_backend_threads.py:**
- Test put_thread and get_thread
- Test get_thread returns None for nonexistent thread
- Test cache behavior (get cached vs read file)
- Test list_threads with filters

**test_file_backend_messages.py:**
- Test append_message creates messages.jsonl
- Test get_messages retrieves all messages
- Test get_messages with limit
- Test get_messages with timestamp filter
- Test multiple appends (efficient, no rewrite)

**test_file_backend_memories.py:**
- Test put_memory writes file and updates index
- Test get_memory retrieves memory
- Test search_memories with filters
- Test search_memories with query (keyword matching)
- Test search_memories ranking by relevance_score

**test_file_backend_spill.py:**
- Test spill_content creates file and returns reference
- Test retrieve_spilled_content returns original content
- Test delete_spilled_content removes file
- Test retrieve_spilled_content returns None after delete

### 4.2 Integration Tests

**test_file_backend_full_workflow.py:**
- Test create thread → add messages → retrieve messages
- Test create memories → search memories → retrieve specific memory
- Test spill content → retrieve → delete
- Test cache behavior across operations
- Test index updates on memory operations

### 4.3 Edge Cases

**test_edge_cases.py:**
- Test empty messages.jsonl (no messages)
- Test empty memories/index.json (no memories)
- Test large message content spill
- Test thread_id not in config raises BackendConfigurationError
- Test malformed JSON files (error handling)
- Test cache expiration (TTL)
- Test disable cache (cache_enabled=False)

---

## 5. Implementation Checklist

### Phase 1: Core Infrastructure
1. ✓ Create context_harness/backend/ directory
2. ✓ Implement base.py (StorageBackend ABC + errors)
3. ✓ Implement serialization.py (domain model serialization)
4. ✓ Implement cache.py (Simple TTL cache)

### Phase 2: FileBackend
5. ✓ Implement file_backend.py initialization
6. ✓ Implement thread operations (get_thread, put_thread, list_threads)
7. ✓ Implement message operations (append_message, get_messages)
8. ✓ Implement memory operations (put_memory, get_memory, search_memories)
9. ✓ Implement spill operations (spill_content, retrieve_spilled_content, delete_spilled_content)

### Phase 3: Testing
10. ✓ Create tests/test_backend/ directory
11. ✓ Implement unit tests for each component
12. ✓ Implement integration tests
13. ✓ Run tests with pytest
14. ✓ Fix any test failures

### Phase 4: Documentation
15. ✓ Add docstrings to all classes and methods
16. ✓ Add type hints for all parameters
17. ✓ Add usage examples in docstrings

---

## 6. Coding Plan

**Step 1: Set up module structure**
- Create backend/__init__.py
- Create empty module files

**Step 2: Implement base.py**
- Define StorageBackend ABC with all abstract methods
- Define error types

**Step 3: Implement serialization.py**
- Serialization utilities for all domain models
- Handle LangChain message types

**Step 4: Implement cache.py**
- Simple TTL cache implementation

**Step 5: Implement file_backend.py**
- Directory structure initialization
- Thread operations with JSON storage
- Message operations with JSONL storage
- Memory operations with indexing
- Spill operations with metadata registry
- Cache integration

**Step 6: Create tests**
- Unit tests for each operation
- Integration tests for workflows
- Edge case tests

**Step 7: Update __init__.py exports**
- Export StorageBackend, FileBackend, errors

---

## 7. Edge Cases and Special Handling

**LangChain message serialization:**
- Store message type as string ("HumanMessage", "AIMessage", etc.)
- Reconstruct using message class from langchain_core.messages
- Preserve all message fields (content, additional_kwargs)

**ThreadMessage.content Union type:**
- If str (insertion syntax): serialize as string
- If BaseMessage: serialize message dict with type field
- Deserialize: check type field to determine reconstruction

**Empty storage files:**
- messages.jsonl can be empty (no messages)
- index.json starts as empty list
- metadata.json starts as empty dict

**Cache invalidation:**
- Update cache on put_thread, put_memory
- No automatic invalidation on append_message (thread file unchanged)
- Lazy expiration check on get operations

**Config validation:**
- thread_id required for thread/message operations
- Raise BackendConfigurationError if missing

---

## 8. Performance Considerations

**JSONL append efficiency:**
- Append single line (no full file rewrite)
- Efficient for high-frequency message addition

**Cache TTL:**
- Default 300 seconds (5 minutes)
- Reduces file reads for frequently accessed threads/memories
- User can disable cache for always-fresh data

**Memory indexing:**
- index.json stores lightweight metadata
- Avoid loading all memory files for search
- Load only matching memory files

**File I/O:**
- Use pathlib for path operations
- Atomic writes where possible (write to temp, then move)
- Handle concurrent access (basic file locking not implemented, future work)

---

## 9. Usage Examples

**Initialize FileBackend:**
```python
from context_harness.backend import FileBackend

backend = FileBackend(base_path=".context_harness")
```

**Thread operations:**
```python
from context_harness.models import Thread

thread = Thread(metadata={"user_id": "user123"})
backend.put_thread({"thread_id": thread.thread_id}, thread)

retrieved = backend.get_thread({"thread_id": thread.thread_id})
threads = backend.list_threads({"user_id": "user123"})
```

**Message operations:**
```python
from langchain_core.messages import HumanMessage
from context_harness.models import ThreadMessage

msg = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Hello"))
backend.append_message({"thread_id": thread.thread_id}, msg)

messages = backend.get_messages({"thread_id": thread.thread_id}, limit=10)
```

**Memory operations:**
```python
from context_harness.models import Memory, MemoryType

memory = Memory(
    memory_type=MemoryType.SUMMARY,
    content="User discussed pricing",
    thread_id=thread.thread_id,
    related_message_ids=[msg.message_id]
)
backend.put_memory(memory)

found = backend.get_memory(memory.memory_id)
results = backend.search_memories(query="pricing", config={"thread_id": thread.thread_id})
```

**Spill operations:**
```python
spill_ref = backend.spill_content(
    content="Large content...",
    spill_metadata={"content_type": "tool_response", "size": 50000}
)

retrieved_content = backend.retrieve_spilled_content(spill_ref.spill_id)
backend.delete_spilled_content(spill_ref.spill_id)
```

---

## 10. Success Criteria

- StorageBackend ABC defines all abstract methods
- FileBackend implements all 13 operations
- JSON/JSONL storage works correctly
- Cache reduces redundant file reads
- Memory indexing enables efficient search
- All unit tests pass
- Integration tests cover full workflows
- Type hints complete
- Docstrings comprehensive
- No dependencies beyond standard library + langchain-core

---

## 11. Notes

**No external dependencies:**
- Uses pathlib, json, dataclasses (standard library)
- langchain-core for message types
- No database libraries, no file locking libraries

**Thread-safe access:**
- Not implemented (future work)
- Basic file operations may have race conditions
- Single-threaded usage recommended for now

**Directory creation:**
- Create directories lazily (on first write)
- threads/, memories/, spilled/ created as needed
- No pre-initialization required

**File naming:**
- Use thread_id, memory_id, spill_id directly as filenames
- No sanitization (assuming valid UUIDs)
- Future: sanitize for security if user-provided IDs