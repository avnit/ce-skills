"""Script to interface with the centralized RAG system for Codelab Creator."""

import argparse
import datetime
import json
import os
import sys
import tempfile

import vertexai
import vertexai.preview.rag

PROJECT_ID = os.environ.get("CE_RAG_PROJECT_ID", "codelab-creator-central")
LOCATION = os.environ.get("CE_RAG_LOCATION", "us-west1")
CORPUS_NAME = os.environ.get("CE_RAG_CORPUS_NAME", f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/4611686018427387904")

def query_centralized_rag(query_text: str, n_results: int = 3):
    """Queries the centralized Vertex AI RAG system."""
    print(f"Querying centralized RAG for: '{query_text}'...")
    
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        response = vertexai.preview.rag.retrieval_query(
            text=query_text,
            rag_resources=[vertexai.preview.rag.RagResource(
                rag_corpus=CORPUS_NAME,
            )],
            similarity_top_k=n_results,
        )
        
        # Format output
        formatted_results = []
        for context in response.contexts.contexts:
             formatted_results.append({
                 "text": context.text,
                 "distance": context.distance if hasattr(context, "distance") else None
             })
             
        print(json.dumps(formatted_results, indent=2))
        return formatted_results
        
    except Exception as e:
        print(f"Error querying RAG: {e}", file=sys.stderr)
        return []

def learn_new_lesson(problem: str, solution: str, context: str):
    """Sends a new lesson to the centralized RAG system by uploading a file."""
    print("Storing new lesson in centralized RAG...")
    
    # Create a structured document
    doc_content = f"Context: {context}\nProblem: {problem}\nSolution: {solution}"
    
    temp_path = None
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Write to a temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(doc_content)
            temp_path = f.name
            
        display_name = f"lesson_{context.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        vertexai.preview.rag.upload_file(
            corpus_name=CORPUS_NAME,
            path=temp_path,
            display_name=display_name,
            description=f"Lesson learned for context: {context}"
        )
        
        print(json.dumps({
            "status": "stored",
            "display_name": display_name,
            "content": doc_content
        }, indent=2))
        return True
        
    except Exception as e:
        print(f"Error storing lesson in RAG: {e}", file=sys.stderr)
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

def main():
    parser = argparse.ArgumentParser(description="Interface with Centralized Vertex AI RAG.")
    parser.add_argument("--query", type=str, help="Query to search for lessons.")
    parser.add_argument("--learn", action="store_true", help="Record a new lesson.")
    parser.add_argument("--problem", type=str, help="The error or problem encountered.")
    parser.add_argument("--solution", type=str, help="The solution or fix applied.")
    parser.add_argument("--context", type=str, default="General", help="The context.")
    parser.add_argument("--n_results", type=int, default=3, help="Number of results to return.")

    args = parser.parse_args()

    if args.query:
        query_centralized_rag(args.query, args.n_results)
    elif args.learn:
        if not args.problem or not args.solution:
            print("Error: --problem and --solution are required for --learn")
            sys.exit(1)
        learn_new_lesson(args.problem, args.solution, args.context)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
