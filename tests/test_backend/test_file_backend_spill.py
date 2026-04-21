"""Test FileBackend spilled content operations."""

import pytest
import tempfile

from context_harness.backend import FileBackend, SpillContentNotFoundError
from context_harness.models import SpillType


class TestFileBackendSpill:
    """Test FileBackend spilled content operations."""

    def test_spill_content_creates_file(self):
        """Test spill_content creates spill file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Large content to spill..."
            spill_metadata = {"content_type": "tool_response", "size": 100}

            spill_ref = backend.spill_content(content, spill_metadata)

            # Check spill file exists
            spill_file = backend._spill_file(spill_ref.spill_id)
            assert spill_file.exists()

    def test_spill_content_returns_reference(self):
        """Test spill_content returns SpilledContentReference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Test content"
            spill_metadata = {"content_type": "ai_report", "size": 50}

            spill_ref = backend.spill_content(content, spill_metadata)

            assert spill_ref.spill_id is not None
            assert spill_ref.spill_type == SpillType.MESSAGE_SPILL
            assert spill_ref.content_type == "ai_report"
            assert spill_ref.content_size == 50

    def test_retrieve_spilled_content(self):
        """Test retrieve_spilled_content returns original content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Original large content"
            spill_metadata = {"content_type": "tool_response", "size": len(content)}

            spill_ref = backend.spill_content(content, spill_metadata)
            retrieved = backend.retrieve_spilled_content(spill_ref.spill_id)

            assert retrieved == content

    def test_retrieve_spilled_content_nonexistent_raises_error(self):
        """Test retrieve_spilled_content for nonexistent ID raises SpillContentNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            with pytest.raises(SpillContentNotFoundError):
                backend.retrieve_spilled_content("nonexistent_id")

    def test_delete_spilled_content(self):
        """Test delete_spilled_content removes file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Content to delete"
            spill_metadata = {"content_type": "test", "size": 10}

            spill_ref = backend.spill_content(content, spill_metadata)
            spill_file = backend._spill_file(spill_ref.spill_id)

            assert spill_file.exists()

            backend.delete_spilled_content(spill_ref.spill_id)

            assert not spill_file.exists()

    def test_delete_spilled_content_nonexistent_raises_error(self):
        """Test delete_spilled_content for nonexistent ID raises SpillContentNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            with pytest.raises(SpillContentNotFoundError):
                backend.delete_spilled_content("nonexistent_id")

    def test_retrieve_after_delete_returns_error(self):
        """Test retrieve_spilled_content after delete raises SpillContentNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Temporary content"
            spill_metadata = {"content_type": "test", "size": 10}

            spill_ref = backend.spill_content(content, spill_metadata)
            backend.delete_spilled_content(spill_ref.spill_id)

            with pytest.raises(SpillContentNotFoundError):
                backend.retrieve_spilled_content(spill_ref.spill_id)

    def test_spill_large_content(self):
        """Test spilling large content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            large_content = "API returned 50000 records..." * 1000
            spill_metadata = {
                "content_type": "tool_response",
                "size": len(large_content),
                "preview": large_content[:50]
            }

            spill_ref = backend.spill_content(large_content, spill_metadata)
            retrieved = backend.retrieve_spilled_content(spill_ref.spill_id)

            assert retrieved == large_content
            assert spill_ref.content_size == len(large_content)
            assert spill_ref.content_preview == large_content[:50]

    def test_spill_content_updates_metadata_registry(self):
        """Test spill_content updates spill metadata registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            content = "Test"
            spill_metadata = {"content_type": "test", "size": 10}

            spill_ref = backend.spill_content(content, spill_metadata)

            metadata_file = backend._spill_metadata_file()
            assert metadata_file.exists()

    def test_spill_json_serializable_content(self):
        """Test spilling JSON-serializable content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            json_content = {"data": [1, 2, 3], "metadata": {"key": "value"}}
            spill_metadata = {"content_type": "generated_data", "size": 100}

            spill_ref = backend.spill_content(json_content, spill_metadata)
            retrieved = backend.retrieve_spilled_content(spill_ref.spill_id)

            # Should retrieve dict
            assert isinstance(retrieved, dict)
            assert retrieved["data"] == [1, 2, 3]

    def test_multiple_spills(self):
        """Test multiple spills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            spill_ref1 = backend.spill_content("Content 1", {"content_type": "test", "size": 10})
            spill_ref2 = backend.spill_content("Content 2", {"content_type": "test", "size": 20})
            spill_ref3 = backend.spill_content("Content 3", {"content_type": "test", "size": 30})

            retrieved1 = backend.retrieve_spilled_content(spill_ref1.spill_id)
            retrieved2 = backend.retrieve_spilled_content(spill_ref2.spill_id)
            retrieved3 = backend.retrieve_spilled_content(spill_ref3.spill_id)

            assert retrieved1 == "Content 1"
            assert retrieved2 == "Content 2"
            assert retrieved3 == "Content 3"