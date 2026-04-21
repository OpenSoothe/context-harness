"""Test base structures: enums and error types."""

import pytest
from context_harness.models.base import (
    MemoryType,
    SpillType,
    RetrievalStrategy,
    InsertionSyntaxError,
    ValidationError,
)


class TestEnums:
    """Test enum value access."""

    def test_memory_type_values(self):
        """Test MemoryType enum values."""
        assert MemoryType.SUMMARY.value == "summary"
        assert MemoryType.EXPERIENCE_PATTERN.value == "experience_pattern"
        assert MemoryType.USER_PREFERENCE.value == "user_preference"
        assert MemoryType.FACT.value == "fact"

    def test_spill_type_values(self):
        """Test SpillType enum values."""
        assert SpillType.MESSAGE_SPILL.value == "message_spill"
        assert SpillType.GENERATED_DATA.value == "generated_data"
        assert SpillType.FUTURE_EXTENSION.value == "future_extension"

    def test_retrieval_strategy_values(self):
        """Test RetrievalStrategy enum values."""
        assert RetrievalStrategy.RECENT_FIRST.value == "recent_first"
        assert RetrievalStrategy.SEMANTIC_SIMILARITY.value == "semantic_similarity"
        assert RetrievalStrategy.HYBRID.value == "hybrid"


class TestErrors:
    """Test error types inheritance."""

    def test_insertion_syntax_error_inheritance(self):
        """Test InsertionSyntaxError inherits from Exception."""
        assert issubclass(InsertionSyntaxError, Exception)

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from Exception."""
        assert issubclass(ValidationError, Exception)

    def test_insertion_syntax_error_message(self):
        """Test InsertionSyntaxError can be raised with message."""
        with pytest.raises(InsertionSyntaxError) as exc_info:
            raise InsertionSyntaxError("Invalid marker format")
        assert "Invalid marker format" in str(exc_info.value)

    def test_validation_error_message(self):
        """Test ValidationError can be raised with message."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Validation failed")
        assert "Validation failed" in str(exc_info.value)