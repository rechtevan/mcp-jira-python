"""Tool for auditing issue quality and completeness."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class AuditIssueTool(BaseTool):
    """Tool to audit issue quality against best practices."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="audit_issue",
            description=(
                "Audit a Jira issue for quality and completeness.\n\n"
                "Checks for:\n"
                "- Required fields presence\n"
                "- Description completeness (acceptance criteria, DoD)\n"
                "- Story points for estimable items\n"
                "- Epic link for trackable items\n"
                "- Proper labeling and components\n\n"
                "Returns a quality score and actionable recommendations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., 'PROJ-123')",
                    },
                    "checkDefinitionOfDone": {
                        "type": "boolean",
                        "description": "Check for Definition of Done criteria (default: true)",
                        "default": True,
                    },
                    "checkAcceptanceCriteria": {
                        "type": "boolean",
                        "description": "Check for acceptance criteria (default: true)",
                        "default": True,
                    },
                },
                "required": ["issueKey"],
            },
        )

    def _check_description_quality(
        self,
        description: str | None,
        check_dod: bool,
        check_ac: bool,
    ) -> tuple[list[str], list[str]]:
        """Check description for quality indicators.

        Returns:
            Tuple of (issues found, suggestions)
        """
        issues: list[str] = []
        suggestions: list[str] = []

        if not description:
            issues.append("No description provided")
            suggestions.append("Add a clear description of the work required")
            return issues, suggestions

        desc_lower = description.lower()
        desc_length = len(description)

        # Check minimum length
        if desc_length < 50:
            issues.append("Description is very short")
            suggestions.append("Expand description with more context")

        # Check for acceptance criteria
        if check_ac:
            ac_keywords = ["acceptance criteria", "given", "when", "then", "ac:", "criteria:"]
            has_ac = any(kw in desc_lower for kw in ac_keywords)
            if not has_ac:
                issues.append("No acceptance criteria found")
                suggestions.append("Add acceptance criteria using Given/When/Then or bullet points")

        # Check for definition of done
        if check_dod:
            dod_keywords = [
                "definition of done",
                "dod",
                "done when",
                "complete when",
                "✓",
                "☑",
                "- [x]",
                "- [ ]",
            ]
            has_dod = any(kw in desc_lower for kw in dod_keywords)
            if not has_dod:
                suggestions.append("Consider adding Definition of Done checklist items")

        return issues, suggestions

    def _get_custom_field(self, fields: Any, field_names: list[str]) -> Any:
        """Get first matching custom field value."""
        for attr in field_names:
            if hasattr(fields, attr):
                value = getattr(fields, attr)
                if value is not None:
                    return value
        return None

    def _check_estimable_fields(
        self, fields: Any, issue_type: str, metadata: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Check story points and epic link for estimable issue types."""
        issues: list[str] = []
        suggestions: list[str] = []

        if issue_type not in ("story", "task", "bug"):
            return issues, suggestions

        # Story points
        story_points = self._get_custom_field(
            fields, ["customfield_10016", "customfield_10026", "story_points"]
        )
        if story_points is None:
            issues.append("No story points assigned")
            suggestions.append("Add story point estimate for capacity planning")
        else:
            metadata["storyPoints"] = story_points

        # Epic link
        epic_link = self._get_custom_field(
            fields, ["customfield_10014", "customfield_10008", "parent"]
        )
        if epic_link is None:
            suggestions.append("Consider linking to an Epic for better tracking")
        elif hasattr(epic_link, "key"):
            metadata["epicLink"] = epic_link.key
        else:
            metadata["epicLink"] = str(epic_link)

        return issues, suggestions

    def _check_issue_metadata(self, issue: Any) -> tuple[list[str], list[str], dict[str, Any]]:
        """Check issue metadata quality."""
        issues: list[str] = []
        suggestions: list[str] = []
        metadata: dict[str, Any] = {}

        fields = issue.fields
        issue_type = str(fields.issuetype).lower()
        metadata["issueType"] = str(fields.issuetype)

        # Check estimable fields (story points, epic link)
        est_issues, est_suggestions = self._check_estimable_fields(fields, issue_type, metadata)
        issues.extend(est_issues)
        suggestions.extend(est_suggestions)

        # Priority
        if fields.priority:
            metadata["priority"] = str(fields.priority)
        else:
            issues.append("No priority set")
            suggestions.append("Set priority to help with triage")

        # Assignee
        if fields.assignee:
            name = getattr(fields.assignee, "displayName", str(fields.assignee))
            metadata["assignee"] = name
        else:
            suggestions.append("Assign to a team member when ready")

        # Labels and components
        if hasattr(fields, "labels") and fields.labels:
            metadata["labels"] = list(fields.labels)
        else:
            suggestions.append("Consider adding labels for categorization")

        if hasattr(fields, "components") and fields.components:
            metadata["components"] = [str(c) for c in fields.components]

        return issues, suggestions, metadata

    def _calculate_score(self, issues: list[str], suggestions: list[str]) -> int:
        """Calculate quality score (0-100).

        Issues reduce score more than missing suggestions.
        """
        score = 100
        score -= len(issues) * 15  # Each issue costs 15 points
        score -= len(suggestions) * 5  # Each suggestion costs 5 points
        return max(0, min(100, score))

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        check_dod = arguments.get("checkDefinitionOfDone", True)
        check_ac = arguments.get("checkAcceptanceCriteria", True)

        if not issue_key:
            raise ValueError("issueKey is required")

        try:
            issue = self.jira.issue(issue_key)

            all_issues: list[str] = []
            all_suggestions: list[str] = []

            # Check description quality
            desc_issues, desc_suggestions = self._check_description_quality(
                issue.fields.description,
                check_dod,
                check_ac,
            )
            all_issues.extend(desc_issues)
            all_suggestions.extend(desc_suggestions)

            # Check metadata
            meta_issues, meta_suggestions, metadata = self._check_issue_metadata(issue)
            all_issues.extend(meta_issues)
            all_suggestions.extend(meta_suggestions)

            # Calculate score
            score = self._calculate_score(all_issues, all_suggestions)

            # Determine quality level
            if score >= 90:
                quality = "Excellent"
            elif score >= 75:
                quality = "Good"
            elif score >= 50:
                quality = "Needs Improvement"
            else:
                quality = "Poor"

            result: dict[str, Any] = {
                "issueKey": issue_key,
                "summary": issue.fields.summary,
                "qualityScore": score,
                "qualityLevel": quality,
                "issues": all_issues,
                "suggestions": all_suggestions,
                "metadata": metadata,
            }

            # Add quick actions based on findings
            if all_issues or all_suggestions:
                result["quickActions"] = []
                if "No description provided" in all_issues:
                    result["quickActions"].append("Use update_issue to add description")
                if "No story points assigned" in all_issues:
                    result["quickActions"].append("Use update_issue to add story points")

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to audit issue: {e!s}") from e
