"""Unit tests for the FieldMapper class."""

from unittest.mock import Mock

import pytest

from mcp_jira_python.field_mapper import FieldMapper


@pytest.fixture
def mock_jira_fields() -> list[dict]:
    """Sample field data mimicking Jira API response."""
    return [
        {
            "id": "summary",
            "name": "Summary",
            "custom": False,
            "schema": {"type": "string"},
        },
        {
            "id": "description",
            "name": "Description",
            "custom": False,
            "schema": {"type": "string"},
        },
        {
            "id": "customfield_10001",
            "name": "Story Points",
            "custom": True,
            "schema": {"type": "number"},
        },
        {
            "id": "customfield_10002",
            "name": "Sprint",
            "custom": True,
            "schema": {"type": "array"},
        },
        {
            "id": "customfield_10003",
            "name": "Epic Link",
            "custom": True,
            "schema": {"type": "string"},
        },
    ]


@pytest.fixture
def mock_jira(mock_jira_fields: list[dict]) -> Mock:
    """Mock Jira client with field data."""
    jira = Mock()
    jira.fields.return_value = mock_jira_fields
    return jira


@pytest.fixture
def field_mapper(mock_jira: Mock) -> FieldMapper:
    """Create a FieldMapper with mock data."""
    mapper = FieldMapper(mock_jira)
    mapper.initialize()
    return mapper


@pytest.mark.unit
class TestFieldMapper:
    """Tests for FieldMapper class."""

    def test_initialization(self, field_mapper: FieldMapper) -> None:
        """Test that mapper initializes correctly."""
        assert len(field_mapper) == 5

    def test_get_id_by_name(self, field_mapper: FieldMapper) -> None:
        """Test getting field ID by name."""
        assert field_mapper.get_id("Story Points") == "customfield_10001"
        assert field_mapper.get_id("Summary") == "summary"

    def test_get_id_case_insensitive(self, field_mapper: FieldMapper) -> None:
        """Test that name lookup is case-insensitive."""
        assert field_mapper.get_id("story points") == "customfield_10001"
        assert field_mapper.get_id("STORY POINTS") == "customfield_10001"

    def test_get_id_not_found(self, field_mapper: FieldMapper) -> None:
        """Test that None is returned for unknown fields."""
        assert field_mapper.get_id("Unknown Field") is None

    def test_get_name_by_id(self, field_mapper: FieldMapper) -> None:
        """Test getting field name by ID."""
        assert field_mapper.get_name("customfield_10001") == "Story Points"
        assert field_mapper.get_name("summary") == "Summary"

    def test_get_name_not_found(self, field_mapper: FieldMapper) -> None:
        """Test that None is returned for unknown IDs."""
        assert field_mapper.get_name("customfield_99999") is None

    def test_is_custom_field(self, field_mapper: FieldMapper) -> None:
        """Test custom field identification."""
        assert field_mapper.is_custom_field("customfield_10001") is True
        assert field_mapper.is_custom_field("summary") is False

    def test_get_custom_fields(self, field_mapper: FieldMapper) -> None:
        """Test getting all custom fields."""
        custom_fields = field_mapper.get_custom_fields()
        assert len(custom_fields) == 3
        names = [f["name"] for f in custom_fields]
        assert "Story Points" in names
        assert "Sprint" in names
        assert "Epic Link" in names

    def test_get_field_metadata(self, field_mapper: FieldMapper) -> None:
        """Test getting full field metadata."""
        field = field_mapper.get_field("customfield_10001")
        assert field is not None
        assert field["name"] == "Story Points"
        assert field["custom"] is True
        assert field["schema"]["type"] == "number"

    def test_translate_fields_names_to_ids(self, field_mapper: FieldMapper) -> None:
        """Test translating field names to IDs."""
        input_fields = {
            "Story Points": 5,
            "summary": "Test Issue",  # Already an ID
            "Sprint": ["Sprint 1"],
        }
        translated = field_mapper.translate_fields(input_fields)

        assert translated["customfield_10001"] == 5
        assert translated["summary"] == "Test Issue"
        assert translated["customfield_10002"] == ["Sprint 1"]

    def test_translate_fields_preserves_ids(self, field_mapper: FieldMapper) -> None:
        """Test that existing IDs are preserved."""
        input_fields = {
            "customfield_10001": 5,
            "customfield_10002": ["Sprint 1"],
        }
        translated = field_mapper.translate_fields(input_fields)

        assert translated == input_fields

    def test_translate_field_names_ids_to_names(self, field_mapper: FieldMapper) -> None:
        """Test translating field IDs to names."""
        raw_fields = {
            "customfield_10001": 5,
            "summary": "Test Issue",
            "unknownfield": "value",
        }
        translated = field_mapper.translate_field_names(raw_fields)

        assert translated["Story Points"] == 5
        assert translated["Summary"] == "Test Issue"
        assert translated["unknownfield"] == "value"

    def test_contains_by_name(self, field_mapper: FieldMapper) -> None:
        """Test __contains__ with field name."""
        assert "Story Points" in field_mapper
        assert "Unknown Field" not in field_mapper

    def test_contains_by_id(self, field_mapper: FieldMapper) -> None:
        """Test __contains__ with field ID."""
        assert "customfield_10001" in field_mapper
        assert "customfield_99999" not in field_mapper

    def test_refresh(self, mock_jira: Mock, field_mapper: FieldMapper) -> None:
        """Test that refresh reloads field data."""
        # Modify the mock to return different data
        mock_jira.fields.return_value = [{"id": "new_field", "name": "New Field", "custom": False}]

        field_mapper.refresh()

        assert len(field_mapper) == 1
        assert field_mapper.get_id("New Field") == "new_field"
        assert field_mapper.get_id("Story Points") is None  # Old field gone

    def test_lazy_initialization(self, mock_jira: Mock) -> None:
        """Test that mapper initializes lazily on first use."""
        mapper = FieldMapper(mock_jira)

        # Should not have called fields() yet
        mock_jira.fields.assert_not_called()

        # Access a method that requires initialization
        _ = mapper.get_id("Summary")

        # Now it should have been called
        mock_jira.fields.assert_called_once()

