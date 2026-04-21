# RFC-003: Domain Models

**Status**: Draft
**Authors**: Xiaming Chen
**Created**: 2026-04-21
**Last Updated**: 2026-04-21
**Depends on**: [RFC-001-world-view](RFC-001-world-view.md), [RFC-002-core-architecture](RFC-002-core-architecture.md)
**Supersedes**: ---
**Kind**: Implementation Interface Design

---

## 1. Abstract

This RFC defines the implementation interface for core domain models: ThreadMessage, Memory, SpilledContentReference, Thread, and supporting structures. These models bridge conceptual abstractions (RFC-001) and architectural schemas (RFC-002) with concrete Python type definitions. The models use dataclasses/Pydantic for type safety, integrate LangChain BaseMessage types, and enforce validation constraints. All models are immutable where possible to ensure consistency.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This RFC defines:

* Python type definitions for Thread, ThreadMessage, Memory, SpilledContentReference
* Field types, validation constraints, and default values
* Enum definitions: MemoryType, SpillType, RetrievalStrategy
* Supporting structures: ContextConfig, AutomationConfig
* Insertion syntax parsing utilities
* LangChain message integration patterns
* Validation rules and error types

### 2.2 Non-Goals

This RFC does **not** define:

* Internal implementation algorithms (serialization, indexing strategies)
* Performance optimization patterns
* Storage format specifics (JSON schema details handled by backend)
* Testing strategies
* Migration or versioning patterns

---

## 3. Background & Motivation

**Why precise interface definitions:** RFC-001 and RFC-002 establish conceptual models and schemas, but implementation needs exact type signatures. Ambiguous types cause:
- Validation gaps (invalid data accepted)
- Integration friction (unclear contract between components)
- Type checking failures (mypy/pyright cannot enforce)

**Why LangChain integration:** Target users use LangChain. Wrapping/unwrapping must preserve message types. Integration through clear type union (String | BaseMessage) with explicit conversion methods.

**Why validation enforcement:** System invariants (RFC-001) require enforcement at model level. Example: Memory.related_message_ids non-empty. Validation in data model ensures invariant compliance at creation time, not scattered across components.

---

## 4. Naming Conventions

| Pattern | Purpose | Example |
|---------|---------|---------|
| `{Name}Type` | Enum types for categorization | `MemoryType`, `SpillType` |
| `{Name}Config` | Configuration dataclasses | `ContextConfig`, `AutomationConfig` |
| `{Name}Reference` | Reference/metadata structures | `SpilledContentReference` |
| `parse_insertion_syntax` | Utility function naming | `parse_insertion_syntax(marker: str) -> dict` |
| `create_{name}` | Factory method naming | `ThreadMessage.create_from_langchain(msg)` |
| `unwrap_to_langchain` | LangChain conversion naming | `ThreadMessage.unwrap_to_langchain() -> BaseMessage` |
| `is_spilled`, `has_marker` | Boolean property naming | `ThreadMessage.is_spilled: bool` |

---

## 5. Data Structures

### 5.1 ThreadMessage

Core message wrapper with spill support and LangChain integration.

