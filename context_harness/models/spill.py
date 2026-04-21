"""Spilled content reference model."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import uuid

from context_harness.models.base import SpillType


@dataclass
class SpilledContentReference:
    """Reference to spilled/offloaded content."""

    # Required fields first (no defaults)
    spill_type: SpillType
    content_location: str  # File path or storage reference
    content_size: int  # Bytes or tokens
    content_type: str  # Category: tool_response, ai_report, generated_dataset

    # Optional/default fields after
    spill_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_preview: Optional[str] = None  # Short summary for LLM
    retrieval_hint: str = "use fetch_spilled_content tool with spill_id"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate spill metadata."""
        if self.content_size <= 0:
            raise ValueError("content_size must be positive")
        if not self.content_location:
            raise ValueError("content_location must be non-empty")