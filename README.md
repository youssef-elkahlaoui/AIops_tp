# TP AIOps - RAG Pipeline with Blue/Green Deployment

Ce TP vous guide dans la mise en place d'un pipeline AIOps complet pour un système RAG (Retrieval Augmented Generation).
L'objectif est de déployer une application capable de se mettre à jour automatiquement (sans interruption de service) lorsque la base de connaissance change.

## Architecture

*   **Backend (v1 & v2)** : Deux instances FastAPI servies en parallèle.
*   **Router** : Un reverse-proxy intelligent qui dirige le trafic vers la version active (v1 ou v2).
*   **Builder** : Un service "Watchdog" qui surveille le dossier `data/`. Dès qu'un fichier est modifié, il reconstruit l'index vectoriel (FAISS) et demande au routeur de basculer sur la nouvelle version.
*   **UI** : Interface Streamlit pour interagir avec le chatbot.

---

## 🚀 Étape 1 : Configuration Initiale

1.  **Pré-requis** : Docker et Docker Compose installés.
2.  **Configuration** :
    *   Ouvrez le fichier `.env` à la racine.
    *   Insérez votre clé API Gemini : `GEMINI_API_KEY=votre_clé_ici`.
    *   (Optionnel) Vérifiez les URLs si nécessaire.

---

## 🏃 Étape 2 : Lancement de l'Application

Dans un terminal à la racine du projet :

```bash
# Construction des images (peut prendre 1-2 minutes)
docker-compose build

# Démarrage des services en arrière-plan
docker-compose up -d
```

Vérifiez que tout tourne :
```bash
docker-compose ps
```

Vous devriez voir : `rag-backend-v1`, `rag-backend-v2`, `router`, `builder`, `ui`.

---

## 🧪 Étape 3 : Test du Chatbot (Version 1)

1.  Ouvrez votre navigateur sur `http://localhost:8501`.
2.  Posez une question simple basée sur le fichier `data/knowledge/doc1.md` (ex: "What is AIOps?").
3.  Le système doit répondre en utilisant le contexte actuel.

---

## 🔥 Étape 4 : Test du Pipeline AIOps (Mise à jour Automatique)

C'est ici que la magie AIOps opère. Nous allons simuler une mise à jour de la connaissance et vérifier que le système s'adapte automatiquement sans redémarrage manuel.

### 1. Modification des Données
Ouvrez le fichier `data/knowledge/doc1.md` (ou créez-en un nouveau `doc2.md`) et ajoutez une information spécifique.
Par exemple, ajoutez cette phrase à la fin :
> "AIOps also includes automated self-healing capabilities to fix issues without human intervention."

Sauvegardez le fichier.

### 2. Observation du Pipeline
Le service **Builder** va détecter ce changement. Vous pouvez observer les logs pour voir le processus en temps réel :

```bash
docker-compose logs -f builder
```

Vous devriez voir :
*   `Detected change -> rebuilding index...`
*   (Construction du nouvel index...)
*   `Activated v2`

### 3. Vérification (Le "Test")
Retournez sur l'interface UI (`http://localhost:8501`) et posez la question :
> "Does AIOps include self-healing?"

**Résultat attendu** :
*   Le chatbot doit répondre **OUI** et mentionner l'information que vous venez d'ajouter.
*   Cela prouve que le trafic a été basculé instantanément vers la nouvelle version (v2) qui contient le nouvel index.

---

## 🛠 Commandes Utiles

*   Arrêter tout : `docker-compose down`
*   Voir les logs du routeur : `docker-compose logs -f router`
*   Reconstruire si modification du code Python : `docker-compose up -d --build`

---

## Structure du Projet

```
.
├── backend/       # API RAG (FastAPI)
├── builder/       # Service de build & Watchdog
├── data/          # Base de connaissance (.md)
├── indices/       # Stockage des index FAISS (v1/v2)
├── router/        # Reverse-proxy (FastAPI)
├── ui/            # Interface Utilisateur (Streamlit)
└── docker-compose.yml
```
