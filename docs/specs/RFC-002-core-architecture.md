# RFC-002: Core Architecture

**Status**: Draft
**Authors**: Xiaming Chen
**Created**: 2026-04-21
**Last Updated**: 2026-04-21
**Depends on**: [RFC-001-world-view](RFC-001-world-view.md)
**Supersedes**: ---
**Kind**: Architecture Design

---

## 1. Abstract

This RFC defines the core architecture of the context-harness library, establishing a three-layer structure: Interface (facade), Core (business logic components), and Data (persistence abstraction). Each layer has distinct responsibilities and communicates through well-defined boundaries. The architecture ensures component independence, backend abstraction, and configurable orchestration. This design balances simplicity for users with extensibility for advanced customization.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This RFC defines:

* Three-layer architectural structure and layer boundaries
* Responsibilities of each layer (Interface, Core, Data)
* Four core components and their specific roles
* Data flow patterns between layers and components
* Architectural invariants and dependency constraints
* Abstract schemas for key domain entities
* Component interaction protocols (orchestrated by facade)

### 2.2 Non-Goals

This RFC does **not** define:

* Concrete API signatures or method-level interfaces (see [RFC-003-domain-models](RFC-003-domain-models.md), [RFC-004-storage-backend](RFC-004-storage-backend.md), [RFC-005-facade-interface](RFC-005-facade-interface.md))
* Implementation algorithms, internal data structures, or optimization strategies
* Specific storage backend implementations beyond FileBackend structure
* Deployment topology, packaging, or operational concerns
* Testing strategies or performance benchmarks

---

## 3. Background & Motivation

**Why layered architecture:** The context-harness library must serve two audiences with different needs:
1. **Application developers:** Need simple facade API for common use cases, minimal configuration, quick onboarding
2. **Advanced users:** Need component access for customization, alternative backends, custom distillation strategies

Layered architecture enables both: Interface layer provides facade simplicity, Core layer exposes components for customization, Data layer abstracts persistence for extensibility.

**Why component independence:** Each core capability (chat history, memory, distillation, context construction) has distinct business logic. Mixing responsibilities creates tangled code, hard to test and extend. Independent components with clear interfaces enable:
- Unit testing (mock dependencies)
- Component replacement (swap distillation strategy)
- Parallel development (different components in parallel)

**Why backend abstraction:** Storage requirements vary by deployment context: file-based for local/prototyping, SQL for production single-file, vector DB for semantic search. Abstracting persistence through StorageBackend interface enables pluggable backends without affecting core logic.

---

## 4. Architecture Overview

### 4.1 System Context

The context-harness library operates within AI application and agent systems:

```
AI Application / Agent System
  ├─ invokes → ContextHarness facade
  │             ├─ manages → conversation threads
  │             ├─ stores → cross-thread memories
  │             ├─ distills → experiences
  │             └─ constructs → query context
  │
  ├─ provides → LangChain Tool (spill content retrieval)
  │              └─ LLM uses tool → fetch spilled content
  │
  └─ configures → StorageBackend implementation
                 ├─ FileBackend (default, local)
                 ├─ InMemoryBackend (testing)
                 └─ Future: SQLBackend, VectorBackend
```

**Positioning:** Library provides context management layer between AI application logic and storage infrastructure. Application uses facade API; storage backend persists state.

### 4.2 Layer Structure

```
┌─────────────────────────────────────────┐
│  Interface Layer                        │
│  ┌─────────────────────────────────┐   │
│  │  ContextHarness (Facade)        │   │
│  │  - Thread management API        │   │
│  │  - Memory management API        │   │
│  │  - Distillation API             │   │
│  │  - Context construction API     │   │
│  │  - Automation configuration     │   │
│  │  - LangChain message handling   │   │
│  │  - Component access methods     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Responsibilities:                      │
│  - Orchestrates core components        │
│  - Provides simple user API            │
│  - Implements automation triggers      │
│  - Wraps/unwraps LangChain messages    │
└─────────────────────────────────────────┘
              ↓ calls (orchestration)
┌─────────────────────────────────────────┐
│  Core Layer                             │
│  ┌───────────┐ ┌───────────┐           │
│  │ChatHistory│ │  Memory   │           │
│  │  Manager  │ │  Manager  │           │
│  └───────────┘ └───────────┘           │
│  ┌───────────┐ ┌───────────┐           │
│  │Experience │ │  Context  │           │
│  │ Distiller │ │  Builder  │           │
│  └───────────┘ └───────────┘           │
│                                         │
│  Responsibilities:                      │
│  - Implement business logic            │
│  - Operate on domain models            │
│  - Never call other components         │
│  - Depend on backend interface only    │
└─────────────────────────────────────────┘
              ↓ depends on (persistence)
┌─────────────────────────────────────────┐
│  Data Layer                             │
│  ┌─────────────────────────────────┐   │
│  │  StorageBackend (Abstract)      │   │
│  │  Interface methods:             │   │
│  │  - Thread operations            │   │
│  │  - Message operations           │   │
│  │  - Memory operations            │   │
│  │  - Spilled content operations   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Implementations:               │   │
│  │  - FileBackend (default)        │   │
│  │  - InMemoryBackend              │   │
│  │  - Future: SQLBackend, etc.     │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Responsibilities:                      │
│  - Abstract all persistence            │
│  - Provide consistent interface        │
│  - Implement storage formats           │
│  - Indexing for searchability          │
└─────────────────────────────────────────┘
```

