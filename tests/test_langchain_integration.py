"""Integration test for LangChain message integration."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from context_harness.models import Thread, ThreadMessage


class TestLangChainIntegration:
    """Test LangChain message wrapping and unwrapping."""

    def test_wrap_all_message_types(self):
        """Test wrapping all LangChain message types."""
        thread = Thread()

        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi!")
        system_msg = SystemMessage(content="You are helpful")
        tool_msg = ToolMessage(content="API result", tool_call_id="call_123")

        wrapped_human = ThreadMessage.create_from_langchain(thread.thread_id, human_msg)
        wrapped_ai = ThreadMessage.create_from_langchain(thread.thread_id, ai_msg)
        wrapped_system = ThreadMessage.create_from_langchain(thread.thread_id, system_msg)
        wrapped_tool = ThreadMessage.create_from_langchain(thread.thread_id, tool_msg)

        thread.messages.extend([wrapped_human, wrapped_ai, wrapped_system, wrapped_tool])

        assert len(thread.messages) == 4
        assert all(msg.is_spilled == False for msg in thread.messages)

    def test_unwrap_preserves_type_and_content(self):
        """Test unwrapping preserves message type and content."""
        human_msg = HumanMessage(content="Test message")
        wrapped = ThreadMessage.create_from_langchain("thread_123", human_msg)

        unwrapped = wrapped.unwrap_to_langchain()

        assert isinstance(unwrapped, HumanMessage)
        assert unwrapped.content == "Test message"
        assert unwrapped == human_msg  # Same object

    def test_unwrap_ai_message(self):
        """Test unwrapping AIMessage."""
        ai_msg = AIMessage(content="AI response")
        wrapped = ThreadMessage.create_from_langchain("thread_123", ai_msg)

        unwrapped = wrapped.unwrap_to_langchain()

        assert isinstance(unwrapped, AIMessage)
        assert unwrapped.content == "AI response"

    def test_unwrap_tool_message(self):
        """Test unwrapping ToolMessage."""
        tool_msg = ToolMessage(content="Tool result", tool_call_id="call_123")
        wrapped = ThreadMessage.create_from_langchain("thread_123", tool_msg)

        unwrapped = wrapped.unwrap_to_langchain()

        assert isinstance(unwrapped, ToolMessage)
        assert unwrapped.content == "Tool result"

    def test_unwrap_system_message(self):
        """Test unwrapping SystemMessage."""
        system_msg = SystemMessage(content="System instruction")
        wrapped = ThreadMessage.create_from_langchain("thread_123", system_msg)

        unwrapped = wrapped.unwrap_to_langchain()

        assert isinstance(unwrapped, SystemMessage)
        assert unwrapped.content == "System instruction"

    def test_metadata_preservation(self):
        """Test metadata preservation during wrapping."""
        human_msg = HumanMessage(content="Test")
        custom_metadata = {
            "token_count": 10,
            "model": "gpt-4",
            "timestamp": 1234567890,
            "custom_field": "custom_value"
        }

        wrapped = ThreadMessage.create_from_langchain(
            "thread_123",
            human_msg,
            metadata=custom_metadata
        )

        assert wrapped.metadata["token_count"] == 10
        assert wrapped.metadata["model"] == "gpt-4"
        assert wrapped.metadata["custom_field"] == "custom_value"

    def test_roundtrip_wrap_unwrap(self):
        """Test roundtrip: wrap then unwrap returns original."""
        original_msg = AIMessage(content="Original content")
        wrapped = ThreadMessage.create_from_langchain("thread_123", original_msg)
        unwrapped = wrapped.unwrap_to_langchain()

        assert unwrapped is original_msg  # Same object reference
        assert unwrapped.content == original_msg.content

    def test_thread_with_mixed_message_types(self):
        """Test thread with mixed LangChain message types."""
        thread = Thread()

        messages = [
            HumanMessage("Question 1"),
            AIMessage("Answer 1"),
            ToolMessage("Tool result 1", tool_call_id="call_1"),
            HumanMessage("Question 2"),
            AIMessage("Answer 2"),
        ]

        for msg in messages:
            wrapped = ThreadMessage.create_from_langchain(thread.thread_id, msg)
            thread.messages.append(wrapped)

        # Unwrap all
        unwrapped_messages = [msg.unwrap_to_langchain() for msg in thread.messages]

        assert len(unwrapped_messages) == 5
        assert isinstance(unwrapped_messages[0], HumanMessage)
        assert isinstance(unwrapped_messages[1], AIMessage)
        assert isinstance(unwrapped_messages[2], ToolMessage)

    def test_message_content_preserved(self):
        """Test message content is preserved exactly."""
        long_content = "This is a long message with multiple lines\nand special characters: !@#$%^&*()\nand unicode: 你好世界"
        ai_msg = AIMessage(content=long_content)

        wrapped = ThreadMessage.create_from_langchain("thread_123", ai_msg)
        unwrapped = wrapped.unwrap_to_langchain()

        assert unwrapped.content == long_content