# IG-005: Facade Interface Implementation Guide

**Target RFC**: RFC-005-facade-interface
**Module**: context_harness (root module)
**Language**: Python 3.8+
**Created**: 2026-04-21
**Status**: Complete

---

## 1. Overview

Implement ContextHarness facade - the single entry point that orchestrates all components with a simple API for common use cases while providing component access for advanced customization.

---

## 2. Implementation Strategy

Since we have complete domain models and storage backend, the facade implementation will:

1. **Create core components first** (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder)
2. **Implement ContextHarness facade** that orchestrates them
3. **Provide LangChain Tool integration** for spilled content retrieval

---

## 3. Module Structure

```
context_harness/
  __init__.py                    # Export ContextHarness + models
  facade.py                      # ContextHarness main facade
  components/
    __init__.py
    chat_history_manager.py      # Thread and message management
    memory_manager.py            # Memory CRUD and search
    experience_distiller.py      # Experience extraction
    context_builder.py           # Context construction
```

---

## 4. Core Components Implementation

### 4.1 ChatHistoryManager

**Responsibility:** Thread lifecycle and message history with spill detection

**Key methods:**
- `create_thread(metadata)`
- `add_message(thread_id, message)` - with auto-spill check
- `get_thread(thread_id)`
- `get_messages(thread_id, limit, include_spilled_markers)`
- `check_spill_needed(message)`
- `spill_message_content(message, backend)`

**Dependencies:** StorageBackend

### 4.2 MemoryManager

**Responsibility:** Memory storage and search

**Key methods:**
- `store_memory(memory)`
- `retrieve_memory(memory_id)`
- `search_memories(query, thread_id, memory_type, limit)`
- `get_thread_memories(thread_id)`
- `update_memory_access(memory_id)`

**Dependencies:** StorageBackend

### 4.3 ExperienceDistiller

**Responsibility:** Extract summaries and patterns from threads

**Key methods:**
- `distill_thread(thread_id)` - returns List[Memory]
- `distill_messages(messages)` - returns List[Memory]
- `extract_summary(messages)` - returns Memory
- `extract_patterns(messages)` - returns List[Memory]
- `link_memory_to_messages(memory, message_ids)` - returns Memory

**Dependencies:** StorageBackend, optional LLM client

**Default strategy:** Simple heuristics (last N messages as summary, keyword extraction)

### 4.4 ContextBuilder

**Responsibility:** Build context for new queries

**Key methods:**
- `build_context(query, thread_id, config)` - returns formatted context string
- `select_messages(query, thread_id, strategy)` - returns List[ThreadMessage]
- `select_memories(query, thread_id)` - returns List[Memory]
- `format_context(messages, memories, template)` - returns str

**Dependencies:** StorageBackend, ContextConfig

---

## 5. ContextHarness Facade

### 5.1 Initialization

```python
def __init__(
    backend: Optional[StorageBackend] = None,
    automation_config: Optional[AutomationConfig] = None,
    context_config: Optional[ContextConfig] = None
):
    # Create backend if None
    if backend is None:
        backend = FileBackend()

    # Initialize components
    self._backend = backend
    self._chat_history_manager = ChatHistoryManager(backend)
    self._memory_manager = MemoryManager(backend)
    self._experience_distiller = ExperienceDistiller(backend)
    self._context_builder = ContextBuilder(backend, context_config)

    # Set automation config
    self._automation_config = automation_config or AutomationConfig()
```

### 5.2 Thread Management

**create_thread(metadata):**
- Call ChatHistoryManager.create_thread()
- Store via backend.put_thread()
- Return thread_id

**add_message(thread_id, message, auto_spill):**
- Wrap LangChain message in ThreadMessage
- Check auto-spill threshold
- Append via ChatHistoryManager
- Check automation triggers (auto-distill)
- Return ThreadMessage

**get_thread_history(thread_id, limit, unwrap_langchain):**
- Get messages via backend
- Unwrap to LangChain if requested
- Return List[BaseMessage]

### 5.3 Memory Management

**save_memory(memory, auto_link):**
- Link to recent messages if auto_link and empty related_message_ids
- Store via MemoryManager

**search_memories(query, thread_id, memory_type):**
- Call MemoryManager.search_memories()

### 5.4 Experience Distillation

**distill_experiences(thread_id, auto_store):**
- Call ExperienceDistiller.distill_thread()
- Store results if auto_store

**trigger_distillation(thread_id, trigger_type):**
- Check automation_config
- Call distill_experiences if enabled

### 5.5 Context Construction

**build_context_for_query(query, thread_id, ...):**
- Call ContextBuilder.build_context()
- Return formatted string

**get_context_messages(query, thread_id):**
- Build context string
- Wrap as SystemMessage + HumanMessage
- Return List[BaseMessage]

### 5.6 Spilled Content

**retrieve_spilled_content(spill_id):**
- Call backend.retrieve_spilled_content()

**provide_spill_retrieval_tool():**
- Create LangChain Tool with spill retrieval function
- Return Tool instance

### 5.7 Automation Configuration

**configure_automation(config):**
- Update automation_config

**enable_auto_distill(trigger, threshold):**
- Set automation_config values

**disable_auto_distill():**
- Set auto_distill = False

### 5.8 Component Access

**get_chat_history_manager():** Return component instance
**get_memory_manager():** Return component instance
**get_experience_distiller():** Return component instance
**get_context_builder():** Return component instance

---

## 6. Testing Strategy

### 6.1 Component Tests

**test_chat_history_manager.py:**
- Test create_thread, add_message, get_messages
- Test spill detection and triggering

**test_memory_manager.py:**
- Test store, retrieve, search

**test_experience_distiller.py:**
- Test distill_thread, extract patterns

**test_context_builder.py:**
- Test build_context, format sections

### 6.2 Facade Tests

**test_facade_init.py:**
- Test initialization with defaults
- Test with custom backend

**test_facade_threads.py:**
- Test create_thread, add_message, get_history
- Test LangChain message wrapping/unwrapping

**test_facade_memories.py:**
- Test save_memory, search_memories

**test_facade_distillation.py:**
- Test manual distillation
- Test auto-distill triggers

**test_facade_context.py:**
- Test build_context_for_query
- Test get_context_messages

**test_facade_spill.py:**
- Test retrieve_spilled_content
- Test LangChain Tool provision

**test_facade_automation.py:**
- Test enable/disable auto-distill
- Test automation triggers

**test_facade_component_access.py:**
- Test getting component instances

### 6.3 Integration Tests

**test_facade_workflow.py:**
- Full workflow: create thread → add messages → distill → build context

---

## 7. Success Criteria

- All components implemented with clear interfaces
- ContextHarness facade orchestrates correctly
- LangChain integration works transparently
- Automation triggers configurable
- Spill retrieval Tool works
- Component access provided
- All tests pass
- Total tests: ~50+ additional tests

---

## 8. Notes

**Simplified implementation:**
- ExperienceDistiller uses simple heuristics (no LLM client initially)
- ContextBuilder uses recent-first strategy
- No distillation_config initially (future enhancement)

**Automation behavior:**
- Default: all automation disabled
- User must explicitly enable via configure_automation or enable_auto_distill

**LangChain Tool:**
- Simple function-based Tool
- Name: "fetch_spilled_content"
- Description explains usage for LLM