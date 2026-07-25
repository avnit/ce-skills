"""Shared MCP client transport helpers for Customer Engineering agent skills."""

import asyncio
import inspect
import json
import logging
import os
import pathlib
from typing import Any, Dict, Optional

import ce_config

DEFAULT_MCP_SERVER_URL = "https://closed-loop-mcp-529861882743.us-west1.run.app/mcp"

def find_mcp_proxy_binary() -> Optional[str]:
    """Finds the local mcp_session_proxy wrapper script if available on workstation."""
    env_path = os.environ.get("MCP_PROXY_BINARY")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    for candidate_name in ["mcp_session_proxy", "mcp_session_proxy_bin"]:
        candidate = repo_root / "bin" / candidate_name
        if candidate.is_file() and os.access(str(candidate), os.X_OK):
            # Test if candidate actually executes without runfiles/environment error
            try:
                import subprocess
                res = subprocess.run([str(candidate), "--help"], capture_output=True, timeout=1)
                if res.returncode == 0:
                    return str(candidate)
            except Exception:
                pass

    return None


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


_get_streamable_client_kwargs = get_streamable_client_kwargs


def _parse_mcp_response(res: Any) -> Any:
    """Parses MCP ClientSession result object into structured data."""
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


async def call_mcp_tool_async(
    tool_name: str, arguments: Dict[str, Any], url: str
) -> Any:
    """
    Invokes a tool on a remote MCP server.
    Prioritizes bin/mcp_session_proxy stdio transport when available for Corp SSO / Uberproxy.
    Falls back to direct streamable-http client.
    """
    proxy_binary = find_mcp_proxy_binary()
    if proxy_binary:
        try:
            from mcp.client.session import ClientSession
            from mcp.client.stdio import stdio_client, StdioServerParameters
        except (ImportError, ModuleNotFoundError) as e:
            raise RuntimeError(
                "CLOSED_LOOP_TRANSPORT=mcp requires extra deps: pip3 install -r <repo>/requirements.txt "
                "(or run via: uv run --with-requirements requirements.txt python3 ...)"
            ) from e

        logging.info(f"Connecting to MCP server via session proxy: {proxy_binary} --mcp_server={url}")
        server_params = StdioServerParameters(
            command=proxy_binary,
            args=[f"--mcp_server={url}"],
            env=dict(os.environ),
        )
        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    res = await session.call_tool(tool_name, arguments=arguments)
                    return _parse_mcp_response(res)
        except BaseException as e:
            logging.warning(f"MCP session proxy stdio call failed ({e}). Falling back to streamable HTTP.")

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
                return _parse_mcp_response(res)
    except Exception as e:
        if "CLOSED_LOOP_TRANSPORT=mcp requires extra deps" in str(e):
            raise
        raise RuntimeError(f"MCP Server communication error: {e}") from e


def call_mcp_tool(
    tool_name: str, arguments: Dict[str, Any], url: Optional[str] = None
) -> Any:
    """Synchronous wrapper to invoke a tool on a remote MCP server."""
    if not url:
        url = (
            os.environ.get("CE_MCP_SERVER_URL")
            or ce_config.get("mcp_server_url")
            or DEFAULT_MCP_SERVER_URL
        )
    return asyncio.run(call_mcp_tool_async(tool_name, arguments, url))
