"""Test ContextHarness facade thread operations."""

import pytest
import tempfile

from langchain_core.messages import HumanMessage, AIMessage

from context_harness import ContextHarness
from context_harness.backend import FileBackend


class TestFacadeThreads:
    """Test ContextHarness thread management."""

    def test_create_thread(self):
        """Test create_thread returns thread_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread(metadata={"user_id": "user123"})

            assert thread_id is not None
            assert isinstance(thread_id, str)

    def test_add_message_human(self):
        """Test add_message with HumanMessage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            result = harness.add_message(thread_id, HumanMessage("Hello"))

            assert result is not None
            assert result.thread_id == thread_id
            assert result.is_spilled == False

    def test_add_message_ai(self):
        """Test add_message with AIMessage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            result = harness.add_message(thread_id, AIMessage("Hi there!"))

            assert result.thread_id == thread_id
            assert result.is_spilled == False

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Hello"))
            harness.add_message(thread_id, AIMessage("Hi!"))
            harness.add_message(thread_id, HumanMessage("How are you?"))

            history = harness.get_thread_history(thread_id)
            assert len(history) == 3

    def test_get_thread_history(self):
        """Test get_thread_history returns LangChain messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Hello"))
            harness.add_message(thread_id, AIMessage("Hi!"))

            history = harness.get_thread_history(thread_id)

            assert len(history) == 2
            assert isinstance(history[0], HumanMessage)
            assert isinstance(history[1], AIMessage)

    def test_get_thread_history_with_limit(self):
        """Test get_thread_history with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            for i in range(10):
                harness.add_message(thread_id, HumanMessage(f"Msg {i}"))

            history = harness.get_thread_history(thread_id, limit=5)
            assert len(history) == 5

    def test_get_thread_history_unwrap_disabled(self):
        """Test get_thread_history with unwrap_langchain=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Test"))

            history = harness.get_thread_history(thread_id, unwrap_langchain=False)

            # Returns ThreadMessage objects
            assert len(history) == 1
            assert hasattr(history[0], 'message_id')
            assert hasattr(history[0], 'thread_id')

    def test_thread_metadata_preserved(self):
        """Test thread metadata is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread(
                metadata={"user_id": "user123", "session": "session_1"}
            )

            # Retrieve thread
            thread = harness._backend.get_thread({"thread_id": thread_id})
            assert thread.metadata["user_id"] == "user123"
            assert thread.metadata["session"] == "session_1"