import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer

from tools import register_tools


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[dict]:
    """Prepare shared configuration when the server starts."""
    app_state = {
        "api_token": os.environ.get("NEWBOOK_API_TOKEN"),
    }

    yield app_state


server = MCPServer(
    "Christina's RV Park MCP Server",
    lifespan=app_lifespan,
)

register_tools(server)


if __name__ == "__main__":
    server.run()