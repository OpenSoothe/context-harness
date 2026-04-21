"""Serialization utilities for domain models."""

import json
from typing import Dict, Any, Union
from dataclasses import asdict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage

from context_harness.models import (
    Thread,
    ThreadMessage,
    Memory,
    SpilledContentReference,
    MemoryType,
    SpillType,
)


# Message type mapping
_MESSAGE_TYPES = {
    "HumanMessage": HumanMessage,
    "AIMessage": AIMessage,
    "SystemMessage": SystemMessage,
    "ToolMessage": ToolMessage,
}


def serialize_base_message(message: BaseMessage) -> Dict[str, Any]:
    """
    Serialize LangChain BaseMessage to dict.

    Args:
        message: LangChain message object

    Returns:
        Dict with message type and content
    """
    return {
        "type": message.__class__.__name__,
        "content": message.content,
        "additional_kwargs": message.additional_kwargs,
    }


def deserialize_base_message(data: Dict[str, Any]) -> BaseMessage:
    """
    Deserialize dict to LangChain BaseMessage.

    Args:
        data: Dict with message type and content

    Returns:
        LangChain message object
    """
    msg_type = data["type"]
    content = data["content"]
    additional_kwargs = data.get("additional_kwargs", {})

    # Get message class
    msg_class = _MESSAGE_TYPES.get(msg_type)
    if not msg_class:
        raise ValueError(f"Unknown message type: {msg_type}")

    return msg_class(content=content, additional_kwargs=additional_kwargs)


def serialize_thread_message(message: ThreadMessage) -> Dict[str, Any]:
    """
    Serialize ThreadMessage to dict.

    Args:
        message: ThreadMessage object

    Returns:
        Dict representation
    """
    data = {
        "message_id": message.message_id,
        "thread_id": message.thread_id,
        "timestamp": message.timestamp,
        "is_spilled": message.is_spilled,
        "metadata": message.metadata,
    }

    # Serialize content
    if message.is_spilled:
        # Content is insertion syntax string
        data["content"] = message.content
        data["content_type"] = "string"
    else:
        # Content is LangChain BaseMessage
        data["content"] = serialize_base_message(message.content)
        data["content_type"] = "base_message"

    # Serialize spill_reference
    if message.spill_reference:
        data["spill_reference"] = serialize_spill_reference(message.spill_reference)
    else:
        data["spill_reference"] = None

    return data


def deserialize_thread_message(data: Dict[str, Any]) -> ThreadMessage:
    """
    Deserialize dict to ThreadMessage.

    Args:
        data: Dict representation

    Returns:
        ThreadMessage object
    """
    # Deserialize content
    content_type = data["content_type"]
    if content_type == "string":
        content = data["content"]
    elif content_type == "base_message":
        content = deserialize_base_message(data["content"])
    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    # Deserialize spill_reference
    spill_ref_data = data.get("spill_reference")
    spill_reference = None
    if spill_ref_data:
        spill_reference = deserialize_spill_reference(spill_ref_data)

    return ThreadMessage(
        thread_id=data["thread_id"],
        content=content,
        message_id=data["message_id"],
        timestamp=data["timestamp"],
        is_spilled=data["is_spilled"],
        spill_reference=spill_reference,
        metadata=data["metadata"],
    )


def serialize_thread(thread: Thread) -> Dict[str, Any]:
    """
    Serialize Thread to dict.

    Args:
        thread: Thread object

    Returns:
        Dict representation
    """
    return asdict(thread)


def deserialize_thread(data: Dict[str, Any]) -> Thread:
    """
    Deserialize dict to Thread.

    Args:
        data: Dict representation

    Returns:
        Thread object
    """
    return Thread(
        thread_id=data["thread_id"],
        metadata=data["metadata"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        # Note: messages loaded separately via get_messages
        messages=[],
    )


def serialize_memory(memory: Memory) -> Dict[str, Any]:
    """
    Serialize Memory to dict.

    Args:
        memory: Memory object

    Returns:
        Dict representation
    """
    data = asdict(memory)
    # Convert enum to string
    data["memory_type"] = memory.memory_type.value
    return data


def deserialize_memory(data: Dict[str, Any]) -> Memory:
    """
    Deserialize dict to Memory.

    Args:
        data: Dict representation

    Returns:
        Memory object
    """
    # Convert string to enum
    memory_type_str = data["memory_type"]
    memory_type = MemoryType(memory_type_str)

    return Memory(
        memory_type=memory_type,
        content=data["content"],
        thread_id=data["thread_id"],
        related_message_ids=data["related_message_ids"],
        memory_id=data["memory_id"],
        relevance_score=data["relevance_score"],
        metadata=data["metadata"],
    )


def serialize_spill_reference(ref: SpilledContentReference) -> Dict[str, Any]:
    """
    Serialize SpilledContentReference to dict.

    Args:
        ref: SpilledContentReference object

    Returns:
        Dict representation
    """
    data = asdict(ref)
    # Convert enum to string
    data["spill_type"] = ref.spill_type.value
    return data


def deserialize_spill_reference(data: Dict[str, Any]) -> SpilledContentReference:
    """
    Deserialize dict to SpilledContentReference.

    Args:
        data: Dict representation

    Returns:
        SpilledContentReference object
    """
    # Convert string to enum
    spill_type_str = data["spill_type"]
    spill_type = SpillType(spill_type_str)

    return SpilledContentReference(
        spill_type=spill_type,
        content_location=data["content_location"],
        content_size=data["content_size"],
        content_type=data["content_type"],
        spill_id=data["spill_id"],
        content_preview=data.get("content_preview"),
        retrieval_hint=data.get("retrieval_hint", "use fetch_spilled_content tool with spill_id"),
        metadata=data.get("metadata", {}),
    )


def to_json(data: Any) -> str:
    """
    Convert data to JSON string.

    Args:
        data: Data to serialize

    Returns:
        JSON string
    """
    return json.dumps(data, indent=2)


def from_json(json_str: str) -> Any:
    """
    Parse JSON string to data.

    Args:
        json_str: JSON string

    Returns:
        Parsed data
    """
    return json.loads(json_str)