"""Test ContextHarness facade component access."""

import pytest
import tempfile

from context_harness import ContextHarness
from context_harness.backend import FileBackend
from context_harness.components import (
    ChatHistoryManager,
    MemoryManager,
    ExperienceDistiller,
    ContextBuilder,
)


class TestFacadeComponentAccess:
    """Test ContextHarness component accessor methods."""

    def test_get_chat_history_manager(self):
        """Test get_chat_history_manager returns component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            manager = harness.get_chat_history_manager()

            assert manager is not None
            assert isinstance(manager, ChatHistoryManager)

    def test_get_memory_manager(self):
        """Test get_memory_manager returns component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            manager = harness.get_memory_manager()

            assert manager is not None
            assert isinstance(manager, MemoryManager)

    def test_get_experience_distiller(self):
        """Test get_experience_distiller returns component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            distiller = harness.get_experience_distiller()

            assert distiller is not None
            assert isinstance(distiller, ExperienceDistiller)

    def test_get_context_builder(self):
        """Test get_context_builder returns component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            builder = harness.get_context_builder()

            assert builder is not None
            assert isinstance(builder, ContextBuilder)

    def test_component_access_allows_direct_usage(self):
        """Test component access allows direct component method calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            # Get component and use directly
            manager = harness.get_chat_history_manager()
            thread = manager.create_thread()

            assert thread is not None
            assert thread.thread_id is not None