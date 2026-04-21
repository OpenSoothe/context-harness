# RFC-001: Context Harness World View

**Status**: Draft
**Authors**: Xiaming Chen
**Created**: 2026-04-21
**Last Updated**: 2026-04-21
**Depends on**: ---
**Supersedes**: ---
**Kind**: Conceptual Design

---

## 1. Abstract

The context-harness library provides a conceptual framework for managing conversational context in AI applications and agents. It defines abstractions for conversation threads, memories, spilled content, and context construction. The system's core vision is to enable sophisticated context management with LangChain compatibility while remaining extensible for future framework-agnostic support. This RFC establishes the foundational concepts, terminology, and system-wide invariants that govern all implementations.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This RFC defines:

* The system's vision and purpose for AI application developers and agent builders
* Core abstractions: Thread, Memory, ThreadMessage, SpilledContentReference, Context
* Conceptual model of how these abstractions relate and interact
* System-wide taxonomy and terminology
* Fundamental invariants all implementations must respect
* Design principles guiding architectural decisions

### 2.2 Non-Goals

This RFC does **not** define:

* Concrete module or component structure (see [RFC-002-core-architecture](RFC-002-core-architecture.md))
* API contracts or interface signatures (see [RFC-003-domain-models](RFC-003-domain-models.md), [RFC-004-storage-backend](RFC-004-storage-backend.md), [RFC-005-facade-interface](RFC-005-facade-interface.md))
* Implementation details, storage formats, or algorithms
* Specific backend implementations beyond abstract concepts

---

## 3. Background & Motivation

**The problem space:** AI applications and agents require sophisticated context management beyond simple chat history. Current solutions fall into two extremes:

1. **Basic thread storage:** Insufficient for agents with tool interactions, large outputs, and cross-session memory needs
2. **Complex framework adoption:** Overkill for focused use cases, introduces dependency lock-in

**Key challenges:**
- Large tool responses or AI outputs exceed context limits and need spilling mechanisms
- Conversations contain reusable experiences (user preferences, effective patterns) that should be extracted and shared across threads
- Memories need to be searchable across threads, not isolated within single conversations
- Context construction for new queries requires intelligent selection, not just chronological retrieval
- Developers need LangChain compatibility but may require framework-agnostic future support

**Why this system exists:** The context-harness library fills the gap between basic chat history and heavyweight frameworks by providing comprehensive context management as a standalone, extensible library.

---

## 4. Design Principles

Core principles guiding all architectural and implementation decisions:

1. **Layered separation:** Interface (facade) orchestrates Core (business logic) which depends on Data (persistence). Each layer has single responsibility. No circular dependencies.

2. **LangChain compatibility first, extensible design:** Use LangChain message types directly for immediate adoption. Keep message module extensible through abstraction for future framework-agnostic support.

3. **Configurable automation:** Default behavior is minimal automation to avoid surprising users. Automation triggers (auto-spill, auto-distill) are opt-in. Users control when and how components interact.

4. **Component independence:** Core components (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder) never call each other directly. The facade orchestrates interactions. This ensures testability and loose coupling.

5. **Extensible insertion syntax:** Generic marker format `[[MARKER:type|metadata|reference]]` supports current message spilling and future scenarios (generated data insertion, external resource linking) without breaking existing implementations.

6. **Backend abstraction:** StorageBackend interface isolates all persistence. Implementations (FileBackend, future SQL/Vector) are pluggable without affecting core logic. Default FileBackend requires no external dependencies.

7. **Memory traceability:** Every memory explicitly links to source message IDs. This enables relevance scoring, audit trails, and understanding how memories evolved from conversations.

---

## 5. Conceptual Model

### 5.1 Core Abstractions

**Thread:** A conversation session between user(s) and AI system(s). Contains ordered messages and metadata. Threads are the primary unit of conversation history and provide the context window for ongoing interactions.

**ThreadMessage:** A single message within a thread, wrapping LangChain messages with harness-specific metadata. Messages may contain actual content or insertion syntax markers pointing to spilled/generated content. Every message has unique identity and belongs to exactly one thread.

