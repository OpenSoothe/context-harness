# Context Harness Architecture Design

**Status:** Draft
**Created:** 2026-04-21
**Last Updated:** 2026-04-21
**Authors:** Xiaming Chen

---

## 1. Abstract

This document defines the architecture for `context-harness`, a standalone Python library for managing conversational context in AI applications and agents. The library provides comprehensive context management including chat thread history, cross-thread memory, experience distillation, intelligent context construction, and message spilling for large content. Designed with LangChain compatibility and extensibility in mind, it uses a layered architecture with a simple facade API while enabling deep customization through modular components.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This design defines:

* Overall three-layer architecture (Interface, Core, Data)
* Domain models for threads, messages, memories, and spilled content
* Storage backend abstraction with file-based default implementation
* Four core components and their interfaces
* Facade API with configurable automation
* Data flows between layers and components
* Message spilling mechanism with extensible insertion syntax
* LangChain message type integration strategy

### 2.2 Non-Goals

This design does **not** define:

* Concrete implementation algorithms or internal data structures (see Implementation Interface Design specs)
* Additional storage backend implementations beyond FileBackend (SQLite, Vector DB - future work)
* LLM integration specifics for intelligent distillation (implementation detail)
* Deployment, packaging, or distribution mechanisms
* Testing strategies or performance benchmarks

---

## 3. Background & Motivation

**Problem:** AI application developers and agent builders need sophisticated context management beyond simple chat history. Current solutions either provide basic thread storage (insufficient for agents with tool interactions) or require complex framework adoption (overkill for focused use cases).

**Challenges:**
- Large tool responses or AI outputs exceed token limits and need spilling mechanisms
- Conversations contain reusable experiences (user preferences, effective patterns) that should be extracted and reused
- Memories need to be searchable across threads, not just within single conversations
- Context construction for new queries requires intelligent selection (not just "last N messages")
- Developers need LangChain compatibility but may want framework-agnostic future support

**Solution:** A standalone library that provides comprehensive context management with:
- Thread-based conversation history with automatic spill handling
- Experience distillation (summaries + pattern extraction)
- Cross-thread memory with semantic search
- Intelligent context construction with templating
- LangChain compatibility with extensible architecture

---

## 4. Design Principles

1. **Layered separation:** Interface (facade) orchestrates Core (business logic) which depends on Data (persistence). Each layer has single responsibility.

2. **LangChain compatibility first:** Use LangChain message types directly. Keep message module extensible for future framework-agnostic support through abstraction.

3. **Configurable automation:** Default behavior is minimal automation. Users enable/disable auto-spill, auto-distill, and other triggers as needed.

4. **Component independence:** Core components (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder) never call each other directly. Facade orchestrates interactions.

5. **Extensible insertion syntax:** Generic marker format `[[MARKER:type|metadata|reference]]` supports message spilling and future scenarios (generated data, external resources).

6. **Backend abstraction:** StorageBackend interface isolates persistence. FileBackend is default, additional backends pluggable without core logic changes.

7. **Memory traceability:** Memories explicitly link to source message IDs. Enables relevance scoring and audit trails.

---

## 5. Overall Architecture

### 5.1 Three-Layer Structure

```
┌─────────────────────────────────────────┐
│  Interface Layer (Facade)               │
│  - ContextHarness                       │
│  - Configurable automation              │
│  - Simple API for common use cases      │
│  - LangChain message integration        │
└─────────────────────────────────────────┘
              ↓ orchestrates
┌─────────────────────────────────────────┐
│  Core Layer (Domain Components)         │
│  - ChatHistoryManager                   │
│  - MemoryManager                        │
│  - ExperienceDistiller                  │
│  - ContextBuilder                       │
│  - Clear interfaces between each        │
│  - Business logic implementation        │
└─────────────────────────────────────────┘
              ↓ depends on
┌─────────────────────────────────────────┐
│  Data Layer (Storage Backends)          │
│  - StorageBackend interface (abstract)  │
│  - FileBackend (default implementation) │
│  - Config-based thread routing          │
│  - Memory indexing for search           │
│  - Spilled content storage              │
└─────────────────────────────────────────┘
```

### 5.2 Layer Responsibilities