**Key architectural characteristic:** Downward dependency flow only. Interface → Core → Data. No upward calls, no circular dependencies.

---

## 5. Components

### 5.1 ChatHistoryManager

**Responsibility**: Manage conversation thread lifecycle and message history with automatic spill detection.

**Core functionality:**
- Create new threads with generated IDs
- Add messages to threads with spill threshold checking
- Retrieve thread state and message history
- Handle message content spilling when size exceeds threshold
- Manage spilled content lifecycle (spill, retrieve, delete)

**Interface contracts:**
- Accepts LangChain BaseMessage types, wraps in ThreadMessage
- Checks message size against configurable threshold
- Calls backend.spill_content() when threshold exceeded
- Calls backend.append_message() for thread history
- Returns messages with optional spill marker replacement

**Key design principle:** Never calls other core components. All persistence through backend interface.

**Dependencies:**
- StorageBackend (injected)
- AutomationConfig (threshold settings)

### 5.2 MemoryManager

**Responsibility**: Store, retrieve, and search memories across threads.

**Core functionality:**
- Store memories with thread linkage
- Retrieve specific memory by ID
- Search memories with filters and optional semantic query
- Get all memories linked to specific thread
- Track memory access frequency for relevance scoring

**Interface contracts:**
- Accepts Memory objects with validated structure
- Calls backend.put_memory() for storage
- Calls backend.search_memories() with query and filters
- Supports keyword-based search (default), semantic search (future)
- Returns memory lists with relevance ranking

**Key design principle:** Cross-thread searchable. Memories not isolated to single thread. Enables experience sharing across conversations.

**Dependencies:**
- StorageBackend (injected)

### 5.3 ExperienceDistiller

**Responsibility**: Extract summaries and reusable experience patterns from conversation threads.

**Core functionality:**
- Distill entire thread into memories (summaries + patterns)
- Distill raw message lists without thread load
- Extract conversation summaries
- Extract reusable patterns (user preferences, effective responses)
- Link memories to source messages for traceability

**Interface contracts:**
- Calls backend.get_thread() and backend.get_messages()
- Processes message sequence, identifies patterns
- Creates Memory objects with related_message_ids populated
- Returns List[Memory] for storage

**Distillation strategies:**
- Default: Heuristic-based (last N messages as summary, keyword extraction)
- Optional LLM: Intelligent summarization and pattern extraction
- Configurable: Custom strategies via strategy interface

**Key design principle:** Memories maintain explicit links to source messages. Enables audit trail and relevance computation.

**Dependencies:**
- StorageBackend (injected)
- Optional: BaseLLM (for intelligent distillation)

### 5.4 ContextBuilder

**Responsibility**: Construct context for new queries by intelligently selecting and formatting history + memories.

**Core functionality:**
- Build full context string for new query
- Select relevant messages from thread based on strategy
- Select relevant memories based on query
- Format assembled content using templates
- Preserve insertion syntax markers for LLM detection

**Interface contracts:**
- Calls backend.get_messages() for thread history
- Calls backend.search_memories() for relevant memories
- Applies retrieval strategy (recent-first, semantic similarity, hybrid)
- Formats sections: recent_history, relevant_memories, experiences, system_prompt
- Returns formatted context string with spill markers intact

**Retrieval strategies:**
- Recent-first: Last N messages + recent memories (simple, predictable)
- Semantic similarity: Rank by query relevance (intelligent, requires scoring)
- Hybrid: Combine recency weight + relevance score (balanced)

