from flask import Flask, jsonify, request, render_template
from flasgger import Swagger
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
import warnings
import mlflow
import matplotlib
matplotlib.use('Agg')  # Utilise 'Agg' backend pour Matplotlib, nécessaire pour les environnements sans interface graphique
import os
import logging
import datetime
from functools import wraps
from db_utils import init_db, add_user, authenticate_user  # Import des utilitaires pour la base de données
from logic import train_model, predict_model, log_rmse, fetch_rmse_history  # Import des fonctions logiques principales
from models import DataCleaner, SARIMAXModel, CustomModel  # Import des modèles
import jwt  # Import pour JSON Web Token
import sqlite3  # Import pour la gestion de la base de données SQLite

warnings.filterwarnings("ignore")  # Ignore les avertissements

app = Flask(__name__)  # Initialise l'application Flask
Swagger(app)  # Initialise Swagger pour la documentation automatique des API
logging.basicConfig(level=logging.INFO)  # Configure le logging au niveau INFO

mlflow.set_tracking_uri("http://localhost:5000")  # Configure l'URI de tracking pour MLflow
mlflow.set_experiment("train_experiment")  # Définit l'expérience MLflow

app.config['SECRET_KEY'] = 'd3a6e8b45f8e4c73a9a4f6e7a9c1b2d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0'  # Clé secrète pour JWT
DATABASE = 'tokens.db'  # Nom du fichier de base de données SQLite pour les tokens

# Ajoute un utilisateur dans la base de données au démarrage
try:
    add_user('arscg', 'arscg')
except Exception as e:
    logging.error(f"Error adding user: {e}")  # Logue une erreur si l'ajout échoue

# Route pour l'authentification des utilisateurs
@app.route('/login', methods=['POST'])
def login():
    """
    Authentification de l'utilisateur
    ---
    tags:
      - Authentification
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: arscg
            password:
              type: string
              example: arscg
    responses:
      200:
        description: Authentification réussie
        schema:
          type: object
          properties:
            token:
              type: string
      401:
        description: Authentification échouée
    """
    auth = request.json  # Récupère les données JSON envoyées avec la requête
    if auth:
        token = authenticate_user(auth['username'], auth['password'], app.config['SECRET_KEY'])  # Authentifie l'utilisateur
        if token:
            return jsonify({'token': token})  # Retourne le token JWT si l'authentification est réussie
    return jsonify({'message': 'Authentification échouée'}), 401  # Retourne une erreur 401 si l'authentification échoue

# Route principale qui affiche la page de connexion
@app.route('/')
def index():
    return render_template('login.html')

# Décorateur pour exiger un token pour accéder à certaines routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')  # Récupère le token des en-têtes de la requête
        if not token:
            return jsonify({'message': 'Token manquant'}), 401  # Retourne une erreur 401 si le token est manquant
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tokens WHERE token=?", (token,))
                token_data = cursor.fetchone()
                if not token_data:
                    return jsonify({'message': 'Token invalide'}), 401  # Retourne une erreur 401 si le token est invalide
                expiration = token_data[3]
                if isinstance(expiration, str):
                    expiration = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S.%f')
                if expiration < datetime.datetime.utcnow():
                    return jsonify({'message': 'Token expiré'}), 401  # Retourne une erreur 401 si le token a expiré
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])  # Décode le token JWT
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(*args, **kwargs)  # Appelle la fonction décorée si tout est correct
    return decorated

# Route pour entraîner un modèle
@app.route('/train', methods=['POST'])
@token_required  # Exige un token pour accéder à cette route
def train():
    """
    Entraîner le modèle
    ---
    tags:
      - Modèle
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
    responses:
      200:
        description: Modèle entraîné avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            validation_rmse:
              type: number
            run_id:
              type: string
      500:
        description: Erreur lors de l'entraînement du modèle
    """
    try:
        data = request.json  # Récupère les données JSON envoyées avec la requête
        predictions_json, validation_rmse, run_id = train_model(data)  # Entraîne le modèle avec les données fournies
        return jsonify({'message': 'Model trained successfully', 'validation_rmse': validation_rmse, 'run_id': run_id,  'predictions': predictions_json})
    except Exception as e:
        logging.error(f"Error during training: {e}")
        return jsonify({'message': 'Erreur lors de l\'entraînement du modèle', 'error': str(e)}), 500  # Retourne une erreur 500 si l'entraînement échoue

