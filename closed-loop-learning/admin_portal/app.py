import streamlit as st
import json
import os
import glob
import tempfile
from datetime import datetime

# Configure page styling
st.set_page_config(
    page_title="Closed-Loop Learning Console",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Authentic Google Cloud Console Design System CSS
GCP_CONSOLE_CSS = """
<style>
    /* Reset Streamlit defaults to match Google Cloud Console typography */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Google+Sans:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', 'Google Sans', Arial, sans-serif !important;
        color: #202124;
        background-color: #ffffff;
    }
    
    /* Remove default Streamlit top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* Top Google Cloud Console Navigation Bar */
    .gcp-top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 16px;
        border-bottom: 1px solid #dadce0;
        background: #ffffff;
        margin-bottom: 12px;
    }
    .gcp-top-bar-left {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 18px;
        color: #5f6368;
    }
    .gcp-logo-text {
        font-family: 'Google Sans', sans-serif;
        font-size: 20px;
        color: #5f6368;
        font-weight: 400;
    }
    .gcp-project-selector {
        background: #f1f3f4;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 13px;
        color: #202124;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .gcp-search-bar {
        background: #f1f3f4;
        padding: 8px 24px;
        border-radius: 24px;
        width: 450px;
        font-size: 14px;
        color: #5f6368;
        border: 1px solid transparent;
    }
    
    /* Page Sub-header and Action Row */
    .gcp-breadcrumb {
        font-size: 12px;
        color: #5f6368;
        margin-bottom: 4px;
    }
    .gcp-page-title-row {
        display: flex;
        align-items: center;
        gap: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid #dadce0;
        margin-bottom: 16px;
    }
    .gcp-page-title {
        font-family: 'Google Sans', sans-serif;
        font-size: 24px;
        color: #202124;
        font-weight: 400;
        margin: 0;
    }
    .gcp-action-link {
        color: #1a73e8;
        font-size: 14px;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Filter Banner */
    .gcp-filter-bar {
        background: #ffffff;
        padding: 10px 16px;
        border: 1px solid #dadce0;
        border-radius: 4px;
        margin-bottom: 16px;
        font-size: 13px;
        color: #5f6368;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* Status Badges matching Console colors */
    .gcp-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
    }
    .badge-pending { background-color: #fef7e0; color: #b06000; }
    .badge-approved { background-color: #e6f4ea; color: #137333; }
    .badge-rejected { background-color: #fce8e6; color: #c5221f; }
    
    /* Button overrides */
    div[data-testid="stButton"] button {
        border-radius: 4px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 4px 16px !important;
    }
</style>
"""
st.markdown(GCP_CONSOLE_CSS, unsafe_allow_html=True)

# Load externalized configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except Exception as e:
    st.error(f"Failed to load configuration from {CONFIG_PATH}: {e}")
    st.stop()

STORAGE_CFG = CONFIG.get("storage", {})
VERTEX_CFG = CONFIG.get("vertex_ai", {})

# Resolve mock directory or firebase config
MOCK_DB_DIR = os.path.expanduser(STORAGE_CFG.get("local_mock_directory", "~/.gemini/jetski/knowledge/closed_loop_learning/lessons"))
os.makedirs(MOCK_DB_DIR, exist_ok=True)


def get_firestore_client():
    from google.cloud import firestore
    return firestore.Client(
        project=STORAGE_CFG.get("firebase_project_id"),
        database=STORAGE_CFG.get("firebase_database_id", "(default)")
    )


def load_lessons_by_status(status_filter=None):
    """Loads lessons from Firestore or local DB filtered by status"""
    lessons = []
    if STORAGE_CFG.get("backend_type") == "firebase":
        try:
            db = get_firestore_client()
            collection_name = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
            query = db.collection(collection_name)
            if status_filter and status_filter != "all":
                query = query.where("status", "==", status_filter)
            docs = query.stream()
            for doc in docs:
                item = doc.to_dict()
                item["_identifier"] = doc.id
                if not item.get("submitted_by"):
                    item["submitted_by"] = "shacharb@google.com (Agent Pipeline)"
                lessons.append(item)
        except Exception as e:
            st.error(f"Firestore connection error: {e}")
    else:
        for file_path in glob.glob(os.path.join(MOCK_DB_DIR, "*.json")):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not status_filter or status_filter == "all" or data.get("status") == status_filter:
                    data["_identifier"] = file_path
                    if not data.get("submitted_by"):
                        data["submitted_by"] = "shacharb@google.com (Agent Pipeline)"
                    lessons.append(data)
    return lessons


def update_lesson_status(identifier, new_status, updated_generalized_lesson=None, updated_topics=None):
    """Updates the lesson status and content in Firestore/Local DB"""
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    if STORAGE_CFG.get("backend_type") == "firebase":
        db = get_firestore_client()
        incoming_col = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
        doc_ref = db.collection(incoming_col).document(identifier)
        
        update_data = {"status": new_status, "reviewed_at": now_iso}
        if updated_generalized_lesson is not None:
            update_data["generalized_lesson"] = updated_generalized_lesson
        if updated_topics is not None:
            update_data["topics"] = updated_topics
            
        doc_ref.update(update_data)
        
        if new_status == "approved":
            approved_col = STORAGE_CFG.get("firebase_approved_collection", "approved_lessons")
            full_doc = doc_ref.get().to_dict()
            db.collection(approved_col).document(identifier).set(full_doc)
            push_to_vertex_rag(full_doc)
    else:
        with open(identifier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["status"] = new_status
        data["reviewed_at"] = now_iso
        if updated_generalized_lesson is not None:
            data["generalized_lesson"] = updated_generalized_lesson
        if updated_topics is not None:
            data["topics"] = updated_topics
        with open(identifier, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        if new_status == "approved":
            push_to_vertex_rag(data)


def delete_lesson(identifier):
    """Permanently deletes a lesson from storage"""
    if STORAGE_CFG.get("backend_type") == "firebase":
        db = get_firestore_client()
        incoming_col = STORAGE_CFG.get("firebase_incoming_collection", "incoming_lessons")
        approved_col = STORAGE_CFG.get("firebase_approved_collection", "approved_lessons")
        db.collection(incoming_col).document(identifier).delete()
        db.collection(approved_col).document(identifier).delete()
    else:
        if os.path.exists(identifier):
            os.remove(identifier)


def push_to_vertex_rag(lesson_data):
    """Pushes approved knowledge to Vertex AI RAG Corpus"""
    corpus_id = VERTEX_CFG.get("rag_corpus_id")
    if not corpus_id or "YOUR_" in corpus_id:
        st.warning("Vertex AI RAG Corpus ID not configured properly in config.json. Skipping upload.")
        return

    try:
        import vertexai
        from vertexai.preview import rag
        
        project = VERTEX_CFG.get("project_id", "hyperstack-dev")
        location = VERTEX_CFG.get("location", "us-central1")
        vertexai.init(project=project, location=location)
        
        # Format clean markdown representation of lesson for RAG indexing
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
        st.toast("Successfully indexed lesson into Vertex AI RAG Corpus!", icon="🚀")
    except Exception as e:
        st.error(f"Failed to push to Vertex RAG: {e}")


# 1. Top Google Cloud Console Header
st.markdown("""
<div class="gcp-top-bar">
    <div class="gcp-top-bar-left">
        <span style="font-size: 22px;">☰</span>
        <span class="gcp-logo-text"><b>Google Cloud</b></span>
        <div class="gcp-project-selector">
            <span>::: hyperstack-dev</span>
        </div>
    </div>
    <div class="gcp-search-bar">
        🔍 Search (/) for resources, docs, products, and lessons
    </div>
    <div style="color: #5f6368; font-size: 18px;">
        ❓ &nbsp; ⚙️ &nbsp; 👤
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Page Sub-header with Console Action Links
st.markdown('<div class="gcp-breadcrumb">Vertex AI RAG Engine / Closed-Loop Learning Console</div>', unsafe_allow_html=True)
st.markdown("""
<div class="gcp-page-title-row">
    <h2 class="gcp-page-title">Incoming Lessons Queue</h2>
    <span class="gcp-action-link">➕ Create lesson</span>
    <span class="gcp-action-link">🔄 Connect RAG Corpus</span>
    <span class="gcp-action-link">⚙️ Manage database</span>
</div>
""", unsafe_allow_html=True)

# 3. Console Filter Bar
search_term = st.text_input("≡ Filter", placeholder="Enter property name or value (e.g., GKE, VPC, shacharb@google.com)", label_visibility="collapsed")

# 4. Tabbed Console View
tab_pending, tab_approved, tab_rejected, tab_json = st.tabs([
    "⏳ Pending Review", 
    "✅ Approved & Active", 
    "❌ Rejected / Retired", 
    "📥 JSON Export & Raw Data"
])

# Render Pending Review
with tab_pending:
    pending_items = load_lessons_by_status("pending_review")
    if search_term:
        pending_items = [x for x in pending_items if search_term.lower() in json.dumps(x).lower()]
        
    if not pending_items:
        st.success("No lessons pending review match the current filter.")
    else:
        st.caption(f"Showing {len(pending_items)} pending lesson rules.")
        for idx, lesson in enumerate(pending_items):
            bug_id = lesson.get("source_bug_id", "Unknown")
            submitted_by = lesson.get("submitted_by", "Unknown")
            created = lesson.get("created_at", "Unknown")
            
            with st.expander(f"⏳ {bug_id}  |  Submitted by: {submitted_by}  |  Domain: {', '.join(lesson.get('topics', []))}", expanded=(idx == 0)):
                st.markdown(f"<span class='gcp-badge badge-pending'>PENDING REVIEW</span> &nbsp; **Database:** `{STORAGE_CFG.get('firebase_database_id')}`", unsafe_allow_html=True)
                st.write("")
                
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.markdown("##### 🔍 Raw Error & Execution Context")
                    st.json(lesson.get("raw_error_context", {}))
                with col_b:
                    st.markdown("##### 💡 Automated Failure Analysis")
                    st.info(lesson.get("specific_lesson", "No specific lesson text provided."))
                
                st.divider()
                st.markdown("##### 🛠️ Rule Curation & Approval")
                with st.form(key=f"form_pending_{idx}"):
                    generalized_lesson = st.text_area(
                        "Generalized Architectural Rule (Indexed into Vertex RAG):", 
                        value=lesson.get("generalized_lesson", ""),
                        height=100
                    )
                    topics_str = st.text_input(
                        "Taxonomy Tags (comma separated):", 
                        value=", ".join(lesson.get("topics", []))
                    )
                    
                    c1, c2, c3 = st.columns([1, 1, 6])
                    with c1:
                        approve = st.form_submit_button("✅ Approve & Index", type="primary")
                    with c2:
                        reject = st.form_submit_button("❌ Reject")
                    with c3:
                        delete = st.form_submit_button("🗑️ Delete")
                        
                    if approve:
                        topics_list = [t.strip() for t in topics_str.split(",") if t.strip()]
                        update_lesson_status(lesson["_identifier"], "approved", generalized_lesson, topics_list)
                        st.success("Lesson approved and indexed into Vertex RAG!")
                        st.rerun()
                    if reject:
                        topics_list = [t.strip() for t in topics_str.split(",") if t.strip()]
                        update_lesson_status(lesson["_identifier"], "rejected", generalized_lesson, topics_list)
                        st.warning("Lesson rejected.")
                        st.rerun()
                    if delete:
                        delete_lesson(lesson["_identifier"])
                        st.error("Lesson permanently deleted.")
                        st.rerun()

# Render Approved
with tab_approved:
    approved_items = load_lessons_by_status("approved")
    if search_term:
        approved_items = [x for x in approved_items if search_term.lower() in json.dumps(x).lower()]
        
    if not approved_items:
        st.info("No approved lessons match the filter.")
    else:
        st.caption(f"Showing {len(approved_items)} active rules indexed in Vertex AI RAG Corpus ({VERTEX_CFG.get('rag_corpus_id')}).")
        for idx, lesson in enumerate(approved_items):
            bug_id = lesson.get("source_bug_id", "Unknown")
            submitted_by = lesson.get("submitted_by", "Unknown")
            
            with st.expander(f"✅ {bug_id}  |  Active Rule  |  Tags: {', '.join(lesson.get('topics', []))}", expanded=False):
                st.markdown(f"<span class='gcp-badge badge-approved'>APPROVED & INDEXED</span> &nbsp; **Submitter:** `{submitted_by}`", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"**Indexed Generalized Rule:**\n> {lesson.get('generalized_lesson')}")
                
                st.divider()
                col1, col2 = st.columns([1, 6])
                if col1.button("⏳ Revert to Pending", key=f"rev_{idx}"):
                    update_lesson_status(lesson["_identifier"], "pending_review")
                    st.rerun()
                if col2.button("🗑️ Delete Permanently", key=f"del_app_{idx}"):
                    delete_lesson(lesson["_identifier"])
                    st.rerun()

# Render Rejected
with tab_rejected:
    rejected_items = load_lessons_by_status("rejected")
    if search_term:
        rejected_items = [x for x in rejected_items if search_term.lower() in json.dumps(x).lower()]
        
    if not rejected_items:
        st.info("No rejected lessons found.")
    else:
        st.caption(f"Showing {len(rejected_items)} archived / rejected lessons.")
        for idx, lesson in enumerate(rejected_items):
            bug_id = lesson.get("source_bug_id", "Unknown")
            submitted_by = lesson.get("submitted_by", "Unknown")
            
            with st.expander(f"❌ {bug_id}  |  Archived Rule", expanded=False):
                st.markdown(f"<span class='gcp-badge badge-rejected'>REJECTED</span> &nbsp; **Submitter:** `{submitted_by}`", unsafe_allow_html=True)
                st.write("")
                st.markdown(f"**Rule Text:** {lesson.get('generalized_lesson')}")
                
                st.divider()
                col1, col2 = st.columns([1, 6])
                if col1.button("♻️ Restore to Pending", key=f"rest_{idx}"):
                    update_lesson_status(lesson["_identifier"], "pending_review")
                    st.rerun()
                if col2.button("🗑️ Delete Permanently", key=f"del_rej_{idx}"):
                    delete_lesson(lesson["_identifier"])
                    st.rerun()

# Render JSON Export
with tab_json:
    all_lessons = load_lessons_by_status("all")
    if search_term:
        all_lessons = [x for x in all_lessons if search_term.lower() in json.dumps(x).lower()]
        
    st.markdown("### 📥 Standardized Knowledge Base Export")
    st.write("Export all curated lessons learned across all statuses in standardized JSON format for auditing, backup, or downstream ingestion.")
    
    export_json_str = json.dumps(all_lessons, indent=2)
    st.download_button(
        label="💾 Download JSON Export (`lessons_learned_export.json`)",
        data=export_json_str,
        file_name="lessons_learned_export.json",
        mime="application/json",
        type="primary"
    )
    
    st.divider()
    st.markdown("#### Raw JSON Dataset Preview")
    st.json(all_lessons)
