"""Root-level MCP entrypoint for mcp dev and python run_graph_mcp.py."""
from agent_core.graph_mcp_server import mcp

if __name__ == '__main__':
    mcp.run()
