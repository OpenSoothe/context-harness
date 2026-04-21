# Context Harness

Standalone context harness library for managing chat thread history, messages, and context construction for AI applications and agents.

## Features

- **Thread Management**: Conversation thread lifecycle with message history
- **Memory Management**: Cross-thread memories with explicit traceability
- **Experience Distillation**: Extract summaries and reusable patterns
- **Context Construction**: Intelligent selection and formatting for new queries
- **Message Spilling**: Automatic offloading of large content with insertion syntax markers
- **LangChain Integration**: Seamless compatibility with LangChain message types

## Installation

```bash
pip install context-harness
```

## Quick Start

```python
from langchain_core.messages import HumanMessage, AIMessage
from context_harness import ContextHarness

# Initialize harness (uses FileBackend by default)
harness = ContextHarness()

# Create thread
thread_id = harness.create_thread(metadata={"user_id": "user123"})

# Add messages
harness.add_message(thread_id, HumanMessage("Hello"))
harness.add_message(thread_id, AIMessage("Hi! How can I help?"))

# Get history
history = harness.get_thread_history(thread_id)

# Build context for new query
context = harness.build_context_for_query("What's the pricing?", thread_id)
```

## Architecture

Three-layer architecture:
- **Interface Layer**: ContextHarness facade for simple API
- **Core Layer**: Domain components (ChatHistoryManager, MemoryManager, ExperienceDistiller, ContextBuilder)
- **Data Layer**: StorageBackend abstraction with FileBackend default

## Documentation

See `docs/specs/` for RFC specifications and `docs/impl/` for implementation guides.

## License

MIT License - see LICENSE file for details.

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/
```

## Status

- ✅ RFC-001: World View (Conceptual Design)
- ✅ RFC-002: Core Architecture (Architecture Design)
- ✅ RFC-003: Domain Models (Implementation Interface Design) - **IMPLEMENTED**
- 🔄 RFC-004: Storage Backend (Implementation Interface Design)
- 🔄 RFC-005: Facade Interface (Implementation Interface Design)
Harnessing agentic context
