# mcp_servers/odoo_mcp.py
"""
Odoo MCP Server
Provides tools to interact with an Odoo instance via JSON-RPC.
"""
import urllib.request
import json
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("odoo")

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")


def json_rpc(url: str, method: str, params: Dict[str, Any]) -> Any:
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if "error" in result:
                raise Exception(result["error"])
            return result.get("result")
    except Exception as e:
        return f"Error connecting to Odoo: {str(e)}"


def authenticate() -> Optional[int]:
    """Authenticate with Odoo and return user uid."""
    url = f"{ODOO_URL}/jsonrpc"
    try:
        result = json_rpc(
            url,
            "call",
            {
                "service": "common",
                "method": "authenticate",
                "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}],
            },
        )
        return result
    except Exception as e:
        print(f"Auth error: {e}")
        return None


@mcp.tool()
def odoo_execute_kw(
    model: str, method: str, args: List[Any], kwargs: Dict[str, Any] = None
) -> Any:
    """
    Execute an Odoo ORM method via JSON-RPC.

    Args:
        model: The Odoo model name (e.g., 'res.partner', 'account.move')
        method: The ORM method to call (e.g., 'search_read', 'create', 'write')
        args: List of positional arguments for the method. (e.g., [[('is_company', '=', True)]])
        kwargs: Keyword arguments for the method (e.g., {'limit': 5, 'fields': ['name']})
    """
    kwargs = kwargs or {}
    uid = authenticate()
    if not isinstance(uid, int):
        return f"Authentication failed. UID: {uid}"

    url = f"{ODOO_URL}/jsonrpc"
    try:
        result = json_rpc(
            url,
            "call",
            {
                "service": "object",
                "method": "execute_kw",
                "args": [ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs],
            },
        )
        return result
    except Exception as e:
        return f"Error executing {method} on {model}: {str(e)}"


@mcp.tool()
def odoo_get_version() -> Any:
    """Get the Odoo server version."""
    url = f"{ODOO_URL}/jsonrpc"
    try:
        result = json_rpc(
            url, "call", {"service": "common", "method": "version", "args": []}
        )
        return result
    except Exception as e:
        return f"Error getting version: {str(e)}"


if __name__ == "__main__":
    mcp.run()
