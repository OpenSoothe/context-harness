"""ContextHarness facade - main entry point for the library."""

from typing import Optional, List, Dict, Any

from langchain_core.messages import BaseMessage
from langchain_core.tools import Tool

from context_harness.backend import StorageBackend, FileBackend
from context_harness.models import (
    Thread,
    ThreadMessage,
    Memory,
    AutomationConfig,
    ContextConfig,
)
from context_harness.components import (
    ChatHistoryManager,
    MemoryManager,
    ExperienceDistiller,
    ContextBuilder,
)


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
        context_config: Optional[ContextConfig] = None
    ):
        """
        Initialize ContextHarness.

        Args:
            backend: StorageBackend instance (default: FileBackend)
            automation_config: Automation trigger configuration (default: disabled)
            context_config: Context construction configuration

        Raises:
            BackendConfigurationError: If backend initialization fails
        """
        # Create backend if None
        if backend is None:
            backend = FileBackend()

        # Store backend
        self._backend = backend

        # Initialize components
        self._chat_history_manager = ChatHistoryManager(
            backend,
            spill_threshold=automation_config.spill_threshold_bytes if automation_config else 10000
        )
        self._memory_manager = MemoryManager(backend)
        self._experience_distiller = ExperienceDistiller(backend)
        self._context_builder = ContextBuilder(backend, context_config)

        # Set automation config
        self._automation_config = automation_config or AutomationConfig()

    # === Thread Management ===

    def create_thread(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new thread.

        Args:
            metadata: Optional thread metadata

        Returns:
            thread_id: Unique thread identifier
        """
        thread = self._chat_history_manager.create_thread(metadata)
        return thread.thread_id

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

        Raises:
            BackendError: If message append fails
        """
        # Add message via ChatHistoryManager
        wrapped_msg = self._chat_history_manager.add_message(
            thread_id, message, auto_spill
        )

        # Check automation triggers
        if self._automation_config.auto_distill:
            # Check message count threshold
            thread = self._backend.get_thread({"thread_id": thread_id})
            if thread:
                # Get message count from thread messages
                messages = self._backend.get_messages({"thread_id": thread_id})
                message_count = len(messages)

                if message_count >= self._automation_config.distill_threshold:
                    self.trigger_distillation(thread_id, "message_count")

        return wrapped_msg

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

        Raises:
            BackendError: If retrieval fails
        """
        # Get messages from backend
        messages = self._backend.get_messages({"thread_id": thread_id}, limit=limit)

        if unwrap_langchain:
            # Unwrap to LangChain messages, skip spilled
            langchain_messages = []
            for msg in messages:
                if not msg.is_spilled:
                    langchain_messages.append(msg.unwrap_to_langchain())

            return langchain_messages
        else:
            return messages

    # === Memory Management ===

    def save_memory(
        self,
        memory: Memory,
        auto_link: bool = True
    ) -> None:
        """
        Save memory with optional auto-linking to recent thread messages.

        Args:
            memory: Memory object to store
            auto_link: Link to recent thread messages if empty (default: True)

        Raises:
            BackendError: If storage fails
        """
        # Auto-link to recent messages if empty
        if auto_link and not memory.related_message_ids:
            # Get recent messages from thread
            messages = self._backend.get_messages(
                {"thread_id": memory.thread_id},
                limit=5
            )
            if messages:
                memory.related_message_ids = [msg.message_id for msg in messages]

        # Store memory
        self._memory_manager.store_memory(memory)

    def search_memories(
        self,
        query: Optional[str] = None,
        thread_id: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> List[Memory]:
        """
        Search memories across threads.

        Args:
            query: Optional search query string
            thread_id: Optional filter by thread
            memory_type: Optional filter by type

        Returns:
            List of matching Memory objects (ranked by relevance)
        """
        return self._memory_manager.search_memories(query, thread_id, memory_type)

    # === Experience Distillation ===

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
            List of distilled Memory objects

        Raises:
            BackendError: If distillation fails
        """
        # Distill thread
        memories = self._experience_distiller.distill_thread(thread_id)

        # Auto-store if enabled
        if auto_store:
            for memory in memories:
                self.save_memory(memory, auto_link=False)

        return memories

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

        Raises:
            BackendError: If distillation fails
        """
        # Check if trigger enabled
        if self._automation_config.auto_distill:
            # Check trigger type matches config
            if trigger_type == self._automation_config.distill_trigger or trigger_type == "manual":
                self.distill_experiences(thread_id)

    # === Context Construction ===

    def build_context_for_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        include_history: bool = True,
        include_memories: bool = True,
        include_experiences: bool = True
    ) -> str:
        """
        Build context string for new query.

        Args:
            query: New user query
            thread_id: Optional thread for history retrieval
            include_history: Include recent thread messages (default: True)
            include_memories: Include relevant memories (default: True)
            include_experiences: Include experience patterns (default: True)

        Returns:
            Formatted context string with spill markers
        """
        # Build context via ContextBuilder
        return self._context_builder.build_context(query, thread_id)

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
        """
        from langchain_core.messages import SystemMessage, HumanMessage

        # Build context string
        context_str = self.build_context_for_query(query, thread_id)

        # Wrap as messages
        messages = [
            SystemMessage(content=context_str),
            HumanMessage(content=query)
        ]

        return messages

    # === Spilled Content Retrieval ===

    def retrieve_spilled_content(self, spill_id: str) -> Any:
        """
        Retrieve spilled content by ID.

        Args:
            spill_id: Unique spill identifier

        Returns:
            Original spilled content

        Raises:
            SpillContentNotFoundError: If spill_id invalid
        """
        return self._backend.retrieve_spilled_content(spill_id)

    def provide_spill_retrieval_tool(self) -> Tool:
        """
        Return LangChain Tool for LLM to fetch spilled content.

        Returns:
            LangChain Tool instance
        """
        def fetch_spilled_content_func(spill_id: str) -> str:
            """Tool function to retrieve spilled content."""
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

    # === Automation Configuration ===

    def configure_automation(self, config: AutomationConfig) -> None:
        """
        Set automation triggers and behaviors.

        Args:
            config: AutomationConfig object
        """
        self._automation_config = config

        # Update ChatHistoryManager spill threshold
        if self._chat_history_manager:
            self._chat_history_manager._spill_threshold = config.spill_threshold_bytes

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
        """
        self._automation_config.auto_distill = True
        self._automation_config.distill_trigger = trigger
        self._automation_config.distill_threshold = threshold

    def disable_auto_distill(self) -> None:
        """Disable automatic distillation."""
        self._automation_config.auto_distill = False

    # === Component Access (Advanced) ===

    def get_chat_history_manager(self) -> ChatHistoryManager:
        """
        Access underlying ChatHistoryManager for customization.

        Returns:
            ChatHistoryManager instance

        Warning:
            Bypasses facade orchestration. Advanced use only.
        """
        return self._chat_history_manager

    def get_memory_manager(self) -> MemoryManager:
        """
        Access underlying MemoryManager.

        Returns:
            MemoryManager instance

        Warning:
            Bypasses facade orchestration. Advanced use only.
        """
        return self._memory_manager

    def get_experience_distiller(self) -> ExperienceDistiller:
        """
        Access underlying ExperienceDistiller.

        Returns:
            ExperienceDistiller instance

        Warning:
            Bypasses facade orchestration. Advanced use only.
        """
        return self._experience_distiller

    def get_context_builder(self) -> ContextBuilder:
        """
        Access underlying ContextBuilder.

        Returns:
            ContextBuilder instance

        Warning:
            Bypasses facade orchestration. Advanced use only.
        """
        return self._context_builder