# Route pour faire des prédictions avec un modèle existant
@app.route('/predict', methods=['POST'])
@token_required  # Exige un token pour accéder à cette route
def predict():
    """
    Faire une prédiction
    ---
    tags:
      - Prédiction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
    responses:
      200:
        description: Prédiction réussie
        schema:
          type: object
          properties:
            predictions:
              type: array
              items:
                type: object
            model:
              type: string
            version:
              type: string
      500:
        description: Erreur lors de la prédiction
    """
    try:
        data = request.get_json()  # Récupère les données JSON envoyées avec la requête
        predictions_json, model_name, model_version, prediction_time = predict_model(data)  # Fait des prédictions avec le modèle
        return jsonify({'predictions': predictions_json, 'model': model_name, 'version': model_version, 'prediction_time': prediction_time})
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return jsonify({'message': 'Erreur lors de la prédiction', 'error': str(e)}), 500  # Retourne une erreur 500 si la prédiction échoue

# Route pour stocker une valeur de RMSE et les artefacts associés
@app.route('/rmse', methods=['POST'])
@token_required  # Exige un token pour accéder à cette route
def stock_rmse():
    """
    Stocker la valeur RMSE
    ---
    tags:
      - RMSE
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            rmse:
              type: number
            model:
              type: string
            version:
              type: string
            ground_truth:
              type: array
              items:
                type: object
            predictions:
              type: array
              items:
                type: object
            graphique:
              type: string
    responses:
      200:
        description: RMSE stocké avec succès
      400:
        description: Valeur RMSE non fournie
      500:
        description: Erreur lors du stockage de RMSE
    """
    try:
        data = request.json  # Récupère les données JSON envoyées avec la requête
        response = log_rmse(data)  # Logue la valeur RMSE et les artefacts associés
        return jsonify(response), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Retourne une erreur 400 si la valeur RMSE n'est pas fournie
    except Exception as e:
        logging.error(f"Error during logging RMSE: {e}")
        return jsonify({'message': 'Erreur lors du stockage de RMSE', 'error': str(e)}), 500  # Retourne une erreur 500 si le stockage échoue

# Route pour récupérer l'historique des valeurs de RMSE
@app.route('/rmse_history', methods=['GET'])
@token_required  # Exige un token pour accéder à cette route
def rmse_history():
    """
    Obtenir l'historique des RMSE
    ---
    tags:
      - RMSE
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
      - name: model
        in: query
        type: string
        required: false
      - name: include_artifacts
        in: query
        type: string
        required: false
        default: "false"
    responses:
      200:
        description: Historique des RMSE récupéré avec succès
        schema:
          type: object
      404:
        description: L'expérience n'existe pas
      500:
        description: Erreur lors de la récupération de l'historique des RMSE
    """
    try:
        experiment_name = "predict_experience"  # Nom de l'expérience MLflow
        client = mlflow.tracking.MlflowClient()
        
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            return jsonify({"message": "L'expérience n'existe pas."}), 404  # Retourne une erreur 404 si l'expérience n'existe pas
        
        experiment_id = experiment.experiment_id

        limit = request.args.get('limit', default=10, type=int)  # Limite du nombre de runs à récupérer
        version = request.args.get('model', default=None, type=str)  # Version du modèle à filtrer
        include_artifacts = request.args.get('include_artifacts', default='false', type=str).lower() == 'true'  # Indicateur pour inclure ou non les artefacts

        response = fetch_rmse_history(client, experiment_id, limit, version, include_artifacts)  # Récupère l'historique des RMSE
        return jsonify(response)
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'historique des RMSE: {e}")
        return jsonify({'message': 'Erreur lors de la récupération de l\'historique des RMSE', 'error': str(e)}), 500  # Retourne une erreur 500 si la récupération échoue
    
if __name__ == '__main__':
    init_db()  # Initialise la base de données au démarrage
    app.run(debug=False, port=5100)  # Démarre l'application Flask sur le port 5100
