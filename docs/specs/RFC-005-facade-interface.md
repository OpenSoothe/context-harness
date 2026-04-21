# RFC-005: Facade Interface

**Status**: Draft
**Authors**: Xiaming Chen
**Created**: 2026-04-21
**Last Updated**: 2026-04-21
**Depends on**: [RFC-001-world-view](RFC-001-world-view.md), [RFC-002-core-architecture](RFC-002-core-architecture.md), [RFC-003-domain-models](RFC-003-domain-models.md), [RFC-004-storage-backend](RFC-004-storage-backend.md)
**Supersedes**: ---
**Kind**: Implementation Interface Design

---

## 1. Abstract

This RFC defines the ContextHarness facade public API—the single entry point for users of the context-harness library. The facade orchestrates core components (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder) with a simple interface for common use cases while exposing component access for advanced customization. LangChain message integration, configurable automation, spilled content retrieval, and component orchestration are the key responsibilities. The facade ensures architectural invariants (component independence, orchestration centralization) while providing an intuitive user API.

---

## 2. Scope and Non-Goals

### 2.1 Scope

This RFC defines:

* ContextHarness class public API method signatures
* Constructor parameters and initialization behavior
* Thread management API (create, add_message, get_history)
* Memory management API (save, search, retrieve)
* Experience distillation API (manual and automated triggers)
* Context construction API (build context for queries)
* Spilled content retrieval API and LangChain Tool integration
* Automation configuration methods
* Component accessor methods for advanced users
* Error handling and exception types
* Method parameter types, return types, and validation

### 2.2 Non-Goals

This RFC does **not** define:

* Internal orchestration logic implementation details
* Component internal implementations (see component classes)
* LangChain Tool implementation specifics beyond interface contract
* Performance optimization patterns (caching strategies, async patterns)
* Testing strategies or API usage patterns beyond examples

---

## 3. Background & Motivation

**Why facade pattern:** Users need simple API for common use cases:
- Create thread, add messages, build context
- Minimal configuration, quick onboarding
- No need to understand component interactions

But advanced users need component access for customization:
- Swap distillation strategy
- Custom backend implementation
- Fine-grained control over automation

Facade provides both: simple API by default, component access when needed.

**Why LangChain integration:** Target users use LangChain. Facade must:
- Accept LangChain BaseMessage as input
- Return LangChain messages from get_history
- Provide LangChain Tool for spill retrieval
- Handle wrapping/unwrapping transparently

**Why automation configuration:** Default behavior should not surprise users:
- Automation triggers disabled by default
- Users explicitly enable auto-spill, auto-distill
- Configuration methods for trigger thresholds

**Why component access:** Advanced users need customization without violating architecture:
- Facade returns component instances (not restricted interfaces)
- Users call component methods directly for fine control
- Architectural invariant: components never call each other, but facade orchestration is bypassed intentionally by advanced users

---

## 4. Naming Conventions

| Pattern | Purpose | Example |
|---------|---------|---------|
| `create_{entity}` | Creation method naming | `create_thread()`, `create_memory()` |
| `add_{entity}` | Append/addition naming | `add_message()` |
| `get_{entity}` | Retrieval naming | `get_thread_history()`, `get_context_messages()` |
| `build_context_for_query` | Context construction naming | `build_context_for_query(query, thread_id)` |
| `distill_experiences` | Process method naming | `distill_experiences(thread_id)` |
| `enable/disable_auto_{feature}` | Automation naming | `enable_auto_distill()` |
| `provide_{name}_tool` | Tool factory naming | `provide_spill_retrieval_tool()` |
| `get_{component}_manager` | Component accessor naming | `get_chat_history_manager()` |

---

## 5. Data Structures

### 5.1 ContextHarness Class