```python
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any, List
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from datetime import datetime
import uuid

@dataclass
class ThreadMessage:
    """Message wrapper with harness metadata and spill support."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    is_spilled: bool = False
    spill_reference: Optional[SpilledContentReference] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    content: Union[str, BaseMessage]  # String for marker, BaseMessage for actual content

    # Validation constraints
    def __post_init__(self):
        """Validate invariants after initialization."""
        # Spill consistency: if spilled, must have reference
        if self.is_spilled and self.spill_reference is None:
            raise ValueError("Spilled message must have spill_reference")

        # Spill consistency: if spilled, content must be marker string
        if self.is_spilled and not isinstance(self.content, str):
            raise ValueError("Spilled message content must be insertion syntax string")

        # Non-spilled: content must be BaseMessage
        if not self.is_spilled and not isinstance(self.content, BaseMessage):
            raise ValueError("Non-spilled message content must be LangChain BaseMessage")

        # Insertion syntax validation if content is string
        if isinstance(self.content, str) and self.is_spilled:
            self._validate_insertion_syntax()

    def _validate_insertion_syntax(self):
        """Validate insertion syntax format."""
        # Must match pattern: [[MARKER:type|metadata_json|reference]]
        if not self.content.startswith("[[") or not self.content.endswith("]]"):
            raise ValueError(f"Invalid insertion syntax: {self.content}")
        # Detailed parsing in utility function

    @classmethod
    def create_from_langchain(
        cls,
        thread_id: str,
        base_message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThreadMessage:
        """Factory method: create from LangChain message."""
        return cls(
            thread_id=thread_id,
            content=base_message,
            metadata=metadata or {},
            is_spilled=False
        )

    def unwrap_to_langchain(self) -> BaseMessage:
        """Unwrap to LangChain message (non-spilled only)."""
        if self.is_spilled:
            raise ValueError("Cannot unwrap spilled message to LangChain")
        return self.content

    def get_marker_info(self) -> Optional[Dict[str, Any]]:
        """Parse insertion syntax if present, return None if not."""
        if not self.is_spilled:
            return None
        return parse_insertion_syntax(self.content)
```

| Field | Type | Description |
|-------|------|-------------|
| message_id | str | UUID, auto-generated, immutable |
| thread_id | str | Parent thread reference |
| timestamp | float | Unix timestamp, auto-generated |
| is_spilled | bool | Flag for content offloading |
| spill_reference | Optional[SpilledContentReference] | Spill metadata (when spilled) |
| metadata | Dict[str, Any] | Custom fields: token_count, model, role |
| content | Union[str, BaseMessage] | Actual message OR marker string |

**Validation constraints:**
1. Spilled message MUST have spill_reference
2. Spilled message content MUST be insertion syntax string
3. Non-spilled message content MUST be BaseMessage
4. Insertion syntax MUST follow format `[[MARKER:type|metadata_json|reference]]`

### 5.2 SpilledContentReference

Metadata for offloaded large content.

```python
from enum import Enum

class SpillType(Enum):
    """Spill content type categories."""
    MESSAGE_SPILL = "message_spill"
    GENERATED_DATA = "generated_data"
    FUTURE_EXTENSION = "future_extension"

@dataclass
class SpilledContentReference:
    """Reference to spilled/offloaded content."""

    spill_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    spill_type: SpillType
    content_location: str  # File path or storage reference
    content_size: int  # Bytes or tokens
    content_type: str  # Category: tool_response, ai_report, generated_dataset
    content_preview: Optional[str] = None  # Short summary for LLM
    retrieval_hint: str = "use fetch_spilled_content tool with spill_id"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate spill metadata."""
        if self.content_size <= 0:
            raise ValueError("content_size must be positive")
        if not self.content_location:
            raise ValueError("content_location must be non-empty")
```

| Field | Type | Description |
|-------|------|-------------|
| spill_id | str | UUID, auto-generated |
| spill_type | SpillType | Enum: MESSAGE_SPILL, GENERATED_DATA, etc. |
| content_location | str | File path or storage key |
| content_size | int | Positive integer (bytes/tokens) |
| content_type | str | Category string |
| content_preview | Optional[str] | Preview text for LLM |
| retrieval_hint | str | Retrieval instructions |
| metadata | Dict[str, Any] | Additional info |

### 5.3 Memory

Extracted knowledge/experience with explicit message linkage.

```python
class MemoryType(Enum):
    """Memory type categories."""
    SUMMARY = "summary"
    EXPERIENCE_PATTERN = "experience_pattern"
    USER_PREFERENCE = "user_preference"
    FACT = "fact"

@dataclass
class Memory:
    """Extracted memory with traceability."""

    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType
    content: str
    thread_id: str  # Source thread
    related_message_ids: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate memory invariants."""
        # Traceability invariant: related_message_ids MUST be non-empty
        if not self.related_message_ids:
            raise ValueError("Memory must have at least one related_message_id")

        # Relevance score range
        if not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError("relevance_score must be in range [0.0, 1.0]")

        # Content non-empty
        if not self.content:
            raise ValueError("Memory content must be non-empty")
```

