"""Test ContextHarness facade distillation operations."""

import pytest
import tempfile

from langchain_core.messages import HumanMessage, AIMessage

from context_harness import ContextHarness
from context_harness.backend import FileBackend
from context_harness.models import AutomationConfig


class TestFacadeDistillation:
    """Test ContextHarness experience distillation."""

    def test_distill_experiences(self):
        """Test manual distillation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()
            harness.add_message(thread_id, HumanMessage("Hello"))
            harness.add_message(thread_id, AIMessage("Hi!"))

            # Distill
            memories = harness.distill_experiences(thread_id, auto_store=True)

            assert len(memories) > 0

    def test_distill_empty_thread(self):
        """Test distillation of empty thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            thread_id = harness.create_thread()

            memories = harness.distill_experiences(thread_id)
            assert len(memories) == 0

    def test_enable_auto_distill(self):
        """Test enable_auto_distill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            harness.enable_auto_distill(threshold=5)

            assert harness._automation_config.auto_distill == True
            assert harness._automation_config.distill_threshold == 5

    def test_disable_auto_distill(self):
        """Test disable_auto_distill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            harness.enable_auto_distill()
            harness.disable_auto_distill()

            assert harness._automation_config.auto_distill == False

    def test_auto_distill_trigger(self):
        """Test auto-distill triggered by message count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config = AutomationConfig(
                auto_distill=True,
                distill_trigger="message_count",
                distill_threshold=5,
                auto_store_memories=True
            )
            harness = ContextHarness(
                backend=FileBackend(base_path=tmpdir),
                automation_config=custom_config
            )

            thread_id = harness.create_thread()

            # Add messages up to threshold
            for i in range(5):
                harness.add_message(thread_id, HumanMessage(f"Msg {i}"))

            # Auto-distill should have triggered
            # Check if memories were created
            memories = harness.search_memories(thread_id=thread_id)
            assert len(memories) > 0

    def test_configure_automation(self):
        """Test configure_automation."""
        from context_harness.models import AutomationConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            new_config = AutomationConfig(
                auto_distill=True,
                distill_threshold=15
            )
            harness.configure_automation(new_config)

            assert harness._automation_config.auto_distill == True
            assert harness._automation_config.distill_threshold == 15