**Memory:** Extracted knowledge, patterns, or summaries derived from threads. Memories can be thread-specific (linked to single thread) or cross-thread (shared across multiple conversations). Memories maintain explicit links to source messages for traceability and relevance.

**SpilledContentReference:** Metadata describing offloaded large content. When message content exceeds thresholds, it is spilled to external storage. The message contains an insertion syntax marker, while SpilledContentReference tracks location, type, preview, and retrieval information.

**Context:** The assembled information used to inform a new query. Context is constructed by selecting and formatting thread messages, relevant memories, and distilled experiences according to configurable templates and retrieval strategies.

### 5.2 Relationships

```
Thread
  ├─ contains → ThreadMessage (ordered, 1:N)
  │              ├─ wraps → LangChain BaseMessage
  │              └─ may reference → SpilledContentReference (0:1)
  │
  ├─ source for → Memory (0:N, via distillation)
  │                └─ links to → ThreadMessage (via related_message_ids, M:N)
  │
  └─ input for → Context construction

Memory
  ├─ searchable across → multiple Threads (cross-thread capability)
  ├─ linked to → ThreadMessage (traceability)
  └─ selected for → Context construction (based on relevance)

Context
  ├─ selects from → ThreadMessage (retrieval strategy)
  ├─ selects from → Memory (relevance scoring)
  └─ formats → assembled information (template-based)
```

**Key relationship characteristics:**

- **Thread-Message:** Composition (thread owns messages). Ordered, append-only sequence.
- **Thread-Memory:** Derivation (threads are source material for memory extraction via distillation). Optional relationship.
- **Memory-ThreadMessage:** Linkage (explicit traceability). Many-to-many: memory links to multiple source messages.
- **Message-SpilledContent:** Reference (when message content is offloaded). Optional, 0-or-1.
- **Context-Source:** Selection (context construction selects from available messages and memories based on relevance).

---

## 6. Taxonomy

Authoritative terminology for the context-harness system.

| Term | Definition |
|------|-----------|
| **Thread** | A conversation session containing ordered messages between user(s) and AI system(s). Primary unit of conversation history. |
| **ThreadMessage** | A message within a thread, wrapping LangChain BaseMessage with metadata. May contain actual content or insertion syntax marker. |
| **Memory** | Extracted knowledge, pattern, or summary derived from conversation threads. Links explicitly to source messages. |
| **SpilledContentReference** | Metadata describing offloaded large message content. Provides location, preview, and retrieval information. |
| **Insertion Syntax** | Structured marker format `[[MARKER:type|metadata|reference]]` embedded in messages to reference external content or resources. |
| **Distillation** | Process of extracting memories (summaries, patterns) from conversation threads. May use heuristics or LLM-based intelligence. |
| **Context** | Assembled information (messages, memories, experiences) formatted to inform a new query. Constructed via retrieval strategies and templates. |
| **Retrieval Strategy** | Method for selecting relevant messages and memories: recent-first, semantic similarity, or hybrid approach. |
| **Backend** | Storage implementation providing persistence for threads, messages, memories, and spilled content. Abstracted through StorageBackend interface. |
| **Automation** | Configurable triggers for automatic component interactions (auto-spill on size threshold, auto-distill on message count). |
| **Facade** | ContextHarness class providing unified API that orchestrates core components with simple interface for users. |
| **Component** | Core business logic module (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder) with single responsibility. |
| **Layer** | Architectural division: Interface (facade), Core (components), or Data (backends). Each layer has distinct responsibility. |
| **Traceability** | Explicit linking of memories to source message IDs, enabling audit trails and relevance scoring. |
| **Relevance Score** | Metric indicating how pertinent a memory or message is to a specific query or context. |

---

## 7. Invariants

System-wide invariants that all implementations MUST respect:

1. **Thread Ownership:** Every ThreadMessage belongs to exactly one Thread. Messages cannot exist independently or be shared across threads.

2. **Message Identity:** Each ThreadMessage has a unique message_id. Once created, identity is immutable. Content may change (via spill), but identity persists.