**Key design principle:** Insertion syntax markers preserved in output. LLM sees markers, can use tools to fetch full content.

**Dependencies:**
- StorageBackend (injected)
- ContextConfig (retrieval strategy, template format)

---

## 6. Data Flow

### 6.1 Primary Flow: Message Addition with Auto-Spill

```
User Application
  │
  ├─ calls harness.add_message(thread_id, AIMessage(content))
  │   │
  │   └─ ContextHarness (Interface Layer)
  │       ├─ wraps AI message → ThreadMessage
  │       ├─ checks automation_config.auto_spill_messages
  │       │
  │       └─ calls ChatHistoryManager.add_message()
  │           │
  │           ├─ ChatHistoryManager (Core Layer)
  │           │   ├─ checks message size vs threshold
  │           │   │
  │           │   ├─ if size > threshold:
  │           │   │   ├─ calls backend.spill_content()
  │           │   │   │   └
  │           │   │   │   └─ FileBackend (Data Layer)
  │           │   │   │       ├─ stores content to spilled/{spill_id}.jsonl
  │           │   │   │       ├─ creates SpilledContentReference
  │           │   │   │       └─ returns reference
  │           │   │   │
  │           │   │   ├─ creates insertion syntax marker [[SPILL:...]]
  │           │   │   └─ updates ThreadMessage.is_spilled = True
  │           │   │
  │           │   ├─ calls backend.append_message(thread_id, message)
  │           │   │   └
  │           │   │   └─ FileBackend (Data Layer)
  │           │   │       ├─ appends to threads/{thread_id}/messages.jsonl
  │           │   │       └ update thread metadata
  │           │   │
  │           │   └─ returns ThreadMessage
  │           │
  │           └─ ContextHarness (Interface Layer)
  │               ├─ checks automation_config.auto_distill
  │               │
  │               ├─ if enabled and message_count reached threshold:
  │               │   ├─ calls ExperienceDistiller.distill_thread()
  │               │   │   │
  │               │   │   └─ ExperienceDistiller (Core Layer)
  │               │   │       ├─ calls backend.get_thread() + get_messages()
  │               │   │       ├─ processes messages, extracts patterns
  │               │   │       ├─ creates Memory objects
  │               │   │       └─ returns List[Memory]
  │               │   │
  │               │   ├─ if automation_config.auto_store_memories:
  │               │   │   ├─ calls MemoryManager.store_memory() for each
  │               │   │   │   │
  │               │   │   │   └─ MemoryManager (Core Layer)
  │               │   │   │       └─ calls backend.put_memory()
  │               │   │   │           │
  │               │   │   │           └─ FileBackend (Data Layer)
  │               │   │   │               ├─ stores to memories/{memory_id}.json
  │               │   │   │               └ update memories/index.json
  │               │   │   │
  │               │   │   └─ returns success
  │               │   │
  │               │   └─ automation complete
  │               │
  │               └─ returns ThreadMessage to user
  │
  └─ application continues
```

### 6.2 Flow: Context Construction for New Query

```
User Application
  │
  ├─ calls harness.build_context_for_query(query, thread_id)
  │   │
  │   └─ ContextHarness (Interface Layer)
  │       └
  │       └─ calls ContextBuilder.build_context()
  │           │
  │           ├─ ContextBuilder (Core Layer)
  │           │   │
  │           │   ├─ calls backend.get_messages(thread_id)
  │           │   │   │
  │           │   │   └─ FileBackend (Data Layer)
  │           │   │       ├─ reads threads/{thread_id}/messages.jsonl
  │           │   │       ├─ returns List[ThreadMessage] (some with spill markers)
  │           │   │
  │           │   ├─ applies retrieval strategy to select messages
  │           │   │   └ recent-first: last N messages
  │           │   │   semantic: rank by relevance
  │           │   │   hybrid: combine factors
  │           │   │
  │           │   ├─ calls backend.search_memories(query, thread_id)
  │           │   │   │
  │           │   │   └─ FileBackend (Data Layer)
  │           │   │       ├─ queries memories/index.json
  │           │   │       ├─ filters by thread_id, relevance
  │           │   │       └─ returns List[Memory]
  │           │   │
  │           │   ├─ formats context using template
  │           │   │   ├─ Section 1: recent_history (messages with spill markers)
  │           │   │   ├─ Section 2: relevant_memories (memory summaries)
  │           │   │   ├─ Section 3: experiences (patterns)
  │           │   │   ├─ Section 4: system_prompt (if configured)
  │           │   │
  │           │   └─ returns formatted context string
  │           │
  │           └─ ContextHarness (Interface Layer)
  │               └─ returns context string to user
  │
  └─ application uses context for LLM invocation
```

