"""
FastMCP Client for Live SaaS Backend
Handles JSON-RPC calls to remote WorkWeek and ServiceImmediately FastMCP servers.
Includes structured logging for API request tracing.
"""

import httpx
from typing import Dict, Any, Optional
from config import WORKWEEK_MCP_URL, SERVICE_IMMEDIATELY_MCP_URL, MCP_AUTH_TOKEN
from logger import logger, log_event

def call_mcp_tool(service_url: str, tool_name: str, arguments: Dict[str, Any], token: str = MCP_AUTH_TOKEN) -> Dict[str, Any]:
    """
    Executes a JSON-RPC tools/call request against a remote FastMCP endpoint with tracing log.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    log_event("MCP_REQUEST_OUTBOUND", {
        "service_url": service_url,
        "tool_name": tool_name,
        "arguments": arguments
    })

    try:
        response = httpx.post(service_url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            err_msg = data["error"].get("message", "MCP Tool Execution Error")
            log_event("MCP_RESPONSE_ERROR", {"tool_name": tool_name, "error": err_msg})
            return {"error": err_msg}
            
        result = data.get("result", {})
        log_event("MCP_RESPONSE_SUCCESS", {"tool_name": tool_name, "raw_result": str(result)[:300]})

        structured = result.get("structuredContent")
        if structured:
            return structured
            
        content_items = result.get("content", [])
        if content_items and isinstance(content_items, list):
            text_val = content_items[0].get("text", "")
            return {"result": text_val}
            
        return result
    except Exception as e:
        log_event("MCP_HTTP_EXCEPTION", {"tool_name": tool_name, "exception": str(e)})
        return {"error": f"MCP Remote Call Failed: {str(e)}"}

def call_workweek_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to execute a WorkWeek MCP tool."""
    return call_mcp_tool(WORKWEEK_MCP_URL, tool_name, arguments)

def call_service_immediately_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to execute a ServiceImmediately MCP tool."""
    return call_mcp_tool(SERVICE_IMMEDIATELY_MCP_URL, tool_name, arguments)
