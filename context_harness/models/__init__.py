"""Domain models for context harness."""

from context_harness.models.base import (
    MemoryType,
    SpillType,
    RetrievalStrategy,
    InsertionSyntaxError,
    ValidationError,
)
from context_harness.models.thread import Thread, ThreadMessage
from context_harness.models.memory import Memory
from context_harness.models.spill import SpilledContentReference
from context_harness.models.config import ContextConfig, AutomationConfig
from context_harness.models.insertion_syntax import (
    parse_insertion_syntax,
    build_insertion_syntax,
)

__all__ = [
    "Thread",
    "ThreadMessage",
    "Memory",
    "MemoryType",
    "SpilledContentReference",
    "SpillType",
    "ContextConfig",
    "AutomationConfig",
    "RetrievalStrategy",
    "parse_insertion_syntax",
    "build_insertion_syntax",
    "InsertionSyntaxError",
    "ValidationError",
]