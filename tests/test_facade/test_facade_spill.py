"""Test ContextHarness facade spill operations."""

import pytest
import tempfile

from langchain_core.messages import HumanMessage

from context_harness import ContextHarness
from context_harness.backend import FileBackend


class TestFacadeSpill:
    """Test ContextHarness spilled content operations."""

    def test_provide_spill_retrieval_tool(self):
        """Test provide_spill_retrieval_tool returns LangChain Tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            tool = harness.provide_spill_retrieval_tool()

            assert tool is not None
            assert tool.name == "fetch_spilled_content"
            assert "spill_id" in tool.description

    def test_retrieve_spilled_content(self):
        """Test retrieve_spilled_content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            # Create spill
            large_content = "Large content " * 1000
            spill_ref = harness._backend.spill_content(
                large_content,
                {"content_type": "test", "size": len(large_content)}
            )

            # Retrieve
            retrieved = harness.retrieve_spilled_content(spill_ref.spill_id)

            assert retrieved == large_content

    def test_add_large_message_auto_spill(self):
        """Test add_message with large content auto-spills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from context_harness.models import AutomationConfig

            config = AutomationConfig(
                auto_spill_messages=True,
                spill_threshold_bytes=100  # Small threshold for testing
            )
            harness = ContextHarness(
                backend=FileBackend(base_path=tmpdir),
                automation_config=config
            )

            thread_id = harness.create_thread()
            large_content = "Large message " * 100  # Exceeds threshold
            result = harness.add_message(thread_id, HumanMessage(large_content))

            # Should be spilled
            assert result.is_spilled == True
            assert result.spill_reference is not None

    def test_add_small_message_no_spill(self):
        """Test add_message with small content does not spill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            result = harness.add_message(thread_id, HumanMessage("Small message"))

            # Should not be spilled
            assert result.is_spilled == False