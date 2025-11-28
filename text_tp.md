# TP AIOps : Pipeline RAG Continu avec Déploiement Blue/Green

**Durée :** 1h30
**Niveau :** Avancé
**Objectif :** Implémenter une architecture AIOps résiliente capable de mettre à jour sa base de connaissance en temps réel sans interruption de service (Zero Downtime).

---

## 1. Introduction et Architecture

Dans ce TP, nous n'allons pas simplement créer un chatbot. Nous allons créer un **système vivant**.
L'objectif est de résoudre un problème classique en production : **Comment mettre à jour les données d'une IA sans éteindre le serveur ?**

Nous utiliserons une architecture **Blue/Green** locale orchestrée par Docker :

*   **📂 Data Layer** : Un dossier partagé contenant vos fichiers de connaissances (`.md`).
*   **👀 Builder (Watchdog)** : Un service autonome qui surveille ce dossier. Dès qu'un fichier est modifié, il :
    1.  Reconstruit l'index vectoriel (FAISS) avec les embeddings Gemini.
    2.  Sauvegarde le nouvel index dans un dossier versionné (ex: `v2`).
    3.  Appelle le **Router** pour basculer le trafic.
*   **🔀 Router** : Un reverse-proxy intelligent. Il sait quelle version (v1 ou v2) est active et redirige le trafic utilisateur vers le bon backend.
*   **🧠 Backend (v1 & v2)** : Deux conteneurs identiques qui tournent en parallèle. Ils chargent l'index qu'on leur assigne.
*   **💻 UI** : Une interface simple (Streamlit) pour tester le chat.

---

## 2. Préparation de l'environnement

### Structure du projet
Créez l'arborescence suivante :

```
aiops-tp/
├── .env                # Vos secrets (API Key)
├── docker-compose.yml  # Orchestration
├── data/
│   └── knowledge/      # Vos fichiers .md
├── backend/            # API RAG (FastAPI)
├── builder/            # Service de build auto
├── router/             # Load balancer intelligent
└── ui/                 # Interface utilisateur
```

### Configuration (.env)
Créez un fichier `.env` à la racine :

```ini
GEMINI_API_KEY=votre_cle_gemini_ici
GEMINI_EMBED_URL=https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent
GEMINI_CHAT_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
ROUTER_PORT=8000
BACKEND_PORT_V1=8101
BACKEND_PORT_V2=8102
DATA_DIR=/data
INDICES_DIR=/data/indices
```

---

## 3. Implémentation des Services

### A. Le Backend RAG (`backend/`)
C'est le cerveau. Il reçoit une question, cherche dans son index FAISS local, et demande à Gemini de répondre.
*   **Fichier clé** : `app.py`
*   Il doit charger l'index situé dans `INDEX_PATH` au démarrage.

### B. Le Router (`router/`)
C'est l'aiguilleur du ciel.
*   **Fichier clé** : `router.py`
*   Il lit un fichier partagé `active_version` (qui contient "v1" ou "v2").
*   Si "v1" est actif, il redirige vers le conteneur `rag-backend-v1`.
*   Il expose un endpoint `/activate?version=v2` que le Builder appellera.

### C. Le Builder / Watchdog (`builder/`)
C'est l'ouvrier automatisé.
*   **Fichier clé** : `builder.py`
*   Utilise la librairie `watchdog` pour écouter les événements fichiers sur `/data/knowledge`.
*   Au moindre changement :
    1.  Il lit tous les fichiers.
    2.  Il génère les embeddings via l'API Gemini.
    3.  Il écrit l'index FAISS dans le dossier de la version inactive (ex: `indices/v2`).
    4.  Il appelle `POST http://router:8000/activate` pour basculer le trafic.

### D. L'Interface UI (`ui/`)
Simple client Streamlit.
*   Appelle uniquement le Router. Elle ne sait pas qu'il y a deux backends derrière.

---

## 4. Orchestration (Docker Compose)

Le fichier `docker-compose.yml` lie tout ensemble.
Points d'attention :
*   Les volumes partagés : `router`, `builder` et `backend` doivent tous voir `/data` et `/indices`.
*   Les variables d'environnement : Chaque backend doit savoir s'il est v1 ou v2 (via `INDEX_PATH`).

---

## 5. Déroulement du TP (Scénario de Test)

### Étape 1 : Démarrage
Lancez la stack :
```bash
docker-compose up --build -d
```
Vérifiez que les 5 conteneurs sont "Up" (`docker-compose ps`).

### Étape 2 : Initialisation des données
Ajoutez un premier fichier de connaissance dans `data/knowledge/intro.md` :
```markdown
# AIOps
AIOps stands for Artificial Intelligence for IT Operations.
```
*Observez les logs du builder* : il doit détecter le fichier et construire l'index v1.

### Étape 3 : Premier Test
Allez sur `http://localhost:8501`.
Demandez : "What is AIOps?".
Le système doit répondre avec la définition ci-dessus.

### Étape 4 : La Mise à Jour "AIOps" (Le cœur du sujet)
C'est le moment de vérité. Nous allons simuler une mise à jour de prod.

1.  **Sans arrêter les conteneurs**, modifiez le fichier `data/knowledge/intro.md` (ou créez-en un nouveau).
2.  Ajoutez une information cruciale, par exemple :
    > "IMPORTANT: The support hotline for AIOps is 555-0199."
3.  Sauvegardez le fichier.

### Étape 5 : Vérification Automatique
Regardez immédiatement les logs du builder :
```bash
docker-compose logs -f builder
```
Vous devriez voir :
> Detected change -> rebuilding index...
> Activated v2

Retournez sur l'UI et posez la question : "What is the support hotline?".
**Si le système vous répond "555-0199", vous avez réussi.**
Vous avez mis à jour la connaissance d'une IA en production sans aucune interruption de service.

---

## 6. Pour aller plus loin (Bonus)
*   Ajouter un endpoint `/health` au Router qui vérifie la santé du backend actif.
*   Ajouter Prometheus pour monitorer le temps de réponse des embeddings.