**Interface Layer:**
- Provides simple facade API for users
- Orchestrates core components
- Handles LangChain message wrapping/unwrapping
- Implements configurable automation triggers
- Exposes component access for advanced customization

**Core Layer:**
- Implements domain logic for each capability
- Operates on domain models (Thread, Memory, ThreadMessage)
- Never calls other components (orchestrated by facade)
- Calls backend through abstract interface

**Data Layer:**
- Abstracts all persistence operations
- Provides consistent StorageBackend interface
- FileBackend implementation as default
- Thread-based storage with config routing
- Message append using JSONL format
- Memory indexing for searchability
- Spilled content offloading and retrieval

---

## 6. Domain Models

### 6.1 ThreadMessage (LangChain Wrapper)

**Purpose:** Wrap LangChain messages with harness metadata while preserving compatibility.

```python
class ThreadMessage:
    message_id: str              # Unique identifier
    thread_id: str               # Parent thread
    timestamp: float             # Creation time
    is_spilled: bool             # Content offloaded flag
    spill_reference: Optional[SpilledContentReference]  # When is_spilled=True
    metadata: Dict[str, Any]     # Custom fields (token_count, model, etc.)
    content: Union[str, BaseMessage]  # Actual content OR insertion marker
```

**Content behavior:**
- When `is_spilled=False`: Contains LangChain message (HumanMessage, AIMessage, ToolMessage, etc.)
- When `is_spilled=True`: Contains insertion syntax marker string

**LangChain integration:**
- Input: Accepts LangChain `BaseMessage` types
- Wraps in ThreadMessage with metadata
- Output: Can unwrap to LangChain messages via facade methods

### 6.2 SpilledContentReference

**Purpose:** Metadata for offloaded large content with retrieval information.

```python
class SpilledContentReference:
    spill_id: str                # Unique identifier
    spill_type: SpillType        # Enum: MESSAGE_SPILL, GENERATED_DATA, FUTURE_TYPE
    content_location: str        # File path or storage reference
    content_size: int            # Original size (bytes/tokens)
    content_type: str            # Category: tool_response, ai_report, generated_dataset
    content_preview: str         # Short summary (optional, helps LLM decide)
    retrieval_hint: str          # How to retrieve: "use fetch_spilled_content tool"
    metadata: Dict[str, Any]     # Spill-specific additional info
```

### 6.3 Insertion Syntax (Extensible Marker System)

**Purpose:** Generic syntax for marking spilled/generated content in message text, enabling LLM detection and tool-based retrieval.

**Format:** `[[MARKER:type|metadata_json|reference]]`

**Examples:**

Message spill:
```
[[SPILL:MESSAGE_SPILL|{"content_type":"tool_response","preview":"API returned 500 results...","size":"12KB"}|spill_id=abc123]]
```

Generated data (future):
```
[[INSERT:GENERATED_DATA|{"data_type":"analytics_report","generated_at":"2026-04-21"}|file=data123.json]]
```

**Design principles:**
- Double-bracket `[[...]]` makes parsing easy and unambiguous
- Structured format: `MARKER:type | metadata_json | reference`
- Extensible: New marker types added without breaking existing syntax
- LLM-friendly: Clear structure that models can understand and act on

### 6.4 Memory

**Purpose:** Stored experiences, summaries, or facts with explicit message linkage.

```python
class Memory:
    memory_id: str               # Unique identifier
    memory_type: MemoryType      # Enum: summary, experience_pattern, user_preference, fact
    content: str                 # Memory content
    thread_id: str               # Source thread
    related_message_ids: List[str]  # Explicit links to source messages (traceability)
    relevance_score: float       # Computed relevance metric
    metadata: Dict[str, Any]     # Timestamps, tags, access_count
```

**Key enhancement:** `related_message_ids` enables:
- Traceability back to original conversation
- Relevance scoring based on message context
- Audit trails for memory evolution

### 6.5 Thread

**Purpose:** Represents a conversation thread with metadata.

```python
class Thread:
    thread_id: str               # Unique identifier
    messages: List[ThreadMessage]  # Message history (not always loaded)
    metadata: Dict[str, Any]     # User_id, session_start, status, etc.
```

### 6.6 ContextConfig

**Purpose:** Configuration for context construction behavior.

