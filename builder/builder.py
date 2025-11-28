import os, time, json, shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import numpy as np
import faiss

DATA_DIR = os.getenv("DATA_DIR", "/data")
INDICES_DIR = os.getenv("INDICES_DIR", "/data/indices")
GEMINI_EMBED_URL = os.getenv("GEMINI_EMBED_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ROUTER_URL = os.getenv("ROUTER_URL", "http://router:8000/activate")

def read_all_docs():
    docs = []
    knowledge_dir = os.path.join(DATA_DIR, "knowledge")
    if not os.path.exists(knowledge_dir):
        return docs
    for fname in os.listdir(knowledge_dir):
        path = os.path.join(knowledge_dir, fname)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                docs.append({"id": fname, "text": f.read()})
    return docs

def get_embeddings(texts):
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    body = {"inputs": texts}
    try:
        r = requests.post(GEMINI_EMBED_URL, json=body, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()["embeddings"]
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        # Return dummy embeddings
        return [np.random.rand(384).tolist() for _ in texts]

def build_faiss_index(docs, outdir):
    if not docs:
        print("No docs to build index.")
        return
    texts = [d["text"] for d in docs]
    embs = get_embeddings(texts)
    arr = np.array(embs).astype("float32")
    d = arr.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(arr)
    os.makedirs(outdir, exist_ok=True)
    faiss.write_index(index, os.path.join(outdir, "faiss.index"))
    with open(os.path.join(outdir, "docs.json"), "w", encoding="utf-8") as f:
        json.dump(docs, f)

def activate_version(version):
    try:
        requests.post(ROUTER_URL, params={"version": version}, timeout=10)
    except Exception as e:
        print(f"Error activating version: {e}")

class WatchHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        print("Detected change -> rebuilding index...")
        try:
            # Wait a bit for file write to complete
            time.sleep(1)
            docs = read_all_docs()
            tmp = os.path.join(INDICES_DIR, "tmp_build")
            if os.path.exists(tmp):
                shutil.rmtree(tmp)
            build_faiss_index(docs, tmp)
            target = os.path.join(INDICES_DIR, "v2")
            if os.path.exists(target):
                shutil.rmtree(target)
            shutil.move(tmp, target)
            # activate v2
            activate_version("v2")
            print("Activated v2")
        except Exception as e:
            print("Build error:", e)

if __name__ == "__main__":
    path = os.path.join(DATA_DIR, "knowledge")
    os.makedirs(path, exist_ok=True)
    os.makedirs(INDICES_DIR, exist_ok=True)
    
    # create default v1 if missing (one-time)
    v1_path = os.path.join(INDICES_DIR, "v1")
    if not os.path.exists(v1_path) or not os.listdir(v1_path):
        print("Building initial v1 index...")
        docs = read_all_docs()
        if docs:
            build_faiss_index(docs, v1_path)
        else:
            print("No docs found for initial build. Waiting for data...")
            
    # ensure active file
    active_file = os.path.join(DATA_DIR, "active_version")
    if not os.path.exists(active_file):
        with open(active_file, "w") as f:
            f.write("v1")
            
    event_handler = WatchHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print("Watcher started on", path)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
