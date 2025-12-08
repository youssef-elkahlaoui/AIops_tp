# Partie 2 : Pipeline RAG

## Objectif

Mettre en pratique la conteneurisation et l'orchestration d'une application de Génération Augmentée par Récupération (RAG) à l'aide de Docker. Ce TP vous permettra de comprendre comment déployer une application d'intelligence artificielle moderne en utilisant les meilleures pratiques DevOps.

### Structure des dossiers et fichiers

```
AIops-RAG/
├── app/
│   ├── main.py                      # Point d'entrée principal de l'application
│   ├── data/                        # Dossier des documents sources
│   │   ├── DevOps_cours.txt         # Informations sur le cours DevOps
│   │   ├── ensa_about.txt           # Description de l'ENSA
│   │   ├── ensa_programs.md         # Programmes d'études (format Markdown)
│   │   └── student_life.txt         # Vie étudiante et activités
│   ├── chroma_db/                   # Base de données vectorielle (générée)
│   │   ├── chroma.sqlite3           # Stockage SQLite des métadonnées
│   │   └── index/                   # Index de recherche vectorielle
│   └── utils/                       # Modules utilitaires
│       ├── chat_interface.py        # Interface utilisateur Streamlit
│       ├── embeddings.py            # Gestion des embeddings (vecteurs)
│       └── rag_pipeline.py          # Logique du pipeline RAG
├── docker-compose.yml               # Configuration d'orchestration Docker
├── Dockerfile                       # Instructions de construction de l'image
├── requirements.txt                 # Dépendances Python
├── .env.example                     # Modèle de fichier d'environnement
├── .env                             # Variables d'environnement (clé API)
└── TP.md                            # Documentation du TP
```

## Qu'est-ce que le RAG ?

**RAG (Retrieval-Augmented Generation)** est une technique d'IA qui combine :

- **Récupération** : Recherche d'informations pertinentes dans une base de données
- **Génération** : Utilisation d'un modèle de langage (LLM) pour créer des réponses contextuelles

**Avantages du RAG** :

- Réduit les hallucinations du modèle
- Permet de travailler avec des données privées/spécifiques
- Plus économique que le fine-tuning complet
- Facilite la mise à jour des connaissances

## Pré-requis

