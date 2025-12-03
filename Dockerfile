# Utiliser une image Python officielle légère
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Installer les dépendances système nécessaires pour ChromaDB (et autres packages C++)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copier le fichier des dépendances
COPY requirements.txt .

# Install CPU-only PyTorch first (avoids downloading 700MB+ CUDA packages)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Installer les dépendances (PyTorch already installed, will be skipped)
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Create directories for data and chroma_db with proper permissions
RUN mkdir -p /app/app/data /app/app/chroma_db && chmod -R 777 /app/app/data /app/app/chroma_db

# Exposer le port utilisé par Streamlit
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]