"""
This module provides a standard I/O interface to run the MCP server.
It imports the MCP server instance and starts its run loop using stdio communication.
"""
from server import mcp


if __name__ == "__main__":
    mcp.run()