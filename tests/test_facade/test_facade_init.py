"""Test ContextHarness facade initialization."""

import pytest
import tempfile

from context_harness import ContextHarness
from context_harness.backend import FileBackend


class TestFacadeInit:
    """Test ContextHarness initialization."""

    def test_init_default_backend(self):
        """Test initialization creates default FileBackend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            assert harness._backend is not None
            assert isinstance(harness._backend, FileBackend)

    def test_init_with_custom_backend(self):
        """Test initialization with custom backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_backend = FileBackend(base_path=tmpdir)
            harness = ContextHarness(backend=custom_backend)

            assert harness._backend == custom_backend

    def test_init_creates_components(self):
        """Test initialization creates all components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            assert harness._chat_history_manager is not None
            assert harness._memory_manager is not None
            assert harness._experience_distiller is not None
            assert harness._context_builder is not None

    def test_init_default_automation_config(self):
        """Test default automation config is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            harness = ContextHarness(backend=FileBackend(base_path=tmpdir))

            assert harness._automation_config.auto_distill == False
            assert harness._automation_config.auto_spill_messages == True

    def test_init_with_custom_automation_config(self):
        """Test initialization with custom automation config."""
        from context_harness.models import AutomationConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config = AutomationConfig(
                auto_distill=True,
                distill_threshold=20
            )
            harness = ContextHarness(
                backend=FileBackend(base_path=tmpdir),
                automation_config=custom_config
            )

            assert harness._automation_config.auto_distill == True
            assert harness._automation_config.distill_threshold == 20

    def test_init_with_context_config(self):
        """Test initialization with context config."""
        from context_harness.models import ContextConfig, RetrievalStrategy

        with tempfile.TemporaryDirectory() as tmpdir:
            context_config = ContextConfig(
                max_tokens=8000,
                retrieval_strategy=RetrievalStrategy.HYBRID
            )
            harness = ContextHarness(
                backend=FileBackend(base_path=tmpdir),
                context_config=context_config
            )

            assert harness._context_builder._config.max_tokens == 8000