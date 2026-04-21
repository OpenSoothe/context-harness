"""Test Memory model."""

import pytest
from context_harness.models import Memory, MemoryType


class TestMemory:
    """Test Memory dataclass."""

    def test_create_memory_summary(self):
        """Test creating Memory with SUMMARY type."""
        memory = Memory(
            memory_type=MemoryType.SUMMARY,
            content="User discussed pricing tiers",
            thread_id="thread_123",
            related_message_ids=["msg_1", "msg_5", "msg_12"],
            relevance_score=0.9
        )

        assert memory.memory_id  # Auto-generated UUID
        assert memory.memory_type == MemoryType.SUMMARY
        assert memory.content == "User discussed pricing tiers"
        assert memory.thread_id == "thread_123"
        assert memory.related_message_ids == ["msg_1", "msg_5", "msg_12"]
        assert memory.relevance_score == 0.9

    def test_create_memory_user_preference(self):
        """Test creating Memory with USER_PREFERENCE type."""
        memory = Memory(
            memory_type=MemoryType.USER_PREFERENCE,
            content="User prefers concise responses",
            thread_id="thread_123",
            related_message_ids=["msg_1"]
        )

        assert memory.memory_type == MemoryType.USER_PREFERENCE

    def test_create_memory_experience_pattern(self):
        """Test creating Memory with EXPERIENCE_PATTERN type."""
        memory = Memory(
            memory_type=MemoryType.EXPERIENCE_PATTERN,
            content="When user asks about pricing, explain tier structure",
            thread_id="thread_123",
            related_message_ids=["msg_1", "msg_2"]
        )

        assert memory.memory_type == MemoryType.EXPERIENCE_PATTERN

    def test_create_memory_fact(self):
        """Test creating Memory with FACT type."""
        memory = Memory(
            memory_type=MemoryType.FACT,
            content="User's company is Acme Corp",
            thread_id="thread_123",
            related_message_ids=["msg_1"]
        )

        assert memory.memory_type == MemoryType.FACT

    def test_auto_generated_memory_id(self):
        """Test memory_id is auto-generated UUID."""
        memory1 = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test 1",
            thread_id="thread_1",
            related_message_ids=["msg_1"]
        )
        memory2 = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test 2",
            thread_id="thread_1",
            related_message_ids=["msg_1"]
        )

        # IDs should be unique
        assert memory1.memory_id != memory2.memory_id

    def test_custom_metadata(self):
        """Test custom metadata field."""
        memory = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test",
            thread_id="thread_123",
            related_message_ids=["msg_1"],
            metadata={"tags": ["pricing", "sales"], "access_count": 5}
        )

        assert memory.metadata["tags"] == ["pricing", "sales"]
        assert memory.metadata["access_count"] == 5

    def test_default_relevance_score(self):
        """Test default relevance_score is 0.0."""
        memory = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test",
            thread_id="thread_123",
            related_message_ids=["msg_1"]
        )

        assert memory.relevance_score == 0.0

    def test_validation_empty_related_message_ids_raises_error(self):
        """Test validation: empty related_message_ids raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Memory(
                memory_type=MemoryType.SUMMARY,
                content="Test",
                thread_id="thread_123",
                related_message_ids=[]  # Empty list violates invariant
            )

        assert "Memory must have at least one related_message_id" in str(exc_info.value)

    def test_validation_relevance_score_out_of_range_high(self):
        """Test validation: relevance_score > 1.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Memory(
                memory_type=MemoryType.SUMMARY,
                content="Test",
                thread_id="thread_123",
                related_message_ids=["msg_1"],
                relevance_score=1.5  # Out of range
            )

        assert "relevance_score must be in range [0.0, 1.0]" in str(exc_info.value)

    def test_validation_relevance_score_out_of_range_low(self):
        """Test validation: relevance_score < 0.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Memory(
                memory_type=MemoryType.SUMMARY,
                content="Test",
                thread_id="thread_123",
                related_message_ids=["msg_1"],
                relevance_score=-0.1  # Out of range
            )

        assert "relevance_score must be in range [0.0, 1.0]" in str(exc_info.value)

    def test_validation_empty_content_raises_error(self):
        """Test validation: empty content raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Memory(
                memory_type=MemoryType.SUMMARY,
                content="",  # Empty content
                thread_id="thread_123",
                related_message_ids=["msg_1"]
            )

        assert "Memory content must be non-empty" in str(exc_info.value)

    def test_relevance_score_at_boundaries(self):
        """Test relevance_score at valid boundaries (0.0 and 1.0)."""
        memory_min = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test",
            thread_id="thread_123",
            related_message_ids=["msg_1"],
            relevance_score=0.0
        )
        memory_max = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test",
            thread_id="thread_123",
            related_message_ids=["msg_1"],
            relevance_score=1.0
        )

        assert memory_min.relevance_score == 0.0
        assert memory_max.relevance_score == 1.0

    def test_multiple_related_message_ids(self):
        """Test memory with multiple related_message_ids."""
        memory = Memory(
            memory_type=MemoryType.SUMMARY,
            content="Test",
            thread_id="thread_123",
            related_message_ids=["msg_1", "msg_2", "msg_3", "msg_4"]
        )

        assert len(memory.related_message_ids) == 4