"""Test SpilledContentReference model."""

import pytest
from context_harness.models import SpilledContentReference, SpillType


class TestSpilledContentReference:
    """Test SpilledContentReference dataclass."""

    def test_create_spill_reference(self):
        """Test creating SpilledContentReference with valid data."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path/to/spilled/content",
            content_size=1000,
            content_type="tool_response"
        )

        assert spill_ref.spill_id  # Auto-generated UUID
        assert spill_ref.spill_type == SpillType.MESSAGE_SPILL
        assert spill_ref.content_location == "/path/to/spilled/content"
        assert spill_ref.content_size == 1000
        assert spill_ref.content_type == "tool_response"
        assert spill_ref.retrieval_hint == "use fetch_spilled_content tool with spill_id"

    def test_auto_generated_spill_id(self):
        """Test spill_id is auto-generated UUID."""
        spill_ref1 = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path/1",
            content_size=100,
            content_type="test"
        )
        spill_ref2 = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path/2",
            content_size=100,
            content_type="test"
        )

        # IDs should be unique
        assert spill_ref1.spill_id != spill_ref2.spill_id

    def test_optional_content_preview(self):
        """Test optional content_preview field."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path/to/content",
            content_size=1000,
            content_type="ai_report",
            content_preview="API returned 50000 records..."
        )

        assert spill_ref.content_preview == "API returned 50000 records..."

    def test_custom_metadata(self):
        """Test custom metadata field."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path/to/content",
            content_size=1000,
            content_type="tool_response",
            metadata={"timestamp": 1234567890, "model": "gpt-4"}
        )

        assert spill_ref.metadata["timestamp"] == 1234567890
        assert spill_ref.metadata["model"] == "gpt-4"

    def test_custom_retrieval_hint(self):
        """Test custom retrieval_hint."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.GENERATED_DATA,
            content_location="/path/to/data",
            content_size=5000,
            content_type="generated_dataset",
            retrieval_hint="use fetch_data tool with dataset_id"
        )

        assert spill_ref.retrieval_hint == "use fetch_data tool with dataset_id"

    def test_validation_negative_content_size_raises_error(self):
        """Test validation: negative content_size raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SpilledContentReference(
                spill_type=SpillType.MESSAGE_SPILL,
                content_location="/path/to/content",
                content_size=-1,
                content_type="test"
            )

        assert "content_size must be positive" in str(exc_info.value)

    def test_validation_zero_content_size_raises_error(self):
        """Test validation: zero content_size raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SpilledContentReference(
                spill_type=SpillType.MESSAGE_SPILL,
                content_location="/path/to/content",
                content_size=0,
                content_type="test"
            )

        assert "content_size must be positive" in str(exc_info.value)

    def test_validation_empty_content_location_raises_error(self):
        """Test validation: empty content_location raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SpilledContentReference(
                spill_type=SpillType.MESSAGE_SPILL,
                content_location="",
                content_size=100,
                content_type="test"
            )

        assert "content_location must be non-empty" in str(exc_info.value)

    def test_spill_type_enum_values(self):
        """Test all SpillType enum values can be used."""
        for spill_type in [SpillType.MESSAGE_SPILL, SpillType.GENERATED_DATA, SpillType.FUTURE_EXTENSION]:
            spill_ref = SpilledContentReference(
                spill_type=spill_type,
                content_location="/path",
                content_size=100,
                content_type="test"
            )
            assert spill_ref.spill_type == spill_type