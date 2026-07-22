"""Script to interface with the centralized RAG system via MCP query_team_knowledge."""

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional


def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return


_setup_ce_config()
import mcp_client  # noqa: E402


def query_centralized_rag(
    query_text: str, n_results: int = 5, topic_filters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Queries the centralized team knowledge base via MCP query_team_knowledge."""
    print(f"Querying team knowledge via MCP for: '{query_text}'...")

    arguments: Dict[str, Any] = {"query": query_text, "top_k": n_results}
    if topic_filters:
        arguments["topic_filters"] = topic_filters

    try:
        result = mcp_client.call_mcp_tool("query_team_knowledge", arguments=arguments)
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error querying team knowledge via MCP: {e}", file=sys.stderr)
        return {
            "retrieval_mode": "database_fallback",
            "degraded_reason": f"Client execution failed: {e}",
            "results": [],
        }


def main():
    parser = argparse.ArgumentParser(
        description="Interface with Centralized Team Knowledge via MCP."
    )
    parser.add_argument("--query", type=str, help="Query to search for lessons.")
    parser.add_argument(
        "--n_results", type=int, default=5, help="Number of results to return."
    )
    parser.add_argument(
        "--topic_filters",
        nargs="*",
        help="Optional topic filters for the search.",
    )

    args = parser.parse_args()

    if args.query:
        query_centralized_rag(args.query, args.n_results, args.topic_filters)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
