# Utiliser une image de base Python
FROM python:3.12.1

# Définir le répertoire de travail dans le conteneur
WORKDIR /code

# Copiez le fichier des dépendances dans le répertoire de travail
COPY ./requirements.txt /code/requirements.txt

# Installer les dépendances Python
# --no-cache-dir pour ne pas stocker le cache pip, réduisant la taille de l'image
RUN pip install --no-cache-dir -r --upgrade -r /code/requirements.txt

# Copier le reste du code source de l'application dans le répertoire de travail
# Cela inclut tous les fichiers et dossiers dans le répertoire src
COPY ./src/  /code/src

# COPY main.py ./
# COPY your_config_file.yml ./

EXPOSE 80
# Commande pour exécuter l'application lorsque le conteneur démarre
CMD ["fastapi", "run", "src/main.py", "--port", "80"]
