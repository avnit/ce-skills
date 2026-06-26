from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import glob
import tempfile
from datetime import datetime
from typing import List, Optional, Dict, Any

app = FastAPI(title="Google Cloud Closed-Loop Learning API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

STORAGE_CFG = CONFIG.get("storage", {})
VERTEX_CFG = CONFIG.get("vertex_ai", {})
MOCK_DB_DIR = os.path.expanduser(STORAGE_CFG.get("local_mock_directory", "~/.gemini/jetski/knowledge/closed_loop_learning/lessons"))
os.makedirs(MOCK_DB_DIR, exist_ok=True)


class LessonUpdate(BaseModel):
    status: str
    generalized_lesson: Optional[str] = None
    topics: Optional[List[str]] = None


def get_firestore_client():
    from google.cloud import firestore
    return firestore.Client(
        project=STORAGE_CFG.get("firebase_project_id"),
        database=STORAGE_CFG.get("firebase_database_id", "(default)")
    )


def push_to_vertex_rag(lesson_data: Dict[str, Any]):
    """Pushes approved knowledge to Vertex AI RAG Corpus"""
    corpus_id = VERTEX_CFG.get("rag_corpus_id")
    if not corpus_id or "YOUR_" in corpus_id:
        return

    import vertexai
    from vertexai.preview import rag

    project = VERTEX_CFG.get("project_id", "hyperstack-dev")
    location = VERTEX_CFG.get("location", "us-central1")
    vertexai.init(project=project, location=location)

    bug_id = lesson_data.get("source_bug_id", "lesson")
    tmp_file = os.path.join(tempfile.gettempdir(), f"{bug_id}.txt")
    content = f"Title: {', '.join(lesson_data.get('topics', []))} Gotcha & Lesson\n\n"
    content += f"Problem Context:\n{json.dumps(lesson_data.get('raw_error_context', {}), indent=2)}\n\n"
    content += f"Generalized Rule & Best Practice:\n{lesson_data.get('generalized_lesson')}\n"

    with open(tmp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    transformation_config = rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=4096, chunk_overlap=0)
    )

    rag.upload_file(
        corpus_name=corpus_id,
        path=tmp_file,
        display_name=f"{bug_id}_approved_rule.txt",
        description="Human approved agent learning rule",
        transformation_config=transformation_config
    )


@app.get("/lessons")
def get_lessons(status: Optional[str] = None):
    lessons = []
    if STORAGE_CFG.get("backend_type") == "firebase":
        db = get_firestore_client()
        collection_name = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
        query = db.collection(collection_name)
        if status and status != "all":
            query = query.where("status", "==", status)
        docs = query.stream()
        for doc in docs:
            item = doc.to_dict()
            item["_identifier"] = doc.id
            if not item.get("submitted_by"):
                item["submitted_by"] = "shacharb@google.com (Agent Pipeline)"
            lessons.append(item)
    else:
        for file_path in glob.glob(os.path.join(MOCK_DB_DIR, "*.json")):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not status or status == "all" or data.get("status") == status:
                    data["_identifier"] = file_path
                    if not data.get("submitted_by"):
                        data["submitted_by"] = "shacharb@google.com (Agent Pipeline)"
                    lessons.append(data)
    return lessons


@app.put("/lessons/{identifier}")
def update_lesson(identifier: str, update: LessonUpdate):
    now_iso = datetime.utcnow().isoformat() + "Z"
    if STORAGE_CFG.get("backend_type") == "firebase":
        db = get_firestore_client()
        incoming_col = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
        doc_ref = db.collection(incoming_col).document(identifier)
        
        update_data = {"status": update.status, "reviewed_at": now_iso}
        if update.generalized_lesson is not None:
            update_data["generalized_lesson"] = update.generalized_lesson
        if update.topics is not None:
            update_data["topics"] = update.topics
            
        doc_ref.update(update_data)
        
        if update.status == "approved":
            approved_col = STORAGE_CFG.get("firebase_approved_collection", "approved_lessons")
            full_doc = doc_ref.get().to_dict()
            db.collection(approved_col).document(identifier).set(full_doc)
            push_to_vertex_rag(full_doc)
    else:
        if not os.path.exists(identifier):
            raise HTTPException(status_code=404, detail="Lesson not found")
        with open(identifier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["status"] = update.status
        data["reviewed_at"] = now_iso
        if update.generalized_lesson is not None:
            data["generalized_lesson"] = update.generalized_lesson
        if update.topics is not None:
            data["topics"] = update.topics
        with open(identifier, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        if update.status == "approved":
            push_to_vertex_rag(data)
    return {"success": True, "identifier": identifier, "status": update.status}


@app.delete("/lessons/{identifier}")
def remove_lesson(identifier: str):
    if STORAGE_CFG.get("backend_type") == "firebase":
        db = get_firestore_client()
        incoming_col = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
        approved_col = STORAGE_CFG.get("firebase_approved_collection", "approved_lessons")
        db.collection(incoming_col).document(identifier).delete()
        db.collection(approved_col).document(identifier).delete()
    else:
        if os.path.exists(identifier):
            os.remove(identifier)
    return {"success": True, "identifier": identifier}