```python
class ContextConfig:
    max_tokens: int              # Token budget
    sections: List[str]          # Ordered sections: recent_history, relevant_memories, experiences, system_prompt
    retrieval_strategy: RetrievalStrategy  # Enum: recent_first, semantic_similarity, hybrid
    template_format: Dict[str, str]  # Formatting rules for each section
```

### 6.7 AutomationConfig

**Purpose:** Configurable automation triggers for component interactions.

```python
class AutomationConfig:
    auto_spill_messages: bool = True
    spill_threshold_bytes: int = 10000  # 10KB threshold
    
    auto_distill: bool = False   # Default: manual distillation
    distill_trigger: str = 'message_count'  # Options: message_count, session_end, manual
    distill_threshold: int = 10  # Every N messages
    
    auto_store_memories: bool = True  # Auto-store distilled results
    auto_link_memories: bool = True   # Link memories to source messages
```

---

## 7. Data Layer: Storage Backend Interface

### 7.1 Abstract StorageBackend

**Purpose:** Define consistent persistence interface inspired by LangChain checkpointer pattern.

```python
class StorageBackend(ABC):
    """Abstract storage backend with config-based thread routing."""
    
    # Thread operations (checkpoint-style)
    @abstractmethod
    def get_thread(self, config: Dict[str, Any]) -> Optional[Thread]
    """Retrieve thread by config (contains thread_id and optional filters)."""
    
    @abstractmethod
    def put_thread(self, config: Dict[str, Any], thread: Thread) -> None
    """Save/update thread state."""
    
    @abstractmethod
    def list_threads(self, config: Optional[Dict[str, Any]] = None) -> List[Dict]
    """List thread metadata with optional filters."""
    
    # Message operations (append-style)
    @abstractmethod
    def append_message(self, config: Dict[str, Any], message: ThreadMessage) -> None
    """Append message to thread (efficient, no full rewrite)."""
    
    @abstractmethod
    def get_messages(
        self,
        config: Dict[str, Any],
        limit: Optional[int] = None,
        before_timestamp: Optional[float] = None
    ) -> List[ThreadMessage]
    """Retrieve messages with pagination/filtering."""
    
    # Memory operations (cross-thread searchable)
    @abstractmethod
    def put_memory(self, memory: Memory, config: Optional[Dict[str, Any]] = None) -> None
    """Store memory (thread-linked or cross-thread)."""
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Memory]
    """Retrieve specific memory."""
    
    @abstractmethod
    def search_memories(
        self,
        query: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]
    """Search memories with semantic query and filters."""
    
    # Spilled content operations
    @abstractmethod
    def spill_content(
        self,
        content: Any,
        spill_metadata: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> SpilledContentReference
    """Offload large content, return reference."""
    
    @abstractmethod
    def retrieve_spilled_content(self, spill_id: str) -> Optional[Any]
    """Retrieve spilled content by ID."""
    
    @abstractmethod
    def delete_spilled_content(self, spill_id: str) -> None
    """Delete spilled content."""
```

**Key design decisions:**
- **Config-based pattern:** Uses `config` dict (like LangChain checkpointer) for flexible routing and filtering
- **Append-style messages:** Efficient JSONL append for message history (no thread file rewrite)
- **Search-first memory:** Memory operations emphasize searchability
- **Separation:** Thread state, message history, memories, and spilled content are distinct operations

### 7.2 FileBackend Implementation

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

**Key features:**
- JSON for threads, memories, metadata (human-readable, easy debugging)
- JSONL for messages and large content (efficient append, streaming support)
- In-memory cache for frequently accessed data (configurable TTL)
- Index files for fast searching without loading full content
- Config-based routing: `{"thread_id": "abc"}` → `threads/abc.json`

---

## 8. Core Layer: Domain Components

### 8.1 ChatHistoryManager

**Responsibility:** Manages conversation thread lifecycle and message history with automatic spill detection.

**Key methods:**
```python
class ChatHistoryManager:
    def __init__(self, backend: StorageBackend)
    
    def create_thread(self, config: Optional[Dict] = None) -> Thread
    """Create new thread, return Thread object with generated thread_id."""
    
    def add_message(self, thread_id: str, message: ThreadMessage) -> None
    """Add message to thread with auto-spill check for large content."""
    
    def get_thread(self, thread_id: str) -> Optional[Thread]
    """Load full thread state."""
    
    def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        include_spilled_markers: bool = True
    ) -> List[ThreadMessage]
    """Retrieve messages, optionally replace spilled content with markers."""
    
    def check_spill_needed(self, message: ThreadMessage) -> bool
    """Check if message exceeds spill threshold."""
    
    def spill_message_content(self, message: ThreadMessage) -> ThreadMessage
    """Spill large content, return message with insertion syntax marker."""
```