**Flow characteristic:** Each layer stays within its responsibility. Interface orchestrates, Core implements logic, Data persists. Clear separation.

---

## 7. Invariants and Constraints

### 7.1 Architectural Invariants

| Invariant | Meaning | Consequence of Violation |
|-----------|---------|------------------------|
| **Layer Downward Dependency** | Interface → Core → Data. No upward calls. | Circular dependencies, tangled logic, hard to test |
| **Component Independence** | Core components never call other core components. | Tight coupling, hard to unit test, difficult to extend |
| **Backend Abstraction** | Core layer calls backend through interface only, never format-specific methods. | Backend lock-in, cannot swap implementations, core logic contaminated with storage details |
| **Facade Orchestration** | Only ContextHarness orchestrates cross-component interactions. | Scattered orchestration logic, unclear responsibility, automation hard to configure |
| **Automation Opt-in** | Default automation_config disables all triggers. Users explicitly enable. | Surprising behavior, user confusion, unwanted resource consumption |
| **Message Thread Ownership** | Every ThreadMessage belongs to exactly one Thread (composition). | Orphaned messages, unclear provenance, hard to query history |
| **Memory Traceability** | Every Memory has non-empty related_message_ids list. | Memories without provenance, cannot audit or compute relevance |
| **Spill Consistency** | Spilled messages contain marker syntax, valid spill_reference. | Unreachable content, broken references, LLM cannot retrieve spilled data |
| **Insertion Syntax Format** | Markers follow `[[MARKER:type|metadata_json|reference]]` format. | Unparseable markers, LLM cannot detect external content, tool invocation fails |
| **LangChain Message Preservation** | Wrapping/unwrapping preserves LangChain message structure and type. | Broken compatibility, users cannot integrate with existing LangChain code |

### 7.2 Dependency Constraints

| Constraint | Rule |
|------------|------|
| **Interface → Core** | Interface layer calls core component methods. Interface MUST NOT directly access backend. |
| **Core → Data** | Core components call backend interface methods. Core MUST NOT know backend implementation class. |
| **Interface → Interface** | Facade is single entry point. No other interface classes. |
| **Core → Core** | Components MUST NOT call other component methods. Only facade orchestrates. |
| **Data → Any** | Backend MUST NOT call core or interface. Backend only implements storage contract. |
| **External Dependencies** | Interface layer MAY depend on LangChain (message types). Core layer MAY depend on LLM client (optional). Data layer MUST NOT depend on external frameworks. |
| **Test Dependencies** | Tests may mock any layer. Tests MUST NOT depend on specific backend implementation (use InMemoryBackend or mocks). |

---

## 8. Abstract Schemas

### 8.1 Thread Schema

High-level thread structure (abstract, not implementation-specific).

| Field | Type | Description |
|-------|------|-------------|
| thread_id | String | Unique identifier, generated on creation |
| messages | List[ThreadMessage] | Ordered message history (may not always be loaded) |
| metadata | Dict[String, Any] | Thread-level info: user_id, session_start, status, custom fields |
| created_at | Timestamp | Thread creation time |
| updated_at | Timestamp | Last modification time |

**Storage responsibility:** Backend implementations define concrete format (JSON, database table, etc.).

### 8.2 ThreadMessage Schema

Message wrapper structure with spill support.

| Field | Type | Description |
|-------|------|-------------|
| message_id | String | Unique message identifier |
| thread_id | String | Parent thread reference (foreign key) |
| timestamp | Float | Message creation timestamp |
| is_spilled | Boolean | Flag indicating content offloaded |
| spill_reference | Optional[SpilledContentReference] | Spill metadata (when is_spilled=True) |
| metadata | Dict[String, Any] | Custom fields: token_count, model, role, etc. |
| content | Union[String, BaseMessage] | Actual content OR insertion syntax marker |

**Content behavior:**
- is_spilled=False: content contains LangChain BaseMessage (HumanMessage, AIMessage, etc.)
- is_spilled=True: content contains insertion syntax marker string

### 8.3 Memory Schema

Extracted knowledge/experience structure.

