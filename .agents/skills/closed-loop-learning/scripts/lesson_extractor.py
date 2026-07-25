#!/usr/bin/env python3
"""
Lesson Extractor for Closed-Loop Learning

Extracts generalized architectural lessons from raw failure logs and verified remediations.
Retrieves live RAG context via query_team_knowledge MCP tool to avoid reliance on static pre-trained model weights,
submitting distillation payloads to the subagent session.
"""

import json
import logging
import os
import shutil
import subprocess
from typing import Dict, Any, Optional

from tag_scrubber import strip_boilerplate, enforce_command_scaffolding, clean_topics


def fetch_mcp_knowledge_context(failed_cmd: str) -> str:
    """
    Queries live team knowledge from the closed-loop MCP server prior to distillation.
    Provides fast-paced ground truth RAG data to the subagent, avoiding reliance on static pre-trained weights alone.
    """
    if not failed_cmd:
        return ""

    try:
        from mcp_client import call_mcp_tool
        mcp_res = call_mcp_tool("query_team_knowledge", {"query": failed_cmd})
        if isinstance(mcp_res, dict) and "results" in mcp_res:
            results = mcp_res.get("results", [])
            snippets = [r.get("text", "") for r in results[:3] if r.get("text")]
            if snippets:
                return "\nRetrieved Live MCP Knowledge Context:\n" + "\n---\n".join(snippets) + "\n"
    except Exception as e:
        logging.info(f"Live MCP RAG context query skipped or failed: {e}")
    return ""


def try_agentapi_extraction(failed_cmd: str, error_msg: str, remediation: str) -> Optional[Dict[str, Any]]:
    """
    Attempts lesson distillation via subagent / Agent API CLI when running within an active agent session.
    Queries live closed-loop MCP team knowledge prior to invocation to ground the subagent in current data.
    """
    if not os.environ.get("ANTIGRAVITY_LS_ADDRESS"):
        return None

    agentapi_cmd = shutil.which("agentapi") or "/usr/local/google/home/shacharb/.gemini/jetski/bin/agentapi"
    if not os.path.exists(agentapi_cmd) and not shutil.which("agentapi"):
        return None

    mcp_context = fetch_mcp_knowledge_context(failed_cmd)

    prompt = f"""You are an expert Google Cloud Cloud Architect. Analyze this bug report and fix:
Failed Command: {failed_cmd}
Error Output: {error_msg}
Verified Remediation: {remediation}
{mcp_context}
Mandatory Knowledge Grounding:
- Prioritize the retrieved live MCP knowledge context and official Google Cloud documentation over pre-trained assumptions.
- Verify CLI command syntax, flags, IAM roles, and architectural rules against current GCP specifications.

Generate a JSON response with exactly three keys:
1. "specific_lesson": Concise explanation of why the command failed and how the remediation fixed it. Strip any introductory boilerplate.
2. "generalized_lesson": Broader architectural or CLI rule grounded in current GCP documentation. You must enforce concise rules paired with exact command syntax samples formatted exactly as:
Command sample:
`<command syntax example>`
3. "topics": List of strings containing strictly product/technology tags (e.g. ["GCS", "CloudStorage", "gcloud"], ["GKE", "Kubernetes"]). NEVER include generic process tags like Validation, Remediation, ClosedLoop, Bug, Error, Test, Fix.

Output ONLY valid JSON."""

    try:
        res = subprocess.run(
            [agentapi_cmd, "new-conversation", "--model=flash", prompt],
            capture_output=True,
            text=True,
            timeout=45
        )
        if res.returncode == 0 and res.stdout.strip():
            text_resp = res.stdout.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]
            data = json.loads(text_resp)
            if isinstance(data, dict) and "specific_lesson" in data and "generalized_lesson" in data:
                logging.info("Successfully extracted lesson via Agent API subagent session with live MCP knowledge grounding.")
                return data
    except Exception as e:
        logging.info(f"Agent API subagent extraction attempt skipped or failed: {e}")
    return None


def extract_generalized_lesson(bug_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes bug and verified remediation to extract a generalized lesson.
    Queries live MCP RAG knowledge first, then tries subagent session distillation,
    falling back to deterministic extraction.
    """
    remediation = strip_boilerplate(bug_payload.get("remediation", "No remediation recorded."))
    error_ctx = bug_payload.get("error_logs", {})
    failed_cmd = error_ctx.get("failed_command", "")
    error_msg = error_ctx.get("error_message", "")

    context_str = f"Command: {failed_cmd} | Error: {error_msg} | Fix: {remediation}"

    # Priority 1: Try subagent / Agent API distillation with live MCP knowledge context
    agentapi_res = try_agentapi_extraction(failed_cmd, error_msg, remediation)
    if agentapi_res:
        specific = strip_boilerplate(agentapi_res.get("specific_lesson", remediation))
        generalized = enforce_command_scaffolding(agentapi_res.get("generalized_lesson", remediation), failed_cmd)
        topics = clean_topics(agentapi_res.get("topics", []), context_str)
        return {
            "specific_lesson": specific,
            "generalized_lesson": generalized,
            "topics": topics
        }

    # Priority 2: Fallback deterministic extraction
    specific_lesson = strip_boilerplate(f"Error executing command '{failed_cmd}': {remediation}" if failed_cmd else remediation)
    generalized_lesson = enforce_command_scaffolding(remediation, failed_cmd)
    topics = clean_topics([], context_str)

    return {
        "specific_lesson": specific_lesson,
        "generalized_lesson": generalized_lesson,
        "topics": topics
    }