3. **Memory Traceability:** Every Memory MUST have a non-empty `related_message_ids` list linking to source ThreadMessages. Memories cannot exist without provenance.

4. **Spill Consistency:** If a ThreadMessage has `is_spilled=True`, it MUST contain insertion syntax marker (not actual content) and MUST have valid `spill_reference`. Spilled content MUST be retrievable via spill_id.

5. **Insertion Syntax Format:** All insertion syntax markers MUST follow format `[[MARKER:type|metadata_json|reference]]`. Unknown marker types MUST be preserved (not rejected) by parsers.

6. **Backend Abstraction:** Core components MUST NOT directly access storage formats or backend internals. All persistence MUST go through StorageBackend interface methods.

7. **Component Independence:** Core components MUST NOT call methods on other core components. Only the facade orchestrates cross-component interactions.

8. **Automation Opt-in:** Default automation configuration MUST be disabled. Users explicitly enable auto-spill, auto-distill, or other triggers. Automation MUST NOT activate without user consent.

9. **LangChain Compatibility:** ThreadMessage MUST wrap LangChain BaseMessage types. Facade MUST accept and return LangChain messages by default. Unwrapping MUST preserve original message structure.

10. **Layer Separation:** Interface layer MUST orchestrate Core layer. Core layer MUST depend on Data layer through abstract interface only. No layer MAY call upward (Data cannot call Core, Core cannot call Interface).

---

## 8. Relationship to Other RFCs

This conceptual design establishes foundational abstractions and principles:

* **[RFC-002-core-architecture](RFC-002-core-architecture.md)**: Architecture Design - Defines concrete layer structure and component responsibilities based on abstractions in this RFC
* **[RFC-003-domain-models](RFC-003-domain-models.md)**: Implementation Interface Design - Defines precise data structures and interfaces for ThreadMessage, Memory, SpilledContentReference based on abstractions here
* **[RFC-004-storage-backend](RFC-004-storage-backend.md)**: Implementation Interface Design - Defines StorageBackend interface contract respecting backend abstraction invariant
* **[RFC-005-facade-interface](RFC-005-facade-interface.md)**: Implementation Interface Design - Defines ContextHarness public API respecting facade orchestration principle

**Dependency flow:** RFC-001 (conceptual) → RFC-002 (architecture) → RFC-003/004/005 (impl interfaces)

---

## 9. Open Questions

Design decisions requiring resolution before finalizing architecture:

1. **Distillation intelligence level:** Should default distillation strategy be LLM-free (heuristic-based) or require LLM client? Trade-off: simplicity vs extraction quality.

2. **Spill threshold unit:** Should spill threshold be token-based (LLM context window limit) or byte-based (storage efficiency)? Different thresholds serve different optimization goals.

3. **Memory relevance scoring method:** How to compute relevance scores? Keyword frequency (simple, fast), semantic similarity (intelligent, requires vector backend), or hybrid (balanced)?

4. **Thread metadata standardization:** Should thread metadata have predefined fields (user_id, session_start, status) or be fully flexible Dict? Standardization enables cross-thread analysis but reduces flexibility.

5. **Insertion syntax parsing policy:** Should parser reject unknown marker types (strict) or pass through unchanged (lenient)? Strict prevents malformed syntax; lenient enables extensions without parser updates.

---

## 10. Conclusion

This RFC establishes the conceptual foundation for the context-harness library: a system for managing conversational context with LangChain compatibility, memory traceability, message spilling, and intelligent context construction. The core abstractions (Thread, ThreadMessage, Memory, SpilledContentReference, Context) form a coherent model where threads contain messages, messages may reference spilled content, threads distill into memories, memories link back to messages, and context construction selects and formats relevant information.

The design principles—layered separation, component independence, backend abstraction, and configurable automation—ensure the system is both simple to use and extensible. The system-wide invariants guarantee consistency across all implementations, while the taxonomy provides precise terminology for all subsequent RFCs.

> **Core vision:** Context management that scales from simple chat history to sophisticated agent workflows, with clear abstractions, traceable memories, and extensible architecture.