"""Context Harness - Standalone context management library for AI applications."""

__version__ = "0.1.0"

from context_harness.facade import ContextHarness
from context_harness.models import (
    Thread,
    ThreadMessage,
    Memory,
    MemoryType,
    SpilledContentReference,
    SpillType,
    ContextConfig,
    AutomationConfig,
    RetrievalStrategy,
    parse_insertion_syntax,
    build_insertion_syntax,
    InsertionSyntaxError,
)

__all__ = [
    "ContextHarness",
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
]