# Projet d'Analyse de Données Animov

Ce projet est une application Flask permettant d'analyser les données d'activité des animaux. Il comprend des fonctionnalités pour l'authentification des utilisateurs, la gestion des bases de données, et l'analyse statistique des données reçues. L'application fournit également des API RESTful pour interagir avec les données.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les éléments suivants :

- Python 3.8 ou plus
- pip (le gestionnaire de paquets Python)
- Un serveur MySQL ou SQLite pour la base de données

## Installation

1. Clonez le dépôt GitHub sur votre machine locale :

2. Installez les dépendances requises à partir du fichier `requirements.txt` :

    ```bash
    pip install -r requirements.txt
    ```

3. Configurez les variables d'environnement nécessaires (si applicables) :

    - `SECRET_KEY` : Clé secrète pour l'application Flask.
    - `MYSQL_DATABASE_URI` : URI de connexion à la base de données MySQL.

4. Configurez le fichier `config.yaml` pour les paramètres de la base de données :

    ```yaml
    database:
        type: "mysql"
        driver: "pymysql"
        username: "votre_nom_utilisateur"
        password: "votre_mot_de_passe"
        host: "localhost"
        port: 3306
        database_name: "ANIMOV"
    ```

5. Initialisez la base de données SQLite :

    ```bash
    python db_utils.py
    ```

## Utilisation

1. Lancer le serveur Flask :

    ```bash
    python test_data_animov.py
    ```

2. Accédez à l'application via votre navigateur à l'adresse suivante :

    ```
    http://127.0.0.1:5500/
    ```

3. Utilisez les différentes routes API pour interagir avec les données :

    - `/login` : Authentification de l'utilisateur.
    - `/get_data_animov_ch` : Récupération des données d'activités.
    - `/chevres_heures` : Récupération des données d'activité à l'heure.
    - `/sources`, `/dates`, etc. : Autres endpoints pour obtenir des informations spécifiques.
    - `/apidocs`, acced à la documentation   

## Fonctionnalités Principales

- **Authentification des Utilisateurs** : Utilisation de tokens JWT pour l'authentification des utilisateurs.
- **Gestion des Données** : Analyse des données reçues et génération de statistiques.
- **API RESTful** : Expose des endpoints pour l'interaction avec les données.

## Fichiers Principaux

- `config.py` : Configuration de l'application Flask.
- `db_utils.py` : Fonctions utilitaires pour la gestion de la base de données.
- `email_utils.py` : Fonctions pour l'envoi d'emails d'alerte.
- `test_data_animov.py` : Fichier principal pour lancer l'application Flask.
- `config.yaml` : Fichier de configuration pour les paramètres de la base de données.