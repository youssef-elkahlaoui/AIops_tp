import streamlit as st
import os
import shutil
import hashlib
from pathlib import Path
from langchain_chroma import Chroma
from dotenv import load_dotenv
from utils.rag_pipeline import build_vector_store
from utils.chat_interface import setup_chat_interface
from utils.embeddings import LocalHuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Configuration - Use absolute paths based on script location
APP_DIR = Path(__file__).parent.resolve()
DATA_PATH = str(APP_DIR / "data")
DB_PATH = str(APP_DIR / "chroma_db")

def get_data_folder_hash(data_path):
    """Calculate a hash of all files in the data folder to detect changes."""
    hash_md5 = hashlib.md5()
    if not os.path.exists(data_path):
        return "empty"
    
    files_found = []
    for root, dirs, files in os.walk(data_path):
        for file in sorted(files):
            if file.endswith(('.txt', '.md', '.json')):
                filepath = os.path.join(root, file)
                files_found.append(file)
                # Include filename and modification time in hash
                hash_md5.update(file.encode())
                hash_md5.update(str(os.path.getmtime(filepath)).encode())
                # Include file content
                with open(filepath, 'rb') as f:
                    hash_md5.update(f.read())
    
    if not files_found:
        return "empty"
    return hash_md5.hexdigest()

# Cache the embeddings model to avoid reloading on every page refresh
@st.cache_resource
def get_embeddings():
    """Load embeddings model once and cache it."""
    return LocalHuggingFaceEmbeddings()

@st.cache_resource
def load_vector_store(_embeddings, db_path, _data_hash):
    """Load existing vector store from disk. The _data_hash parameter forces reload when data changes."""
    if os.path.exists(db_path):
        return Chroma(persist_directory=db_path, embedding_function=_embeddings)
    return None

# Page Config
st.set_page_config(page_title="ENSA Al Hoceima Assistant", page_icon="🎓", layout="wide")

