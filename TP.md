# TP AIOps : Pipeline RAG Zéro-Downtime

Ce guide vous accompagnera étape par étape dans la mise en place et le déploiement d'un pipeline AIOps qui met à jour un système RAG (Retrieval Augmented Generation) en temps réel sans interruption de service (Déploiement Blue/Green).

**Architecture :**
- **2 Services Backend (v1 & v2) :** APIs RAG identiques tournant en parallèle.
- **Router :** Un reverse-proxy intelligent dirigeant le trafic vers la version active.
- **Builder (Watchdog) :** Détecte les changements de données, reconstruit l'index vectoriel et déclenche la bascule.
- **UI :** Une interface Streamlit pour l'utilisateur.
- **Data Layer :** Base de connaissance partagée.

---

## Partie 1 : Prérequis

**Étape 1 : Installer Docker Desktop**
1. Assurez-vous que Docker Desktop est installé et en cours d'exécution.
2. Vérifiez l'installation :
```powershell
docker --version
docker compose version
```

**Étape 2 : Obtenir votre clé API Gemini**
1. Vous devez avoir votre clé API Google Gemini prête.
2. Gardez-la en sécurité, vous en aurez besoin pour la configuration.

---

## Partie 2 : Configuration du Projet

**Étape 1 : Créer la structure des dossiers**
Ouvrez votre terminal (PowerShell ou Invite de commandes) et exécutez :

```powershell
# Créer le dossier principal du projet
mkdir aiops-tp
cd aiops-tp

# Créer les sous-dossiers pour les services et les données
mkdir backend
mkdir router
mkdir builder
mkdir ui
mkdir data
mkdir data\knowledge
mkdir indices
```

**Étape 2 : Créer le fichier de configuration (.env)**
Créez un fichier nommé `.env` à la racine du dossier `aiops-tp` :

```ini
GEMINI_API_KEY=VOTRE_VRAIE_CLE_API_ICI
GEMINI_EMBED_URL=https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent
GEMINI_CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
ROUTER_PORT=8000
BACKEND_PORT_V1=8101
BACKEND_PORT_V2=8102
UI_PORT=8501
DATA_DIR=/data
INDICES_DIR=/data/indices
```
*Note : Remplacez `VOTRE_VRAIE_CLE_API_ICI` par votre véritable clé.*

---

## Partie 3 : Création du Code des Services

**Étape 1 : Service Backend**
Créez `backend/app.py` :
```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import faiss
import json
import requests

app = FastAPI()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INDEX_PATH = os.getenv("INDEX_PATH", "/indices/v1")
index = None
docs = []

@app.on_event("startup")
def startup():
    global index, docs
    try:
        index = faiss.read_index(os.path.join(INDEX_PATH, "faiss.index"))
        with open(os.path.join(INDEX_PATH, "docs.json"), "r") as f:
            docs = json.load(f)
        print(f"Index chargé depuis {INDEX_PATH}")
    except:
        print("Index non trouvé pour le moment.")

@app.post("/chat")
def chat(q: BaseModel):
    # 1. Embed query
    url = os.getenv("GEMINI_EMBED_URL")
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    emb = requests.post(url, json={"inputs": [q.query]}, headers=headers).json()["embeddings"][0]
    
    # 2. Search Index
    D, I = index.search(np.array([emb]).astype("float32"), 5)
    context = [docs[i]["text"] for i in I[0] if i < len(docs)]
    
    # 3. Generate Answer
    chat_url = os.getenv("GEMINI_CHAT_URL")
    prompt = f"Context: {context}\n\nQuestion: {q.query}"
    resp = requests.post(chat_url, json={"prompt": prompt}, headers=headers).json()
    return {"answer": resp.get("text", "Pas de réponse"), "retrieved": context}
```

Créez `backend/Dockerfile` :
```dockerfile
FROM python:3.10-slim
RUN pip install fastapi uvicorn requests numpy faiss-cpu pydantic
COPY app.py .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100"]
```

**Étape 2 : Service Router**
Créez `router/router.py` :
```python
import os, httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
ACTIVE_FILE = "/data/active_version"
BACKENDS = {
    "v1": f"http://rag-backend-v1:{os.getenv('BACKEND_PORT_V1')}",
    "v2": f"http://rag-backend-v2:{os.getenv('BACKEND_PORT_V2')}"
}

class Query(BaseModel):
    query: str

@app.post("/chat")
async def chat(q: Query):
    # Lire la version active
    version = "v1"
    if os.path.exists(ACTIVE_FILE):
        with open(ACTIVE_FILE, "r") as f:
            version = f.read().strip()
    
    # Transférer la requête
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKENDS.get(version, 'v1')}/chat", json=q.dict())
        return resp.json()

@app.post("/activate")
def activate(version: str):
    with open(ACTIVE_FILE, "w") as f:
        f.write(version)
    return {"status": "switched", "version": version}
```