| Field | Type | Description |
|-------|------|-------------|
| memory_id | str | UUID, auto-generated |
| memory_type | MemoryType | Enum: summary, experience_pattern, etc. |
| content | str | Memory text, non-empty |
| thread_id | str | Source thread reference |
| related_message_ids | List[str] | Source message IDs, non-empty list |
| relevance_score | float | Range [0.0, 1.0] |
| metadata | Dict[str, Any] | timestamps, tags, access_count |

**Validation constraints:**
1. related_message_ids MUST be non-empty (traceability invariant)
2. relevance_score MUST be in [0.0, 1.0]
3. content MUST be non-empty

### 5.4 Thread

Conversation thread with metadata.

```python
@dataclass
class Thread:
    """Conversation thread."""

    thread_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ThreadMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def __post_init__(self):
        """Validate thread structure."""
        # Message ownership: all messages must have matching thread_id
        for msg in self.messages:
            if msg.thread_id != self.thread_id:
                raise ValueError(f"Message {msg.message_id} has wrong thread_id")

    def update_timestamp(self):
        """Update modified timestamp."""
        self.updated_at = datetime.now().timestamp()
```

| Field | Type | Description |
|-------|------|-------------|
| thread_id | str | UUID, auto-generated |
| messages | List[ThreadMessage] | Ordered message history |
| metadata | Dict[str, Any] | user_id, session_start, status |
| created_at | float | Unix timestamp |
| updated_at | float | Unix timestamp |

**Validation constraints:**
1. All messages MUST have matching thread_id (ownership invariant)

### 5.5 Supporting Structures

**ContextConfig:**

```python
class RetrievalStrategy(Enum):
    """Context retrieval strategies."""
    RECENT_FIRST = "recent_first"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID = "hybrid"

@dataclass
class ContextConfig:
    """Configuration for context construction."""

    max_tokens: int = 4000  # Default context window
    sections: List[str] = field(default_factory=lambda: [
        "recent_history",
        "relevant_memories",
        "experiences",
        "system_prompt"
    ])
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.RECENT_FIRST
    template_format: Dict[str, str] = field(default_factory=lambda: {
        "recent_history": "### Recent Conversation\n{content}",
        "relevant_memories": "### Relevant Memories\n{content}",
        "experiences": "### Experience Patterns\n{content}",
        "system_prompt": "{content}"
    })
```

**AutomationConfig:**

```python
@dataclass
class AutomationConfig:
    """Automation trigger configuration."""

    auto_spill_messages: bool = True
    spill_threshold_bytes: int = 10000  # 10KB

    auto_distill: bool = False  # Default: disabled
    distill_trigger: str = "message_count"  # message_count, session_end, manual
    distill_threshold: int = 10  # Every N messages

    auto_store_memories: bool = True
    auto_link_memories: bool = True
```

---

## 6. Interface Contracts

### 6.1 Insertion Syntax Utilities

**Parser contract:**

```python
def parse_insertion_syntax(marker: str) -> Dict[str, Any]:
    """
    Parse insertion syntax marker into structured dict.

    Args:
        marker: Insertion syntax string [[MARKER:type|metadata_json|reference]]

    Returns:
        Dict with keys: marker_type, spill_type, metadata, reference

    Raises:
        InsertionSyntaxError: If marker format invalid
    """
    # Implementation contract:
    # 1. Validate format: [[...]]
    # 2. Split by '|' into parts: MARKER:type, metadata_json, reference
    # 3. Parse metadata_json with json.loads()
    # 4. Return dict structure

    result = {
        "marker_type": str,  # e.g., "SPILL", "INSERT"
        "type": str,  # e.g., "MESSAGE_SPILL"
        "metadata": Dict[str, Any],
        "reference": str  # e.g., "spill_id=abc123"
    }
    return result
```

| Behavior | Description |
|----------|-------------|
| Format validation | MUST raise InsertionSyntaxError if not `[[...]]` |
| Unknown marker types | MUST NOT reject unknown MARKER:type, return parsed anyway |
| Metadata parsing | MUST use json.loads(), raise InsertionSyntaxError if invalid JSON |
| Reference parsing | MUST return reference string as-is (no parsing logic) |

**Builder contract:**

