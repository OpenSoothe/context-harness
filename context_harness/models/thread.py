"""Thread and ThreadMessage models."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid

from langchain_core.messages import BaseMessage

from context_harness.models.spill import SpilledContentReference
from context_harness.models.insertion_syntax import parse_insertion_syntax


@dataclass
class ThreadMessage:
    """Message wrapper with harness metadata and spill support."""

    # Required fields first
    thread_id: str
    content: Union[str, BaseMessage]  # String for marker, BaseMessage for actual content

    # Optional/default fields after
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    is_spilled: bool = False
    spill_reference: Optional[SpilledContentReference] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

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

    @classmethod
    def create_from_langchain(
        cls,
        thread_id: str,
        base_message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThreadMessage:
        """
        Factory method: create from LangChain message.

        Args:
            thread_id: Thread identifier
            base_message: LangChain BaseMessage
            metadata: Optional custom metadata

        Returns:
            ThreadMessage wrapping the LangChain message
        """
        return cls(
            thread_id=thread_id,
            content=base_message,
            metadata=metadata or {},
            is_spilled=False
        )

    def unwrap_to_langchain(self) -> BaseMessage:
        """
        Unwrap to LangChain message (non-spilled only).

        Returns:
            LangChain BaseMessage

        Raises:
            ValueError: If message is spilled
        """
        if self.is_spilled:
            raise ValueError("Cannot unwrap spilled message to LangChain")
        return self.content

    def get_marker_info(self) -> Optional[Dict[str, Any]]:
        """
        Parse insertion syntax if present, return None if not.

        Returns:
            Dict with marker info or None if not spilled
        """
        if not self.is_spilled:
            return None
        return parse_insertion_syntax(self.content)


@dataclass
class Thread:
    """Conversation thread."""

    # All fields have defaults, so order doesn't matter as much
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