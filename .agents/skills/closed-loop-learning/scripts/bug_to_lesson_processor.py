#!/usr/bin/env python3
"""
Bug to Lesson Processor for Closed-Loop Learning

Consolidated master production script implementing:
1. Dual-Identity ADC Authentication (GcloudUserCredentials with 55-minute cache).
2. Service-Specific Knowledge Topics / Tags (Vertex AI prompt + tag scrubbing + domain keyword fallback).
3. Boilerplate Stripping (Case-insensitive iterative regex cleaning across string fields).
4. Command Scaffolding (Concise rules paired with exact command syntax samples).
5. Atomic Error Handling (Strict exception propagation to guarantee data integrity).
"""

import argparse
import datetime
import glob
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return

_setup_ce_config()
import ce_config  # noqa: E402
import mcp_client  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load externalized configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except Exception as e:
    logging.error(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    CONFIG = {}

STORAGE_CFG = CONFIG.get("storage", {})
VERTEX_CFG = CONFIG.get("vertex_ai", {})

# Safely handle google.auth import for dual-identity credential subclassing
try:
    import google.auth.credentials
    BaseCredentials = google.auth.credentials.Credentials
except ImportError:
    BaseCredentials = object


# ---------------------------------------------------------------------------
# 1. Dual-Identity ADC Authentication
# ---------------------------------------------------------------------------
class GcloudUserCredentials(BaseCredentials):
    """
    Custom credentials subclass that dynamically executes
    `gcloud auth print-access-token --account=<user-corporate-email>` on demand
    with 55-minute in-memory caching so global Argolis sandbox ADC remains untouched.
    """
    def __init__(self, account: Optional[str] = None):
        if BaseCredentials is not object:
            super().__init__()
        self.account = (
            account
            or ce_config.get_secret("closed_loop_account")
            or STORAGE_CFG.get("account")
            or STORAGE_CFG.get("firebase_account_email")
        )
        if not self.account:
            raise ValueError(
                "No credentials account configured. Please run onboarding workflow or set CLOSED_LOOP_CREDENTIAL_ACCOUNT."
            )
        self.token: Optional[str] = None
        self.expiry: Optional[datetime.datetime] = None
        self._cache_duration_sec: float = 55 * 60

    @property
    def valid(self) -> bool:
        if self.token is None or self.expiry is None:
            return False
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return now < (self.expiry - datetime.timedelta(seconds=30))

    def refresh(self, request=None) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        if self.valid:
            return
        try:
            logging.info(f"Refreshing gcloud access token for account {self.account}...")
            cmd = ["gcloud", "auth", "print-access-token", f"--account={self.account}"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = res.stdout.strip()
            if not output:
                raise ValueError("Received empty access token from gcloud command.")
            self.token = output
            self.expiry = now + datetime.timedelta(seconds=self._cache_duration_sec)
            logging.info(f"Successfully refreshed token for {self.account} (cached for 55 minutes).")
        except Exception as e:
            logging.error(f"Failed to fetch access token via gcloud for {self.account}: {e}")
            raise RuntimeError(f"Authentication failed for {self.account}: {e}") from e


def get_user_credentials() -> Any:
    """Returns an instance of GcloudUserCredentials."""
    return GcloudUserCredentials()


# ---------------------------------------------------------------------------
# 3. Boilerplate Stripping & 4. Command Scaffolding Helpers
# ---------------------------------------------------------------------------
def strip_boilerplate(text: Any) -> str:
    """
    Iterative case-insensitive regex cleaning across fields to remove repetitive prefixes.
    Handles nested or multi-layered boilerplate cleanly.
    """
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ""

    cleaned = text.strip()
    pattern = r"(?i)^\s*(?:verified architectural resolution|verified remediation|remediation|lesson learned|generalized lesson|specific lesson|error (?:in|executing) command '[^']*'):\s*"
    while True:
        new_cleaned = re.sub(pattern, "", cleaned).strip()
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    return cleaned


def enforce_command_scaffolding(text: str, failed_cmd: Optional[str] = None) -> str:
    """
    Enforces concise rules paired with exact command syntax samples (`Command sample:\n...`).
    """
    cleaned = strip_boilerplate(text)
    if not cleaned:
        cleaned = "Ensure exact syntax and appropriate IAM permissions when executing commands."
    if "Command sample:" not in cleaned and failed_cmd:
        cmd_str = failed_cmd.strip()
        # Clean existing backticks if any before re-wrapping
        cmd_str = cmd_str.strip("`").strip()
        if cmd_str:
            cmd_str = f"`{cmd_str}`"
            return f"{cleaned}\n\nCommand sample:\n{cmd_str}"
    return cleaned


# ---------------------------------------------------------------------------
# 2. Service-Specific Knowledge Topics / Tags & Filtering Layer
# ---------------------------------------------------------------------------
BANNED_PROCESS_TAGS = {
    "validation", "remediation", "closedloop", "bug", "error", "test",
    "fix", "issue", "failure", "failed", "verified", "resolution", "lesson",
    "general", "pending", "review", "architectural", "architecture"
}

FALLBACK_DOMAIN_MAPPING = {
    "storage": ["GCS", "CloudStorage", "gcloud"],
    "gsutil": ["GCS", "CloudStorage", "gsutil"],
    "gcs": ["GCS", "CloudStorage"],
    "gke": ["GKE", "Kubernetes"],
    "container": ["GKE", "Kubernetes"],
    "kubectl": ["GKE", "Kubernetes"],
    "bigquery": ["BigQuery", "SQL"],
    "bq": ["BigQuery", "bq"],
    "iam": ["IAM", "Security", "Permissions"],
    "compute": ["ComputeEngine", "VM", "gcloud"],
    "instances": ["ComputeEngine", "VM"],
    "gce": ["ComputeEngine", "VM"],
    "vpc": ["VPC", "Networking"],
    "subnets": ["VPC", "Networking"],
    "firewall": ["VPC", "Firewall"],
    "run": ["CloudRun", "Serverless"],
    "pubsub": ["PubSub", "Messaging"],
    "functions": ["CloudFunctions", "Serverless"],
    "sql": ["CloudSQL", "Database"],
    "cloudsql": ["CloudSQL", "Database"],
    "secret": ["SecretManager", "Security"],
    "secretmanager": ["SecretManager", "Security"],
    "artifact": ["ArtifactRegistry"],
    "gcloud": ["gcloud"]
}


def clean_topics(raw_topics: List[Any], context_text: str = "") -> List[str]:
    """
    Scrubs generic process tags and ensures strictly product/technology tags.
    Applies fallback domain mapping conditionally ONLY if valid product tags are empty,
    strictly using word boundary matching to avoid false positives.
    """
    valid_tags = []
    seen = set()
    if isinstance(raw_topics, list):
        for tag in raw_topics:
            if not isinstance(tag, str):
                continue
            clean_tag = tag.strip()
            if clean_tag and clean_tag.lower() not in BANNED_PROCESS_TAGS and clean_tag.lower() not in seen:
                valid_tags.append(clean_tag)
                seen.add(clean_tag.lower())

    # Conditional fallback: augment only if valid tags are sparse or empty
    if not valid_tags:
        context_lower = context_text.lower()
        for keyword, mapped_tags in FALLBACK_DOMAIN_MAPPING.items():
            if re.search(rf"\b{re.escape(keyword)}\b", context_lower):
                for m_tag in mapped_tags:
                    if m_tag.lower() not in seen and m_tag.lower() not in BANNED_PROCESS_TAGS:
                        valid_tags.append(m_tag)
                        seen.add(m_tag.lower())

    if not valid_tags:
        valid_tags = ["GCP", "gcloud"]

    return valid_tags


# ---------------------------------------------------------------------------
# Extraction & Processing Pipeline
# ---------------------------------------------------------------------------
def extract_generalized_lesson(bug_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes bug and verified remediation to extract a generalized lesson.
    Uses Vertex AI Gemini with prompt instructing strict product tags and scaffolding,
    falling back to robust deterministic extraction.
    """
    remediation = strip_boilerplate(bug_payload.get("remediation", "No remediation recorded."))
    error_ctx = bug_payload.get("error_logs", {})
    failed_cmd = error_ctx.get("failed_command", "")
    error_msg = error_ctx.get("error_message", "")

    context_str = f"Command: {failed_cmd} | Error: {error_msg} | Fix: {remediation}"

    # Try calling Vertex AI Gemini
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig

        project = ce_config.get("closed_loop_vertex_project") or VERTEX_CFG.get("project_id") or os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError(
                "No Vertex AI project_id configured. Please configure it in gcp_config.txt or set CLOSED_LOOP_VERTEX_PROJECT."
            )
        location = VERTEX_CFG.get("location", "us-central1")
        model_name = VERTEX_CFG.get("extraction_model", "gemini-1.5-pro")

        creds = get_user_credentials()
        vertexai.init(project=project, location=location, credentials=creds)

        prompt = f"""You are an expert Google Cloud Cloud Architect. Analyze this bug report and fix:
Failed Command: {failed_cmd}
Error Output: {error_msg}
Verified Remediation: {remediation}

Generate a JSON response with exactly three keys:
1. "specific_lesson": Concise explanation of why the command failed and how the remediation fixed it. Strip any introductory boilerplate.
2. "generalized_lesson": Broader architectural or CLI rule. You must enforce concise rules paired with exact command syntax samples formatted exactly as:
Command sample:
`<command syntax example>`
3. "topics": List of strings containing strictly product/technology tags (e.g. ["GCS", "CloudStorage", "gcloud"], ["GKE", "Kubernetes"]). NEVER include generic process tags like Validation, Remediation, ClosedLoop, Bug, Error, Test, Fix.

Output ONLY valid JSON."""

        model = GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(response_mime_type="application/json")
        )
        text_resp = response.text.strip()
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]

        data = json.loads(text_resp)
        specific = strip_boilerplate(data.get("specific_lesson", remediation))
        generalized = enforce_command_scaffolding(data.get("generalized_lesson", remediation), failed_cmd)
        topics = clean_topics(data.get("topics", []), context_str)
        return {
            "specific_lesson": specific,
            "generalized_lesson": generalized,
            "topics": topics
        }
    except Exception as e:
        logging.info(f"Vertex AI LLM extraction unavailable or failed ({e}). Using robust fallback extractor.")

    # Fallback deterministic extraction
    specific_lesson = strip_boilerplate(f"Error executing command '{failed_cmd}': {remediation}" if failed_cmd else remediation)
    generalized_lesson = enforce_command_scaffolding(remediation, failed_cmd)
    topics = clean_topics([], context_str)

    return {
        "specific_lesson": specific_lesson,
        "generalized_lesson": generalized_lesson,
        "topics": topics
    }


# ---------------------------------------------------------------------------
# 5. Atomic Error Handling in Storage & Processing
# ---------------------------------------------------------------------------
def push_to_firebase(lesson_payload: Dict[str, Any]) -> None:
    """
    Pushes structured lesson to storage. Enforces atomic error handling by raising
    exceptions on failure so local file status never prematurely transitions to PROCESSED.
    """
    backend_type = os.environ.get("CLOSED_LOOP_STORAGE_BACKEND", STORAGE_CFG.get("backend_type"))
    if backend_type == "firebase":
        try:
            from google.cloud import firestore
            creds = get_user_credentials()
            firestore_project = (
                ce_config.get("closed_loop_firestore_project")
                or STORAGE_CFG.get("firebase_project_id")
                or os.environ.get("GCP_PROJECT")
                or os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
            if not firestore_project:
                raise ValueError(
                    "No Firestore project configured. Please configure it in gcp_config.txt or set CLOSED_LOOP_FIRESTORE_PROJECT."
                )
            db = firestore.Client(
                project=firestore_project,
                database=STORAGE_CFG.get("firebase_database_id", "(default)"),
                credentials=creds
            )
            collection = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
            doc_id = lesson_payload.get("source_bug_id", f"bug_{int(time.time())}")
            db.collection(collection).document(doc_id).set(lesson_payload)
            logging.info(f"Successfully pushed lesson '{doc_id}' to Firestore collection '{collection}'.")
        except Exception as e:
            logging.error(f"Atomic Write Error: Failed pushing to Firestore: {e}")
            raise RuntimeError(f"Firestore storage write failed: {e}") from e
    else:
        # Save to local mock DB directory
        mock_dir = os.path.expanduser(STORAGE_CFG.get("local_mock_directory", "~/.gemini/jetski/knowledge/closed_loop_learning/lessons"))
        try:
            os.makedirs(mock_dir, exist_ok=True)
            filename = f"lesson_{lesson_payload.get('source_bug_id', 'unknown')}.json"
            target_path = os.path.join(mock_dir, filename)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(lesson_payload, f, indent=2)
            logging.info(f"Saved lesson payload atomic write to mock storage: {target_path}")
        except Exception as e:
            logging.error(f"Atomic Write Error: Failed saving to local mock storage: {e}")
            raise RuntimeError(f"Local storage write failed: {e}") from e


def _get_mcp_auth_headers(url: str) -> Dict[str, str]:
    return mcp_client.get_mcp_auth_headers(url)


def _get_streamable_client_kwargs(headers: Dict[str, str]) -> Dict[str, Any]:
    return mcp_client.get_streamable_client_kwargs(headers)


async def submit_to_mcp_async(submission_payload: Dict[str, Any], url: str) -> Dict[str, Any]:
    return await mcp_client.call_mcp_tool_async("submit_lesson", {"submission": submission_payload}, url)


def submit_to_mcp(submission_payload: Dict[str, Any]) -> Dict[str, Any]:
    return mcp_client.call_mcp_tool("submit_lesson", {"submission": submission_payload})


def validate_submission(submission_payload: Dict[str, Any]) -> None:
    try:
        import jsonschema
    except (ImportError, ModuleNotFoundError) as e:
        raise RuntimeError("CLOSED_LOOP_TRANSPORT=mcp requires extra deps: pip3 install -r <repo>/requirements.txt (or run via: uv run --with-requirements requirements.txt python3 ...)") from e

    schema_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "lesson_submission.schema.json")
    if not os.path.exists(schema_path):
        raise ValueError(f"Vendored schema not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=submission_payload, schema=schema)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Submission payload failed schema validation: {e}") from e


def process_bug_file(filepath: str) -> bool:
    """
    Processes a single bug file. Returns True if successful or cleanly skipped, False on failure.
    Guarantee: local file status never mutates to PROCESSED if push_to_firebase or submit_to_mcp fails.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            bug_payload = json.load(f)

        if bug_payload.get("status") == "PROCESSED":
            return True

        if bug_payload.get("status") != "FIXED":
            logging.info(f"Skipping {filepath}: status is '{bug_payload.get('status')}' (must be 'FIXED').")
            return True

        logging.info(f"Processing verified FIXED bug file: {filepath}")

        transport = os.environ.get("CLOSED_LOOP_TRANSPORT") or ce_config.get("closed_loop_transport") or "firestore"
        if transport.lower() == "mcp":
            error_logs = bug_payload.get("error_logs", {})
            submitted_by = (
                ce_config.get_secret("closed_loop_account")
                or os.environ.get("CLOSED_LOOP_ACCOUNT")
                or os.environ.get("CE_CLOSED_LOOP_ACCOUNT")
                or STORAGE_CFG.get("account")
                or STORAGE_CFG.get("firebase_account_email")
            )
            if not submitted_by:
                raise ValueError("Missing required closed_loop_account in environment (CLOSED_LOOP_ACCOUNT/CE_CLOSED_LOOP_ACCOUNT) or gcp_config.txt for CLOSED_LOOP_TRANSPORT=mcp")

            lesson_submission = {
                "source_bug_id": bug_payload.get("bug_id") or bug_payload.get("source_bug_id"),
                "raw_error_context": {
                    "failed_command": error_logs.get("failed_command", ""),
                    "stderr_output": error_logs.get("stderr_output") or error_logs.get("error_message", ""),
                },
                "remediation": strip_boilerplate(bug_payload.get("remediation", "")),
                "submitted_by": submitted_by,
            }
            if "exit_code" in error_logs and error_logs["exit_code"] is not None:
                lesson_submission["raw_error_context"]["exit_code"] = error_logs["exit_code"]

            origin_dict = {}
            if bug_payload.get("lab_name") is not None:
                origin_dict["lab_name"] = str(bug_payload.get("lab_name"))
            if bug_payload.get("step_number") is not None:
                try:
                    origin_dict["step_number"] = int(bug_payload.get("step_number"))
                except (ValueError, TypeError):
                    pass
            if bug_payload.get("workflow") is not None:
                origin_dict["workflow"] = str(bug_payload.get("workflow"))
            if origin_dict:
                lesson_submission["origin"] = origin_dict

            validate_submission(lesson_submission)
            try:
                receipt = submit_to_mcp(lesson_submission)
                logging.info(f"MCP submission successful for {lesson_submission['source_bug_id']}. Extraction mode: {receipt.get('extraction_mode')}")
                possible_dups = receipt.get("possible_duplicates", [])
                if possible_dups:
                    logging.info(f"Advisory: possible duplicates found: {possible_dups}")
            except Exception as e:
                err_str = str(e)
                if "already exists with status" in err_str or "Conflict" in err_str:
                    logging.warning(f"Terminal conflict error for {filepath}: {err_str}. Transitioning status to PROCESSED to stop retry loop.")
                else:
                    raise
        else:
            # Extract generalized lesson
            extracted_info = extract_generalized_lesson(bug_payload)

            # Build lesson record with stripped boilerplate and scrubbed tags
            lesson_record = {
                "source_bug_id": bug_payload.get("bug_id"),
                "status": "pending_review",
                "raw_error_context": bug_payload.get("error_logs", {}),
                "verified_remediation": strip_boilerplate(bug_payload.get("remediation", "")),
                "specific_lesson": extracted_info["specific_lesson"],
                "generalized_lesson": extracted_info["generalized_lesson"],
                "topics": extracted_info["topics"],
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            # Push to storage (will raise exception on write/network error)
            push_to_firebase(lesson_record)

        # Atomic transition: reached ONLY if push_to_firebase or submit_to_mcp succeeded without raising
        bug_payload["status"] = "PROCESSED"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(bug_payload, f, indent=2)

        logging.info(f"Successfully processed and updated status for {filepath}")
        return True

    except Exception as e:
        logging.error(f"Processing aborted for {filepath} due to error: {e}. File status preserved.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Process bugs into lessons learned.")
    parser.add_argument("--scan-dir", type=str, required=True, help="Directory to scan for bug JSON files.")
    args = parser.parse_args()

    search_pattern = os.path.join(args.scan_dir, "bug_*.json")
    bug_files = glob.glob(search_pattern)

    if not bug_files:
        logging.info(f"No bug files found in {args.scan_dir}")
        return

    error_count = 0
    success_count = 0
    for bug_file in bug_files:
        if process_bug_file(bug_file):
            success_count += 1
        else:
            error_count += 1

    logging.info(f"Completed scanning {len(bug_files)} files: {success_count} succeeded/skipped, {error_count} failed.")
    if error_count > 0:
        exit(1)


if __name__ == "__main__":
    main()
