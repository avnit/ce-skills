"""Shared MCP client transport helpers for Customer Engineering agent skills."""

import asyncio
import inspect
import json
import logging
import os
from typing import Any, Dict, Optional

import ce_config


def get_mcp_auth_headers(url: str) -> Dict[str, str]:
    """Generates OIDC ID token authorization headers for the target MCP server URL."""
    try:
        from urllib.parse import urlparse
        from google.auth.transport.requests import Request as AuthRequest
        from google.oauth2 import id_token

        parsed = urlparse(url)
        aud = f"{parsed.scheme}://{parsed.netloc}"
        auth_req = AuthRequest()
        token = id_token.fetch_id_token(auth_req, aud)
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        logging.warning(f"Could not fetch OIDC ID token for {url}: {e}")
    return {}


# Backwards-compatible alias
_get_mcp_auth_headers = get_mcp_auth_headers


def get_streamable_client_kwargs(headers: Dict[str, str]) -> Dict[str, Any]:
    """Returns compatible keyword arguments for streamable_http_client across SDK versions."""
    try:
        from mcp.client.streamable_http import streamable_http_client
    except (ImportError, ModuleNotFoundError) as e:
        raise RuntimeError(
            "CLOSED_LOOP_TRANSPORT=mcp requires extra deps: pip3 install -r <repo>/requirements.txt "
            "(or run via: uv run --with-requirements requirements.txt python3 ...)"
        ) from e

    params = inspect.signature(streamable_http_client).parameters
    if "headers" in params:
        return {"headers": headers} if headers else {}
    elif "http_client" in params:
        try:
            import httpx
        except (ImportError, ModuleNotFoundError) as e:
            raise RuntimeError(
                "CLOSED_LOOP_TRANSPORT=mcp requires extra deps: pip3 install -r <repo>/requirements.txt "
                "(or run via: uv run --with-requirements requirements.txt python3 ...)"
            ) from e
        return {"http_client": httpx.AsyncClient(headers=headers)} if headers else {}
    return {}


# Backwards-compatible alias
_get_streamable_client_kwargs = get_streamable_client_kwargs


async def call_mcp_tool_async(
    tool_name: str, arguments: Dict[str, Any], url: str
) -> Any:
    """Invokes a tool on a remote MCP server over streamable-http and returns the structured result."""
    try:
        from mcp.client.session import ClientSession
        from mcp.client.streamable_http import streamable_http_client
    except (ImportError, ModuleNotFoundError) as e:
        raise RuntimeError(
            "CLOSED_LOOP_TRANSPORT=mcp requires extra deps: pip3 install -r <repo>/requirements.txt "
            "(or run via: uv run --with-requirements requirements.txt python3 ...)"
        ) from e

    headers = get_mcp_auth_headers(url)
    kwargs = get_streamable_client_kwargs(headers)
    try:
        async with streamable_http_client(url, **kwargs) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                res = await session.call_tool(tool_name, arguments=arguments)
                if getattr(res, "isError", False):
                    content = getattr(res, "content", [])
                    err_text = (
                        content[0].text
                        if content and hasattr(content[0], "text")
                        else "MCP tool error"
                    )
                    raise RuntimeError(f"MCP tool error: {err_text}")
                structured = getattr(res, "structuredContent", None)
                if structured and isinstance(structured, dict):
                    return structured.get("result", structured)
                content = getattr(res, "content", [])
                text = (
                    content[0].text
                    if content and hasattr(content[0], "text")
                    else "{}"
                )
                return json.loads(text)
    except Exception as e:
        if "CLOSED_LOOP_TRANSPORT=mcp requires extra deps" in str(e):
            raise
        raise RuntimeError(f"MCP Server communication error: {e}") from e


def call_mcp_tool(
    tool_name: str, arguments: Dict[str, Any], url: Optional[str] = None
) -> Any:
    """Synchronous wrapper to invoke a tool on a remote MCP server."""
    if not url:
        url = ce_config.get("mcp_server_url") or os.environ.get("CE_MCP_SERVER_URL")
    if not url:
        raise ValueError(
            "Missing required mcp_server_url in environment or gcp_config.txt for CLOSED_LOOP_TRANSPORT=mcp"
        )
    return asyncio.run(call_mcp_tool_async(tool_name, arguments, url))
