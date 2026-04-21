"""Insertion syntax parsing and building utilities."""

import json
from typing import Dict, Any
from context_harness.models.base import InsertionSyntaxError


def parse_insertion_syntax(marker: str) -> Dict[str, Any]:
    """
    Parse insertion syntax marker into structured dict.

    Args:
        marker: Insertion syntax string [[MARKER:type|metadata_json|reference]]

    Returns:
        Dict with keys: marker_type, type, metadata, reference

    Raises:
        InsertionSyntaxError: If marker format invalid or JSON malformed
    """
    # Validate format: must start with [[ and end with ]]
    if not marker.startswith("[[") or not marker.endswith("]]"):
        raise InsertionSyntaxError(f"Marker must be enclosed in [[...]]: {marker}")

    # Strip brackets
    inner = marker[2:-2]

    # Split by '|' separator
    parts = inner.split("|")

    if len(parts) != 3:
        raise InsertionSyntaxError(f"Marker must have 3 parts separated by '|': {marker}")

    # Parse MARKER:type
    marker_type_part = parts[0]
    if ":" not in marker_type_part:
        raise InsertionSyntaxError(f"First part must contain MARKER:type: {marker_type_part}")

    marker_type, type_str = marker_type_part.split(":", 1)

    # Parse metadata JSON
    metadata_json = parts[1]
    try:
        metadata = json.loads(metadata_json) if metadata_json else {}
    except json.JSONDecodeError as e:
        raise InsertionSyntaxError(f"Invalid JSON in metadata: {metadata_json}") from e

    # Parse reference (as-is, no parsing logic)
    reference = parts[2]

    return {
        "marker_type": marker_type,
        "type": type_str,
        "metadata": metadata,
        "reference": reference,
    }


def build_insertion_syntax(
    marker_type: str,
    type_str: str,
    metadata: Dict[str, Any],
    reference: str
) -> str:
    """
    Build insertion syntax marker from components.

    Args:
        marker_type: Marker category (SPILL, INSERT, LINK)
        type_str: Type string (MESSAGE_SPILL, GENERATED_DATA)
        metadata: Metadata dict (will be JSON encoded)
        reference: Reference string

    Returns:
        Insertion syntax string [[MARKER:type|metadata_json|reference]]
    """
    # Format MARKER:type
    marker_type_part = f"{marker_type}:{type_str}"

    # JSON encode metadata
    metadata_json = json.dumps(metadata) if metadata else "{}"

    # Concatenate with '|' separators and wrap in [[...]]
    marker = f"[[{marker_type_part}|{metadata_json}|{reference}]]"

    return marker