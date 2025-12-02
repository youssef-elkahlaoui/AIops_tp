# ChromaDB & Embeddings - Documentation

## 📌 How Embeddings Work in This Project

### What are Embeddings?

Embeddings are **numerical vector representations** of text. They convert human-readable text into arrays of numbers (vectors) that capture the **semantic meaning** of the text.

```
"ENSA Al Hoceima is an engineering school"
        ↓ Embedding Model
[0.023, -0.156, 0.892, 0.445, ..., 0.112]  # 384 dimensions
```

### The Embedding Model Used

This project uses **`all-MiniLM-L6-v2`** from Sentence Transformers:

| Property    | Value                                    |
| ----------- | ---------------------------------------- |
| Model       | `all-MiniLM-L6-v2`                       |
| Vector Size | 384 dimensions                           |
| Type        | Local (no API needed)                    |
| Speed       | Very fast (~14,000 sentences/sec on GPU) |
| Quality     | Good for semantic similarity             |

### How It's Implemented

**File: `app/utils/embeddings.py`**

```python
from sentence_transformers import SentenceTransformer

class LocalHuggingFaceEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        # Convert list of texts to vectors
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        # Convert single query to vector
        return self.model.encode(text).tolist()
```

---

## 📌 How ChromaDB Works

### What is ChromaDB?

ChromaDB is a **vector database** - it stores embeddings and allows fast **similarity search**. When you ask a question, it finds the most similar documents based on vector distance.

### The RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDEXING (Build Phase)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📄 Documents        →  ✂️ Chunks         →  🔢 Embeddings       │
│  (txt, md files)        (500 chars)          (384-dim vectors)  │
│                                                                  │
│  "ENSA Al Hoceima    →  ["ENSA Al         →  [[0.02, -0.15,    │
│   is located in         Hoceima is           0.89, ...],       │
│   northern Morocco      located...",         [0.11, 0.33,      │
│   and offers..."        "offers             -0.22, ...]]       │
│                          engineering..."]                       │
│                                                                  │
│                              ↓                                   │
│                     💾 Store in ChromaDB                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL (Query Phase)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ❓ User Question    →  🔢 Query Embedding  →  🔍 Similarity    │
│  "What programs        [0.05, -0.12,          Search            │
│   does ENSA offer?"     0.77, ...]                              │
│                                                                  │
│                              ↓                                   │
│                     📋 Top K Similar Chunks                      │
│                     (returned to LLM as context)                │
└─────────────────────────────────────────────────────────────────┘
```

### Similarity Search

ChromaDB uses **cosine similarity** to find relevant documents:

```
Cosine Similarity = (A · B) / (||A|| × ||B||)

Result: -1 (opposite) to 1 (identical)
```

Example:

- Query: "engineering programs" → vector A
- Doc 1: "ENSA offers engineering degrees" → vector B (similarity: 0.89 ✅)
- Doc 2: "Student cafeteria hours" → vector C (similarity: 0.23 ❌)

---

## 📁 ChromaDB Folder Structure

```
app/chroma_db/
├── chroma.sqlite3                    # Main database file
├── .data_hash                        # Hash for change detection (custom)
└── 59d84b0c-e773-4d51-9790-.../     # Collection folder (UUID)
    ├── data_level0.bin               # Vector data (HNSW index)
    ├── header.bin                    # Index header
    ├── index_metadata.pickle         # Index configuration
    ├── length.bin                    # Vector lengths
    └── link_lists.bin                # HNSW graph links
