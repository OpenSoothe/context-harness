"""Configuration structures."""

from dataclasses import dataclass, field
from typing import Dict, List

from context_harness.models.base import RetrievalStrategy


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