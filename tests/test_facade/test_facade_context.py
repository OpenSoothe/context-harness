"""Test ContextHarness facade context construction."""

import pytest
import tempfile

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from context_harness import ContextHarness
from context_harness.backend import FileBackend


class TestFacadeContext:
    """Test ContextHarness context construction."""

    def test_build_context_for_query(self):
        """Test build_context_for_query returns string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Hello"))
            harness.add_message(thread_id, AIMessage("Hi!"))

            context = harness.build_context_for_query("What's next?", thread_id)

            assert isinstance(context, str)
            assert len(context) > 0

    def test_build_context_empty_thread(self):
        """Test build_context_for_query with empty thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()

            context = harness.build_context_for_query("Query", thread_id)

            # Should still work, just no history
            assert isinstance(context, str)

    def test_get_context_messages(self):
        """Test get_context_messages returns LangChain messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from langchain_core.messages import SystemMessage, HumanMessage

            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Hello"))

            messages = harness.get_context_messages("Query", thread_id)

            assert len(messages) == 2  # SystemMessage + HumanMessage
            assert isinstance(messages[0], SystemMessage)
            assert isinstance(messages[1], HumanMessage)

    def test_build_context_includes_history(self):
        """Test build_context includes message history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("User message"))

            context = harness.build_context_for_query("Query", thread_id)

            # Should include message content
            assert "User message" in context or "Hello" in context