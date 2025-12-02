# Partie 2 : Pipeline RAG

## Objectif

Mettre en pratique la conteneurisation et l'orchestration d'une application de Génération Augmentée par Récupération (RAG) à l'aide de Docker.

## Pré-requis

- Docker Desktop est installé
- Compte GitHub actif
- Clé API Google Gemini ([À obtenir ici](https://aistudio.google.com/app/apikey))

## Étape 1 : Acquérir le Projet

1. Dupliquer le dépôt sur votre profil GitHub (bouton "Fork" en haut à droite)
2. Récupérer votre duplicata :

```bash
git clone https://github.com/youssef-elkahlaoui/AIops_tp.git
cd AIops_tp
```

3. Définir la clé API :

```bash
cp .env.example .env
```

Modifiez le fichier `.env` pour insérer votre clé :

```
GOOGLE_API_KEY=AIzaSy... (votre clé)
```

## Étape 2 : Conditionnement Docker

Le fichier `Dockerfile` est déjà présent. Examinez son contenu et comprenez la fonction de chaque directive :

| Directive | Fonction |
|-----------|----------|
| `FROM python:3.9-slim` | Base d'image légère |
| `WORKDIR /app` | Répertoire de travail principal |
| `RUN apt-get...` | Dépendances système pour ChromaDB |
| `COPY requirements.txt .` | Transfert des dépendances |
| `RUN pip install...` | Installation des modules Python |
| `COPY . .` | Transfert du code source |
| `EXPOSE 8501` | Exposition du port Streamlit |
| `CMD [...]` | Instruction de démarrage |

## Étape 3 : Gestion avec Docker Compose

Le fichier `docker-compose.yml` est disponible. Démarrer l'application :

```bash
docker-compose up --build
```

> ⏳ Patientez jusqu'à la fin de la construction (cela peut prendre quelques minutes la première fois).

> 🌐 Accédez à l'interface : [http://localhost:8501](http://localhost:8501)

## Étape 4 : Vérification de la Chaîne MLOps

### 4.1 Paramétrage Initial

1. Ouvrez [http://localhost:8501](http://localhost:8501)
2. Dans le volet latéral, entrez votre clé API Google
3. Cliquez sur "Rebuild Vector Store"

### 4.2 Contrôler les 4 Phases de la Chaîne

Vous devriez voir les étapes suivantes s'exécuter :

| Phase | Description | Résultat Attendu |
|-------|-------------|------------------|
| Phase 1 | Ingestion de Données | Fichiers `.txt` et `.md` chargés |
| Phase 2 | Segmentation de Texte | Documents divisés en fragments (chunks) |
| Phase 3 | Création d'Embeddings | Vecteurs générés (384 dimensions) |
| Phase 4 | Sauvegarde Vectorielle | Base de données ChromaDB mise à jour |

### 4.3 Évaluer le Chatbot

Posez les questions suivantes :

- "Quand l'ENSA Al Hoceima a-t-elle été établie ?"
- "Quels sont les clubs étudiants répertoriés ?"
- "What programming languages are taught?"

## Étape 5 : Mise à Jour Instantanée (Hot Reload)

**Objectif** : Confirmer que la chaîne peut intégrer de nouvelles données sans nécessiter une reconstruction de l'image Docker.

### 5.1 Ajout d'un Nouveau Document

Créez le fichier `app/data/DevOps_cours.txt` avec ce contenu :

```
Le cours de DevOps est dispensé le mercredi matin à 9 h.
Le professeur responsable est Dr. Bahri.
```

### 5.2 Constater la Détection Automatique

1. Actualisez la page dans le navigateur
2. Le message "Data folder changes detected!" doit s'afficher
3. La chaîne se relance sans intervention

### 5.3 Interroger la Nouvelle Donnée

- Posez la question : "Quand est prévu le cours de DevOps ?"
    - **Réponse souhaitée** : "Le mercredi matin à 9h"
- Posez la question : "Qui est le professeur responsable du cours de DevOps ?"
    - **Réponse souhaitée** : "Le professeur responsable du cours de DevOps est Dr. Bahri"

---

## 🏃 Plan B : Exécution Locale (Sans Docker)

En cas de difficultés avec Docker :

```bash
# Installation des dépendances
pip install -r requirements.txt

# Démarrage de l'application
python -m streamlit run app/main.py
```