```

### File Explanations

| File                    | Purpose                                                              |
| ----------------------- | -------------------------------------------------------------------- |
| `chroma.sqlite3`        | SQLite database storing metadata, document text, and collection info |
| `.data_hash`            | Custom file to track data folder changes for auto-rebuild            |
| `data_level0.bin`       | Binary file containing the actual embedding vectors                  |
| `header.bin`            | HNSW index header information                                        |
| `index_metadata.pickle` | Python pickle with index configuration                               |
| `length.bin`            | Length information for vectors                                       |
| `link_lists.bin`        | HNSW graph structure for fast nearest-neighbor search                |

### SQLite Tables (in chroma.sqlite3)

| Table                | Content                                     |
| -------------------- | ------------------------------------------- |
| `collections`        | Collection names and metadata               |
| `embedding_metadata` | Document metadata (source file, chunk info) |
| `embeddings`         | Raw embedding vectors (if not using HNSW)   |
| `segments`           | Segment information for the collection      |

---

## 📌 How to Explore ChromaDB

### Method 1: Python Shell

```python
import chromadb

# Connect
client = chromadb.PersistentClient(path="app/chroma_db")

# Get collection
collection = client.get_collection("langchain")

# Count documents
print(f"Documents: {collection.count()}")

# View documents
results = collection.get(include=["documents", "metadatas"])
for i, doc in enumerate(results["documents"][:3]):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Text: {doc[:150]}...")
    print(f"Source: {results['metadatas'][i]}")

# Search
results = collection.query(
    query_texts=["What programs does ENSA offer?"],
    n_results=3
)
print(results)
```

### Method 2: SQLite Browser

1. Download [DB Browser for SQLite](https://sqlitebrowser.org/)
2. Open `app/chroma_db/chroma.sqlite3`
3. Browse tables: `embedding_metadata`, `collections`

### Method 3: VS Code Extension

1. Install "SQLite Viewer" extension
2. Click on `chroma.sqlite3` file
3. Browse tables visually

---

## 📌 Key Code Files

### 1. `app/utils/embeddings.py` - Embedding Wrapper

```python
class LocalHuggingFaceEmbeddings:
    """Wrapper for sentence-transformers to work with LangChain."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list) -> list:
        return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> list:
        return self.model.encode(text).tolist()
```

### 2. `app/utils/rag_pipeline.py` - Vector Store Builder

```python
def build_vector_store(data_path, db_path):
    # 1. Load documents
    documents = []
    for file in Path(data_path).glob("*.txt"):
        documents.append(file.read_text())

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    # 3. Create embeddings & store
    embeddings = LocalHuggingFaceEmbeddings()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path
    )

    return vector_store
```

### 3. `app/main.py` - Using the Vector Store

```python
# Load vector store
vector_store = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings
)

# Create retriever
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# Query
docs = retriever.get_relevant_documents("What is ENSA?")
```

---

## 📌 HNSW Algorithm (How ChromaDB Searches Fast)

ChromaDB uses **HNSW (Hierarchical Navigable Small World)** for fast similarity search:

```
Level 2:  [A]--------[B]           (few nodes, long jumps)
           |          |
Level 1:  [A]--[C]--[B]--[D]       (more nodes, medium jumps)
           |   |     |   |
Level 0:  [A][C][E][B][D][F][G]    (all nodes, short jumps)
```

- **Search**: Start at top level, greedily move to nearest neighbor, drop down
- **Complexity**: O(log n) instead of O(n) for brute force
- **Speed**: Can search millions of vectors in milliseconds

---

## 📌 Summary

| Component        | Technology            | Purpose                        |
| ---------------- | --------------------- | ------------------------------ |
| Embedding Model  | `all-MiniLM-L6-v2`    | Convert text → 384-dim vectors |
| Vector Database  | ChromaDB              | Store & search vectors         |
| Search Algorithm | HNSW                  | Fast nearest-neighbor search   |
| Storage          | SQLite + Binary files | Persist data to disk           |
| Integration      | LangChain             | Connect retriever to LLM       |

The complete flow:

1. **User uploads documents** → stored in `app/data/`
2. **Build pipeline** → chunks documents, creates embeddings, stores in ChromaDB
3. **User asks question** → question embedded, similar chunks retrieved
4. **LLM generates answer** → using retrieved context + question
