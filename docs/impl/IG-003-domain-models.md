# IG-003: Domain Models Implementation Guide

**Target RFC**: RFC-003-domain-models
**Module**: context_harness/models
**Language**: Python 3.8+
**Created**: 2026-04-21
**Status**: Complete

---

## 1. Overview

Implement core domain models (ThreadMessage, Memory, SpilledContentReference, Thread) with validation, LangChain integration, and insertion syntax utilities. These models form the foundation for all other components.

---

## 2. Module Structure

```
context_harness/
  __init__.py
  models/
    __init__.py          # Export all models
    base.py              # Enums, errors, base structures
    thread.py            # Thread, ThreadMessage
    memory.py            # Memory, MemoryType
    spill.py             # SpilledContentReference, SpillType
    config.py            # ContextConfig, AutomationConfig, RetrievalStrategy
    insertion_syntax.py  # parse_insertion_syntax, build_insertion_syntax
```

---

## 3. Implementation Details

### 3.1 base.py - Enums and Errors

**Implement:**
- `MemoryType` enum (SUMMARY, EXPERIENCE_PATTERN, USER_PREFERENCE, FACT)
- `SpillType` enum (MESSAGE_SPILL, GENERATED_DATA, FUTURE_EXTENSION)
- `RetrievalStrategy` enum (RECENT_FIRST, SEMANTIC_SIMILARITY, HYBRID)
- `InsertionSyntaxError` custom exception
- `ValidationError` custom exception (domain-specific)

**Implementation notes:**
- Use Python `enum.Enum` base class
- Custom exceptions inherit from base Exception
- Clear error messages for debugging

### 3.2 spill.py - SpilledContentReference

**Implement:**
- `SpilledContentReference` dataclass
- Fields: spill_id (UUID), spill_type, content_location, content_size, content_type, content_preview, retrieval_hint, metadata
- Validation in `__post_init__`: content_size positive, content_location non-empty
- Use `field(default_factory=lambda: str(uuid.uuid4()))` for auto-generated IDs

**Implementation notes:**
- Import `dataclasses.dataclass`, `field`
- Import `uuid.uuid4` for ID generation
- Import `SpillType` from base.py

### 3.3 thread.py - Thread and ThreadMessage

**ThreadMessage:**
- Dataclass with fields: message_id, thread_id, timestamp, is_spilled, spill_reference, metadata, content
- Content type: `Union[str, BaseMessage]` (import from langchain.schema)
- Validation in `__post_init__`:
  - Spilled message must have spill_reference
  - Spilled message content must be str (insertion syntax)
  - Non-spilled message content must be BaseMessage
  - If spilled, validate insertion syntax format
- Factory method: `create_from_langchain(thread_id, base_message, metadata=None)`
- Method: `unwrap_to_langchain()` - returns BaseMessage (error if spilled)
- Method: `get_marker_info()` - parse insertion syntax if spilled

**Thread:**
- Dataclass with fields: thread_id, messages (list), metadata, created_at, updated_at
- Validation: all messages must have matching thread_id
- Method: `update_timestamp()` - update updated_at field

**Implementation notes:**
- Import `datetime.datetime` for timestamps
- Import `langchain.schema.BaseMessage` (and HumanMessage, AIMessage, SystemMessage, ToolMessage for type checks)
- Import `parse_insertion_syntax` from insertion_syntax.py for marker parsing
- Use `datetime.now().timestamp()` for Unix timestamps

### 3.4 memory.py - Memory

**Implement:**
- `Memory` dataclass
- Fields: memory_id, memory_type (MemoryType enum), content, thread_id, related_message_ids (list), relevance_score, metadata
- Validation in `__post_init__`:
  - related_message_ids MUST be non-empty (traceability invariant)
  - relevance_score in [0.0, 1.0]
  - content non-empty
- Import MemoryType from base.py

**Implementation notes:**
- Critical invariant: related_message_ids cannot be empty
- Clear error message if violated: "Memory must have at least one related_message_id"

### 3.5 config.py - Configuration Structures

**ContextConfig:**
- Dataclass for context construction configuration
- Fields: max_tokens (4000), sections (list), retrieval_strategy (enum), template_format (dict)
- Default sections: ["recent_history", "relevant_memories", "experiences", "system_prompt"]
- Default template_format with section formatting templates