**LangChain integration:**
- Input: Accepts LangChain `BaseMessage` types (HumanMessage, AIMessage, ToolMessage)
- Wraps in `ThreadMessage` with harness metadata
- Output: Can unwrap to LangChain messages via facade

### 8.2 ExperienceDistiller

**Responsibility:** Extract summaries and reusable experience patterns from conversation threads.

**Key methods:**
```python
class ExperienceDistiller:
    def __init__(
        self,
        backend: StorageBackend,
        llm_client: Optional[BaseLLM] = None  # Optional LLM for intelligent distillation
    )
    
    def distill_thread(self, thread_id: str) -> List[Memory]
    """Distill a thread into summaries and experience patterns."""
    
    def distill_messages(self, messages: List[ThreadMessage]) -> List[Memory]
    """Distill raw message list (doesn't require thread load)."""
    
    def extract_summary(self, messages: List[ThreadMessage]) -> Memory
    """Create conversation summary."""
    
    def extract_patterns(self, messages: List[ThreadMessage]) -> List[Memory]
    """Extract reusable experience patterns (preferences, effective responses)."""
    
    def link_memory_to_messages(self, memory: Memory, message_ids: List[str]) -> Memory
    """Connect memory to source messages for traceability."""
```

**Distillation strategies:**
- **Default (LLM-free):** Simple heuristics (last N messages as summary, keyword extraction for patterns)
- **LLM-powered:** Use language model for intelligent summarization and pattern extraction
- **Configurable:** Users provide custom distillation strategies

### 8.3 MemoryManager

**Responsibility:** Store, retrieve, and search memories across threads.

**Key methods:**
```python
class MemoryManager:
    def __init__(self, backend: StorageBackend)
    
    def store_memory(self, memory: Memory) -> None
    """Save memory to backend."""
    
    def retrieve_memory(self, memory_id: str) -> Optional[Memory]
    """Get specific memory."""
    
    def search_memories(
        self,
        query: Optional[str] = None,
        thread_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Memory]
    """Search memories with semantic query and filters."""
    
    def get_thread_memories(self, thread_id: str) -> List[Memory]
    """Get all memories linked to a thread."""
    
    def update_memory_access(self, memory_id: str) -> None
    """Increment access count for relevance scoring."""
```

**Search capabilities:**
- Keyword-based search (default FileBackend)
- Semantic search (future: vector backend integration)
- Filter by thread_id, memory_type, date_range, tags

### 8.4 ContextBuilder

**Responsibility:** Construct context for new queries by intelligently selecting and formatting history + memories.

**Key methods:**
```python
class ContextBuilder:
    def __init__(
        self,
        backend: StorageBackend,
        config: ContextConfig
    )
    
    def build_context(
        self,
        query: str,
        thread_id: Optional[str] = None,
        config: Optional[ContextConfig] = None
    ) -> str
    """Build full context string for new query."""
    
    def select_messages(
        self,
        query: str,
        thread_id: str,
        strategy: RetrievalStrategy
    ) -> List[ThreadMessage]
    """Select relevant messages from thread."""
    
    def select_memories(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> List[Memory]
    """Select relevant memories."""
    
    def format_context(
        self,
        messages: List[ThreadMessage],
        memories: List[Memory],
        template: ContextConfig
    ) -> str
    """Format selected items into context string using template."""
```

**Retrieval strategies:**
- **Recent-first:** Last N messages + recent memories
- **Semantic similarity:** Rank by relevance to query (requires vector backend or keyword scoring)
- **Hybrid:** Combine recency + relevance scoring

**Template format:**
- Sections: `recent_history`, `relevant_memories`, `experiences`, `system_prompt`
- Configurable section order and formatting
- Insertion syntax markers preserved in output for LLM to detect

**Component interaction principle:** Components are independent with clear interfaces. Never call each other directly. Orchestrated by ContextHarness facade. Backend is shared persistence dependency.

---

