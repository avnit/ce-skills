#!/usr/bin/env python3
"""Hermetic unit tests for W4-3 query_rag.py MCP cutover.

Covers:
- MCP tool invocation shape (query_team_knowledge with top_k and topic_filters).
- Both 'rag' and 'database_fallback' retrieval shapes.
- Exception handling returning degraded fallback structure.
- CLI argument parsing for --query without legacy --learn arguments.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / ".agents" / "lib"
SKILL_SCRIPTS_DIR = REPO_ROOT / ".agents" / "skills" / "codelab-memory" / "scripts"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(SKILL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS_DIR))

import mcp_client  # noqa: E402
import query_rag  # noqa: E402


class TestQueryRagMcp(unittest.TestCase):

    @patch.object(mcp_client, "call_mcp_tool")
    def test_query_rag_mode(self, mock_call):
        """Verify query_team_knowledge returns 'rag' retrieval mode with score_kind."""
        mock_res = {
            "retrieval_mode": "rag",
            "degraded_reason": None,
            "results": [
                {
                    "text": "Check VPC firewall rules",
                    "score": 0.92,
                    "score_kind": "score",
                    "source": "lesson/BUG_VPC_01",
                }
            ],
        }
        mock_call.return_value = mock_res

        res = query_rag.query_centralized_rag(
            "firewall issue", n_results=3, topic_filters=["VPC"]
        )
        mock_call.assert_called_once_with(
            "query_team_knowledge",
            arguments={"query": "firewall issue", "top_k": 3, "topic_filters": ["VPC"]},
        )
        self.assertEqual(res["retrieval_mode"], "rag")
        self.assertIsNone(res["degraded_reason"])
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["score_kind"], "score")

    @patch.object(mcp_client, "call_mcp_tool")
    def test_query_database_fallback_mode(self, mock_call):
        """Verify query_team_knowledge handles 'database_fallback' mode and keyword score_kind."""
        mock_res = {
            "retrieval_mode": "database_fallback",
            "degraded_reason": "RAG index temporarily unavailable",
            "results": [
                {
                    "text": "Grant Spanner admin IAM role",
                    "score": None,
                    "score_kind": "keyword",
                    "source": "lesson/BUG_IAM_02",
                }
            ],
        }
        mock_call.return_value = mock_res

        res = query_rag.query_centralized_rag("spanner iam")
        mock_call.assert_called_once_with(
            "query_team_knowledge",
            arguments={"query": "spanner iam", "top_k": 5},
        )
        self.assertEqual(res["retrieval_mode"], "database_fallback")
        self.assertEqual(
            res["degraded_reason"], "RAG index temporarily unavailable"
        )
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["score_kind"], "keyword")
        self.assertIsNone(res["results"][0]["score"])

    @patch.object(mcp_client, "call_mcp_tool")
    def test_query_exception_handles_gracefully(self, mock_call):
        """Verify communication exception returns a degraded fallback structure."""
        mock_call.side_effect = RuntimeError("Connection refused")

        res = query_rag.query_centralized_rag("test query")
        self.assertEqual(res["retrieval_mode"], "database_fallback")
        self.assertIn("Client execution failed: Connection refused", res["degraded_reason"])
        self.assertEqual(res["results"], [])

    @patch.object(query_rag, "query_centralized_rag")
    def test_cli_query_invocation(self, mock_query):
        """Verify main() parses arguments correctly and calls query_centralized_rag."""
        with patch.object(
            sys,
            "argv",
            [
                "query_rag.py",
                "--query",
                "quota limits",
                "--n_results",
                "2",
                "--topic_filters",
                "Spanner",
                "Compute",
            ],
        ):
            query_rag.main()
            mock_query.assert_called_once_with(
                "quota limits", 2, ["Spanner", "Compute"]
            )


if __name__ == "__main__":
    unittest.main()
