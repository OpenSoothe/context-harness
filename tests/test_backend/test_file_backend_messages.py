"""Test FileBackend message operations."""

import pytest
import tempfile

from langchain_core.messages import HumanMessage, AIMessage

from context_harness.backend import FileBackend, BackendConfigurationError
from context_harness.models import Thread, ThreadMessage


class TestFileBackendMessages:
    """Test FileBackend message operations."""

    def test_append_message_creates_messages_file(self):
        """Test append_message creates messages.jsonl."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            msg = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Hello"))
            backend.append_message({"thread_id": thread.thread_id}, msg)

            # Check messages file exists
            messages_file = backend._thread_messages_file(thread.thread_id)
            assert messages_file.exists()

    def test_append_message_missing_thread_id_raises_error(self):
        """Test append_message without thread_id raises BackendConfigurationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            msg = ThreadMessage.create_from_langchain("thread_123", HumanMessage("Test"))

            with pytest.raises(BackendConfigurationError):
                backend.append_message({}, msg)

    def test_append_multiple_messages(self):
        """Test appending multiple messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            msg1 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Hello"))
            msg2 = ThreadMessage.create_from_langchain(thread.thread_id, AIMessage("Hi!"))
            msg3 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("How are you?"))

            backend.append_message({"thread_id": thread.thread_id}, msg1)
            backend.append_message({"thread_id": thread.thread_id}, msg2)
            backend.append_message({"thread_id": thread.thread_id}, msg3)

            messages = backend.get_messages({"thread_id": thread.thread_id})
            assert len(messages) == 3
            assert messages[0].unwrap_to_langchain().content == "Hello"
            assert messages[1].unwrap_to_langchain().content == "Hi!"
            assert messages[2].unwrap_to_langchain().content == "How are you?"

    def test_get_messages_empty(self):
        """Test get_messages returns empty list when no messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            messages = backend.get_messages({"thread_id": thread.thread_id})
            assert messages == []

    def test_get_messages_with_limit(self):
        """Test get_messages with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            # Add 10 messages
            for i in range(10):
                msg = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage(f"Msg {i}"))
                backend.append_message({"thread_id": thread.thread_id}, msg)

            # Get last 5 messages
            messages = backend.get_messages({"thread_id": thread.thread_id}, limit=5)
            assert len(messages) == 5
            # Should be most recent 5
            assert messages[0].unwrap_to_langchain().content == "Msg 5"
            assert messages[-1].unwrap_to_langchain().content == "Msg 9"

    def test_get_messages_before_timestamp(self):
        """Test get_messages with timestamp filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            # Add messages
            import time
            msg1 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Msg 1"))
            backend.append_message({"thread_id": thread.thread_id}, msg1)
            time.sleep(0.1)

            cutoff_time = time.time()
            time.sleep(0.1)

            msg2 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Msg 2"))
            backend.append_message({"thread_id": thread.thread_id}, msg2)
            msg3 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Msg 3"))
            backend.append_message({"thread_id": thread.thread_id}, msg3)

            # Get messages before cutoff
            messages = backend.get_messages({"thread_id": thread.thread_id}, before_timestamp=cutoff_time)
            assert len(messages) == 1
            assert messages[0].unwrap_to_langchain().content == "Msg 1"

    def test_get_messages_missing_thread_id_raises_error(self):
        """Test get_messages without thread_id raises BackendConfigurationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            with pytest.raises(BackendConfigurationError):
                backend.get_messages({})

    def test_append_message_updates_thread_timestamp(self):
        """Test append_message updates thread updated_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)
            original_updated_at = thread.updated_at

            import time
            time.sleep(0.01)

            msg = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Test"))
            backend.append_message({"thread_id": thread.thread_id}, msg)

            # Check thread timestamp updated
            updated_thread = backend.get_thread({"thread_id": thread.thread_id})
            assert updated_thread.updated_at > original_updated_at

    def test_message_order_preserved(self):
        """Test message chronological order is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileBackend(base_path=tmpdir)

            thread = Thread()
            backend.put_thread({"thread_id": thread.thread_id}, thread)

            for i in range(5):
                msg = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage(f"Message {i}"))
                backend.append_message({"thread_id": thread.thread_id}, msg)

            messages = backend.get_messages({"thread_id": thread.thread_id})
            # Verify chronological order
            for i, msg in enumerate(messages):
                assert msg.unwrap_to_langchain().content == f"Message {i}"