```python
from typing import Optional, List, Dict, Any
from langchain.schema import BaseMessage
from langchain.tools import Tool

class ContextHarness:
    """
    Main facade for context-harness library.

    Provides:
    - Simple API for common use cases (thread, memory, context)
    - Configurable automation for component interactions
    - Access to individual components for advanced customization
    - LangChain message integration
    """

    def __init__(
        self,
        backend: Optional[StorageBackend] = None,
        automation_config: Optional[AutomationConfig] = None,
        context_config: Optional[ContextConfig] = None,
        distillation_config: Optional[DistillationConfig] = None
    ):
        """
        Initialize ContextHarness.

        Args:
            backend: StorageBackend instance (default: FileBackend)
            automation_config: Automation trigger configuration (default: disabled)
            context_config: Context construction configuration
            distillation_config: Distillation strategy configuration

        Behavior:
            - If backend is None, creates FileBackend with default path
            - Initializes core components with backend injection
            - Sets automation_config defaults (all triggers disabled)
            - Validates configuration parameters

        Raises:
            BackendConfigurationError: If backend initialization fails
            ValidationError: If config parameters invalid
        """
        # Implementation contract:
        # 1. Create backend if None (FileBackend)
        # 2. Initialize ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder
        # 3. Set automation_config (default: disabled)
        # 4. Store context_config, distillation_config
```

**Component initialization contract:**

```python
# Internal (not exposed in RFC, but defined for clarity)
self._backend = backend or FileBackend()
self._chat_history_manager = ChatHistoryManager(self._backend)
self._memory_manager = MemoryManager(self._backend)
self._experience_distiller = ExperienceDistiller(self._backend, distillation_config.llm_client)
self._context_builder = ContextBuilder(self._backend, context_config)
self._automation_config = automation_config or AutomationConfig()
```

---

## 6. Interface Contracts

### 6.1 Thread Management API

```python
    def create_thread(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new conversation thread.

        Args:
            metadata: Optional thread metadata (user_id, session_start, etc.)

        Returns:
            thread_id: Unique thread identifier

        Behavior:
            - Creates Thread object with generated thread_id
            - Stores thread via backend.put_thread()
            - Returns thread_id for subsequent operations

        Raises:
            BackendError: If thread creation/storage fails

        Example:
            thread_id = harness.create_thread(metadata={"user_id": "user123"})
        """

    def add_message(
        self,
        thread_id: str,
        message: BaseMessage,
        auto_spill: bool = True
    ) -> ThreadMessage:
        """
        Add message to thread with automatic spill detection.

        Args:
            thread_id: Thread identifier
            message: LangChain BaseMessage (HumanMessage, AIMessage, etc.)
            auto_spill: Enable automatic spill for large content (default: True)

        Returns:
            ThreadMessage: Wrapped message (may be spilled if large)

        Behavior:
            - Wraps LangChain message in ThreadMessage
            - Checks message size against automation_config.spill_threshold_bytes
            - If auto_spill=True and size > threshold:
                - Spills content via ChatHistoryManager
                - Returns ThreadMessage with insertion syntax marker
            - Appends message to thread via ChatHistoryManager
            - Checks automation triggers:
                - If auto_distill enabled and message_count reached threshold:
                    - Triggers ExperienceDistiller.distill_thread()
                    - If auto_store_memories: stores via MemoryManager

        Raises:
            ThreadNotFoundError: If thread_id invalid
            BackendError: If message append fails
            ValidationError: If message structure invalid

        Example:
            from langchain.schema import HumanMessage, AIMessage

            harness.add_message(thread_id, HumanMessage("Hello"))
            harness.add_message(thread_id, AIMessage("Hi! How can I help?"))
        """

    def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        unwrap_langchain: bool = True
    ) -> List[BaseMessage]:
        """
        Get conversation history as LangChain messages.

        Args:
            thread_id: Thread identifier
            limit: Optional max number of messages
            unwrap_langchain: Return LangChain messages (default: True)

        Returns:
            List of BaseMessage (spilled messages skipped if unwrap_langchain=True)

        Behavior:
            - Retrieves messages via ChatHistoryManager
            - If unwrap_langchain=True:
                - Unwraps ThreadMessage to BaseMessage
                - Skips spilled messages (cannot unwrap to LangChain)
            - If unwrap_langchain=False:
                - Returns ThreadMessage objects (includes spilled with markers)

        Raises:
            ThreadNotFoundError: If thread_id invalid
            BackendError: If retrieval fails

        Example:
            history = harness.get_thread_history(thread_id, limit=10)
            # [HumanMessage("Hello"), AIMessage("Hi!"), ...]
        """
```

