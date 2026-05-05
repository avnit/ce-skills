---
id: hello-mcp-cloudrun
summary: Learn how to build and deploy a simple MCP server on Cloud Run.
authors: Jetski
keywords: category:Cloud,product:CloudRun,docType:Codelab
layout: paginated
---

# Hello MCP on Cloud Run

Duration: 15:00

## 1. Introduction
Duration: 02:00

In this codelab, you will learn how to build a simple Model Context Protocol (MCP) server and deploy it to Google Cloud Run.

### What you'll learn
- How to create an MCP server with FastMCP.
- How to deploy it to Cloud Run.
- How to test it.

## 2. Setup
Duration: 03:00

First, create a new directory and initialize a Python project.

```bash
mkdir hello-mcp && cd hello-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp
```

## 3. Create the Server
Duration: 05:00

Create a file named `server.py` with the following content:

```python
from fastmcp import FastMCP
import os
import asyncio

mcp = FastMCP("Hello MCP")

@mcp.tool()
def echo(text: str) -> str:
    """Echoes back the input text."""
    return f"Echo: {text}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    asyncio.run(mcp.run_async(transport="http", host="0.0.0.0", port=port))
```

## 4. Deploy to Cloud Run
Duration: 05:00

Create a `Dockerfile`:

```dockerfile
FROM python:3.13-slim
COPY . /app
WORKDIR /app
RUN pip install fastmcp
EXPOSE $PORT
CMD ["python", "server.py"]
```

Deploy using gcloud:

```bash
gcloud run deploy hello-mcp-server \
    --source=. \
    --no-allow-unauthenticated \
    --region=us-central1
```

> aside positive
> Verification: You should see the service URL in the output.

## 5. Conclusion
Duration: 01:00

Congratulations! You have deployed your first MCP server to Cloud Run.