- **Docker Desktop** installé ([Télécharger](https://www.docker.com/products/docker-desktop))
  - _Pourquoi ?_ Permet de créer des environnements isolés et reproductibles
- **Clé API Google Gemini** ([À obtenir ici](https://aistudio.google.com/app/apikey))
  - _Pourquoi ?_ Accéder au modèle de langage Gemini pour la génération de texte

## Étape 1 : Acquérir le Projet

### 1.1 Fork du dépôt GitHub

**Action** : Dupliquer le dépôt sur votre profil GitHub

1. Rendez-vous sur le dépôt original
2. Cliquez sur le bouton "Fork" en haut à droite
3. Sélectionnez votre compte GitHub comme destination

**Pourquoi forker ?**

- Vous obtenez votre propre copie du projet
- Vous pouvez modifier sans affecter l'original
- Facilite la contribution et le suivi de vos modifications

### 1.2 Cloner le dépôt localement

**Outil utilisé** : Git (système de contrôle de version)

```bash
git clone https://github.com/youssef-elkahlaoui/AIops_tp.git
cd AIops_tp
```

**Explication des commandes** :

- `git clone` : Télécharge l'intégralité du dépôt sur votre machine
- `cd AIops_tp` : Se déplace dans le répertoire du projet

**Qu'est-ce qui est téléchargé ?**

- Le code source de l'application
- Les fichiers de configuration Docker
- Les données d'exemple
- L'historique Git complet

### 1.3 Configuration de la clé API

**Étape 1** : Créer le fichier d'environnement

```bash
cp .env.example .env
```

**Pourquoi utiliser un fichier .env ?**

- Sépare les secrets du code source
- Évite d'exposer les clés API dans Git
- Facilite la configuration pour différents environnements (dev, prod)

**Étape 2** : Insérer votre clé API

Ouvrez le fichier `.env` et modifiez-le :

```
GOOGLE_API_KEY=AIzaSy... (votre clé obtenue depuis Google AI Studio)
```

**Sécurité** :

- ⚠️ Ne commitez JAMAIS le fichier `.env` dans Git
- Le fichier `.gitignore` doit contenir `.env` pour éviter cela
- Utilisez des variables d'environnement en production

## Étape 2 : Conditionnement Docker

### 2.1 Qu'est-ce que Docker ?

**Docker** est une plateforme de conteneurisation qui permet de :

- Empaqueter une application avec toutes ses dépendances
- Garantir un fonctionnement identique sur tous les environnements
- Isoler l'application du système hôte

**Concepts clés** :

- **Image Docker** : Modèle immuable contenant l'application et ses dépendances
- **Conteneur** : Instance en cours d'exécution d'une image
- **Dockerfile** : Fichier de recette pour construire une image

### 2.2 Analyse du Dockerfile

Le fichier `Dockerfile` est déjà présent dans le projet. Examinez son contenu ligne par ligne :

| Directive                                                             | Fonction                  | Explication détaillée                                                                                  |
| --------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------ |
| `FROM python:3.9-slim`                                                | Image de base             | Utilise Python 3.9 dans une version légère (sans paquets inutiles), réduit la taille de l'image finale |
| `WORKDIR /app`                                                        | Répertoire de travail     | Définit `/app` comme dossier principal où toutes les commandes seront exécutées                        |
| `RUN apt-get update && apt-get install -y build-essential`            | Dépendances système       | Installe les outils de compilation nécessaires pour ChromaDB (gcc, g++, make)                          |
| `COPY requirements.txt .`                                             | Transfert des dépendances | Copie uniquement le fichier de dépendances en premier (optimise le cache Docker)                       |
| `RUN pip install --no-cache-dir -r requirements.txt`                  | Installation Python       | Installe tous les packages Python nécessaires sans garder le cache (réduit la taille)                  |
| `COPY . .`                                                            | Transfert du code source  | Copie tout le code de l'application dans le conteneur                                                  |
| `EXPOSE 8501`                                                         | Exposition du port        | Indique que Streamlit écoute sur le port 8501 (documentation, pas de sécurité réelle)                  |
| `CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]` | Commande de démarrage     | Lance l'application Streamlit au démarrage du conteneur                                                |

### 2.3 Pourquoi cet ordre spécifique ?

**Optimisation du cache Docker** :

1. Les couches qui changent rarement (image de base, dépendances système) sont en premier
2. `requirements.txt` est copié avant le code source
3. Le code source (qui change fréquemment) est copié en dernier

**Avantage** : Si vous modifiez seulement le code, Docker réutilise les couches précédentes (gain de temps considérable)

### 2.4 Construction manuelle (optionnelle)

Pour comprendre le processus, vous pouvez construire l'image manuellement :

```bash
docker build -t rag-app:latest .
```

**Explication** :

- `docker build` : Commande de construction d'image
- `-t rag-app:latest` : Nomme l'image "rag-app" avec le tag "latest"
- `.` : Utilise le Dockerfile du répertoire courant

**Processus de construction** :

1. Docker lit le Dockerfile
2. Exécute chaque instruction dans l'ordre
3. Crée une couche intermédiaire pour chaque instruction
4. Produit l'image finale

## Étape 3 : Gestion avec Docker Compose

### 3.1 Qu'est-ce que Docker Compose ?

**Docker Compose** est un outil d'orchestration qui permet de :

- Définir des applications multi-conteneurs
- Gérer les configurations via un fichier YAML
- Démarrer tous les services avec une seule commande
- Gérer les réseaux et volumes automatiquement

**Pourquoi utiliser Docker Compose ?**

- Simplifie la gestion des conteneurs
- Configuration reproductible
- Idéal pour les environnements de développement
- Facilite la collaboration en équipe

### 3.2 Analyse du docker-compose.yml

Le fichier `docker-compose.yml` contient la configuration complète de l'application. Éléments typiques :

```yaml
version: "3.8" # Version du format Compose
services:
  rag-app: # Nom du service
    build: . # Construit depuis le Dockerfile local
    ports:
      - "8501:8501" # Mappe le port hôte:conteneur
    volumes:
      - ./app:/app/app # Monte le code pour hot-reload
    env_file:
      - .env # Charge les variables d'environnement
    restart: unless-stopped # Redémarre automatiquement en cas d'erreur
```

**Explication des paramètres** :

- **build** : Indique où trouver le Dockerfile
- **ports** : Permet d'accéder à l'application depuis l'hôte
- **volumes** : Synchronise les fichiers entre hôte et conteneur (permet les modifications à chaud)
- **env_file** : Charge les variables d'environnement depuis `.env`
- **restart** : Politique de redémarrage automatique

### 3.3 Démarrage de l'application

**Commande principale** :

```bash
docker-compose up --build
```

**Décomposition de la commande** :

- `docker-compose up` : Lance tous les services définis
- `--build` : Force la reconstruction des images (utile après modification du code)

**Processus détaillé** :

1. **Lecture du docker-compose.yml** : Docker Compose analyse la configuration
2. **Construction de l'image** : Exécute le Dockerfile
   - Téléchargement de l'image Python de base (~50 MB)
   - Installation des dépendances système (~100 MB)
   - Installation des packages Python (~200 MB)
   - Durée totale : 3-5 minutes la première fois
3. **Création du réseau** : Réseau Docker isolé pour le projet
4. **Montage des volumes** : Synchronisation des dossiers
5. **Démarrage du conteneur** : Lance Streamlit
6. **Affichage des logs** : Montre la sortie en temps réel

**Indicateurs de réussite** :

```
✓ Network aiops-rag_default  Created
✓ Container aiops-rag-app    Started
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### 3.4 Accès à l'interface

**URL** : [http://localhost:8501](http://localhost:8501)

**Que se passe-t-il ?**

1. Votre navigateur envoie une requête au port 8501
2. Docker redirige vers le conteneur
3. Streamlit traite la requête et renvoie l'interface web

**Vérifications** :

- ✓ La page se charge correctement
- ✓ L'interface Streamlit s'affiche
- ✓ Le panneau latéral est visible

### 3.5 Commandes Docker Compose utiles

| Commande                           | Action                              | Quand l'utiliser                      |
| ---------------------------------- | ----------------------------------- | ------------------------------------- |
| `docker-compose up -d`             | Lance en arrière-plan               | Pour continuer à utiliser le terminal |
| `docker-compose down`              | Arrête et supprime les conteneurs   | Pour nettoyer l'environnement         |
| `docker-compose logs -f`           | Affiche les logs en temps réel      | Pour déboguer                         |
| `docker-compose restart`           | Redémarre les services              | Après modification de .env            |
| `docker-compose exec rag-app bash` | Ouvre un terminal dans le conteneur | Pour explorer l'intérieur             |

**Arrêt de l'application** :

- Méthode 1 : `Ctrl + C` dans le terminal
- Méthode 2 : `docker-compose down` dans un autre terminal

## Étape 4 : Vérification de la Chaîne MLOps

### 4.1 Qu'est-ce qu'un pipeline MLOps ?

**MLOps** (Machine Learning Operations) applique les principes DevOps au machine learning :

- Automatisation du flux de données
- Reproductibilité des résultats
- Déploiement continu des modèles
- Monitoring et maintenance

**Notre pipeline RAG** comporte 4 phases essentielles qui transforment des documents bruts en un système de question-réponse intelligent.

### 4.2 Paramétrage Initial

**Actions à effectuer** :

1. **Ouvrir l'interface** : [http://localhost:8501](http://localhost:8501)

2. **Localiser le panneau latéral** (sidebar à gauche)

   - Si masqué, cliquez sur la flèche en haut à gauche

3. **Entrer la clé API Google**
   - Collez votre clé dans le champ prévu
   - Format : `AIzaSy...` (environ 39 caractères)
4. **Lancer la construction** : Cliquez sur "Rebuild Vector Store"

**Pourquoi ce bouton ?**

- Initialise la base de données vectorielle
- Traite tous les documents du dossier `app/data/`
- Crée les embeddings nécessaires pour la recherche sémantique

### 4.3 Phase 1 : Ingestion de Données

**Objectif** : Charger les documents sources dans le système

**Outil utilisé** : `LangChain Document Loaders`

- `TextLoader` pour les fichiers `.txt`
- `UnstructuredMarkdownLoader` pour les fichiers `.md`

**Processus détaillé** :

1. **Scan du dossier** : Le système parcourt `app/data/`
2. **Détection des fichiers** : Identifie les formats supportés
3. **Lecture du contenu** : Charge chaque fichier en mémoire
4. **Création de documents** : Chaque fichier devient un objet Document avec :
   - `page_content` : Le texte du fichier
   - `metadata` : Nom du fichier, chemin, type

**Fichiers traités** :

- ✓ `DevOps_cours.txt` : Informations sur le cours DevOps
- ✓ `ensa_about.txt` : Description de l'ENSA
- ✓ `ensa_programs.md` : Liste des programmes d'études
- ✓ `student_life.txt` : Vie étudiante et activités

**Résultat attendu** :

```
Loaded 4 documents from app/data/
Total characters: ~5000
```

**Points de vigilance** :

- Les fichiers doivent être en UTF-8
- Les noms de fichiers sans caractères spéciaux
- Taille maximale recommandée : 5 MB par fichier

### 4.4 Phase 2 : Segmentation de Texte (Chunking)

**Objectif** : Diviser les documents en fragments gérables

**Outil utilisé** : `RecursiveCharacterTextSplitter` de LangChain

**Pourquoi segmenter ?**

- Les modèles ont des limites de tokens
- Améliore la précision de la recherche
- Réduit le coût des API (moins de tokens traités)
- Permet de retrouver des passages spécifiques

**Paramètres de segmentation** :

```python
chunk_size=1000        # Taille maximale d'un fragment (en caractères)
chunk_overlap=200      # Chevauchement entre fragments
```

**Pourquoi le chevauchement ?**

- Évite de couper des informations importantes
- Maintient le contexte entre les chunks
- Améliore la qualité des réponses

**Processus** :

1. **Découpage intelligent** :

   - Tente de couper aux sauts de paragraphe
   - Sinon aux points
   - Sinon aux virgules
   - En dernier recours : coupe au caractère

2. **Préservation du contexte** :
   - Les 200 derniers caractères d'un chunk apparaissent dans le suivant
   - Les métadonnées sont conservées

**Résultat attendu** :

```
Split into 45 chunks
Average chunk size: 850 characters
```

**Exemple de chunk** :

```
Chunk 1: "L'ENSA Al Hoceima a été établie en 2008..."
Chunk 2: "...établie en 2008. Elle offre plusieurs programmes..."
```

### 4.5 Phase 3 : Création d'Embeddings

**Objectif** : Transformer le texte en vecteurs numériques

**Qu'est-ce qu'un embedding ?**

- Représentation mathématique du sens d'un texte
- Vecteur de nombres (ex: [0.23, -0.45, 0.67, ...])
- Les textes similaires ont des vecteurs proches

**Outil utilisé** : `SentenceTransformers` avec le modèle `all-MiniLM-L6-v2`

**Caractéristiques du modèle** :

- **Dimensions** : 384 (taille du vecteur)
- **Langue** : Multilingue (français, anglais, arabe)
- **Taille** : ~80 MB
- **Performance** : Excellent rapport qualité/vitesse

**Processus** :

1. **Chargement du modèle** : Téléchargé depuis Hugging Face (première fois uniquement)
2. **Encodage des chunks** :
   - Chaque chunk est transformé en vecteur de 384 dimensions
   - Traitement par batch pour optimiser la vitesse
3. **Normalisation** : Les vecteurs sont normalisés pour la recherche par similarité cosinus

**Exemple simplifié** :

```
Texte: "L'ENSA offre des formations en génie informatique"
→ Embedding: [0.234, -0.456, 0.678, ..., 0.123]  (384 valeurs)
```

**Pourquoi ce modèle ?**

- ✓ Rapide (environ 1000 chunks/seconde)
- ✓ Fonctionne sans connexion internet après téléchargement
- ✓ Gratuit et open-source
- ✓ Bonne qualité pour le français

**Résultat attendu** :

```
Generated 45 embeddings
Dimensions: 384
Model: all-MiniLM-L6-v2
```

### 4.6 Phase 4 : Sauvegarde Vectorielle

**Objectif** : Stocker les embeddings dans une base de données optimisée

**Outil utilisé** : ChromaDB

**Qu'est-ce que ChromaDB ?**

- Base de données vectorielle open-source
- Optimisée pour la recherche de similarité
- Persistance sur disque
- Interface Python simple

**Processus de stockage** :

1. **Initialisation de ChromaDB** :

   - Création du dossier `app/chroma_db/` si inexistant
   - Configuration de la collection "rag_collection"

2. **Insertion des données** :

   - Chaque chunk est stocké avec :
     - Son embedding (vecteur)
     - Son contenu textuel
     - Ses métadonnées (source, page, etc.)
     - Un ID unique

3. **Création d'index** :
   - ChromaDB construit des index HNSW (Hierarchical Navigable Small World)
   - Permet des recherches ultra-rapides (millisecondes)

**Structure de stockage** :

```
chroma_db/
├── chroma.sqlite3        # Base de données SQLite
├── index/                # Index de recherche
└── metadata/             # Métadonnées
```

**Avantages de ChromaDB** :

- ✓ Recherche rapide même avec des millions de vecteurs
- ✓ Persistance locale (pas besoin de serveur)
- ✓ Mise à jour incrémentale (ajouter sans tout recréer)
- ✓ Gratuit et sans limites

**Résultat attendu** :

```
💾 Vector store saved
Location: app/chroma_db/
Total documents: 45
Status: Ready for queries
```

### 4.7 Récapitulatif du pipeline complet

**Flux de données** :

```
📄 Documents (.txt, .md)
    ↓ Phase 1: Ingestion
📚 Documents chargés en mémoire
    ↓ Phase 2: Chunking
✂️ Fragments de texte (1000 chars)
    ↓ Phase 3: Embeddings
🔢 Vecteurs numériques (384 dimensions)
    ↓ Phase 4: Stockage
💾 ChromaDB (recherche vectorielle)
    ↓ Utilisation
💬 Chatbot RAG opérationnel
```

**Temps d'exécution typique** :

- Phase 1 : < 1 seconde
- Phase 2 : < 1 seconde
- Phase 3 : 5-10 secondes (selon nombre de chunks)
- Phase 4 : 2-3 secondes
- **Total** : ~15 secondes pour le jeu de données fourni

### 4.8 Évaluer le Chatbot

**Objectif** : Tester la qualité du système RAG avec des questions variées

**Comment fonctionne une requête ?**

1. **Saisie de la question** : L'utilisateur tape dans le chat
2. **Embedding de la question** : Transformation en vecteur (384D)
3. **Recherche vectorielle** : ChromaDB trouve les chunks les plus similaires
4. **Sélection du contexte** : Les 3 meilleurs chunks sont récupérés
5. **Construction du prompt** : Combinaison du contexte + question
6. **Appel à Gemini** : Le LLM génère la réponse
7. **Affichage** : La réponse apparaît dans l'interface

**Tests à effectuer** :

#### Test 1 : Question factuelle simple

**Question** : "Quand l'ENSA Al Hoceima a-t-elle été établie ?"

**Réponse attendue** : "L'ENSA Al Hoceima a été établie en 2008."

**Ce test valide** :

- ✓ La recherche vectorielle fonctionne
- ✓ Le chunk contenant la date est bien retrouvé
- ✓ Gemini extrait correctement l'information

#### Test 2 : Question nécessitant agrégation

**Question** : "Quels sont les clubs étudiants répertoriés ?"

**Réponse attendue** : Une liste des clubs mentionnés dans `student_life.txt`

**Ce test valide** :

- ✓ Capacité à retrouver plusieurs informations
- ✓ Structuration de la réponse (liste)
- ✓ Exhaustivité de la recherche

#### Test 3 : Question en anglais

**Question** : "What programming languages are taught?"

**Réponse attendue** : Liste des langages de programmation du cursus

**Ce test valide** :

- ✓ Support multilingue du modèle d'embeddings
- ✓ Capacité de Gemini à répondre en anglais
- ✓ Recherche cross-lingue (question EN, docs FR)

**Analyse de la qualité** :

**Bon indicateurs** :

- ✅ Réponse précise et concise
- ✅ Information directement extraite des documents
- ✅ Pas d'invention d'informations (hallucination)
- ✅ Citation implicite de la source

**Mauvais indicateurs** :

- ❌ Réponse générique ("Je ne sais pas")
- ❌ Information inventée non présente dans les docs
- ❌ Réponse hors sujet
- ❌ Mélange de sources contradictoires

**Comprendre les limites** :

Si le chatbot répond "Je n'ai pas cette information" :

1. **Vérifiez** que le document contient bien l'info
2. **Reformulez** la question différemment
3. **Chunking** : L'info est peut-être coupée entre 2 chunks

**Panel de test avancé** :

| Type de question | Exemple                                | Difficulté     |
| ---------------- | -------------------------------------- | -------------- |
| Factuelle        | "Quelle est la date de fondation ?"    | Facile         |
| Agrégation       | "Liste tous les programmes"            | Moyenne        |
| Comparaison      | "Quelle est la différence entre ..."   | Difficile      |
| Temporelle       | "Quand se déroule le cours X ?"        | Facile         |
| Négation         | "Quels clubs ne sont pas mentionnés ?" | Très difficile |

## Étape 5 : Mise à Jour Instantanée (Hot Reload)

### 5.1 Qu'est-ce que le Hot Reload ?

**Hot Reload** (rechargement à chaud) est une fonctionnalité DevOps qui permet :

- Mise à jour de l'application sans redémarrage complet
- Synchronisation automatique des fichiers modifiés
- Gain de temps considérable en développement

**Comment ça fonctionne ici ?**

1. Docker monte le dossier `app/` local dans le conteneur
2. Streamlit détecte les changements de fichiers
3. Le système recharge automatiquement les données

**Pourquoi c'est important ?**

- Itération rapide sur les données
- Pas besoin de `docker-compose down/up`
- La base vectorielle se met à jour automatiquement
- Environnement de développement agile

### 5.2 Objectif de ce test

**Démontrer** que la chaîne MLOps peut intégrer de nouvelles données sans nécessiter :

- Reconstruction de l'image Docker
- Redémarrage du conteneur
- Intervention manuelle complexe

**Scénario réel** : Un professeur ajoute des informations de dernière minute

### 5.3 Ajout d'un Nouveau Document

**Étape 1** : Créer le fichier `app/data/DevOps_cours.txt`

**Emplacement** : `c:\Users\jozef\OneDrive\Desktop\AIops-RAG\app\data\DevOps_cours.txt`

**Méthode 1 - Via l'éditeur** :

1. Ouvrir VS Code
2. Naviguer vers `app/data/`
3. Créer un nouveau fichier : `DevOps_cours.txt`
4. Coller le contenu ci-dessous
5. Sauvegarder (`Ctrl+S`)

**Méthode 2 - Via PowerShell** :

```powershell
cd app\data
New-Item -Path "DevOps_cours.txt" -ItemType File
notepad DevOps_cours.txt
```

**Contenu à insérer** :

```
Le cours de DevOps est dispensé le mercredi matin à 9 h.
Le professeur responsable est Dr. Bahri.
Les étudiants apprennent Docker, Kubernetes et CI/CD.
Le TP pratique couvre la conteneurisation d'applications.
```

**Pourquoi ce contenu ?**

- Information factuelle simple (date, heure)
- Nom propre spécifique (Dr. Bahri)
- Termes techniques (Docker, Kubernetes)
- Facilement vérifiable dans les réponses

### 5.4 Constater la Détection Automatique

**Mécanisme de surveillance** :

Le système utilise un **watchdog** (chien de garde) qui :

1. **Surveille** le dossier `app/data/` en permanence
2. **Calcule** un hash (empreinte numérique) du contenu
3. **Compare** avec le hash précédent
4. **Déclenche** le rebuild si différence détectée

**Processus automatique** :

```
📁 Fichier ajouté/modifié
    ↓
🔍 Détection du changement (hash différent)
    ↓
⚠️ Alerte "Data folder changes detected!"
    ↓
🔄 Rebuild automatique du vector store
    ↓
✅ Système à jour
```

**Indicateurs visuels** :

1. **Actualisez** la page dans le navigateur (`F5`)

2. **Message attendu** dans le panneau latéral :

   ```
   ⚠️ Data folder changes detected!
   The vector store needs to be rebuilt.
   ```

3. **Bouton activé** : "Rebuild Vector Store" devient cliquable

4. **Cliquez** sur le bouton pour lancer le rebuild

5. **Progression** : Les 4 phases se relancent
   - ✓ Phase 1 : Détection de 5 documents (au lieu de 4)
   - ✓ Phase 2 : Nouveau nombre de chunks
   - ✓ Phase 3 : Embeddings recalculés
   - ✓ Phase 4 : ChromaDB mis à jour

**Temps de rebuild** : 10-20 secondes

**Optimisation possible** :

- Version avancée : Ne traiter que les nouveaux fichiers (delta update)
- Version actuelle : Rebuild complet (plus simple, plus fiable)

### 5.5 Vérification technique (optionnelle)

**Inspecter les logs Docker** :

```powershell
docker-compose logs -f rag-app
```

**Messages attendus** :

```
[INFO] File watcher detected changes
[INFO] Starting vector store rebuild...
[INFO] Loaded 5 documents (1 new)
[INFO] Generated 52 chunks
[INFO] Vector store updated successfully
```

### 5.6 Interroger la Nouvelle Donnée

**Test 1 : Question temporelle**

**Question** : "Quand est prévu le cours de DevOps ?"

**Réponse attendue** : "Le cours de DevOps est prévu le mercredi matin à 9h."

**Validation** :

- ✅ Le système a bien indexé le nouveau fichier
- ✅ La recherche vectorielle fonctionne sur les nouvelles données
- ✅ L'information temporelle est correctement extraite

**Analyse** : Si la réponse est incorrecte ou absente :

1. Vérifiez que le fichier est bien dans `app/data/`
2. Confirmez que le rebuild a été effectué
3. Regardez les logs pour d'éventuelles erreurs

**Test 2 : Question sur personne**

**Question** : "Qui est le professeur responsable du cours de DevOps ?"

**Réponse attendue** : "Le professeur responsable du cours de DevOps est Dr. Bahri."

**Validation** :

- ✅ Extraction de nom propre fonctionnelle
- ✅ Association correcte (cours ↔ professeur)
- ✅ Formulation naturelle de la réponse

**Test 3 : Question technique**

**Question** : "Quelles technologies sont enseignées dans le cours de DevOps ?"

**Réponse attendue** : "Docker, Kubernetes et CI/CD"

**Validation** :

- ✅ Énumération correcte
- ✅ Pas d'ajout d'informations non présentes
- ✅ Formatage lisible

### 5.7 Comprendre l'avantage du volume Docker

**Sans volume Docker** :

```yaml
# Mauvaise pratique
services:
  rag-app:
    build: .
    # Pas de volume
```

- ❌ Modifications de code non prises en compte
- ❌ Nécessite `docker-compose up --build` à chaque fois
- ❌ Perte de temps (3-5 minutes par rebuild)

**Avec volume Docker** (configuration actuelle) :

```yaml
# Bonne pratique
services:
  rag-app:
    build: .
    volumes:
      - ./app:/app/app # Synchronisation bidirectionnelle
```

- ✅ Modifications instantanées
- ✅ Workflow de développement fluide
- ✅ Rebuild uniquement si changement de dépendances

**Cas d'usage réels** :

- **Développement** : Itération rapide sur les données/code
- **Démo** : Ajout de données devant le client
- **Production** : ⚠️ À désactiver (stabilité requise)

### 5.8 Expérimentations suggérées

**Exercice 1** : Modifier un fichier existant

1. Éditez `app/data/ensa_about.txt`
2. Ajoutez une phrase
3. Observez la détection automatique
4. Posez une question sur la nouvelle info

**Exercice 2** : Supprimer un document

1. Supprimez `app/data/student_life.txt`
2. Rebuild le vector store
3. Tentez une question sur les clubs
4. Résultat : "Information non disponible"

**Exercice 3** : Format Markdown

1. Créez `app/data/horaires.md`
2. Utilisez la syntaxe Markdown (titres, listes)
3. Vérifiez que le système traite correctement le formatage

**Limites à connaître** :

- Formats supportés : `.txt`, `.md` uniquement
- Encodage : UTF-8 obligatoire
- Taille : Éviter les fichiers > 5 MB
- Noms : Pas de caractères spéciaux (é, à, ç, espaces)

---

## 🎯 Récapitulatif et Concepts Clés

### Technologies et leur rôle

| Technologie              | Rôle                | Alternatives possibles            |
| ------------------------ | ------------------- | --------------------------------- |
| **Docker**               | Conteneurisation    | Podman, LXC                       |
| **Docker Compose**       | Orchestration       | Kubernetes (pour production)      |
| **Python 3.9**           | Langage principal   | Python 3.10+, 3.11                |
| **Streamlit**            | Framework web       | Gradio, Flask, FastAPI            |
| **LangChain**            | Framework RAG       | LlamaIndex, Haystack              |
| **ChromaDB**             | Base vectorielle    | Pinecone, Weaviate, Milvus, FAISS |
| **SentenceTransformers** | Modèle d'embeddings | OpenAI Ada-002, Cohere            |
| **Google Gemini**        | LLM génératif       | GPT-4, Claude, Llama              |

### Concepts DevOps appliqués

1. **Infrastructure as Code** : `Dockerfile` + `docker-compose.yml`
2. **Immutabilité** : Conteneurs identiques sur tous les environnements
3. **Isolation** : Application séparée du système hôte
4. **Reproductibilité** : Build identique partout
5. **Hot Reload** : Développement itératif rapide
6. **Surveillance** : Détection automatique des changements
7. **Logs centralisés** : `docker-compose logs`

### Flux d'une requête utilisateur

```
1. 💬 Utilisateur : "Quand l'ENSA a-t-elle été créée ?"
           ↓
2. 🔢 Embedding : [0.23, -0.45, 0.67, ...] (384D)
           ↓
3. 🔍 ChromaDB : Recherche par similarité cosinus
           ↓
4. 📄 Top 3 chunks :
   - "L'ENSA Al Hoceima établie en 2008..." (score: 0.92)
   - "Histoire de l'établissement..." (score: 0.87)
   - "Création et développement..." (score: 0.81)
           ↓
5. 📝 Construction du prompt :
   Contexte: [chunks récupérés]
   Question: "Quand l'ENSA a-t-elle été créée ?"
   Instruction: Réponds précisément basé sur le contexte.
           ↓
6. 🤖 Gemini API : Génération de la réponse
           ↓
7. ✅ Réponse : "L'ENSA Al Hoceima a été créée en 2008."
```

### Métriques de performance

**Temps de réponse typique** :

- Embedding de la question : ~50 ms
- Recherche vectorielle : ~10 ms
- Appel API Gemini : 1-3 secondes
- **Total** : 1-3 secondes

**Coûts** :

- Embeddings locaux : Gratuit (SentenceTransformers)
- ChromaDB : Gratuit (open-source)
- Gemini API : ~15 requêtes gratuites/minute
- **Coût total pour ce TP** : 0 €

**Scalabilité** :

- Documents : Jusqu'à 10 000 sans problème
- Requêtes simultanées : 10-50 (selon config serveur)
- Pour plus : Passer à une architecture distribuée

---

## 🏃 Plan B : Exécution Locale (Sans Docker)

### Quand utiliser cette méthode ?

- ❌ Docker Desktop ne fonctionne pas
- ❌ Problèmes de virtualisation (Hyper-V)
- ❌ Ressources système limitées
- ✅ Développement rapide et léger
- ✅ Débogage approfondi nécessaire

### Prérequis système

- **Python** : Version 3.9, 3.10 ou 3.11 installée
- **Pip** : Gestionnaire de packages Python
- **Git** : Pour cloner le dépôt
- **Espace disque** : ~2 GB (modèles + dépendances)

### Installation pas à pas

**Étape 1** : Vérifier Python

```powershell
python --version
```

**Résultat attendu** : `Python 3.9.x` ou supérieur

**Si Python n'est pas installé** :

1. Télécharger depuis [python.org](https://www.python.org/downloads/)
2. Cocher "Add Python to PATH" pendant l'installation
3. Redémarrer PowerShell

**Étape 2** : Créer un environnement virtuel

```powershell
# Se placer dans le dossier du projet
cd c:\Users\jozef\OneDrive\Desktop\AIops-RAG

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
.\venv\Scripts\Activate.ps1
```

**Pourquoi un environnement virtuel ?**

- Isole les dépendances du projet
- Évite les conflits avec d'autres projets Python
- Facilite la gestion des versions de packages

**Étape 3** : Installer les dépendances

```powershell
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer tous les packages requis
pip install -r requirements.txt
```

**Packages installés** (principaux) :

- `streamlit` : Framework web
- `langchain` : Framework RAG
- `chromadb` : Base vectorielle
- `sentence-transformers` : Modèle d'embeddings
- `google-generativeai` : SDK Gemini

**Temps d'installation** : 3-5 minutes

**Étape 4** : Configurer la clé API

```powershell
# Copier le fichier d'exemple
copy .env.example .env

# Éditer avec notepad
notepad .env
```

Insérer votre clé :

```
GOOGLE_API_KEY=AIzaSy...
```

**Étape 5** : Démarrer l'application

```powershell
# Lancer Streamlit
python -m streamlit run app/main.py
```

**Alternative** :

```powershell
streamlit run app/main.py
```

**Sortie attendue** :

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

**Étape 6** : Accéder à l'interface

Ouvrir [http://localhost:8501](http://localhost:8501) dans votre navigateur

## 📚 Pour aller plus loin

**Documentation officielle** :

- [Docker](https://docs.docker.com/)
- [LangChain](https://python.langchain.com/)
- [ChromaDB](https://docs.trychroma.com/)
- [Streamlit](https://docs.streamlit.io/)

**Tutoriels avancés** :

- [RAG from Scratch](https://github.com/langchain-ai/rag-from-scratch)
- [Vector Databases Explained](https://www.pinecone.io/learn/vector-database/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

**Communautés** :

- [LangChain Discord](https://discord.gg/langchain)
- [r/MachineLearning](https://reddit.com/r/MachineLearning)
- [Docker Community Forum](https://forums.docker.com/)

---