### 6.2 Memory Management API

```python
    def save_memory(
        self,
        memory: Memory,
        auto_link: bool = True
    ) -> None:
        """
        Save memory with optional auto-linking to recent thread messages.

        Args:
            memory: Memory object to store
            auto_link: Link to recent thread messages if related_message_ids empty (default: True)

        Behavior:
            - If auto_link=True and memory.related_message_ids is empty:
                - Links to last N messages from thread (N configurable)
            - Stores memory via MemoryManager

        Raises:
            ValidationError: If memory structure invalid (missing traceability)
            BackendError: If storage fails

        Example:
            memory = Memory(
                memory_type=MemoryType.USER_PREFERENCE,
                content="User prefers detailed explanations",
                thread_id=thread_id
            )
            harness.save_memory(memory)
        """

    def search_memories(
        self,
        query: Optional[str] = None,
        thread_id: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> List[Memory]:
        """
        Search memories across threads with filters.

        Args:
            query: Optional search query string
            thread_id: Optional filter by thread
            memory_type: Optional filter by type (summary, experience_pattern)

        Returns:
            List of matching Memory objects (ranked by relevance_score)

        Behavior:
            - Searches via MemoryManager
            - Applies filters (thread_id, memory_type)
            - Returns memories with highest relevance_score first

        Raises:
            BackendError: If search fails

        Example:
            memories = harness.search_memories(query="pricing", thread_id=thread_id)
        """

    def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Unique memory identifier

        Returns:
            Memory object if exists, None otherwise

        Raises:
            BackendError: If retrieval fails

        Example:
            memory = harness.retrieve_memory("mem_abc123")
        """
```

### 6.3 Experience Distillation API

```python
    def distill_experiences(
        self,
        thread_id: str,
        auto_store: bool = True
    ) -> List[Memory]:
        """
        Distill thread into memories (manual trigger).

        Args:
            thread_id: Thread to distill
            auto_store: Auto-store distilled memories (default: True)

        Returns:
            List of distilled Memory objects (summaries + patterns)

        Behavior:
            - Calls ExperienceDistiller.distill_thread()
            - If auto_store=True: stores via MemoryManager
            - Returns memories for inspection (even if auto-stored)

        Raises:
            ThreadNotFoundError: If thread_id invalid
            BackendError: If distillation or storage fails

        Example:
            memories = harness.distill_experiences(thread_id)
            # List[Memory] with summaries and experience patterns
        """

    def trigger_distillation(
        self,
        thread_id: str,
        trigger_type: str = "manual"
    ) -> None:
        """
        Trigger distillation based on automation config.

        Args:
            thread_id: Thread to distill
            trigger_type: Trigger type (manual, message_count, session_end)

        Behavior:
            - Checks automation_config if trigger enabled for trigger_type
            - Calls distill_experiences() if enabled
            - No explicit return (automation-driven)

        Raises:
            ThreadNotFoundError: If thread_id invalid
            BackendError: If distillation fails

        Example:
            harness.trigger_distillation(thread_id, trigger_type="session_end")
        """
```

### 6.4 Context Construction API