**AutomationConfig:**
- Dataclass for automation triggers
- Fields: auto_spill_messages (True), spill_threshold_bytes (10000), auto_distill (False), distill_trigger ("message_count"), distill_threshold (10), auto_store_memories (True), auto_link_memories (True)
- Default: auto_distill disabled

**Implementation notes:**
- Use `field(default_factory=lambda: [...])` for list/dict defaults
- Import RetrievalStrategy from base.py

### 3.6 insertion_syntax.py - Insertion Syntax Utilities

**parse_insertion_syntax(marker: str) -> Dict[str, Any]:**
- Validate format: starts with "[[" and ends with "]]"
- Split by "|" separator into 3 parts: MARKER:type, metadata_json, reference
- Parse metadata_json with `json.loads()`
- Return dict: {"marker_type": str, "type": str, "metadata": dict, "reference": str}
- Raise InsertionSyntaxError if format invalid or JSON malformed
- Do NOT reject unknown marker types (lenient parsing)

**build_insertion_syntax(marker_type, type_str, metadata, reference) -> str:**
- Format: marker_type:type_str
- JSON encode metadata dict
- Concatenate: "[[MARKER:type|metadata_json|reference]]"
- Return formatted string

**Implementation notes:**
- Import `json` for JSON parsing/encoding
- Use regex or simple string operations for parsing
- Handle edge cases: empty metadata, special characters in reference

---

## 4. Dependencies

**External dependencies:**
- `langchain` >= 0.0.200 (for BaseMessage types)
- Python standard library: `dataclasses`, `enum`, `uuid`, `datetime`, `json`, `typing`

**Install requirements:**
```bash
pip install langchain>=0.0.200
```

**setup.py or requirements.txt:**
- Add langchain dependency
- Python 3.8+ required (dataclasses built-in)

---

## 5. Testing Strategy

### 5.1 Unit Tests

**test_base.py:**
- Test enum value access
- Test error types inheritance

**test_thread.py:**
- Test ThreadMessage creation from LangChain messages (HumanMessage, AIMessage, ToolMessage)
- Test auto-generated IDs and timestamps
- Test validation: spilled message without reference (should raise ValueError)
- Test validation: non-spilled message with str content (should raise ValueError)
- Test unwrap_to_langchain() for non-spilled messages
- Test unwrap_to_langchain() for spilled messages (should raise ValueError)
- Test get_marker_info() for spilled messages
- Test Thread creation and message ownership validation

**test_memory.py:**
- Test Memory creation with valid data
- Test validation: empty related_message_ids (should raise ValueError)
- Test validation: relevance_score out of range (should raise ValueError)
- Test validation: empty content (should raise ValueError)

**test_spill.py:**
- Test SpilledContentReference creation
- Test validation: negative content_size (should raise ValueError)
- Test validation: empty content_location (should raise ValueError)

**test_config.py:**
- Test ContextConfig default values
- Test AutomationConfig default values
- Test custom configuration override

**test_insertion_syntax.py:**
- Test parse_insertion_syntax() with valid marker
- Test parse_insertion_syntax() with invalid format (missing brackets)
- Test parse_insertion_syntax() with malformed JSON (should raise InsertionSyntaxError)
- Test parse_insertion_syntax() with unknown marker type (should succeed, lenient)
- Test build_insertion_syntax() with various metadata
- Test round-trip: build then parse

### 5.2 Integration Tests

**test_langchain_integration.py:**
- Test creating ThreadMessage from each LangChain message type
- Test unwrapping preserves message type and content
- Test metadata preservation

**test_validation_comprehensive.py:**
- Test all validation constraints across models
- Test error messages are clear and actionable

---

## 6. Implementation Checklist

### Phase 1: Core Models
1. ✓ Create context_harness/ directory structure
2. ✓ Implement base.py (enums, errors)
3. ✓ Implement spill.py (SpilledContentReference)
4. ✓ Implement thread.py (Thread, ThreadMessage)
5. ✓ Implement memory.py (Memory)
6. ✓ Implement config.py (ContextConfig, AutomationConfig)

### Phase 2: Utilities
7. ✓ Implement insertion_syntax.py (parse, build functions)
8. ✓ Update thread.py to import insertion_syntax utilities
9. ✓ Add __init__.py exports

### Phase 3: Testing
10. ✓ Create tests/ directory
11. ✓ Implement unit tests for each module
12. ✓ Implement integration tests
13. ✓ Run tests with pytest
14. ✓ Fix any test failures

