import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import faiss
import json
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_CHAT_URL = os.getenv("GEMINI_CHAT_URL")
INDEX_PATH = os.getenv("INDEX_PATH", "/indices/v1")

app = FastAPI()

class Query(BaseModel):
    query: str

# global index and doc store
index = None
docs = []
last_loaded_time = 0

def load_index(index_dir):
    global index, docs, last_loaded_time
    faiss_index_file = os.path.join(index_dir, "faiss.index")
    docs_file = os.path.join(index_dir, "docs.json")
    
    if not os.path.exists(faiss_index_file) or not os.path.exists(docs_file):
        # Files not ready yet
        return

    try:
        mtime = os.path.getmtime(faiss_index_file)
        # Reload if never loaded or file changed
        if index is None or mtime > last_loaded_time:
            print(f"Loading index from {index_dir} (mtime={mtime})...")
            index = faiss.read_index(faiss_index_file)
            with open(docs_file, "r", encoding="utf-8") as f:
                docs = json.load(f)
            last_loaded_time = mtime
            print("Index loaded successfully.")
    except Exception as e:
        print(f"Could not load index: {e}")

@app.on_event("startup")
def startup_event():
    load_index(INDEX_PATH)

def call_gemini_chat(prompt, context_docs):
    body = {
        "prompt": prompt,
        "context": "\n\n".join(context_docs),
        "max_tokens": 512
    }
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(GEMINI_CHAT_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("text", resp.text)
    except Exception as e:
        print(f"Error calling Gemini Chat: {e}")
        return "Error generating answer."

def embed_texts(texts):
    url = os.getenv("GEMINI_EMBED_URL")
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    body = {"inputs": texts}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()["embeddings"]
    except Exception as e:
        print(f"Error calling Gemini Embed: {e}")
        return [np.random.rand(384).tolist() for _ in texts]

@app.post("/chat")
def chat(q: Query):
    global index, docs
    # Check for updates before answering
    load_index(INDEX_PATH)
    
    if index is None:
        raise HTTPException(status_code=503, detail="Index not loaded")
    
    try:
        q_emb = embed_texts([q.query])[0]
    except Exception:
        raise HTTPException(status_code=500, detail="Embedding failed")
        
    xq = np.array([q_emb]).astype("float32")
    k = 5
    if index.d != xq.shape[1]:
        # Dimension mismatch (e.g. dummy embedding vs real index)
        # Just return empty or error
        return {"answer": "Error: Embedding dimension mismatch.", "retrieved": []}

    D, I = index.search(xq, k)
    hits = []
    for i in I[0]:
        if i < len(docs) and i >= 0:
            hits.append(docs[i])
            
    context = [h["text"] for h in hits]
    answer = call_gemini_chat(q.query, context)
    return {"answer": answer, "retrieved": context}

@app.get("/health")
def health():
    return {"status": "ok", "index_loaded": index is not None}