```python
    def build_context_for_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        include_history: bool = True,
        include_memories: bool = True,
        include_experiences: bool = True
    ) -> str:
        """
        Build context string for new query with intelligent selection.

        Args:
            query: New user query
            thread_id: Optional thread for history retrieval
            include_history: Include recent thread messages (default: True)
            include_memories: Include relevant memories (default: True)
            include_experiences: Include experience patterns (default: True)

        Returns:
            Formatted context string with sections and spill markers

        Behavior:
            - Calls ContextBuilder.build_context()
            - Selects relevant messages based on retrieval_strategy
            - Selects relevant memories based on query
            - Formats using template (sections ordered by context_config)
            - Preserves insertion syntax markers for spilled content

        Raises:
            BackendError: If retrieval fails

        Example:
            context = harness.build_context_for_query(
                query="What's the pricing?",
                thread_id=thread_id
            )
            # Context string with recent history, relevant memories
        """

    def get_context_messages(
        self,
        query: str,
        thread_id: Optional[str] = None
    ) -> List[BaseMessage]:
        """
        Get context as LangChain messages ready for LLM invocation.

        Args:
            query: New user query
            thread_id: Optional thread for history

        Returns:
            List of BaseMessage (context formatted as messages)

        Behavior:
            - Builds context string (same as build_context_for_query)
            - Wraps context sections as LangChain messages
            - Returns list ready for LLM invocation

        Raises:
            BackendError: If context construction fails

        Example:
            context_messages = harness.get_context_messages(query, thread_id)
            # [SystemMessage(context), HumanMessage(query)]
        """
```

### 6.5 Spilled Content Retrieval API

```python
    def retrieve_spilled_content(self, spill_id: str) -> Any:
        """
        Retrieve spilled content by ID.

        Args:
            spill_id: Unique spill identifier

        Returns:
            Original spilled content (text, data, etc.)

        Raises:
            SpillContentNotFoundError: If spill_id invalid
            BackendError: If retrieval fails

        Example:
            content = harness.retrieve_spilled_content("spill_abc123")
        """

    def provide_spill_retrieval_tool(self) -> Tool:
        """
        Return LangChain Tool for LLM to fetch spilled content.

        Returns:
            LangChain Tool instance with spill retrieval function

        Behavior:
            - Creates Tool with name "fetch_spilled_content"
            - Tool description explains usage for LLM
            - Tool implementation calls retrieve_spilled_content()

        Example:
            tool = harness.provide_spill_retrieval_tool()
            # Tool: "fetch_spilled_content(spill_id: str) -> str"
            # LLM can use this tool when seeing [[SPILL:...]] markers
        """
```

### 6.6 Automation Configuration API

```python
    def configure_automation(self, config: AutomationConfig) -> None:
        """
        Set automation triggers and behaviors.

        Args:
            config: AutomationConfig object

        Behavior:
            - Replaces current automation_config
            - Applies to subsequent operations (add_message, etc.)

        Raises:
            ValidationError: If config invalid

        Example:
            config = AutomationConfig(
                auto_spill_messages=True,
                spill_threshold_bytes=10000,
                auto_distill=True,
                distill_threshold=20
            )
            harness.configure_automation(config)
        """

    def enable_auto_distill(
        self,
        trigger: str = "message_count",
        threshold: int = 10
    ) -> None:
        """
        Enable automatic distillation every N messages.

        Args:
            trigger: Trigger type (message_count, session_end)
            threshold: Message count threshold

        Behavior:
            - Sets automation_config.auto_distill = True
            - Sets distill_trigger and distill_threshold
            - Auto-distill activates on subsequent add_message() calls

        Example:
            harness.enable_auto_distill(threshold=15)
        """

    def disable_auto_distill(self) -> None:
        """
        Disable automatic distillation.

        Behavior:
            - Sets automation_config.auto_distill = False
            - Manual distill_experiences() still works

        Example:
            harness.disable_auto_distill()
        """
```

### 6.7 Component Access API (Advanced)

```python
    def get_chat_history_manager(self) -> ChatHistoryManager:
        """
        Access underlying ChatHistoryManager for customization.

        Returns:
            ChatHistoryManager instance

        Warning:
            - Bypasses facade orchestration
            - User must ensure architectural invariants (no cross-component calls)
            - Advanced use only

        Example:
            manager = harness.get_chat_history_manager()
            manager.add_message(thread_id, message)  # Direct call
        """

    def get_memory_manager(self) -> MemoryManager:
        """
        Access underlying MemoryManager.

        Returns:
            MemoryManager instance

        Warning:
            - Bypasses facade orchestration
            - Advanced use only

        Example:
            manager = harness.get_memory_manager()
        """

    def get_experience_distiller(self) -> ExperienceDistiller:
        """
        Access underlying ExperienceDistiller.

        Returns:
            ExperienceDistiller instance

        Warning:
            - Bypasses facade orchestration
            - Advanced use only

        Example:
            distiller = harness.get_experience_distiller()
        """

    def get_context_builder(self) -> ContextBuilder:
        """
        Access underlying ContextBuilder.

        Returns:
            ContextBuilder instance

        Warning:
            - Bypasses facade orchestration
            - Advanced use only

        Example:
            builder = harness.get_context_builder()
        """
```

