#!/usr/bin/env python3
"""
Vertex AI RAG Corpus Setup Script

This script initializes a Vertex AI RAG Corpus in your GCP project and outputs
the exact Corpus ID to put in `config/config.json`.
"""

import sys
import json
import os

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except Exception as e:
    print(f"Failed to load config: {e}", file=sys.stderr)
    sys.exit(1)

VERTEX_CFG = CONFIG.get("vertex_ai", {})
PROJECT_ID = VERTEX_CFG.get("project_id", "hyperstack-dev")
LOCATION = VERTEX_CFG.get("location", "us-central1")

def create_corpus():
    print(f"Initializing Vertex AI RAG Corpus in project '{PROJECT_ID}' ({LOCATION})...")
    try:
        import vertexai
        from vertexai.preview import rag
        
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Configure RAG Engine to use Serverless mode (avoids Spanner allowlist restriction)
        print("Configuring RAG Engine backend mode to Serverless...")
        try:
            rag_engine_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
            rag.update_rag_engine_config(
                rag_engine_config=rag.RagEngineConfig(
                    name=rag_engine_name,
                    rag_managed_db_config=rag.RagManagedDbConfig(mode=rag.Serverless())
                )
            )
            print("Successfully switched to Serverless mode.")
        except Exception as ex:
            print(f"Note on Serverless switch: {ex}")
        
        # Create RAG Corpus
        corpus_display_name = "closed_loop_learning_knowledge_base"
        embedding_model_config = rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-004"
        )
        
        corpus = rag.create_corpus(
            display_name=corpus_display_name,
            embedding_model_config=embedding_model_config
        )
        
        print("\n✅ RAG Corpus Created Successfully!")
        print(f"Corpus Name / ID: {corpus.name}")
        print("\nCopy the above Corpus ID into your `config/config.json` under `rag_corpus_id`!")
        
    except Exception as e:
        print(f"\n❌ Failed to create RAG Corpus: {e}", file=sys.stderr)
        print("\nTip: Ensure you ran `gcloud auth application-default login` and enabled the Vertex AI API.", file=sys.stderr)

if __name__ == "__main__":
    create_corpus()
