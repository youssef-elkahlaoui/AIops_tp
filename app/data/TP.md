# TP : Pipeline RAG MLOps & DevOps (Docker, Compose)

## 🎯 Objectif du TP

Ce TP a pour but de vous faire pratiquer la chaîne d'ingénierie pour une application d'IA (MLOps/DevOps). Vous partirez d'une application RAG existante pour l'amener jusqu'à un déploiement orchestré.

## 🏗️ Stack Technique

Ce projet repose sur une stack moderne pour le RAG (Retrieval-Augmented Generation) :

*   **Streamlit** : Framework Python pour créer l'interface utilisateur (UI) interactive et les visualisations.
*   **LangChain** : Orchestrateur qui gère la logique du pipeline RAG (chargement, découpage, chaîne de questions-réponses).
*   **Google Gemini (via API)** : Le "Cerveau". Il est utilisé pour :
    1.  **Embeddings** : Transformer le texte en vecteurs mathématiques.
    2.  **LLM (Génération)** : Générer la réponse finale à l'utilisateur.
*   **ChromaDB** : Base de données vectorielle. Elle stocke les vecteurs générés pour permettre une recherche sémantique ultra-rapide.
*   **Docker** : Pour conteneuriser l'application et garantir qu'elle tourne partout de la même façon.

## 🛠️ Pré-requis

- Compte GitHub.
- Docker Desktop installé.
- Clé API Google Gemini.

## 📝 Étape 1 : Initialisation

1.  **Forkez ce dépôt :**

    - Cliquez sur le bouton **"Fork"** en haut à droite de la page GitHub du projet.
    - Cela créera une copie du projet sur votre propre compte GitHub.

2.  **Clonez votre fork :**

    - Ouvrez votre terminal (Git Bash ou VS Code).
    - Exécutez la commande suivante (remplacez `VOTRE_USERNAME` par votre nom d'utilisateur GitHub) :
      ```bash
      git clone https://github.com/VOTRE_USERNAME/AIops_tp.git
      cd AIops_tp
      ```

3.  **Configuration de la Clé API :**
    - Obtenez votre clé API gratuite sur [Google AI Studio](https://aistudio.google.com/).
    - Dans le dossier du projet, dupliquez le fichier `.env.example` et renommez-le en `.env`.
    - Ouvrez le fichier `.env` et collez votre clé :
      ```env
      GOOGLE_API_KEY=AIzaSyD... (votre clé ici)
      ```
    - _Note : Ce fichier `.env` est ignoré par Git pour la sécurité._

## 🐳 Étape 2 : Conteneurisation (Docker)

Votre mission est de créer un conteneur pour cette application. Créez un fichier nommé `Dockerfile` (sans extension) à la racine du projet.

**Spécifications Techniques du Dockerfile :**

1.  **Image de Base :**

    - Utilisez une image Python légère pour optimiser la taille.
    - _Instruction :_ `FROM python:3.9-slim`

2.  **Dépendances Système (Crucial) :**

    - La base de données vectorielle `chromadb` nécessite des outils de compilation C++.
    - Vous devez installer `build-essential` avant d'installer les paquets Python.
    - _Instruction :_ `RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*`

3.  **Répertoire de Travail :**

    - Définissez le dossier de travail à `/app`.
    - _Instruction :_ `WORKDIR /app`

4.  **Dépendances Python :**

    - Copiez le fichier `requirements.txt` dans le conteneur.
    - Installez les dépendances via `pip`.
    - _Instructions :_
      ```dockerfile
      COPY requirements.txt .
      RUN pip install --no-cache-dir -r requirements.txt
      ```

5.  **Code Source :**

    - Copiez tout le reste du code du projet dans le conteneur.
    - _Instruction :_ `COPY . .`

6.  **Port Réseau :**

    - Streamlit écoute par défaut sur le port 8501.
    - _Instruction :_ `EXPOSE 8501`

7.  **Commande de Démarrage :**
    - Lancez l'application Streamlit et rendez-la accessible depuis l'extérieur du conteneur.
    - _Instruction :_ `CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]`

## 🐙 Étape 3 : Orchestration (Docker Compose)

Lancer des commandes `docker run` à la main est fastidieux.
**Tâche :** Créez un fichier `docker-compose.yml` à la racine.

- Définissez un service nommé `rag-app`.
- Utilisez le `Dockerfile` présent (build context: `.`).
- Mappez le port 8501.
- Chargez automatiquement le fichier `.env`.
- _(Bonus)_ Ajoutez un volume pour que les données dans `app/data` soient persistantes ou modifiables depuis l'hôte.

**Commande attendue pour lancer :**

```bash
docker-compose up --build
```

## 🏃 Option Alternative : Exécution Locale (Sans Docker)
*Si vous avez une connexion internet lente ou des problèmes avec Docker, vous pouvez tester l'application directement sur votre machine.*

1.  **Installation des dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Lancement de l'application :**
    ```bash
    streamlit run app/main.py
    ```

    L'application s'ouvrira automatiquement dans votre navigateur (généralement à l'adresse `http://localhost:8501`).

---

## 🔄 Étape 4 : Simulation MLOps (Mise à jour des données)

L'objectif est de vérifier que votre pipeline MLOps est capable d'ingérer de nouvelles données sans avoir à reconstruire l'image Docker.

**Scénario de Test :**

1.  **Lancement :**

    - Assurez-vous que votre conteneur tourne avec `docker-compose up`.

2.  **Ajout de Données à Chaud :**

    - Créez un nouveau fichier texte sur votre machine hôte dans le dossier `app/data/`.
    - _Exemple :_ Créez `app/data/nouveau_cours.txt` avec le contenu : "Le cours de MLOps est enseigné le Lundi matin."

3.  **Vérification de la Persistance (Volume) :**

    - Allez sur l'interface Streamlit (`http://localhost:8501`).
    - Ouvrez la **Sidebar** (panneau latéral).
    - Vous devriez voir votre nouveau fichier listé (ou cliquez sur "Reset" si nécessaire).
    - _Si vous ne le voyez pas, votre mapping de volume dans docker-compose.yml est incorrect !_

4.  **Exécution du Pipeline :**

    - Cliquez sur le bouton **"Build/Update Vector Store"**.
    - **Résultats Attendus (Logs UI & Terminal) :**
      - **Stage 1 (Ingestion)** : Doit afficher "Found 1 files with extension \*.txt" (ou plus).
      - **Stage 2 (Splitting)** : Doit indiquer le nombre de "Chunks" créés.
      - **Stage 3 (Embedding)** : Doit confirmer l'initialisation du modèle `embedding-001`.
      - **Stage 4 (Storage)** : Doit afficher "✅ ChromaDB updated successfully".

5.  **Test Chatbot :**
    - Posez la question : "Quand est le cours de MLOps ?"
    - Le bot doit répondre "Lundi matin" (preuve que la nouvelle donnée a été ingérée).

## 📦 Livrables

- Lien vers votre dépôt GitHub avec :
  - `Dockerfile`
  - `docker-compose.yml`
- Une capture d'écran de l'interface `st.status` montrant les 4 étapes du pipeline MLOps validées.
