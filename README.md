# Projet CERTIF

Ce projet est une application composée de plusieurs services et modules, comprenant des API et une interface utilisateur.

## Prérequis

Avant de pouvoir installer et exécuter ce projet, assurez-vous d'avoir les éléments suivants installés sur votre machine :

- **Docker pour Windows** : Pour l'orchestration des conteneurs.
- **Docker Compose** : Inclus avec Docker pour Windows, pour faciliter la gestion multi-conteneurs.
- **Anaconda** : Pour la gestion de l'environnement Python.

## Installation

Suivez les étapes ci-dessous pour configurer et exécuter le projet sur votre environnement local.

### 1. Cloner le dépôt

Ouvrez une invite de commande Anaconda (Anaconda Prompt) et clonez le dépôt GitHub :

```bash
git clone https://github.com/arscg/Certif_projet.git
cd "cerfif projet"
```

### 2. Créer et activer l'environnement Anaconda

Créez un environnement virtuel avec Anaconda et activez-le :

```bash
conda create --name mon_env python=3.x
conda activate mon_env
```

### 3. Configurer les variables d'environnement

Accédez au dossier `Docker_compose` et modifiez le fichier `.env` pour définir les variables d'environnement nécessaires au bon fonctionnement des services. Vous pouvez utiliser un éditeur de texte comme Notepad++ pour cela.

```bash
cd Docker_compose
notepad .env
```

### 4. Installer les dépendances Python

Installez les dépendances Python listées dans `requirements.txt` :

```bash
pip install -r requirements.txt
```

### 5. Lancer les services avec Docker Compose

Pour lancer tous les services définis dans le fichier `docker-compose.yaml`, exécutez la commande suivante depuis le dossier `Docker_compose` :

```bash
docker-compose up -d
```

### 6. Installer et lancer Grafana manuellement

Installer et lancer manuellement avec Docker en suivant ces étapes :

1. **Téléchargez l'image Grafana :**

   ```bash
   docker pull grafana/grafana:latest
   ```

2. **Lancez un conteneur Grafana :**

   ```bash
   docker run -d --name=grafana -p 3001:3000 grafana/grafana:latest
   ```

   Cette commande lance Grafana en arrière-plan et mappe le port 3000 du conteneur au port 3001 de votre machine.

### 7. Lancer les applications et serveurs

Une fois Docker Compose configuré et les dépendances installées, vous pouvez lancer les applications et serveurs en exécutant le script `certif 2.bat`. Pour cela, depuis l'explorateur de fichiers Windows ou via une invite de commande, exécutez :

```bash
certif 2.bat
```

Ce script automatisera le démarrage de toutes les applications et serveurs nécessaires au projet.

### 8. Accéder aux services

Après l'exécution du script `certif 2.bat`, vous pouvez accéder aux différentes applications et services via leurs ports respectifs définis dans le fichier `docker-compose.yaml`.

### 9. Structure des répertoires

Le projet est organisé comme suit :

- **Docker_compose/** : Contient le fichier Docker Compose et les variables d'environnement.
- **E3/** : Contient une API Flask pour la gestion du model IA SARIMAX et des applications.
    - **api_flask/** : Contient le code source de l'API Flask.
    - **app/** : Contient un script Python et des fichiers nécessaires à l'application.
- **E4/** : Contient des services API et une interface Streamlit pour l'analyse de données.
    - **API/** : Dossier contenant des scripts et des utilitaires pour l'API.
    - **Streamlit/** : Interface utilisateur basée sur Streamlit.
- **E5/** : Contient des templates et des utilitaires pour les services de monitoring de la machine hébergeant le projet.
    - **templates/** : Contient des fichiers HTML pour le rendu.
    - **api/** : Contient une API supplémentaire.
    - **config/** : Fichier de configuration YAML pour l'API.
    - **demon/** : Script d'initialisation et de gestion du démon de l'application.

## Usage

Vous pouvez maintenant utiliser et interagir avec les différents services API, Interface utilisateur, et autres composants en fonction de votre projet.