| Field | Type | Description |
|-------|------|-------------|
| memory_id | String | Unique memory identifier |
| memory_type | Enum | Type: summary, experience_pattern, user_preference, fact |
| content | String | Memory content text |
| thread_id | String | Source thread reference |
| related_message_ids | List[String] | Explicit links to source messages (traceability) |
| relevance_score | Float | Computed relevance metric |
| metadata | Dict[String, Any] | Timestamps, tags, access_count, etc. |

**Traceability invariant:** related_message_ids MUST be non-empty. Memories derive from messages.

### 8.4 SpilledContentReference Schema

Offloaded content metadata structure.

| Field | Type | Description |
|-------|------|-------------|
| spill_id | String | Unique spill identifier |
| spill_type | Enum | Type: MESSAGE_SPILL, GENERATED_DATA, FUTURE_EXTENSION |
| content_location | String | File path or storage reference |
| content_size | Integer | Original size (bytes or tokens) |
| content_type | String | Category: tool_response, ai_report, generated_dataset |
| content_preview | String | Short summary (optional, helps LLM decide) |
| retrieval_hint | String | Instructions: "use fetch_spilled_content tool with spill_id" |
| metadata | Dict[String, Any] | Additional spill-specific info |

**Retrieval invariant:** spill_id MUST be retrievable via backend.retrieve_spilled_content().

---

## 9. Relationship to Other RFCs

This architecture design builds on [RFC-001-world-view](RFC-001-world-view.md) conceptual abstractions:

* **[RFC-001-world-view](RFC-001-world-view.md)**: Conceptual Design - Defines Thread, Memory, ThreadMessage, SpilledContentReference, Context abstractions. This RFC realizes those concepts into concrete layer structure and component responsibilities.

Implementation interface RFCs detail this architecture:

* **[RFC-003-domain-models](RFC-003-domain-models.md)**: Implementation Interface Design - Defines exact data structures, type signatures, field constraints for ThreadMessage, Memory, SpilledContentReference, Thread based on abstract schemas in this RFC.

* **[RFC-004-storage-backend](RFC-004-storage-backend.md)**: Implementation Interface Design - Defines StorageBackend interface contract, method signatures, error handling, and FileBackend implementation details respecting backend abstraction invariant.

* **[RFC-005-facade-interface](RFC-005-facade-interface.md)**: Implementation Interface Design - Defines ContextHarness public API method signatures, parameter types, return types, and behavior contracts respecting facade orchestration principle.

**Dependency flow:** RFC-001 (abstractions) → RFC-002 (architecture) → RFC-003/004/005 (interfaces)

---

## 10. Open Questions

Architecture-level decisions requiring resolution:

1. **LLM client injection for distillation:** Should ExperienceDistiller require LLM client injection (making intelligent distillation optional dependency) or provide default heuristic strategy that works without LLM? Trade-off: dependency overhead vs extraction quality.

2. **Automation trigger timing:** When auto_distill triggers on message_count threshold, should distillation happen synchronously (blocking add_message call) or asynchronously (background task)? Synchronous simplifies error handling; asynchronous improves responsiveness.

3. **Memory relevance scoring:** Should relevance_score be computed at memory creation time (static) or updated dynamically on each retrieval (adaptive)? Static is predictable; adaptive improves accuracy over time.

4. **Backend error propagation:** When backend operations fail (e.g., file write error), should facade retry automatically, raise exception, or log and continue? Retry may succeed but adds latency; exception is explicit but requires user handling.

5. **Component access scope:** Should facade component access methods (get_chat_history_manager, etc.) return full component instances or restricted interface subsets? Full instances enable maximum customization but risk violating architectural invariants.

---

## 11. Conclusion

This architecture establishes a three-layer structure with clear responsibilities: Interface (facade orchestration and user API), Core (business logic components), Data (persistence abstraction). The four core components—ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder—implement distinct capabilities while maintaining independence (never calling each other). Backend abstraction enables pluggable storage without affecting core logic.

Architectural invariants enforce downward dependency flow, component independence, memory traceability, and spill consistency. Data flows demonstrate clear orchestration patterns: facade coordinates components, components implement logic, backend persists state. This design balances simplicity for users (facade API) with power for advanced users (component access), ensuring the library scales from basic chat history to sophisticated agent context management.

> **Architecture principle:** Layers separate concerns, components implement distinct capabilities, backend abstracts persistence, facade orchestrates everything—enabling both simplicity and extensibility.