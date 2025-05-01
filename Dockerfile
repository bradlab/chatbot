# Utilisez une image de base Python. Choisissez une version stable et adaptée à votre projet.
FROM python:slime

# Définissez le répertoire de travail dans le conteneur
WORKDIR /app

# Copiez le fichier des dépendances dans le répertoire de travail
COPY requirements.txt .

# Installer les dépendances Python
# --no-cache-dir pour ne pas stocker le cache pip, réduisant la taille de l'image
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source de l'application dans le répertoire de travail
# Cela inclut tous les fichiers et dossiers dans le répertoire src
COPY src/ ./src/

# COPY main.py ./
# COPY your_config_file.yml ./

# Commande pour exécuter votre application lorsque le conteneur démarre
CMD ["python", "src/main.py"]

# EXPOSE 8000