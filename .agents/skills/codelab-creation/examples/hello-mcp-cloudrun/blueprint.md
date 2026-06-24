# Blueprint: Hello MCP on Cloud Run

## Objective

Create a simple Model Context Protocol (MCP) server using FastMCP and deploy it to Google Cloud Run.

## Target Audience

Developers wanting to understand how to host custom tools for LLMs securely on Google Cloud.

## Topology

- **FastMCP**: Python framework for MCP.
- **Cloud Run**: Serverless compute platform.
- **Gemini CLI**: Client to test the MCP server.

## Step-by-Step Plan

1.  **Setup**: Create project directory, initialize Python environment.
2.  **Code**: Write a simple MCP server with one tool (e.g., `echo`).
3.  **Deploy**: Create Dockerfile and deploy to Cloud Run with authentication required.
4.  **Verify**: Configure Gemini CLI to use the remote MCP server and test the tool.

## Key Commands to Verify

- `python3 -m venv .venv`
- `pip install fastmcp`
- `gcloud run deploy`
