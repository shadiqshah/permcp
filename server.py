import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("yo-babes")


@mcp.tool()
def greet() -> str:
    """Greet the user."""
    return "yo babes how are you"


if __name__ == "__main__":
    if os.environ.get("MCP_TRANSPORT") == "http":
        # 0.0.0.0 so tunnel Host headers (cloudflared/ngrok) pass the SDK's host check.
        mcp.run("streamable-http", host="0.0.0.0", port=8000)
    else:
        mcp.run()