```python
def build_insertion_syntax(
    marker_type: str,
    type_str: str,
    metadata: Dict[str, Any],
    reference: str
) -> str:
    """
    Build insertion syntax marker from components.

    Args:
        marker_type: Marker category (SPILL, INSERT, LINK)
        type_str: Type string (MESSAGE_SPILL, GENERATED_DATA)
        metadata: Metadata dict (will be JSON encoded)
        reference: Reference string

    Returns:
        Insertion syntax string [[MARKER:type|metadata_json|reference]]
    """
    # Implementation contract:
    # 1. Format: marker_type:type_str
    # 2. JSON encode metadata
    # 3. Concatenate with '|' separators
    # 4. Wrap in [[...]]
```

---

## 7. Implementation Patterns

### 7.1 LangChain Message Handling Pattern

**Wrapping pattern:**

```python
# Component creates ThreadMessage from LangChain
def add_user_message(thread_id: str, user_input: str) -> ThreadMessage:
    langchain_msg = HumanMessage(content=user_input)
    wrapped_msg = ThreadMessage.create_from_langchain(
        thread_id=thread_id,
        base_message=langchain_msg,
        metadata={"role": "user"}
    )
    return wrapped_msg
```

**Unwrapping pattern:**

```python
# Facade returns LangChain messages to user
def get_thread_history(thread_id: str) -> List[BaseMessage]:
    thread_messages = backend.get_messages(thread_id)
    langchain_messages = []
    for tm in thread_messages:
        if tm.is_spilled:
            # Return marker string wrapped in custom message type
            # or skip spilled messages based on include_spilled_markers flag
            continue
        else:
            langchain_messages.append(tm.unwrap_to_langchain())
    return langchain_messages
```

### 7.2 Spill Creation Pattern

```python
def spill_large_content(message: ThreadMessage, backend: StorageBackend) -> ThreadMessage:
    """
    Spill message content and return new ThreadMessage with marker.

    Steps:
    1. Extract content from message
    2. Create SpilledContentReference via backend.spill_content()
    3. Build insertion syntax marker
    4. Create new ThreadMessage with is_spilled=True
    """
    content = message.unwrap_to_langchain().content

    # Backend handles storage
    spill_ref = backend.spill_content(
        content=content,
        spill_metadata={
            "content_type": "ai_report",
            "size": len(content)
        }
    )

    # Build marker
    marker = build_insertion_syntax(
        marker_type="SPILL",
        type_str=SpillType.MESSAGE_SPILL.value,
        metadata={
            "content_type": spill_ref.content_type,
            "preview": spill_ref.content_preview,
            "size": spill_ref.content_size
        },
        reference=f"spill_id={spill_ref.spill_id}"
    )

    # Create spilled ThreadMessage
    spilled_message = ThreadMessage(
        message_id=message.message_id,  # Preserve identity
        thread_id=message.thread_id,
        timestamp=message.timestamp,
        is_spilled=True,
        spill_reference=spill_ref,
        metadata=message.metadata,
        content=marker
    )

    return spilled_message
```

### 7.3 Error Handling

**Domain validation errors:**

| Error Category | Handling Approach |
|----------------|-------------------|
| **ValidationError** | Raised in __post_init__ when invariants violated. User must fix input data. |
| **InsertionSyntaxError** | Raised when marker format invalid. Parser fails on malformed syntax. |
| **MessageTypeError** | Raised when content type mismatch (spilled expects str, non-spilled expects BaseMessage). |
| **SpillConsistencyError** | Raised when spill_reference missing for spilled message. |

**Pattern:**

```python
try:
    memory = Memory(
        memory_type=MemoryType.SUMMARY,
        content="Conversation summary",
        thread_id="thread_123",
        related_message_ids=[]  # Violates invariant
    )
except ValueError as e:
    # Validation error, invariant violated
    print(f"Memory creation failed: {e}")
```

---

## 8. Examples

### 8.1 Creating ThreadMessage from LangChain

