"""Test insertion syntax parsing and building utilities."""

import pytest
from context_harness.models.insertion_syntax import (
    parse_insertion_syntax,
    build_insertion_syntax,
)
from context_harness.models.base import InsertionSyntaxError


class TestParseInsertionSyntax:
    """Test parse_insertion_syntax function."""

    def test_parse_valid_marker(self):
        """Test parsing valid insertion syntax marker."""
        marker = "[[SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123]]"
        result = parse_insertion_syntax(marker)

        assert result["marker_type"] == "SPILL"
        assert result["type"] == "MESSAGE_SPILL"
        assert result["metadata"]["content_type"] == "tool_response"
        assert result["reference"] == "spill_id=abc123"

    def test_parse_empty_metadata(self):
        """Test parsing marker with empty metadata."""
        marker = "[[SPILL:MESSAGE_SPILL||spill_id=abc123]]"
        result = parse_insertion_syntax(marker)

        assert result["metadata"] == {}
        assert result["reference"] == "spill_id=abc123"

    def test_parse_complex_metadata(self):
        """Test parsing marker with complex metadata."""
        marker = "[[INSERT:GENERATED_DATA|{\"data_type\":\"report\",\"size\":1000}|file=data.json]]"
        result = parse_insertion_syntax(marker)

        assert result["marker_type"] == "INSERT"
        assert result["type"] == "GENERATED_DATA"
        assert result["metadata"]["data_type"] == "report"
        assert result["metadata"]["size"] == 1000
        assert result["reference"] == "file=data.json"

    def test_parse_unknown_marker_type(self):
        """Test parsing unknown marker type (lenient parsing)."""
        marker = "[[UNKNOWN:FUTURE_TYPE|{\"key\":\"value\"}|ref=xyz]]"
        result = parse_insertion_syntax(marker)

        # Should succeed, not reject unknown marker
        assert result["marker_type"] == "UNKNOWN"
        assert result["type"] == "FUTURE_TYPE"

    def test_parse_missing_brackets_raises_error(self):
        """Test parsing marker without brackets raises error."""
        marker = "SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_only_opening_bracket_raises_error(self):
        """Test parsing marker with only opening bracket raises error."""
        marker = "[[SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_only_closing_bracket_raises_error(self):
        """Test parsing marker with only closing bracket raises error."""
        marker = "SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123]]"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_missing_separator_raises_error(self):
        """Test parsing marker with missing separator raises error."""
        marker = "[[SPILL:MESSAGE_SPILL{\"content_type\":\"tool_response\"}|spill_id=abc123]]"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_wrong_number_of_parts_raises_error(self):
        """Test parsing marker with wrong number of parts raises error."""
        marker = "[[SPILL:MESSAGE_SPILL|{\"content_type\":\"tool_response\"}]]"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_malformed_json_raises_error(self):
        """Test parsing marker with malformed JSON raises error."""
        marker = "[[SPILL:MESSAGE_SPILL|{invalid_json}|spill_id=abc123]]"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)

    def test_parse_missing_colon_raises_error(self):
        """Test parsing marker without colon in first part raises error."""
        marker = "[[SPILLMESSAGE_SPILL|{\"content_type\":\"tool_response\"}|spill_id=abc123]]"

        with pytest.raises(InsertionSyntaxError):
            parse_insertion_syntax(marker)


class TestBuildInsertionSyntax:
    """Test build_insertion_syntax function."""

    def test_build_simple_marker(self):
        """Test building simple insertion syntax marker."""
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str="MESSAGE_SPILL",
            metadata={"content_type": "tool_response"},
            reference="spill_id=abc123"
        )

        assert marker.startswith("[[")
        assert marker.endswith("]]")
        assert "SPILL:MESSAGE_SPILL" in marker
        assert "content_type" in marker
        assert "spill_id=abc123" in marker

    def test_build_empty_metadata(self):
        """Test building marker with empty metadata."""
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str="MESSAGE_SPILL",
            metadata={},
            reference="spill_id=abc123"
        )

        assert marker == "[[SPILL:MESSAGE_SPILL|{}|spill_id=abc123]]"

    def test_build_complex_metadata(self):
        """Test building marker with complex metadata."""
        marker = build_insertion_syntax(
            marker_type="INSERT",
            type_str="GENERATED_DATA",
            metadata={"data_type": "report", "size": 1000},
            reference="file=data.json"
        )

        assert "INSERT:GENERATED_DATA" in marker
        assert "data_type" in marker
        assert "size" in marker
        assert "file=data.json" in marker


class TestRoundTrip:
    """Test round-trip: build then parse."""

    def test_round_trip_simple(self):
        """Test building and parsing returns same data."""
        original_metadata = {"content_type": "tool_response", "size": 1000}
        original_reference = "spill_id=abc123"

        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str="MESSAGE_SPILL",
            metadata=original_metadata,
            reference=original_reference
        )

        parsed = parse_insertion_syntax(marker)

        assert parsed["marker_type"] == "SPILL"
        assert parsed["type"] == "MESSAGE_SPILL"
        assert parsed["metadata"] == original_metadata
        assert parsed["reference"] == original_reference

    def test_round_trip_empty_metadata(self):
        """Test round-trip with empty metadata."""
        marker = build_insertion_syntax(
            marker_type="SPILL",
            type_str="MESSAGE_SPILL",
            metadata={},
            reference="spill_id=xyz"
        )

        parsed = parse_insertion_syntax(marker)

        assert parsed["metadata"] == {}
        assert parsed["reference"] == "spill_id=xyz"