## 9. Interface Layer: ContextHarness Facade

**Responsibility:** Unified API orchestrating core components with configurable automation.

### 9.1 Main Facade Class

```python
class ContextHarness:
    """
    Main facade for context-harness library.
    
    Provides:
    - Simple API for common use cases
    - Configurable automation for component interactions
    - Access to individual components for advanced customization
    - LangChain message integration
    """
    
    def __init__(
        self,
        backend: StorageBackend = None,  # Default: FileBackend
        automation_config: Optional[AutomationConfig] = None,
        context_config: Optional[ContextConfig] = None,
        distillation_config: Optional[DistillationConfig] = None
    )
```

### 9.2 Thread Management

```python
    def create_thread(self, metadata: Optional[Dict] = None) -> str
    """Create new thread, return thread_id."""
    
    def add_message(
        self,
        thread_id: str,
        message: BaseMessage,  # LangChain message type
        auto_spill: bool = True
    ) -> ThreadMessage
    """Add message to thread with automatic spill detection."""
    
    def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        unwrap_langchain: bool = True
    ) -> List[BaseMessage]
    """Get conversation history as LangChain messages."""
```

### 9.3 Memory Management

```python
    def save_memory(
        self,
        memory: Memory,
        auto_link: bool = True
    ) -> None
    """Save memory with optional auto-linking to recent thread messages."""
    
    def search_memories(
        self,
        query: Optional[str] = None,
        thread_id: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> List[Memory]
    """Search memories across threads."""
```

### 9.4 Experience Distillation

```python
    def distill_experiences(
        self,
        thread_id: str,
        auto_store: bool = True
    ) -> List[Memory]
    """Distill thread and optionally auto-store results."""
    
    def trigger_distillation(
        self,
        thread_id: str,
        trigger_type: str  # 'message_count', 'session_end', 'manual'
    ) -> None
    """Trigger distillation based on automation config."""
```

### 9.5 Context Construction

```python
    def build_context_for_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        include_history: bool = True,
        include_memories: bool = True,
        include_experiences: bool = True
    ) -> str
    """Build context string for new query with intelligent selection."""
    
    def get_context_messages(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> List[BaseMessage]
    """Get context as LangChain messages ready for LLM invocation."""
```

### 9.6 Spilled Content Management

```python
    def retrieve_spilled_content(self, spill_id: str) -> Any
    """Retrieve spilled content by ID."""
    
    def provide_spill_retrieval_tool(self) -> Tool
    """Return LangChain Tool for LLM to fetch spilled content."""
```

### 9.7 Automation Configuration

```python
    def configure_automation(self, config: AutomationConfig) -> None
    """Set automation triggers and behaviors."""
    
    def enable_auto_distill(
        self,
        trigger: str = 'message_count',
        threshold: int = 10
    ) -> None
    """Enable automatic distillation every N messages."""
    
    def disable_auto_distill(self) -> None
    """Disable automatic distillation."""
```

### 9.8 Component Access (Advanced)

```python
    def get_chat_history_manager(self) -> ChatHistoryManager
    """Access underlying ChatHistoryManager for customization."""
    
    def get_memory_manager(self) -> MemoryManager
    """Access underlying MemoryManager."""
    
    def get_experience_distiller(self) -> ExperienceDistiller
    """Access underlying ExperienceDistiller."""
    
    def get_context_builder(self) -> ContextBuilder
    """Access underlying ContextBuilder."""
```

**Key facade features:**
1. **Simple onboarding:** `harness = ContextHarness()`, `harness.create_thread()`, `harness.add_message()`
2. **LangChain integration:** Accepts and returns LangChain messages by default
3. **Configurable automation:** Default minimal automation, users enable/disable triggers
4. **Advanced access:** Component access for fine-grained control
5. **Spill tool integration:** Provides LangChain Tool for LLMs to fetch spilled content

---

## 10. Data Flow Between Components

**Design principle:** Components never call each other directly. ContextHarness facade orchestrates all interactions. This keeps components independent and testable.

### 10.1 Flow: Message Addition with Auto-Spill

