# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:14:24 2024

@author: arsca
"""

import pytest
import os
import tempfile
import json
import sys
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
# from sklearn.metrics import mean_squared_error
import random

# Configurez le logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Ajoutez le chemin du module ici
sys.path.append('D:/inrae_new_2023/inrae_new_2023/api_flask')

from appjwt_refactoring import app, init_db


def generate_random_data(seed, num_days=7, freq='H'):
    np.random.seed(seed)
    date_rng = pd.date_range(start=datetime.now() - timedelta(days=num_days), end=datetime.now(), freq=freq)
    df = pd.DataFrame(date_rng, columns=['date'])
    df['Effectif debout'] = np.random.uniform(0, 100, size=(len(date_rng)))
    df['Effectif couche'] = np.random.uniform(0, 100, size=(len(date_rng)))
    # Convertir les timestamps en chaînes de caractères
    df['date'] = df['date'].astype(str)
    return df.to_dict(orient='records')

def generate_random_data_input(start_date_str, num_entries):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    data = []
    
    for i in range(num_entries):
        # Générer des valeurs aléatoires pour 'Effectif debout' et 'Effectif couche'
        effectif_debout = random.randint(0, 25000)
        effectif_couche = random.randint(0, 25000)
        
        # Calculer la date et l'heure pour cette entrée
        date = start_date + timedelta(minutes=15 * i)
        
        # Ajouter l'entrée à la liste des données
        data.append({
            'date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'Effectif debout': effectif_debout,
            'Effectif couche': effectif_couche
        })
    
    return data

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_login(client):
    rv = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    json_data = rv.get_json()
    assert rv.status_code == 200
    assert 'token' in json_data
    

def test_predict(client):
    # def generate_random_data(start_date_str, num_entries):
    #     start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    #     data = []
        
    #     for i in range(num_entries):
    #         # Générer des valeurs aléatoires pour 'Effectif debout' et 'Effectif couche'
    #         effectif_debout = random.randint(0, 25000)
    #         effectif_couche = random.randint(0, 25000)
            
    #         # Calculer la date et l'heure pour cette entrée
    #         date = start_date + timedelta(minutes=15 * i)
            
    #         # Ajouter l'entrée à la liste des données
    #         data.append({
    #             'date': date.strftime('%Y-%m-%d %H:%M:%S'),
    #             'Effectif debout': effectif_debout,
    #             'Effectif couche': effectif_couche
    #         })
        
    #     return data
    
    # Authentification pour obtenir le token
    url_login = '/login'
    auth_data = {'username': 'arscg', 'password': 'arscg'}
    response_login = client.post(url_login, json=auth_data)
    assert response_login.status_code == 200
    token = response_login.get_json()['token']

    # Données de test
    data = generate_random_data_input('2023-08-12 00:00:00', 96)

    headers = {
        'x-access-tokens': token,
        'Content-Type': 'application/json'
    }

    # Requête de prédiction
    url_predict = '/predict'
    response_predict = client.post(url_predict, headers=headers, json=data)

    assert response_predict.status_code == 200
    response_data = response_predict.get_json()

    # Vérification de la réponse
    assert 'predictions' in response_data
    assert 'model' in response_data
    assert 'version' in response_data

    predictions = json.loads(response_data['predictions'])
    assert isinstance(predictions, list)
    assert len(predictions) == len(data)

    for prediction in predictions:
        assert 'Date' in prediction
        assert 'Valeurs' in prediction

def test_train_route(client):
   
    logging.info("Starting test_train")
    rv = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    json_data = rv.get_json()
    token = json_data['token']
    
    # Générer des données aléatoires avec une graine
    # data = generate_random_data(seed=42)
    data = generate_random_data_input('2023-08-1 00:00:00', (96*4))
    
    print (data)
    logging.info("Sending training data: %s", json.dumps(data, indent=2))
    response = client.post('/train', json=data, headers={'x-access-tokens': token})
    
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert response_data['message'] == 'Model trained successfully'
    assert 'validation_rmse' in response_data
    assert 'run_id' in response_data

def test_rmse_history(client):
    logging.info("Starting test_rmse_history")
    rv = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    json_data = rv.get_json()
    token = json_data['token']
    
    rv = client.get('/rmse_history', headers={'x-access-tokens': token})
    if rv.status_code != 200:
        logging.error("RMSE history request failed with status code %d: %s", rv.status_code, rv.get_data(as_text=True))
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert 'rmse_history' in json_data