import asyncio
import os
from pathlib import Path
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from jira import JIRA
from dotenv import load_dotenv
#from tools import get_all_tools, get_tool  # Changed from relative import
from mcp_jira_python.tools import get_all_tools, get_tool

# Load environment from .env file (if present)
# Checks for .env.jira first, then falls back to .env
# Environment variables passed via MCP client config will override these
env_file = Path(".env.jira")
if not env_file.exists():
    env_file = Path(".env")
load_dotenv(env_file)

server = Server("jira-api")

# Jira client setup 
# Required: JIRA_HOST (can be just hostname or full URL)
# Auth option 1 (Jira Cloud): JIRA_EMAIL + JIRA_API_TOKEN
# Auth option 2 (Jira Server/DC with PAT): JIRA_BEARER_TOKEN
JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_BEARER_TOKEN = os.getenv("JIRA_BEARER_TOKEN")

if not JIRA_HOST:
    raise ValueError("Missing required environment variable: JIRA_HOST")

# Build server URL - support both bare hostname and full URL
if JIRA_HOST.startswith("http://") or JIRA_HOST.startswith("https://"):
    jira_server_url = JIRA_HOST
else:
    jira_server_url = f"https://{JIRA_HOST}"

# Initialize Jira client based on available auth method
if JIRA_BEARER_TOKEN:
    # Jira Server/Data Center with Personal Access Token (PAT)
    jira_client = JIRA(
        server=jira_server_url,
        token_auth=JIRA_BEARER_TOKEN
    )
elif JIRA_EMAIL and JIRA_API_TOKEN:
    # Jira Cloud with email + API token
    jira_client = JIRA(
        server=jira_server_url,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
    )
else:
    raise ValueError(
        "Missing authentication credentials. Provide either:\n"
        "  - JIRA_BEARER_TOKEN (for Jira Server/DC with PAT), or\n"
        "  - JIRA_EMAIL + JIRA_API_TOKEN (for Jira Cloud)"
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return get_all_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    try:
        tool = get_tool(name)
        tool.jira = jira_client
        return await tool.execute(arguments or {})
    except Exception as e:
        return [types.TextContent(
            type="text", 
            text=f"Operation failed: {str(e)}",
            isError=True
        )]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-api",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
