"""Test FileBackend memory operations."""

import pytest
import tempfile

from context_harness.backend import FileBackend
from context_harness.models import Memory, MemoryType


class TestFileBackendMemories:
    """Test FileBackend memory operations."""

    def test_put_memory_creates_file(self):
        """Test put_memory creates memory file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory = Memory(
                memory_type=MemoryType.SUMMARY,
                content="User discussed pricing",
                thread_id="thread_123",
                related_message_ids=["msg_1", "msg_2"]
            )
            backend.put_memory(memory)

            memory_file = backend._memory_file(memory.memory_id)
            assert memory_file.exists()

    def test_get_memory(self):
        """Test get_memory retrieves memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Test content",
                thread_id="thread_123",
                related_message_ids=["msg_1"]
            )
            backend.put_memory(memory)

            retrieved = backend.get_memory(memory.memory_id)
            assert retrieved is not None
            assert retrieved.memory_id == memory.memory_id
            assert retrieved.content == "Test content"
            assert retrieved.memory_type == MemoryType.SUMMARY

    def test_get_memory_nonexistent(self):
        """Test get_memory returns None for nonexistent memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            retrieved = backend.get_memory("nonexistent_id")
            assert retrieved is None

    def test_put_memory_updates_index(self):
        """Test put_memory updates index.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Test",
                thread_id="thread_123",
                related_message_ids=["msg_1"]
            )
            backend.put_memory(memory)

            index_file = backend._memory_index_file()
            assert index_file.exists()

    def test_search_memories_empty(self):
        """Test search_memories returns empty list when no memories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memories = backend.search_memories()
            assert memories == []

    def test_search_memories_by_thread_id(self):
        """Test search_memories with thread_id filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory1 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary for thread1",
                thread_id="thread_1",
                related_message_ids=["msg_1"]
            )
            memory2 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary for thread2",
                thread_id="thread_2",
                related_message_ids=["msg_2"]
            )

            backend.put_memory(memory1)
            backend.put_memory(memory2)

            memories = backend.search_memories(config={"thread_id": "thread_1"})
            assert len(memories) == 1
            assert memories[0].thread_id == "thread_1"

    def test_search_memories_by_memory_type(self):
        """Test search_memories with memory_type filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory1 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary",
                thread_id="thread_1",
                related_message_ids=["msg_1"]
            )
            memory2 = Memory(
                memory_type=MemoryType.USER_PREFERENCE,
                content="User preference",
                thread_id="thread_1",
                related_message_ids=["msg_2"]
            )

            backend.put_memory(memory1)
            backend.put_memory(memory2)

            memories = backend.search_memories(memory_type="summary")
            assert len(memories) == 1
            assert memories[0].memory_type == MemoryType.SUMMARY

    def test_search_memories_with_query(self):
        """Test search_memories with keyword query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory1 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="User discussed pricing tiers",
                thread_id="thread_1",
                related_message_ids=["msg_1"]
            )
            memory2 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="User asked about features",
                thread_id="thread_1",
                related_message_ids=["msg_2"]
            )

            backend.put_memory(memory1)
            backend.put_memory(memory2)

            memories = backend.search_memories(query="pricing")
            assert len(memories) == 1
            assert "pricing" in memories[0].content

    def test_search_memories_ranked_by_relevance(self):
        """Test search_memories ranked by relevance_score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory1 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary 1",
                thread_id="thread_1",
                related_message_ids=["msg_1"],
                relevance_score=0.5
            )
            memory2 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary 2",
                thread_id="thread_1",
                related_message_ids=["msg_2"],
                relevance_score=0.9
            )
            memory3 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Summary 3",
                thread_id="thread_1",
                related_message_ids=["msg_3"],
                relevance_score=0.7
            )

            backend.put_memory(memory1)
            backend.put_memory(memory2)
            backend.put_memory(memory3)

            memories = backend.search_memories()
            # Should be sorted by relevance descending
            assert memories[0].relevance_score == 0.9
            assert memories[1].relevance_score == 0.7
            assert memories[2].relevance_score == 0.5

    def test_search_memories_with_limit(self):
        """Test search_memories with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            for i in range(10):
                memory = Memory(
                    memory_type=MemoryType.SUMMARY,
                    content=f"Summary {i}",
                    thread_id="thread_1",
                    related_message_ids=[f"msg_{i}"]
                )
                backend.put_memory(memory)

            memories = backend.search_memories(limit=5)
            assert len(memories) == 5

    def test_search_memories_combined_filters(self):
        """Test search_memories with combined filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            memory1 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Pricing discussion",
                thread_id="thread_1",
                related_message_ids=["msg_1"]
            )
            memory2 = Memory(
                memory_type=MemoryType.USER_PREFERENCE,
                content="Pricing preference",
                thread_id="thread_1",
                related_message_ids=["msg_2"]
            )
            memory3 = Memory(
                memory_type=MemoryType.SUMMARY,
                content="Pricing discussion",
                thread_id="thread_2",
                related_message_ids=["msg_3"]
            )

            backend.put_memory(memory1)
            backend.put_memory(memory2)
            backend.put_memory(memory3)

            # Combine filters
            memories = backend.search_memories(
                query="pricing",
                config={"thread_id": "thread_1"},
                memory_type="summary"
            )
            assert len(memories) == 1
            assert memories[0].thread_id == "thread_1"
            assert memories[0].memory_type == MemoryType.SUMMARY
            assert "Pricing" in memories[0].content  # Case-sensitive match