---

## 7. Implementation Patterns

### 7.1 LangChain Tool Integration Pattern

```python
from langchain.tools import Tool

def provide_spill_retrieval_tool(self) -> Tool:
    """
    Create LangChain Tool for spilled content retrieval.
    """

    def fetch_spilled_content_func(spill_id: str) -> str:
        """Tool function implementation."""
        content = self.retrieve_spilled_content(spill_id)
        return str(content)

    tool = Tool(
        name="fetch_spilled_content",
        description=(
            "Retrieve spilled/offloaded content by spill_id. "
            "Use when seeing [[SPILL:MESSAGE_SPILL|...|spill_id=XYZ]] markers. "
            "Returns full content that was too large to include in context."
        ),
        func=fetch_spilled_content_func
    )

    return tool
```

### 7.2 Automation Trigger Pattern

```python
def add_message(self, thread_id: str, message: BaseMessage, auto_spill: bool = True) -> ThreadMessage:
    """
    Add message with automation checks.
    """

    # Wrap LangChain message
    wrapped_msg = ThreadMessage.create_from_langchain(thread_id, message)

    # Check spill threshold
    if auto_spill and self._automation_config.auto_spill_messages:
        if len(message.content) > self._automation_config.spill_threshold_bytes:
            wrapped_msg = self._chat_history_manager.spill_message_content(wrapped_msg)

    # Append message
    self._chat_history_manager.add_message(thread_id, wrapped_msg)

    # Check distillation trigger
    if self._automation_config.auto_distill:
        thread = self._backend.get_thread({"thread_id": thread_id})
        message_count = thread.metadata.get("message_count", 0)

        if message_count >= self._automation_config.distill_threshold:
            memories = self._experience_distiller.distill_thread(thread_id)

            if self._automation_config.auto_store_memories:
                for memory in memories:
                    self._memory_manager.store_memory(memory)

    return wrapped_msg
```

### 7.3 Context Construction Pattern

```python
def build_context_for_query(
    self,
    query: str,
    thread_id: Optional[str] = None,
    include_history: bool = True,
    include_memories: bool = True,
    include_experiences: bool = True
) -> str:
    """
    Build context by orchestrating ContextBuilder.
    """

    context_config = self._context_config or ContextConfig()

    # Call ContextBuilder
    context = self._context_builder.build_context(
        query=query,
        thread_id=thread_id,
        config=context_config
    )

    return context
```

---

## 8. Examples

### 8.1 Basic Usage Flow

```python
from langchain.schema import HumanMessage, AIMessage
from context_harness import ContextHarness

# Initialize facade
harness = ContextHarness()  # Uses FileBackend by default

# Create thread
thread_id = harness.create_thread(metadata={"user_id": "user123"})

# Add messages
harness.add_message(thread_id, HumanMessage("What's the pricing?"))
harness.add_message(thread_id, AIMessage("We have three tiers: Basic ($10), Pro ($50), Enterprise ($100)"))

# Get history
history = harness.get_thread_history(thread_id)
# [HumanMessage("What's the pricing?"), AIMessage("We have three tiers...")]

# Build context for new query
context = harness.build_context_for_query(
    query="Which tier is best for a small team?",
    thread_id=thread_id
)
# Context includes recent history + relevant memories

# Use with LLM
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI()
response = llm.invoke([
    SystemMessage(context),
    HumanMessage("Which tier is best for a small team?")
])
```

### 8.2 With Automation Enabled

