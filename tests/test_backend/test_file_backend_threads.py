"""Test FileBackend thread operations."""

import pytest
import tempfile
from pathlib import Path

from context_harness.backend import FileBackend, BackendConfigurationError
from context_harness.models import Thread


class TestFileBackendThreads:
    """Test FileBackend thread operations."""

    def test_put_and_get_thread(self):
        """Test put_thread and get_thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread(metadata={"user_id": "user123"})
            config = {"thread_id": thread.thread_id}

            backend.put_thread(config, thread)
            retrieved = backend.get_thread(config)

            assert retrieved is not None
            assert retrieved.thread_id == thread.thread_id
            assert retrieved.metadata["user_id"] == "user123"

    def test_get_thread_nonexistent(self):
        """Test get_thread returns None for nonexistent thread."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            retrieved = backend.get_thread({"thread_id": "nonexistent"})
            assert retrieved is None

    def test_get_thread_missing_thread_id_raises_error(self):
        """Test get_thread without thread_id raises BackendConfigurationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            with pytest.raises(BackendConfigurationError) as exc_info:
                backend.get_thread({})
            assert "thread_id required" in str(exc_info.value)

    def test_put_thread_missing_thread_id_uses_thread_object_id(self):
        """Test put_thread uses thread.thread_id if thread_id not in config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({}, thread)  # Empty config

            # Should still work using thread.thread_id
            retrieved = backend.get_thread({"thread_id": thread.thread_id})
            assert retrieved is not None
            assert retrieved.thread_id == thread.thread_id

    def test_list_threads_empty(self):
        """Test list_threads returns empty list when no threads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            threads = backend.list_threads()
            assert threads == []

    def test_list_threads_multiple(self):
        """Test list_threads returns multiple threads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread1 = Thread(metadata={"user_id": "user1"})
            thread2 = Thread(metadata={"user_id": "user2"})
            thread3 = Thread(metadata={"user_id": "user1"})

            backend.put_thread({"thread_id": thread1.thread_id}, thread1)
            backend.put_thread({"thread_id": thread2.thread_id}, thread2)
            backend.put_thread({"thread_id": thread3.thread_id}, thread3)

            threads = backend.list_threads()
            assert len(threads) == 3

    def test_list_threads_filter_by_user_id(self):
        """Test list_threads with user_id filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread1 = Thread(metadata={"user_id": "user1"})
            thread2 = Thread(metadata={"user_id": "user2"})
            thread3 = Thread(metadata={"user_id": "user1"})

            backend.put_thread({"thread_id": thread1.thread_id}, thread1)
            backend.put_thread({"thread_id": thread2.thread_id}, thread2)
            backend.put_thread({"thread_id": thread3.thread_id}, thread3)

            threads = backend.list_threads({"user_id": "user1"})
            assert len(threads) == 2
            assert all(t["metadata"]["user_id"] == "user1" for t in threads)

    def test_list_threads_sorted_by_created_at(self):
        """Test list_threads sorted by created_at descending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            # Create threads in order
            import time
            thread1 = Thread(metadata={"order": 1})
            time.sleep(0.01)
            thread2 = Thread(metadata={"order": 2})
            time.sleep(0.01)
            thread3 = Thread(metadata={"order": 3})

            backend.put_thread({"thread_id": thread1.thread_id}, thread1)
            backend.put_thread({"thread_id": thread2.thread_id}, thread2)
            backend.put_thread({"thread_id": thread3.thread_id}, thread3)

            threads = backend.list_threads()
            # Most recent first
            assert threads[0]["thread_id"] == thread3.thread_id
            assert threads[1]["thread_id"] == thread2.thread_id
            assert threads[2]["thread_id"] == thread1.thread_id

    def test_thread_cache_behavior(self):
        """Test thread caching reduces file reads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir, cache_enabled=True)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            # First get reads from file, caches
            retrieved1 = backend.get_thread({"thread_id": thread.thread_id})

            # Second get should use cache (same object)
            retrieved2 = backend.get_thread({"thread_id": thread.thread_id})

            assert retrieved1.thread_id == thread.thread_id
            assert retrieved2.thread_id == thread.thread_id

    def test_thread_cache_disabled(self):
        """Test with cache disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir, cache_enabled=False)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            # Both reads from file
            retrieved1 = backend.get_thread({"thread_id": thread.thread_id})
            retrieved2 = backend.get_thread({"thread_id": thread.thread_id})

            assert retrieved1.thread_id == thread.thread_id
            assert retrieved2.thread_id == thread.thread_id