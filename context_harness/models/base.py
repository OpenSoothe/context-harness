"""Base structures: enums and error types."""

from enum import Enum


class MemoryType(Enum):
    """Memory type categories."""
    SUMMARY = "summary"
    EXPERIENCE_PATTERN = "experience_pattern"
    USER_PREFERENCE = "user_preference"
    FACT = "fact"


class SpillType(Enum):
    """Spill content type categories."""
    MESSAGE_SPILL = "message_spill"
    GENERATED_DATA = "generated_data"
    FUTURE_EXTENSION = "future_extension"


class RetrievalStrategy(Enum):
    """Context retrieval strategies."""
    RECENT_FIRST = "recent_first"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID = "hybrid"


class InsertionSyntaxError(Exception):
    """Raised when insertion syntax format is invalid."""
    pass


class ValidationError(Exception):
    """Domain-specific validation error."""
    pass