#!/usr/bin/env python3
"""
Bug to Lesson Processor for Closed-Loop Learning

This script scans for `bug_*.json` files created by `tester.py`,
extracts the lesson learned (using Vertex AI), and uploads the result
to the Firebase `incoming_lessons` collection for pre-processing/review.
"""

import argparse
import glob
import json
import logging
import os
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load externalized configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except Exception as e:
    logging.error(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    CONFIG = {}

STORAGE_CFG = CONFIG.get("storage", {})
VERTEX_CFG = CONFIG.get("vertex_ai", {})

def extract_generalized_lesson(bug_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls an LLM (Vertex AI) to analyze the bug and generalize it into a lesson.
    """
    model = VERTEX_CFG.get("extraction_model", "gemini-1.5-pro")
    logging.info(f"Analyzing bug {bug_payload.get('bug_id')} using {model}...")
    
    # Mocked LLM Processing
    return {
        "specific_lesson": "Command failed.",
        "generalized_lesson": "Mocked generalized lesson from Vertex AI.",
        "topics": ["MockTopic", "Generalization"],
    }

def push_to_firebase(lesson_payload: Dict[str, Any]):
    """
    Pushes the structured lesson to the Firebase `incoming_lessons` collection.
    """
    if STORAGE_CFG.get("backend_type") == "firebase":
        try:
            from google.cloud import firestore
            db = firestore.Client(
                project=STORAGE_CFG.get("firebase_project_id"),
                database=STORAGE_CFG.get("firebase_database_id", "(default)")
            )
            collection = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
            doc_id = lesson_payload.get("source_bug_id", f"bug_{int(time.time())}")
            db.collection(collection).document(doc_id).set(lesson_payload)
            logging.info(f"Successfully pushed lesson '{doc_id}' to Firestore database '{STORAGE_CFG.get('firebase_database_id')}' collection '{collection}'!")
        except Exception as e:
            logging.error(f"Failed pushing to Firestore: {e}")
    else:
        # Save to local mock DB directory
        mock_dir = os.path.expanduser(STORAGE_CFG.get("local_mock_directory", "~/.gemini/jetski/knowledge/closed_loop_learning/lessons"))
        os.makedirs(mock_dir, exist_ok=True)
        filename = f"lesson_{lesson_payload.get('source_bug_id')}.json"
        target_path = os.path.join(mock_dir, filename)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(lesson_payload, f, indent=2)
        logging.info(f"Saved lesson payload to mock storage: {target_path}")

def process_bug_file(filepath: str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            bug_payload = json.load(f)
            
        if bug_payload.get("status") == "PROCESSED":
            return # Already processed

        logging.info(f"Processing new bug file: {filepath}")
        
        # 1. Extract generalized lesson
        extracted_info = extract_generalized_lesson(bug_payload)
        
        # 2. Build the income table record
        lesson_record = {
            "source_bug_id": bug_payload.get("bug_id"),
            "status": "pending_review",
            "raw_error_context": bug_payload.get("error_logs", {}),
            "specific_lesson": extracted_info["specific_lesson"],
            "generalized_lesson": extracted_info["generalized_lesson"],
            "topics": extracted_info["topics"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        
        # 3. Push to Firebase / storage
        push_to_firebase(lesson_record)
        
        # 4. Mark bug as processed locally
        bug_payload["status"] = "PROCESSED"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(bug_payload, f, indent=2)
            
        logging.info(f"Successfully processed {filepath}")

    except Exception as e:
        logging.error(f"Failed to process {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process bugs into lessons learned.")
    parser.add_argument("--scan-dir", type=str, required=True, help="Directory to scan for bug JSON files.")
    args = parser.parse_args()

    search_pattern = os.path.join(args.scan_dir, "bug_*.json")
    bug_files = glob.glob(search_pattern)
    
    if not bug_files:
        logging.info(f"No bug files found in {args.scan_dir}")
        return

    for bug_file in bug_files:
        process_bug_file(bug_file)

if __name__ == "__main__":
    main()