### Phase 4: Documentation
15. ✓ Add docstrings to all classes and methods
16. ✓ Add type hints for all parameters
17. ✓ Add usage examples in docstrings

---

## 7. Coding Plan

**Step 1: Set up package structure**
- Create `context_harness/__init__.py`
- Create `context_harness/models/__init__.py`
- Create empty module files for each component

**Step 2: Implement base.py**
- Define enums and error types
- Simple, no dependencies

**Step 3: Implement insertion_syntax.py**
- Parsing and building utilities
- Test independently

**Step 4: Implement spill.py**
- SpilledContentReference dataclass
- Depends on base.py (SpillType)

**Step 5: Implement thread.py**
- Thread and ThreadMessage dataclasses
- Depends on spill.py, insertion_syntax.py, langchain.schema

**Step 6: Implement memory.py**
- Memory dataclass
- Depends on base.py (MemoryType)

**Step 7: Implement config.py**
- Configuration dataclasses
- Depends on base.py (RetrievalStrategy)

**Step 8: Create tests**
- Test each module independently
- Test validation constraints
- Test LangChain integration

**Step 9: Update __init__.py exports**
- Export all models from models/__init__.py
- Export models from context_harness/__init__.py (top-level access)

---

## 8. Edge Cases and Special Handling

**LangChain message type detection:**
- Use `isinstance(message, HumanMessage)` etc. for type checks
- Or check `message.type` attribute if available

**Insertion syntax escaping:**
- Current approach: metadata JSON must not contain "|" or "[["
- Future: implement escaping if needed
- Restrict metadata to safe characters for now

**Frozen vs mutable dataclasses:**
- Decision: Use mutable dataclasses (frozen=False)
- Reason: Some fields need updates (Thread.updated_at, Memory.metadata.access_count)
- Users can manually protect critical fields if needed

**UUID generation:**
- Use uuid.uuid4() (random, collision-resistant)
- Future: uuid.uuid5() option for deterministic test IDs

**Metadata flexibility:**
- Keep metadata Dict fully flexible
- No predefined keys validation
- User applications define their own metadata schema

---

## 9. Performance Considerations

**Timestamp generation:**
- datetime.now().timestamp() is fast
- No optimization needed

**UUID generation:**
- uuid.uuid4() is fast
- No optimization needed

**Validation overhead:**
- Validation in __post_init__ runs once on creation
- Minimal overhead for type checks
- No performance concern for normal usage

**Insertion syntax parsing:**
- json.loads() is efficient
- Simple string splitting
- No regex needed

---

## 10. Usage Examples

**Create thread and add messages:**
```python
from langchain.schema import HumanMessage, AIMessage
from context_harness.models import Thread, ThreadMessage

thread = Thread(metadata={"user_id": "user123"})
msg1 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Hello"))
msg2 = ThreadMessage.create_from_langchain(thread.thread_id, AIMessage("Hi!"))

thread.messages.append(msg1)
thread.messages.append(msg2)
```

**Create memory:**
```python
from context_harness.models import Memory, MemoryType

memory = Memory(
    memory_type=MemoryType.USER_PREFERENCE,
    content="User prefers concise responses",
    thread_id=thread.thread_id,
    related_message_ids=[msg1.message_id, msg2.message_id],
    relevance_score=0.85
)
```

**Parse insertion syntax:**
```python
from context_harness.models import parse_insertion_syntax

marker = "[[SPILL:MESSAGE_SPILL|{\"preview\":\"Large content\"}|spill_id=abc123]]"
parsed = parse_insertion_syntax(marker)
print(parsed["metadata"]["preview"])  # "Large content"
```

---

## 11. Success Criteria

- All models implemented with complete validation
- LangChain integration works for all message types
- Insertion syntax parsing/building functional
- All unit tests pass
- Type hints complete for all public methods
- Docstrings clear and comprehensive
- No circular dependencies between modules
- Package imports work correctly

---

## 12. Notes

**No backend dependency:**
- Models are pure domain structures
- No import of backend types
- Backend uses models, models don't use backend

**No facade dependency:**
- Models are foundational
- Used by facade, don't know about facade

**Validation strictness:**
- Enforce invariants at creation time
- Prevent invalid data entering system
- Clear error messages for debugging

**Extensibility:**
- Models designed for future extension
- Insertion syntax lenient for unknown types
- Metadata fields flexible for user customization