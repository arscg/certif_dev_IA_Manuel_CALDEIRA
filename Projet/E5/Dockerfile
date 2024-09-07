# Utilise l'image Alpine comme base
FROM alpine:latest

# Installe les dépendances nécessaires, y compris les outils de compilation et les fichiers d'en-tête Python
RUN apk add --no-cache python3 py3-pip bash gcc musl-dev linux-headers python3-dev

# Crée un environnement virtuel Python
RUN python3 -m venv /opt/venv

# Active l'environnement virtuel et met à jour pip
RUN . /opt/venv/bin/activate && pip install --upgrade pip

# Crée un répertoire pour l'application
RUN mkdir -p /app

# Copie des fichiers de configuration et des scripts dans le conteneur
COPY app/config.yaml config.yaml
COPY app/api.py /api.py

# Copie du fichier requirements.txt et installation des dépendances Python
COPY ./requirements.txt /requirements.txt
RUN . /opt/venv/bin/activate && pip install -r /requirements.txt

# Définit le répertoire de travail
WORKDIR /

# Active l'environnement virtuel
ENV PATH="/opt/venv/bin:$PATH"

# Expose le port utilisé par l'application Flask (port 5002 par exemple)
EXPOSE 5002

# Commande pour exécuter le script Python
CMD ["python3", "api.py"]
