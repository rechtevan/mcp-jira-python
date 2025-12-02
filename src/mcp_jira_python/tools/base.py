from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from jira import JIRA


class BaseTool(ABC):
    def __init__(self) -> None:
        self.jira: JIRA | None = None

    @abstractmethod
    def get_tool_definition(self) -> Tool:
        """Return tool metadata."""
        pass

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute tool with given arguments."""
        pass
