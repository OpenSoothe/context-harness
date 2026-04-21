"""Test backend base components."""

import pytest
from context_harness.backend import (
    StorageBackend,
    BackendError,
    ThreadNotFoundError,
    MemoryNotFoundError,
    SpillContentNotFoundError,
    BackendConfigurationError,
)


class TestBackendErrors:
    """Test backend error types."""

    def test_backend_error_inheritance(self):
        """Test BackendError inherits from Exception."""
        assert issubclass(BackendError, Exception)

    def test_thread_not_found_error_inheritance(self):
        """Test ThreadNotFoundError inherits from BackendError."""
        assert issubclass(ThreadNotFoundError, BackendError)

    def test_memory_not_found_error_inheritance(self):
        """Test MemoryNotFoundError inherits from BackendError."""
        assert issubclass(MemoryNotFoundError, BackendError)

    def test_spill_content_not_found_error_inheritance(self):
        """Test SpillContentNotFoundError inherits from BackendError."""
        assert issubclass(SpillContentNotFoundError, BackendError)

    def test_backend_configuration_error_inheritance(self):
        """Test BackendConfigurationError inherits from BackendError."""
        assert issubclass(BackendConfigurationError, BackendError)

    def test_error_messages(self):
        """Test error types can be raised with messages."""
        with pytest.raises(ThreadNotFoundError) as exc_info:
            raise ThreadNotFoundError("Thread not found")
        assert "Thread not found" in str(exc_info.value)

        with pytest.raises(MemoryNotFoundError) as exc_info:
            raise MemoryNotFoundError("Memory not found")
        assert "Memory not found" in str(exc_info.value)

        with pytest.raises(SpillContentNotFoundError) as exc_info:
            raise SpillContentNotFoundError("Spill content not found")
        assert "Spill content not found" in str(exc_info.value)

        with pytest.raises(BackendConfigurationError) as exc_info:
            raise BackendConfigurationError("Invalid configuration")
        assert "Invalid configuration" in str(exc_info.value)


class TestStorageBackendAbstract:
    """Test StorageBackend is abstract and cannot be instantiated."""

    def test_storage_backend_is_abstract(self):
        """Test StorageBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageBackend()

    def test_storage_backend_subclass_needs_all_methods(self):
        """Test subclass without implementing all methods raises TypeError."""

        class IncompleteBackend(StorageBackend):
            # Only implement one method
            def get_thread(self, config):
                return None

        with pytest.raises(TypeError):
            IncompleteBackend()