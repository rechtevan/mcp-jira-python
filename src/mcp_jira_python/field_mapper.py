"""Field mapping service for translating between field names and IDs.

This module provides a FieldMapper class that caches Jira field metadata
and provides bidirectional lookups between human-readable field names
and internal field IDs (e.g., customfield_12345).
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jira import JIRA


class FieldMapper:
    """Maps between Jira field names and IDs.

    This class fetches field metadata from Jira and provides:
    - name -> id lookups
    - id -> name lookups
    - Field type information
    - Custom field identification

    Example:
        >>> mapper = FieldMapper(jira_client)
        >>> mapper.get_id("Story Points")
        'customfield_10001'
        >>> mapper.get_name("customfield_10001")
        'Story Points'
    """

    def __init__(self, jira: "JIRA") -> None:
        """Initialize the field mapper.

        Args:
            jira: An authenticated JIRA client instance.
        """
        self._jira = jira
        self._fields: list[dict[str, Any]] = []
        self._name_to_id: dict[str, str] = {}
        self._id_to_name: dict[str, str] = {}
        self._id_to_field: dict[str, dict[str, Any]] = {}
        self._custom_fields: set[str] = set()
        self._initialized = False

    def initialize(self) -> None:
        """Fetch and cache field metadata from Jira.

        This method should be called once after creating the mapper.
        It fetches all field definitions and builds the lookup caches.
        """
        if self._initialized:
            return

        self._fields = self._jira.fields()
        self._build_caches()
        self._initialized = True

    def _build_caches(self) -> None:
        """Build internal lookup caches from field data."""
        self._name_to_id.clear()
        self._id_to_name.clear()
        self._id_to_field.clear()
        self._custom_fields.clear()

        for field in self._fields:
            field_id = field["id"]
            field_name = field["name"]
            is_custom = field.get("custom", False)

            self._name_to_id[field_name] = field_id
            self._name_to_id[field_name.lower()] = field_id  # Case-insensitive
            self._id_to_name[field_id] = field_name
            self._id_to_field[field_id] = field

            if is_custom:
                self._custom_fields.add(field_id)

    def refresh(self) -> None:
        """Refresh the field cache from Jira.

        Call this if fields have been added/modified in Jira.
        """
        self._initialized = False
        self.initialize()

    def get_id(self, name: str) -> str | None:
        """Get the field ID for a given field name.

        Args:
            name: The human-readable field name (case-insensitive).

        Returns:
            The field ID (e.g., 'customfield_12345') or None if not found.
        """
        self._ensure_initialized()
        # Try exact match first, then case-insensitive
        return self._name_to_id.get(name) or self._name_to_id.get(name.lower())

    def get_name(self, field_id: str) -> str | None:
        """Get the field name for a given field ID.

        Args:
            field_id: The field ID (e.g., 'customfield_12345').

        Returns:
            The human-readable field name or None if not found.
        """
        self._ensure_initialized()
        return self._id_to_name.get(field_id)

    def get_field(self, field_id: str) -> dict[str, Any] | None:
        """Get the full field metadata for a given field ID.

        Args:
            field_id: The field ID.

        Returns:
            The field metadata dict or None if not found.
        """
        self._ensure_initialized()
        return self._id_to_field.get(field_id)

    def is_custom_field(self, field_id: str) -> bool:
        """Check if a field is a custom field.

        Args:
            field_id: The field ID to check.

        Returns:
            True if the field is a custom field, False otherwise.
        """
        self._ensure_initialized()
        return field_id in self._custom_fields

    def get_custom_fields(self) -> list[dict[str, Any]]:
        """Get all custom fields.

        Returns:
            List of custom field metadata dicts.
        """
        self._ensure_initialized()
        return [self._id_to_field[fid] for fid in self._custom_fields if fid in self._id_to_field]

    def get_all_fields(self) -> list[dict[str, Any]]:
        """Get all fields.

        Returns:
            List of all field metadata dicts.
        """
        self._ensure_initialized()
        return self._fields.copy()

    def translate_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Translate field names to IDs in a fields dict.

        This allows users to specify fields by name instead of ID.
        Field IDs are passed through unchanged.

        Args:
            fields: Dict with field names or IDs as keys.

        Returns:
            Dict with all keys translated to field IDs.

        Example:
            >>> mapper.translate_fields({"Story Points": 5})
            {"customfield_10001": 5}
        """
        self._ensure_initialized()
        translated: dict[str, Any] = {}

        for key, value in fields.items():
            # If it's already an ID (starts with customfield_ or is a known system field)
            if key in self._id_to_name:
                translated[key] = value
            # Try to translate name to ID
            elif field_id := self.get_id(key):
                translated[field_id] = value
            else:
                # Keep as-is (might be a system field like 'summary')
                translated[key] = value

        return translated

    def translate_field_names(self, raw_fields: dict[str, Any]) -> dict[str, Any]:
        """Translate field IDs to names in a raw fields dict.

        This is used to make API responses more human-readable.

        Args:
            raw_fields: Dict with field IDs as keys (from Jira API).

        Returns:
            Dict with field names as keys where possible.
        """
        self._ensure_initialized()
        translated: dict[str, Any] = {}

        for key, value in raw_fields.items():
            if name := self.get_name(key):
                translated[name] = value
            else:
                translated[key] = value

        return translated

    def _ensure_initialized(self) -> None:
        """Ensure the mapper has been initialized."""
        if not self._initialized:
            self.initialize()

    def __len__(self) -> int:
        """Return the number of fields."""
        self._ensure_initialized()
        return len(self._fields)

    def __contains__(self, key: str) -> bool:
        """Check if a field name or ID exists."""
        self._ensure_initialized()
        return key in self._name_to_id or key in self._id_to_name
