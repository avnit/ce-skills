# Closed-Loop Learning System (Server & Admin Repository)

This repository contains the backend and frontend management components for the Closed-Loop Learning System.

## Directory Structure

- **`admin_portal/`**: Contains the Streamlit frontend application (`app.py`) for human-in-the-loop curation and approval of incoming lessons learned.
- **`mcp/`**: Contains the FastMCP server (`mcp_server.py`) ready to be deployed on Google Cloud Run. It queries Vertex AI RAG to serve approved knowledge to enterprise agents during their planning phase.
- **`config/`**: Contains `config.json` for externalized configuration of Firebase collections, project IDs, Vertex AI embeddings, and RAG corpus IDs.
- **`doc/`**: Contains system design architecture and GCP project infrastructure tracking logs.

## Quickstart (Using Python Virtual Environment)

Always isolate dependencies using a Python virtual environment (`venv`).

### 1. Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure the System

Edit `config/config.json` with your GCP Project ID (`hyperstack-dev`), Firebase details (`losed-loop-learning`), and Vertex AI RAG Corpus ID.

### 3. Run the Admin Portal Locally

```bash
source .venv/bin/activate
streamlit run admin_portal/app.py
```

### 4. Run the MCP Server Locally

```bash
source .venv/bin/activate
python3 mcp/mcp_server.py
```
