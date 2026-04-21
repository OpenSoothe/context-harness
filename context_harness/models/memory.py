"""Memory model."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import uuid

from context_harness.models.base import MemoryType


@dataclass
class Memory:
    """Extracted memory with traceability."""

    # Required fields first
    memory_type: MemoryType
    content: str
    thread_id: str  # Source thread
    related_message_ids: List[str]  # Must be provided, cannot be empty

    # Optional/default fields after
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
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