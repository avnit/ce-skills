#!/usr/bin/env python3
"""
RAG MCP Server for Closed-Loop Learning

This MCP Server runs on Cloud Run and exposes a tool for agents to query
the Vertex AI RAG corpus or live Firestore Database for generalized team knowledge.
"""

import sys
import json
import os
import glob
from mcp.server.fastmcp import FastMCP

# Load externalized configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except Exception as e:
    print(f"Failed to load configuration from {CONFIG_PATH}: {e}", file=sys.stderr)
    CONFIG = {}

STORAGE_CFG = CONFIG.get("storage", {})
VERTEX_CFG = CONFIG.get("vertex_ai", {})

# Initialize FastMCP Server
mcp = FastMCP("vertex-rag-mcp")

# Resolve mock directory
MOCK_DB_DIR = os.path.expanduser(STORAGE_CFG.get("local_mock_directory", "~/.gemini/jetski/knowledge/closed_loop_learning/lessons"))

def fetch_approved_lessons():
    """Fetches approved lessons from live Firestore or local mock DB"""
    lessons = []
    if STORAGE_CFG.get("backend_type") == "firebase":
        try:
            from google.cloud import firestore
            db = firestore.Client(
                project=STORAGE_CFG.get("firebase_project_id"),
                database=STORAGE_CFG.get("firebase_database_id", "(default)")
            )
            approved_col = STORAGE_CFG.get("firebase_approved_collection", "approved_lessons")
            docs = db.collection(approved_col).stream()
            for doc in docs:
                lessons.append(doc.to_dict())
        except Exception as e:
            print(f"Firestore fetch error: {e}", file=sys.stderr)
    else:
        if not os.path.exists(MOCK_DB_DIR):
            return lessons
            
        for file_path in glob.glob(os.path.join(MOCK_DB_DIR, "*.json")):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get("status") == "approved":
                        lessons.append(data)
            except Exception:
                pass
    return lessons

@mcp.tool()
def query_team_knowledge(query: str, topic_filters: list[str] = None) -> str:
    """
    Query the team's centralized Vertex AI RAG corpus / Firestore for generalized lessons learned, 
    best practices, and known gotchas.
    
    Args:
        query: The search query describing the problem or architecture you are planning.
        topic_filters: Optional list of topics (e.g., ["GKE", "VPC"]) to narrow the search.
        
    Returns:
        A formatted string of relevant lessons and guidelines.
    """
    corpus_id = VERTEX_CFG.get("rag_corpus_id")
    if corpus_id and "YOUR_" not in corpus_id:
        try:
            import vertexai
            from vertexai.preview import rag
            
            project = VERTEX_CFG.get("project_id", "hyperstack-dev")
            location = VERTEX_CFG.get("location", "us-central1")
            vertexai.init(project=project, location=location)
            
            search_query = query
            if topic_filters:
                search_query = f"{', '.join(topic_filters)}: {query}"
                
            response = rag.retrieval_query(
                text=search_query,
                rag_resources=[rag.RagResource(rag_corpus=corpus_id)],
                similarity_top_k=5
            )
            
            if response and response.contexts and response.contexts.contexts:
                output = f"Here are the team's lessons learned retrieved from Vertex AI RAG Corpus ({corpus_id}):\n\n"
                for idx, ctx in enumerate(response.contexts.contexts, 1):
                    output += f"--- Result {idx} (Distance: {ctx.distance:.2f}) ---\n{ctx.text.strip()}\n\n"
                return output
        except Exception as e:
            print(f"Vertex AI RAG retrieval failed: {e}. Falling back to Firestore...", file=sys.stderr)

    # Fallback to Firestore / Local filtering
    approved_lessons = fetch_approved_lessons()
    results = []
    
    for lesson in approved_lessons:
        if topic_filters:
            lesson_topics = [t.lower() for t in lesson.get("topics", [])]
            if not any(t.lower() in lesson_topics for t in topic_filters):
                continue
                
        generalized_text = lesson.get("generalized_lesson", "").lower()
        if any(word.lower() in generalized_text for word in query.split() if len(word) > 3) or not query:
            results.append(lesson)
            
    if not results:
        return f"No specific lessons or gotchas found for this query in the team knowledge base (Database: {STORAGE_CFG.get('firebase_database_id', 'Mock')})."
        
    output = "Here are the team's lessons learned and best practices:\n\n"
    for idx, res in enumerate(results, 1):
        output += f"{idx}. **Topic:** {', '.join(res.get('topics', []))}\n"
        output += f"   **Lesson:** {res.get('generalized_lesson')}\n\n"
        
    return output

if __name__ == "__main__":
    mcp.run(transport='stdio')
