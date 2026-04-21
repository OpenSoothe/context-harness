"""Test Thread and ThreadMessage models."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from context_harness.models import Thread, ThreadMessage, SpilledContentReference, SpillType
from context_harness.models.insertion_syntax import build_insertion_syntax


class TestThreadMessage:
    """Test ThreadMessage dataclass."""

    def test_create_from_langchain_human_message(self):
        """Test creating ThreadMessage from HumanMessage."""
        human_msg = HumanMessage(content="Hello")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=human_msg,
            metadata={"role": "user"}
        )

        assert thread_msg.thread_id == "thread_123"
        assert thread_msg.message_id  # Auto-generated UUID
        assert thread_msg.timestamp  # Auto-generated
        assert thread_msg.is_spilled == False
        assert thread_msg.content == human_msg
        assert thread_msg.metadata["role"] == "user"

    def test_create_from_langchain_ai_message(self):
        """Test creating ThreadMessage from AIMessage."""
        ai_msg = AIMessage(content="Hi! How can I help?")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=ai_msg,
            metadata={"model": "gpt-4"}
        )

        assert thread_msg.is_spilled == False
        assert thread_msg.content == ai_msg
        assert thread_msg.metadata["model"] == "gpt-4"

    def test_create_from_langchain_tool_message(self):
        """Test creating ThreadMessage from ToolMessage."""
        tool_msg = ToolMessage(content="API returned 500 results", tool_call_id="call_123")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=tool_msg
        )

        assert thread_msg.content == tool_msg

    def test_create_from_langchain_system_message(self):
        """Test creating ThreadMessage from SystemMessage."""
        system_msg = SystemMessage(content="You are a helpful assistant")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=system_msg
        )

        assert thread_msg.content == system_msg

    def test_unwrap_to_langchain_non_spilled(self):
        """Test unwrapping non-spilled message to LangChain."""
        human_msg = HumanMessage(content="Test")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=human_msg
        )

        unwrapped = thread_msg.unwrap_to_langchain()

        assert unwrapped == human_msg
        assert isinstance(unwrapped, HumanMessage)
        assert unwrapped.content == "Test"

    def test_unwrap_to_langchain_spilled_raises_error(self):
        """Test unwrapping spilled message raises ValueError."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path",
            content_size=100,
            content_type="test"
        )
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str=SpillType.MESSAGE_SPILL.value,
            metadata={"content_type": "test"},
            reference="spill_id=abc"
        )
        thread_msg = ThreadMessage(
            thread_id="thread_123",
            is_spilled=True,
            spill_reference=spill_ref,
            content=marker
        )

        with pytest.raises(ValueError) as exc_info:
            thread_msg.unwrap_to_langchain()

        assert "Cannot unwrap spilled message to LangChain" in str(exc_info.value)

    def test_get_marker_info_spilled(self):
        """Test get_marker_info for spilled message."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path",
            content_size=100,
            content_type="tool_response"
        )
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str=SpillType.MESSAGE_SPILL.value,
            metadata={"content_type": "tool_response", "preview": "API returned 500"},
            reference="spill_id=abc123"
        )
        thread_msg = ThreadMessage(
            thread_id="thread_123",
            is_spilled=True,
            spill_reference=spill_ref,
            content=marker
        )

        marker_info = thread_msg.get_marker_info()

        assert marker_info is not None
        assert marker_info["marker_type"] == "SPILL"
        assert marker_info["type"] == "message_spill"  # Note: enum value is lowercase
        assert marker_info["metadata"]["content_type"] == "tool_response"

    def test_get_marker_info_non_spilled(self):
        """Test get_marker_info for non-spilled message returns None."""
        human_msg = HumanMessage(content="Test")
        thread_msg = ThreadMessage.create_from_langchain(
            thread_id="thread_123",
            base_message=human_msg
        )

        marker_info = thread_msg.get_marker_info()

        assert marker_info is None

    def test_validation_spilled_without_reference_raises_error(self):
        """Test validation: spilled message without reference raises ValueError."""
        marker = "[[SPILL:MESSAGE_SPILL|{}|spill_id=abc]]"

        with pytest.raises(ValueError) as exc_info:
            ThreadMessage(
                thread_id="thread_123",
                is_spilled=True,
                spill_reference=None,  # Missing
                content=marker
            )

        assert "Spilled message must have spill_reference" in str(exc_info.value)

    def test_validation_spilled_with_base_message_content_raises_error(self):
        """Test validation: spilled message with BaseMessage content raises ValueError."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path",
            content_size=100,
            content_type="test"
        )

        with pytest.raises(ValueError) as exc_info:
            ThreadMessage(
                thread_id="thread_123",
                is_spilled=True,
                spill_reference=spill_ref,
                content=HumanMessage("Test")  # Wrong: should be str
            )

        assert "Spilled message content must be insertion syntax string" in str(exc_info.value)

    def test_validation_non_spilled_with_str_content_raises_error(self):
        """Test validation: non-spilled message with str content raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ThreadMessage(
                thread_id="thread_123",
                is_spilled=False,
                content="Plain text"  # Wrong: should be BaseMessage
            )

        assert "Non-spilled message content must be LangChain BaseMessage" in str(exc_info.value)

    def test_validation_spilled_invalid_insertion_syntax_raises_error(self):
        """Test validation: spilled message with invalid insertion syntax raises ValueError."""
        spill_ref = SpilledContentReference(
            spill_type=SpillType.MESSAGE_SPILL,
            content_location="/path",
            content_size=100,
            content_type="test"
        )

        with pytest.raises(ValueError) as exc_info:
            ThreadMessage(
                thread_id="thread_123",
                is_spilled=True,
                spill_reference=spill_ref,
                content="Invalid marker without brackets"
            )

        assert "Invalid insertion syntax" in str(exc_info.value)

    def test_auto_generated_message_id(self):
        """Test message_id is auto-generated UUID."""
        msg1 = ThreadMessage.create_from_langchain("thread_1", HumanMessage("A"))
        msg2 = ThreadMessage.create_from_langchain("thread_1", HumanMessage("B"))

        # IDs should be unique
        assert msg1.message_id != msg2.message_id

    def test_auto_generated_timestamp(self):
        """Test timestamp is auto-generated."""
        msg = ThreadMessage.create_from_langchain("thread_123", HumanMessage("Test"))

        assert msg.timestamp > 0
        assert isinstance(msg.timestamp, float)


class TestThread:
    """Test Thread dataclass."""

    def test_create_thread(self):
        """Test creating Thread with valid data."""
        thread = Thread(metadata={"user_id": "user123", "session_start": "2026-04-21"})

        assert thread.thread_id  # Auto-generated UUID
        assert thread.messages == []
        assert thread.metadata["user_id"] == "user123"
        assert thread.created_at > 0
        assert thread.updated_at > 0

    def test_auto_generated_thread_id(self):
        """Test thread_id is auto-generated UUID."""
        thread1 = Thread()
        thread2 = Thread()

        # IDs should be unique
        assert thread1.thread_id != thread2.thread_id

    def test_add_messages(self):
        """Test adding messages to thread."""
        thread = Thread()
        msg1 = ThreadMessage.create_from_langchain(thread.thread_id, HumanMessage("Hello"))
        msg2 = ThreadMessage.create_from_langchain(thread.thread_id, AIMessage("Hi!"))

        thread.messages.append(msg1)
        thread.messages.append(msg2)

        assert len(thread.messages) == 2
        assert thread.messages[0].content.content == "Hello"
        assert thread.messages[1].content.content == "Hi!"

    def test_update_timestamp(self):
        """Test update_timestamp method."""
        thread = Thread()
        original_updated_at = thread.updated_at

        # Wait a tiny bit (simulate time passing)
        import time
        time.sleep(0.01)

        thread.update_timestamp()

        assert thread.updated_at > original_updated_at

    def test_validation_message_wrong_thread_id_raises_error(self):
        """Test validation: message with wrong thread_id raises ValueError."""
        msg1 = ThreadMessage.create_from_langchain("thread_1", HumanMessage("Test"))
        msg2 = ThreadMessage.create_from_langchain("thread_2", AIMessage("Response"))

        with pytest.raises(ValueError) as exc_info:
            # Thread with thread_1, but contains message from thread_2
            thread = Thread(thread_id="thread_1", messages=[msg2])

        assert "has wrong thread_id" in str(exc_info.value)

    def test_validation_multiple_messages_wrong_thread_id(self):
        """Test validation catches multiple messages with wrong thread_id."""
        thread_id = "thread_correct"
        msg1 = ThreadMessage.create_from_langchain(thread_id, HumanMessage("Test"))
        msg2 = ThreadMessage.create_from_langchain("thread_wrong", AIMessage("Response"))

        with pytest.raises(ValueError):
            Thread(thread_id=thread_id, messages=[msg1, msg2])

    def test_empty_thread_valid(self):
        """Test creating empty thread is valid."""
        thread = Thread()

        assert len(thread.messages) == 0
        assert thread.metadata == {}