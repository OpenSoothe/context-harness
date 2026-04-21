# context-harness Terminology Reference

Authoritative terminology reference for context-harness RFC specifications.

---

## Rules

1. All RFCs **MUST** use the terms defined here when referring to project concepts
2. New terms introduced in an RFC **MUST** be registered in this document
3. Deprecated terms **MUST** be removed when the defining RFC is deprecated
4. This document reflects the **current** state of terminology (not historical)

---

## Terms

| Term | Source RFC | Brief Description |
|------|-----------|-------------------|
| Thread | RFC-001-world-view | Conversation session containing ordered messages between user(s) and AI system(s) |
| ThreadMessage | RFC-001-world-view | Message within a thread, wrapping LangChain BaseMessage with metadata, may contain insertion syntax marker |
| Memory | RFC-001-world-view | Extracted knowledge, pattern, or summary derived from conversation threads, links to source messages |
| SpilledContentReference | RFC-001-world-view | Metadata describing offloaded large message content with retrieval information |
| Insertion Syntax | RFC-001-world-view | Structured marker format [[MARKER:type|metadata|reference]] for external content references |
| Distillation | RFC-001-world-view | Process of extracting memories (summaries, patterns) from conversation threads |
| Context | RFC-001-world-view | Assembled information formatted to inform a new query |
| Retrieval Strategy | RFC-001-world-view | Method for selecting relevant messages and memories: recent-first, semantic similarity, hybrid |
| Backend | RFC-001-world-view | Storage implementation providing persistence for threads, messages, memories, spilled content |
| Automation | RFC-001-world-view | Configurable triggers for automatic component interactions (auto-spill, auto-distill) |
| Facade | RFC-001-world-view | ContextHarness class providing unified API orchestrating core components |
| Component | RFC-001-world-view | Core business logic module with single responsibility (ChatHistoryManager, etc.) |
| Layer | RFC-001-world-view | Architectural division: Interface (facade), Core (components), or Data (backends) |
| Traceability | RFC-001-world-view | Explicit linking of memories to source message IDs for audit trails and relevance |
| Relevance Score | RFC-001-world-view | Metric indicating pertinence of memory or message to specific query or context |
| ChatHistoryManager | RFC-002-core-architecture | Core component managing thread lifecycle and message history with spill detection |
| MemoryManager | RFC-002-core-architecture | Core component storing, retrieving, and searching memories across threads |
| ExperienceDistiller | RFC-002-core-architecture | Core component extracting summaries and reusable patterns from threads |
| ContextBuilder | RFC-002-core-architecture | Core component constructing context for queries by selecting and formatting information |
| StorageBackend | RFC-004-storage-backend | Abstract interface isolating persistence with config-based routing pattern |
| FileBackend | RFC-004-storage-backend | Default backend implementation using JSON/JSONL storage with indexing |
| ContextHarness | RFC-005-facade-interface | Main facade class providing simple API and orchestrating core components |

---

## Usage Guidelines

- **Capitalization**: Use the capitalization shown in the Term column when referring to defined terms
- **First use**: On first use in an RFC, link to this document or the defining RFC
- **Synonyms**: Avoid synonyms; use the canonical term from this table

---

## Related Documents

- [rfc-standard.md](rfc-standard.md) - RFC process and conventions
- [rfc-index.md](rfc-index.md) - RFC index
- [rfc-history.md](rfc-history.md) - Change history