```python
from langchain.schema import AIMessage

# Create AI response message
ai_msg = AIMessage(content="The answer is 42.")
wrapped = ThreadMessage.create_from_langchain(
    thread_id="thread_abc",
    base_message=ai_msg,
    metadata={"model": "gpt-4", "token_count": 10}
)

print(wrapped.message_id)  # UUID
print(wrapped.is_spilled)  # False
print(wrapped.unwrap_to_langchain())  # AIMessage instance
```

### 8.2 Spilling Large Tool Response

```python
from langchain.schema import ToolMessage

# Large tool response
tool_msg = ToolMessage(content="API returned 50000 records...")
large_msg = ThreadMessage.create_from_langchain(
    thread_id="thread_xyz",
    base_message=tool_msg
)

# Check size threshold
if len(large_msg.unwrap_to_langchain().content) > 10000:
    # Spill to backend
    spilled = spill_large_content(large_msg, backend)

    print(spilled.is_spilled)  # True
    print(spilled.content)  # [[SPILL:MESSAGE_SPILL|{"preview":"API returned 50000..."}|spill_id=...]]
```

### 8.3 Creating Memory with Traceability

```python
# Extract memory from conversation
memory = Memory(
    memory_type=MemoryType.USER_PREFERENCE,
    content="User prefers concise responses",
    thread_id="thread_abc",
    related_message_ids=["msg_1", "msg_5", "msg_12"],  # Source messages
    relevance_score=0.85
)

print(memory.memory_id)  # UUID
print(memory.related_message_ids)  # ["msg_1", "msg_5", "msg_12"]  # Traceability
```

### 8.4 Parsing Insertion Syntax

```python
marker = "[[SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123]]"

parsed = parse_insertion_syntax(marker)

print(parsed["marker_type"])  # "SPILL"
print(parsed["type"])  # "MESSAGE_SPILL"
print(parsed["metadata"]["content_type"])  # "tool_response"
print(parsed["reference"])  # "spill_id=abc123"
```

---

## 9. Relationship to Other RFCs

This implementation interface builds on:

* **[RFC-001-world-view](RFC-001-world-view.md)**: Conceptual Design - Defines Thread, Memory, ThreadMessage, SpilledContentReference as abstractions. This RFC provides concrete type definitions.

* **[RFC-002-core-architecture](RFC-002-core-architecture.md)**: Architecture Design - Defines abstract schemas (field names, high-level types). This RFC specifies exact Python types and validation.

Enables:

* **[RFC-004-storage-backend](RFC-004-storage-backend.md)**: Backend operations use these domain models as parameters and return types.

* **[RFC-005-facade-interface](RFC-005-facade-interface.md)**: Facade API accepts/returns these domain models and LangChain messages.

---

## 10. Open Questions

1. **UUID generation strategy:** Should message_id/thread_id use uuid.uuid4() (random) or uuid.uuid5() (namespace-based deterministic)? Random is collision-resistant; deterministic enables reproducibility in tests.

2. **Metadata field standardization:** Should metadata Dict have predefined keys (token_count, model) with Optional types, or remain fully flexible? Standardization aids validation; flexibility enables customization.

3. **Insertion syntax escaping:** If metadata JSON contains special characters (|, [[), how to escape? Should parser handle escaped delimiters or restrict metadata content?

4. **LangChain message type detection:** How to determine message role (user/ai/system/tool) from BaseMessage type? Use isinstance checks or message.type field?

5. **Frozen vs mutable dataclasses:** Should models use frozen=True (immutable) or allow updates (e.g., Memory.access_count increment)? Immutable prevents accidental modification; mutable enables dynamic updates.

---

## 11. Conclusion

This RFC defines precise Python type definitions for core domain models, bridging conceptual abstractions with implementation contracts. Key features: ThreadMessage with LangChain integration and spill support, Memory with traceability enforcement, SpilledContentReference for offloaded content metadata, and insertion syntax utilities for parsing/building markers.

Validation constraints enforce system invariants at model creation time, ensuring compliance before data enters components. The models provide clear factory methods (create_from_langchain) and conversion methods (unwrap_to_langchain) for LangChain integration. Insertion syntax utilities enable extensible marker handling for spill and future scenarios.

> **Interface principle:** Domain models define the contract between layers—precise types, validated invariants, clear conversion methods—enabling type-safe component interaction.