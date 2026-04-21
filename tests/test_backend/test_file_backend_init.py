"""Test FileBackend initialization."""

import pytest
import tempfile
from pathlib import Path

from context_harness.backend import FileBackend, BackendConfigurationError


class TestFileBackendInit:
    """Test FileBackend initialization."""

    def test_init_creates_directory_structure(self):
        """Test initialization creates directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            base_path = Path(tmpdir)
            assert base_path.exists()
            assert (base_path / "threads").exists()
            assert (base_path / "memories").exists()
            assert (base_path / "spilled").exists()

    def test_init_with_custom_base_path(self):
        """Test initialization with custom base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / ".custom_backend"
            backend = FileBackend(base_path=str(custom_path))

            assert custom_path.exists()
            assert (custom_path / "threads").exists()

    def test_init_with_existing_directory(self):
        """Test initialization with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory first
            backend1 = FileBackend(base_path=tmpdir)
            # Initialize again on same directory
            backend2 = FileBackend(base_path=tmpdir)

            # Should not raise error
            assert Path(tmpdir).exists()

    def test_init_with_cache_enabled(self):
        """Test initialization with cache enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir, cache_enabled=True)

            assert backend.cache_enabled == True
            assert backend.cache is not None

    def test_init_with_cache_disabled(self):
        """Test initialization with cache disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir, cache_enabled=False)

            assert backend.cache_enabled == False
            assert backend.cache is None

    def test_init_with_custom_cache_ttl(self):
        """Test initialization with custom cache TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir, cache_ttl=600)

            if backend.cache:
                assert backend.cache.ttl_seconds == 600

    def test_init_creates_nested_directories(self):
        """Test initialization creates nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "path" / ".backend"
            backend = FileBackend(base_path=str(nested_path))

            assert nested_path.exists()
            assert (nested_path / "threads").exists()
            assert (nested_path / "memories").exists()
            assert (nested_path / "spilled").exists()