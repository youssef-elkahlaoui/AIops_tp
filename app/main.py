import streamlit as st
import os
import sys
from pathlib import Path
from langchain_chroma import Chroma
from dotenv import load_dotenv
from utils.rag_pipeline import build_vector_store, reset_vector_store
from utils.chat_interface import setup_chat_interface
from utils.embeddings import LocalHuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Configuration - Use absolute paths based on script location
APP_DIR = Path(__file__).parent.resolve()
DATA_PATH = str(APP_DIR / "data")
DB_PATH = str(APP_DIR / "chroma_db")

# Cache the embeddings model to avoid reloading on every page refresh
@st.cache_resource
def get_embeddings():
    """Load embeddings model once and cache it."""
    return LocalHuggingFaceEmbeddings()

@st.cache_resource
def load_vector_store(_embeddings, db_path):
    """Load existing vector store from disk."""
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
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)
        
        for uploaded_file in uploaded_files:
            with open(os.path.join(DATA_PATH, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded {len(uploaded_files)} files to {DATA_PATH}")

    st.divider()
    
    # Reset Button - marks for reset on next run
    if st.button("🔄 Reset Knowledge Base"):
        st.session_state["reset_requested"] = True
        st.warning("Reset requested! Click 'Build/Update Vector Store' to rebuild.")
        st.rerun()

# Check if reset was requested
if st.session_state.get("reset_requested", False):
    # Delete the database folder
    if os.path.exists(DB_PATH):
        try:
            import shutil
            shutil.rmtree(DB_PATH)
            st.success("Old database deleted!")
        except PermissionError:
            st.error("Could not delete database. Close other apps using it and restart Streamlit.")
    st.session_state["reset_requested"] = False

# Initialize Vector Store
embeddings = get_embeddings()  # Use cached embeddings
vector_store = load_vector_store(embeddings, DB_PATH)  # Use cached vector store

# Show rebuild button when DB exists
if vector_store is not None:
    if st.sidebar.button("🔄 Rebuild Vector Store"):
        # Clear cache and rebuild
        load_vector_store.clear()
        vector_store.reset_collection()
        vector_store = build_vector_store(DATA_PATH, DB_PATH)
        st.success("Database rebuilt!")
        st.rerun()

if vector_store is None:
    if os.path.exists(DATA_PATH) and os.listdir(DATA_PATH):
        if st.sidebar.button("🚀 Build Vector Store"):
            vector_store = build_vector_store(DATA_PATH, DB_PATH)
        else:
            st.info("👈 Click 'Build Vector Store' to initialize the AI.")
    else:
        st.warning("No data found in `app/data/`. Please upload files.")

# Chat Interface
if vector_store:
    if not os.environ.get("GOOGLE_API_KEY"):
        st.warning("⚠️ Please enter your Google API Key in the sidebar to enable the chatbot.")
    else:
        setup_chat_interface(vector_store)