```
User → harness.add_message(thread_id, AIMessage(large_content))
  ↓
ChatHistoryManager.check_spill_needed(message)
  ↓ (if size > threshold)
ChatHistoryManager.spill_message_content(message)
  ↓ calls backend.spill_content()
StorageBackend.spill_content() → SpilledContentReference
  ↓ returns ThreadMessage with [[SPILL:...]] marker
ChatHistoryManager.add_message(thread_id, marked_message)
  ↓ calls backend.append_message()
StorageBackend.append_message(config, marked_message)
  ↓
Automation check: if auto_distill enabled and message_count reached threshold
  ↓
ExperienceDistiller.distill_thread(thread_id)
  ↓ returns List[Memory]
MemoryManager.store_memory(memories) [if auto_store enabled]
  ↓ calls backend.put_memory()
StorageBackend.put_memory(memories)
```

### 10.2 Flow: Context Construction for New Query

```
User → harness.build_context_for_query(query, thread_id)
  ↓
ContextBuilder.build_context(query, thread_id)
  ↓
ContextBuilder.select_messages(query, thread_id, strategy)
  ↓ calls backend.get_messages()
StorageBackend.get_messages(config, limit)
  ↓ returns messages (some with [[SPILL:...]] markers)
  ↓
ContextBuilder.select_memories(query, thread_id)
  ↓ calls backend.search_memories()
StorageBackend.search_memories(query, filters)
  ↓ returns relevant memories
  ↓
ContextBuilder.format_context(messages, memories, template)
  ↓ formats with sections, preserves spill markers
  ↓ returns formatted context string
```

### 10.3 Flow: Manual Experience Distillation

```
User → harness.distill_experiences(thread_id)
  ↓
ExperienceDistiller.distill_thread(thread_id)
  ↓ calls backend.get_thread() and backend.get_messages()
StorageBackend.get_thread(config) + get_messages(config)
  ↓ returns Thread + messages
  ↓
Distiller processes messages, extracts patterns
  ↓ creates Memory objects with related_message_ids
MemoryManager.store_memory(memories)
  ↓ calls backend.put_memory()
StorageBackend.put_memory(memories)
```

### 10.4 Flow: LLM Retrieving Spilled Content

```
LLM sees [[SPILL:MESSAGE_SPILL|{"preview":"..."}|spill_id=abc123]]
  ↓ LLM decides to fetch full content
LLM uses Tool: fetch_spilled_content(spill_id="abc123")
  ↓ Tool implementation
harness.retrieve_spilled_content(spill_id)
  ↓ calls backend.retrieve_spilled_content()
StorageBackend.retrieve_spilled_content(spill_id)
  ↓ returns full content
LLM receives full content, continues reasoning
```

---

## 11. Extensibility Points

### 11.1 Framework-Agnostic Future

**Current:** LangChain message types imported directly from `langchain.schema`.

**Future abstraction strategy:**
- Define `MessageAdapter` interface with methods:
  - `wrap(base_message) → ThreadMessage`
  - `unwrap(thread_message) → BaseMessage`
- Implement `LangChainMessageAdapter` (current)
- Future: `GenericMessageAdapter` for framework-agnostic support
- Facade uses adapter interface, not direct imports

**Migration path:**
1. Phase 1: Use LangChain directly (current design)
2. Phase 2: Introduce adapter abstraction
3. Phase 3: Add alternative framework adapters

### 11.2 Additional Storage Backends

**Pluggable backend system:**
- Implement `StorageBackend` interface
- Register backend factory in facade
- Core components unchanged (backend is dependency injection)

**Future backends:**
- `SQLiteBackend`: Structured queries, single-file, embedded
- `PostgreSQLBackend`: Production-grade, concurrent access
- `VectorBackend`: Semantic search (Chroma, Pinecone, Qdrant, Weaviate)

### 11.3 Insertion Syntax Extensions

**Current:** `[[SPILL:MESSAGE_SPILL|metadata|reference]]`

**Future markers:**
- `[[INSERT:GENERATED_DATA|metadata|file_reference]]` - Generated datasets, reports
- `[[LINK:EXTERNAL_RESOURCE|metadata|url]]` - External URLs, documents
- `[[EMBED:MULTIMEDIA|metadata|media_id]]` - Images, audio, video references

**Extensibility:** Parser ignores unknown marker types, passes through unchanged. New markers added without breaking existing parsing logic.

---

## 12. Error Handling Patterns

### 12.1 Backend Errors