# Custom CSS for "Fancy" UI
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        border-radius: 10px;
    }
    .sidebar-content {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎓 ENSA Al Hoceima AI Assistant</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ MLOps Control Panel")
    
    # API Key Input
    api_key = st.text_input("🔑 Google API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    
    # File Upload
    st.subheader("📂 Data Ingestion")
    uploaded_files = st.file_uploader("Upload Knowledge Base (Supported: .txt, .md, .json)", accept_multiple_files=True, type=['txt', 'md', 'json'])
    
    if uploaded_files:
        # Check if we already processed these files
        uploaded_names = sorted([f.name for f in uploaded_files])
        last_uploaded = st.session_state.get("last_uploaded_files", [])
        
        if uploaded_names != last_uploaded:
            if not os.path.exists(DATA_PATH):
                os.makedirs(DATA_PATH)
            
            for uploaded_file in uploaded_files:
                with open(os.path.join(DATA_PATH, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ Uploaded {len(uploaded_files)} files!")
            st.session_state["last_uploaded_files"] = uploaded_names
            st.session_state["trigger_rebuild"] = True
            st.rerun()

    st.divider()
    
    # Manual Rebuild Button
    rebuild_clicked = st.button("🔄 Rebuild Vector Store")
    
    # Show sync status
    st.divider()
    st.subheader("📊 Status")
    
    # Data folder info
    data_files = [f for f in os.listdir(DATA_PATH) if f.endswith(('.txt', '.md', '.json'))] if os.path.exists(DATA_PATH) else []
    st.caption(f"**Data Files:** {len(data_files)}")
    
    # Vector store status
    vs_exists = os.path.exists(os.path.join(DB_PATH, "chroma.sqlite3"))
    if vs_exists:
        st.caption("**Vector Store:** ✅ Ready")
    else:
        st.caption("**Vector Store:** ⚠️ Not built")

# Calculate current data folder hash
current_hash = get_data_folder_hash(DATA_PATH)

# Get stored hash from vector store metadata file (persists across sessions)
HASH_FILE = os.path.join(DB_PATH, ".data_hash")

def read_stored_hash():
    """Read the stored data hash from disk."""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            return f.read().strip()
    return None

def write_stored_hash(hash_value):
    """Write the data hash to disk for persistence."""
    os.makedirs(DB_PATH, exist_ok=True)
    with open(HASH_FILE, 'w') as f:
        f.write(hash_value)

stored_hash = read_stored_hash()

# Determine if we need to rebuild
needs_rebuild = False
auto_rebuild = False
rebuild_reason = ""

# Check for manual rebuild or upload trigger
if rebuild_clicked or st.session_state.get("trigger_rebuild", False):
    needs_rebuild = True
    rebuild_reason = "manual"
    st.session_state["trigger_rebuild"] = False
elif current_hash != "empty":
    # Check if vector store exists
    vector_store_exists = os.path.exists(DB_PATH) and os.path.exists(os.path.join(DB_PATH, "chroma.sqlite3"))
    
    if not vector_store_exists:
        # No vector store yet - need initial build
        needs_rebuild = True
        rebuild_reason = "initial"
    elif stored_hash is None:
        # Vector store exists but no hash file - need to sync
        needs_rebuild = True
        rebuild_reason = "sync"
        auto_rebuild = True
    elif stored_hash != current_hash:
        # Data folder changed - auto rebuild
        needs_rebuild = True
        rebuild_reason = "changed"
        auto_rebuild = True

# Initialize embeddings
embeddings = get_embeddings()

# Check if data folder has valid files
def has_valid_data_files(data_path):
    """Check if data folder has .txt, .md, or .json files."""
    if not os.path.exists(data_path):
        return False
    return any(f.endswith(('.txt', '.md', '.json')) for f in os.listdir(data_path))

# Handle rebuild if needed
if needs_rebuild and has_valid_data_files(DATA_PATH):
    if rebuild_reason == "manual":
        st.info("🔄 **Manual rebuild requested.** Rebuilding knowledge base...")
    elif rebuild_reason == "changed":
        st.info("📁 **Data folder changes detected!** Auto-rebuilding knowledge base...")
    elif rebuild_reason == "sync":
        st.info("🔄 **Syncing vector store with data folder...**")
    elif rebuild_reason == "initial":
        st.info("🚀 **Building initial knowledge base...**")
    
    # Clear Streamlit cache to release any cached vector store connections
    load_vector_store.clear()
    
    # Force Python to release all references and file handles
    import gc
    gc.collect()
    
    # Use a fresh temporary directory for the new build, then swap
    import time
    temp_db_path = DB_PATH + "_new_" + str(int(time.time()))
    old_db_path = DB_PATH + "_old_" + str(int(time.time()))
    
    # Ensure the temp directory exists
    os.makedirs(temp_db_path, exist_ok=True)
    st.write(f"📂 Building in temporary location...")
    
    # Run the pipeline with the new temp directory
    try:
        vector_store = build_vector_store(DATA_PATH, temp_db_path)
    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        vector_store = None
        # Cleanup temp dir on failure
        if os.path.exists(temp_db_path):
            shutil.rmtree(temp_db_path, ignore_errors=True)
    
    if vector_store:
        # Swap directories: rename old to backup, new to current
        try:
            if os.path.exists(DB_PATH):
                os.rename(DB_PATH, old_db_path)
            os.rename(temp_db_path, DB_PATH)
            
            # Clean up old directory (might fail if locked, that's ok)
            shutil.rmtree(old_db_path, ignore_errors=True)
            
            # Also clean up any other old temp directories
            parent_dir = os.path.dirname(DB_PATH)
            for item in os.listdir(parent_dir):
                if item.startswith("chroma_db_") and os.path.isdir(os.path.join(parent_dir, item)):
                    shutil.rmtree(os.path.join(parent_dir, item), ignore_errors=True)
            
            # Reload the vector store from the new location
            vector_store = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
            
            st.write("🗑️ Swapped to new vector store.")
        except Exception as e:
            st.warning(f"Note: {e}")
        
        write_stored_hash(current_hash)
        st.session_state["last_data_hash"] = current_hash
        st.balloons()
        st.success("✅ Vector store rebuilt successfully!")
    else:
        st.error("❌ Failed to rebuild vector store. Check the logs for details.")
else:
    # Load existing vector store or None
    if os.path.exists(DB_PATH) and os.path.exists(os.path.join(DB_PATH, "chroma.sqlite3")) and current_hash != "empty":
        vector_store = load_vector_store(embeddings, DB_PATH, current_hash)
        st.session_state["last_data_hash"] = current_hash
    else:
        vector_store = None

# Show build button if no vector store and data exists
if vector_store is None and not needs_rebuild:
    if has_valid_data_files(DATA_PATH):
        st.info("👈 Click **'Rebuild Vector Store'** in the sidebar to initialize the AI.")
    else:
        st.warning("⚠️ No data found in `app/data/`. Please upload files or add `.txt`/`.md` files to the folder.")

# Chat Interface
if vector_store:
    if not os.environ.get("GOOGLE_API_KEY"):
        st.warning("⚠️ Please enter your Google API Key in the sidebar to enable the chatbot.")
    else:
        setup_chat_interface(vector_store)