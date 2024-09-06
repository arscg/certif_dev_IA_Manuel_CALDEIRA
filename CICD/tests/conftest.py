# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 16:34:20 2024

@author: arsca
"""

import pytest
import sys
import os

# Ajouter le chemin du module app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_data_animov import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    with app.test_client() as client:
        with app.app_context():
            # Configurer la base de données de test si nécessaire
            pass
        yield client