- **StorageBackendError:** Base exception for all backend failures
- **ThreadNotFoundError:** Thread doesn't exist
- **MemoryNotFoundError:** Memory ID invalid
- **SpillContentNotFoundError:** Spilled content deleted or missing
- **BackendConfigurationError:** Invalid config or backend initialization failure

**Handling pattern:** Facade catches backend errors, provides user-friendly messages with recovery suggestions.

### 12.2 Spill Threshold Errors

- **SpillThresholdExceededError:** Content exceeds threshold but spill disabled
- **SpillStorageError:** Spill content storage failed (disk full, permissions)

**Handling pattern:** ChatHistoryManager checks threshold before spill, provides fallback options (truncate or reject).

### 12.3 Component Logic Errors

- **DistillationError:** Distillation process failed (LLM error, invalid messages)
- **ContextConstructionError:** Context building failed (invalid config, template error)

**Handling pattern:** Components raise specific exceptions, facade orchestrates recovery or provides diagnostics.

---

## 13. Testing Strategy

### 13.1 Layer-by-Layer Testing

**Data layer:**
- Test each backend implementation independently
- Mock backend for core layer tests
- In-memory backend for integration tests

**Core layer:**
- Test each component with mocked backend
- Test component interfaces independently
- Verify business logic without persistence concerns

**Interface layer:**
- Test facade with mocked components
- Test orchestration flows
- Test automation trigger behavior

### 13.2 Integration Testing

**End-to-end flows:**
- Message addition → spill → retrieval → context construction
- Distillation → memory storage → cross-thread search
- LLM tool invocation for spilled content retrieval

---

## 14. Implementation Priorities

### 14.1 Phase 1: Core Infrastructure (MVP)

1. Domain models implementation
2. StorageBackend interface + FileBackend
3. ChatHistoryManager basic operations
4. ContextHarness facade core methods
5. LangChain message integration

### 14.2 Phase 2: Advanced Features

1. ExperienceDistiller implementation
2. MemoryManager with search
3. ContextBuilder with intelligent selection
4. Message spilling mechanism
5. Insertion syntax parsing

### 14.3 Phase 3: Optimization & Extensions

1. Automation triggers implementation
2. Performance optimization (caching, indexing)
3. Additional backend implementations
4. Framework-agnostic abstraction
5. Advanced retrieval strategies

---

## 15. Relationship to Other RFCs

This design draft will be formalized into RFCs following Platonic Coding Phase 1:

* **RFC-001-world-view:** Conceptual design - system vision, core abstractions, taxonomy
* **RFC-002-core-architecture:** Architecture design - layered structure, component responsibilities, data flow
* **RFC-003-domain-models:** Implementation interface design - ThreadMessage, Memory, SpilledContentReference interfaces
* **RFC-004-storage-backend:** Implementation interface design - StorageBackend interface and FileBackend contract
* **RFC-005-facade-interface:** Implementation interface design - ContextHarness public API contract

Dependencies flow: RFC-001 → RFC-002 → RFC-003/004/005

---

## 16. Open Questions

1. **Distillation LLM integration:** Should default distillation strategy be LLM-free (heuristics only) or require LLM client? Trade-off: simplicity vs intelligence.

2. **Spill threshold determination:** How to determine optimal spill threshold? Should it be token-based (LLM context limit) or byte-based (storage efficiency)?

3. **Memory relevance scoring:** How to compute relevance scores for memories? Keyword frequency, semantic similarity, or hybrid approach?

4. **Thread metadata schema:** Should thread metadata have standardized fields (user_id, session_start) or be fully flexible Dict?

5. **Insertion syntax parsing:** Should parser be strict (reject unknown markers) or lenient (pass through unknown types)?

---

## 17. Conclusion

This architecture design defines a comprehensive context management library with clear layered separation, LangChain compatibility, and extensibility for future growth. The three-layer structure (Interface → Core → Data) balances simplicity for users with power for advanced customization. Key innovations include message spilling with extensible insertion syntax, memory-to-message traceability, configurable automation, and pluggable storage backends.

The design enables AI application developers and agent builders to manage sophisticated conversational context without framework lock-in, while providing clear extension points for future framework-agnostic support and additional storage backends.

> **Core principle:** Layered architecture with component independence enables both simple facade API for common use cases and deep customization for advanced scenarios.