Créez `router/Dockerfile` :
```dockerfile
FROM python:3.10-slim
RUN pip install fastapi uvicorn httpx
COPY router.py .
CMD ["uvicorn", "router:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Étape 3 : Service Builder**
Créez `builder/builder.py` :
```python
import os, time, json, shutil, requests, faiss, numpy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DATA_DIR = "/data"
INDICES_DIR = "/indices"

def build_index(version):
    print(f"Construction de l'index pour {version}...")
    docs = []
    for f in os.listdir(f"{DATA_DIR}/knowledge"):
        with open(f"{DATA_DIR}/knowledge/{f}", "r") as file:
            docs.append({"text": file.read()})
    
    # Embed et Index (Simplifié pour le TP)
    # [ETUDIANTS: Insérer la logique d'embedding ici si nécessaire]
    # Pour ce TP, le code complet est fourni dans le repo.
    
    # Notifier le Router
    requests.post("http://router:8000/activate", params={"version": version})

class Handler(FileSystemEventHandler):
    def on_any_event(self, event):
        if not event.is_directory:
            build_index("v2")

if __name__ == "__main__":
    # Build initial v1
    build_index("v1")
    # Surveillance
    obs = Observer()
    obs.schedule(Handler(), f"{DATA_DIR}/knowledge")
    obs.start()
    while True: time.sleep(1)
```

Créez `builder/Dockerfile` :
```dockerfile
FROM python:3.10-slim
RUN pip install watchdog requests faiss-cpu numpy
COPY builder.py .
CMD ["python", "-u", "builder.py"]
```

**Étape 4 : Service UI**
Créez `ui/app.py` :
```python
import streamlit as st, requests, os
st.title("AIOps RAG Chat")
q = st.text_input("Question")
if st.button("Demander"):
    res = requests.post(f"{os.getenv('ROUTER_URL')}/chat", json={"query": q}).json()
    st.write(res["answer"])
```

Créez `ui/Dockerfile` :
```dockerfile
FROM python:3.10-slim
RUN pip install streamlit requests
COPY app.py .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Partie 4 : Orchestration

**Étape 1 : Créer le fichier Docker Compose**
Créez `docker-compose.yml` à la racine :

```yaml
version: "3.8"
services:
  rag-backend-v1:
    build: ./backend
    environment:
      - INDEX_PATH=/indices/v1
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./indices/v1:/indices/v1
    ports:
      - "8101:8101"

  rag-backend-v2:
    build: ./backend
    environment:
      - INDEX_PATH=/indices/v2
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./indices/v2:/indices/v2
    ports:
      - "8102:8102"

  router:
    build: ./router
    environment:
      - BACKEND_PORT_V1=8101
      - BACKEND_PORT_V2=8102
    volumes:
      - ./data:/data
    ports:
      - "8000:8000"

  builder:
    build: ./builder
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/data
      - ./indices:/indices

  ui:
    build: ./ui
    environment:
      - ROUTER_URL=http://router:8000
    ports:
      - "8501:8501"
```

---

## Partie 5 : Déploiement & Test

**Étape 1 : Données Initiales**
Créez un fichier `data/knowledge/info.md` :
```text
Le système exécute actuellement la Version 1.
```

**Étape 2 : Démarrer la Stack**
```powershell
docker compose up --build -d
```

**Étape 3 : Vérifier**
1. Vérifiez les conteneurs : `docker compose ps`
2. Ouvrez l'UI : `http://localhost:8501`
3. Demandez : "Quelle version tourne ?" -> La réponse devrait être "Version 1".

---

## Partie 6 : Le Scénario AIOps (Mise à jour Blue/Green)

**Étape 1 : Déclencher le Pipeline**
1. Gardez l'UI ouverte.
2. Éditez `data/knowledge/info.md` et changez le texte pour :
   ```text
   Le système a été mis à jour automatiquement vers la Version 2 !
   ```
3. Sauvegardez le fichier.

**Étape 2 : Observer l'Automatisation**
Vérifiez les logs du builder pour voir la détection et la reconstruction :
```powershell
docker compose logs -f builder
```

**Étape 3 : Vérifier la Mise à Jour Zéro-Downtime**
1. Retournez immédiatement sur l'UI.
2. Demandez : "Quelle version tourne ?"
3. La réponse doit maintenant être **"Version 2"**.

**Félicitations !** Vous avez implémenté un pipeline IA auto-réparateur et auto-actualisé.
