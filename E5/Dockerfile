# Utiliser une image Python Alpine comme image de base
FROM python:3.9-alpine

# Installer les dépendances nécessaires pour construire les paquets Python et pour psutil
RUN apk add --no-cache gcc musl-dev linux-headers

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers requirements.txt et les fichiers .py dans le répertoire de travail
COPY requirements.txt requirements.txt
COPY api.py api.py
COPY config.yaml config.yaml

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port sur lequel l'application Flask va tourner
EXPOSE 5002

# Démarrer le script api.py
CMD ["python", "api.py"]
