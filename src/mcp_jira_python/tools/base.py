"""Base class for all MCP Jira tools.

All tools inherit from BaseTool and implement:
- get_tool_definition(): Returns MCP Tool schema
- execute(): Performs the tool action
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from jira import JIRA


class BaseTool(ABC):
    """Abstract base class for MCP Jira tools.

    Attributes:
        jira: JIRA client instance, set by the server before execution.
    """

    def __init__(self) -> None:
        """Initialize the tool with no JIRA client."""
        self.jira: JIRA | None = None

    @abstractmethod
    def get_tool_definition(self) -> Tool:
        """Return the MCP tool definition.

        Returns:
            Tool with name, description, and input schema.
        """
        pass

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute the tool with given arguments.

        Args:
            arguments: Tool-specific arguments from MCP client.

        Returns:
            List of TextContent with the result.

        Raises:
            ValueError: If required arguments are missing.
            Exception: If the tool operation fails.
        """
        pass