```python
harness = ContextHarness()

# Enable auto-distill every 10 messages
harness.enable_auto_distill(threshold=10)

thread_id = harness.create_thread()

# Add 10 messages (auto-distill triggers after 10th)
for i in range(10):
    harness.add_message(thread_id, HumanMessage(f"Query {i}"))
    harness.add_message(thread_id, AIMessage(f"Response {i}"))

# After 10th message, distillation triggered automatically
# Memories stored automatically

# Search memories (created by auto-distill)
memories = harness.search_memories(thread_id=thread_id)
print(len(memories))  # >0 (auto-distilled)
```

### 8.3 Spilled Content Retrieval

```python
# Large tool response
large_response = ToolMessage(content="API returned 50000 records...")
harness.add_message(thread_id, large_response)  # Auto-spills if > threshold

# Get history (spilled message shows marker)
history = harness.get_thread_history(thread_id, unwrap_langchain=False)
# ThreadMessage with content: [[SPILL:MESSAGE_SPILL|...|spill_id=XYZ]]

# Provide tool to LLM
tool = harness.provide_spill_retrieval_tool()

# LLM can use tool to fetch full content when needed
# Tool: "fetch_spilled_content(spill_id=XYZ) -> full API response"
```

### 8.4 Advanced Customization

```python
# Access component for custom strategy
distiller = harness.get_experience_distiller()

# Use custom distillation (bypass facade)
custom_memories = distiller.distill_messages(
    messages=my_custom_message_list,
    strategy="custom_pattern_extraction"
)

# Store via facade
for memory in custom_memories:
    harness.save_memory(memory)
```

---

## 9. Relationship to Other RFCs

This implementation interface depends on:

* **[RFC-001-world-view](RFC-001-world-view.md)**: Facade orchestration invariant - facade orchestrates components, automation opt-in.

* **[RFC-002-core-architecture](RFC-002-core-architecture.md)**: Interface layer structure - facade resides in Interface layer, orchestrates Core components.

* **[RFC-003-domain-models](RFC-003-domain-models.md)**: Domain model types - facade accepts/returns ThreadMessage, Memory, BaseMessage.

* **[RFC-004-storage-backend](RFC-004-storage-backend.md)**: Backend injection - facade creates/injects backend into components.

All core RFCs complete the architecture from abstraction → architecture → models → backend → facade.

---

## 10. Open Questions

1. **Component accessor warning scope:** Should facade log warnings when users access components directly, or trust users to respect invariants? Warnings prevent accidental invariant violations; trust reduces friction for advanced users.

2. **Automation trigger persistence:** Should automation_config persist across harness instances (stored in backend) or reset on each initialization? Persistence maintains consistent behavior; reset gives explicit control.

3. **Spilled marker handling in history:** When get_thread_history(unwrap_langchain=True) encounters spilled message, should it skip silently, raise warning, or return placeholder message? Skip is silent; warning is explicit; placeholder preserves marker visibility.

4. **Tool naming collision:** If user application already has "fetch_spilled_content" tool, should facade customize tool name or rely on namespace? Customizable name avoids collision; fixed name is predictable.

5. **get_context_messages format:** Should get_context_messages return [SystemMessage(context), HumanMessage(query)] or single SystemMessage with context + query combined? Split messages mirror conversation structure; combined simplifies invocation.

---

## 11. Conclusion

This RFC defines the ContextHarness facade public API—the single entry point that orchestrates core components with simple interface for users while providing component access for advanced customization. Key features: thread management (create, add_message, get_history with LangChain integration), memory management (save, search, retrieve), experience distillation (manual and automated), context construction (intelligent selection, template formatting), spilled content retrieval with LangChain Tool integration, and configurable automation.

The facade ensures architectural invariants: orchestrates components (no cross-component calls), automation is opt-in (no surprising behavior), LangChain integration transparent (wrap/unwrap messages). Component accessors enable advanced users to bypass orchestration for fine-grained control, with implicit trust that users respect architectural constraints. This design balances simplicity for common use cases with power for advanced customization, fulfilling the facade pattern goal.

> **Facade principle:** One entry point orchestrates everything—simple API for users, component access for advanced users, LangChain integration transparent, automation configurable—balancing simplicity and power.