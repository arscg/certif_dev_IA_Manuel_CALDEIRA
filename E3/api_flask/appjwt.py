# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 10:35:03 2024

@author: dsite
"""

from flask import Flask, jsonify, request, render_template
from flasgger import Swagger
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
import warnings
import mlflow
import matplotlib
matplotlib.use('Agg')
import os
import logging
import datetime
from functools import wraps
from db_utils import init_db, add_user, authenticate_user
from logic import train_model, predict_model, log_rmse, fetch_rmse_history
from models import DataCleaner, SARIMAXModel, CustomModel
import jwt
import sqlite3

warnings.filterwarnings("ignore")

app = Flask(__name__)
Swagger(app)  # Initialiser Swagger
logging.basicConfig(level=logging.INFO)

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("train_experiment")

app.config['SECRET_KEY'] = 'd3a6e8b45f8e4c73a9a4f6e7a9c1b2d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0'
DATABASE = 'tokens.db'

try:
    add_user('arscg', 'arscg')
except Exception as e:
    logging.error(f"Error adding user: {e}")

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
    auth = request.json
    if auth:
        token = authenticate_user(auth['username'], auth['password'], app.config['SECRET_KEY'])
        if token:
            return jsonify({'token': token})
    return jsonify({'message': 'Authentification échouée'}), 401

@app.route('/')
def index():
    return render_template('login.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tokens WHERE token=?", (token,))
                token_data = cursor.fetchone()
                if not token_data:
                    return jsonify({'message': 'Token invalide'}), 401
                expiration = token_data[3]
                if isinstance(expiration, str):
                    expiration = datetime.datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S.%f')
                if expiration < datetime.datetime.utcnow():
                    return jsonify({'message': 'Token expiré'}), 401
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/train', methods=['POST'])
@token_required
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
        data = request.json
        predictions_json, validation_rmse, run_id = train_model(data)
        return jsonify({'message': 'Model trained successfully', 'validation_rmse': validation_rmse, 'run_id': run_id,  'predictions':predictions_json})
    except Exception as e:
        logging.error(f"Error during training: {e}")
        return jsonify({'message': 'Erreur lors de l\'entraînement du modèle', 'error': str(e)}), 500


@app.route('/predict', methods=['POST'])
@token_required
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
        data = request.get_json()
        predictions_json, model_name, model_version = predict_model(data)
        return jsonify({'predictions': predictions_json, 'model': model_name, 'version': model_version})
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return jsonify({'message': 'Erreur lors de la prédiction', 'error': str(e)}), 500

@app.route('/rmse', methods=['POST'])
@token_required
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
        data = request.json
        response = log_rmse(data)
        return jsonify(response), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.error(f"Error during logging RMSE: {e}")
        return jsonify({'message': 'Erreur lors du stockage de RMSE', 'error': str(e)}), 500


@app.route('/rmse_history', methods=['GET'])
@token_required
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
        experiment_name = "predict_experience"
        client = mlflow.tracking.MlflowClient()
        
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            return jsonify({"message": "L'expérience n'existe pas."}), 404
        
        experiment_id = experiment.experiment_id

        limit = request.args.get('limit', default=10, type=int)
        version = request.args.get('model', default=None, type=str)
        include_artifacts = request.args.get('include_artifacts', default='false', type=str).lower() == 'true'

        response = fetch_rmse_history(client, experiment_id, limit, version, include_artifacts)
        return jsonify(response)
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'historique des RMSE: {e}")
        return jsonify({'message': 'Erreur lors de la récupération de l\'historique des RMSE', 'error': str(e)}), 500
    
if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5100)
