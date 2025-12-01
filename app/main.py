import streamlit as st
import os
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
            if file.endswith(('.txt', '.md')):
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
    uploaded_files = st.file_uploader("Upload Knowledge Base (Supported: .txt, .md)", accept_multiple_files=True, type=['txt', 'md'])
    
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

# Calculate current data folder hash
current_hash = get_data_folder_hash(DATA_PATH)
stored_hash = st.session_state.get("last_data_hash", None)

# Determine if we need to rebuild
needs_rebuild = False
auto_rebuild = False

# Check for manual rebuild or upload trigger
if rebuild_clicked or st.session_state.get("trigger_rebuild", False):
    needs_rebuild = True
    st.session_state["trigger_rebuild"] = False
elif stored_hash is not None and stored_hash != current_hash:
    # Data folder changed externally - auto rebuild
    needs_rebuild = True
    auto_rebuild = True

# Initialize embeddings
embeddings = get_embeddings()

# Handle rebuild if needed
if needs_rebuild and os.path.exists(DATA_PATH) and os.listdir(DATA_PATH):
    if auto_rebuild:
        st.info("📁 **Data folder changes detected!** Auto-rebuilding knowledge base...")
    
    # Clear cache
    load_vector_store.clear()
    
    # Run the pipeline with full visualization
    vector_store = build_vector_store(DATA_PATH, DB_PATH)
    
    if vector_store:
        st.session_state["last_data_hash"] = current_hash
        st.balloons()
else:
    # Load existing vector store or None
    if os.path.exists(DB_PATH) and current_hash != "empty":
        vector_store = load_vector_store(embeddings, DB_PATH, current_hash)
        # Store the hash if not already stored
        if "last_data_hash" not in st.session_state:
            st.session_state["last_data_hash"] = current_hash
    else:
        vector_store = None

# Show build button if no vector store and data exists
if vector_store is None and not needs_rebuild:
    if os.path.exists(DATA_PATH) and os.listdir(DATA_PATH):
        st.info("👈 Click **'Rebuild Vector Store'** in the sidebar to initialize the AI.")
    else:
        st.warning("⚠️ No data found in `app/data/`. Please upload files or add `.txt`/`.md` files to the folder.")

# Chat Interface
if vector_store:
    if not os.environ.get("GOOGLE_API_KEY"):
        st.warning("⚠️ Please enter your Google API Key in the sidebar to enable the chatbot.")
    else:
        setup_chat_interface(vector_store)