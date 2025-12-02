import os
import shutil
import time
import streamlit as st
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from utils.embeddings import LocalHuggingFaceEmbeddings

def build_vector_store(data_path, db_path):
    """
    Orchestrates the RAG pipeline: Load -> Split -> Embed -> Store.
    Returns the vector store object or None on failure.
    Uses local HuggingFace embeddings (no API key required for embeddings).
    """

    # MLOps Pipeline Visualization
    st.subheader("🚀 MLOps Pipeline Execution")
    
    # Stage 1: Data Loading
    with st.status("📥 Stage 1: Data Ingestion (Loading)", expanded=True) as status:
        st.write(f"Scanning `{data_path}` for documents...")
        print("\\n--- [MLOps] Stage 1: Data Ingestion ---")
        documents = []
        for ext in ["*.md", "*.txt", "*.json"]:
            try:
                loader = DirectoryLoader(
                    data_path, 
                    glob=ext, 
                    loader_cls=TextLoader,
                    loader_kwargs={"encoding": "utf-8"}
                )
                docs = loader.load()
                if docs:
                    documents.extend(docs)
                    print(f"Loaded {len(docs)} files with extension {ext}")
                    st.write(f"Found {len(docs)} files with extension `{ext}`")
            except Exception as e:
                st.warning(f"Error loading {ext} files: {e}")
        
        if not documents:
            status.update(label="⚠️ Stage 1 Failed: No documents found!", state="error")
            return None
            
        print(f"Total documents loaded: {len(documents)}")
        st.write(f"**Total Documents:** {len(documents)}")
        
        # Show sample content
        if documents:
            with st.expander("📄 View Sample Loaded Data"):
                st.text(documents[0].page_content[:500] + "...")
        
        status.update(label="✅ Stage 1 Completed", state="complete", expanded=False)

    # Stage 2: Text Splitting
    with st.status("✂️ Stage 2: Data Preprocessing (Splitting)", expanded=True) as status:
        st.write("Splitting documents into chunks...")
        print("\n--- [MLOps] Stage 2: Data Preprocessing ---")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        st.write(f"**Total Chunks Created:** {len(chunks)}")
        
        # Show sample chunk
        if chunks:
            with st.expander("🧩 View Sample Chunk"):
                st.info(f"Chunk 1/{len(chunks)}")
                st.text(chunks[0].page_content)
                
        status.update(label="✅ Stage 2 Completed", state="complete", expanded=False)

    # Stage 3 & 4: Embedding & Storage (Batched)
    with st.status("🧠 Stage 3 & 4: Embedding & Vector Storage (Batched)", expanded=True) as status:
        st.write("Initializing Local HuggingFace Embeddings...")
        print("\n--- [MLOps] Stage 3: Feature Engineering ---")
        
        embeddings = LocalHuggingFaceEmbeddings()
        st.write("Model: `sentence-transformers/all-MiniLM-L6-v2` (Local - No API limits)")
        
        # Visualize embedding (Real Sample)
        if chunks:
            sample_text = chunks[0].page_content[:20]
            st.write(f"Generating sample vector for: `'{sample_text}...'`")
            try:
                sample_vector = embeddings.embed_query(chunks[0].page_content)
                st.write(f"**Vector Dimensions:** {len(sample_vector)}")
                st.write(f"**Sample Vector (First 5 dims):** `{sample_vector[:5]}...`")
            except Exception as e:
                st.warning(f"Could not generate sample embedding: {e}")

        # Process all chunks at once (local embeddings - no rate limits)
        total_chunks = len(chunks)
        st.write(f"Processing {total_chunks} chunks...")
        
        try:
            # Create the vector store with all documents
            if total_chunks > 0:
                vector_store = Chroma.from_documents(
                    documents=chunks, 
                    embedding=embeddings, 
                    persist_directory=db_path
                )
                st.write(f"✅ All {total_chunks} chunks processed successfully.")
            else:
                return None

            print("Vector store updated and persisted.")
            st.write("✅ ChromaDB updated successfully.")
            
        except Exception as e:
            print(f"Error in Stage 3/4: {e}")
            status.update(label="❌ Stage 3/4 Failed", state="error")
            st.error(f"Error: {str(e)}")
            return None
            
        status.update(label="✅ Stage 3 & 4 Completed", state="complete", expanded=False)

    st.success("🎉 MLOps Pipeline Finished Successfully!")
    return vector_store
