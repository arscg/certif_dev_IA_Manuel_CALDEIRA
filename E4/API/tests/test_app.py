import json

# Test de la route de login avec des informations d'identification correctes
def test_login_success(client):
    # Envoyer une requête POST à la route de login avec un utilisateur valide
    response = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    # Vérifier que la réponse a un statut 200 OK
    assert response.status_code == 200
    # Charger la réponse JSON
    data = json.loads(response.data)
    # Vérifier que le token est présent dans la réponse
    assert 'token' in data

# Test de la route de login avec des informations d'identification incorrectes
def test_login_failure(client):
    # Envoyer une requête POST à la route de login avec des informations incorrectes
    response = client.post('/login', json={
        'username': 'wronguser',
        'password': 'wrongpass'
    })
    # Vérifier que la réponse a un statut 401 Unauthorized
    assert response.status_code == 401
    # Charger la réponse JSON
    data = json.loads(response.data)
    # Vérifier que le message d'erreur d'authentification échouée est présent
    assert data['message'] == 'Authentification échouée'

# Test d'accès à une route protégée sans token
def test_protected_route_no_token(client):
    # Envoyer une requête GET à une route protégée sans token
    response = client.get('/get_data_animov_ch')
    # Vérifier que la réponse a un statut 401 Unauthorized
    assert response.status_code == 401
    # Charger la réponse JSON
    data = json.loads(response.data)
    # Vérifier que le message d'erreur de token manquant est présent
    assert data['message'] == 'Token manquant'

# Liste des routes protégées à tester
protected_routes = [
    '/chevres_heures',
    '/chevres_minutes',
    '/sources',
    '/dates',
    '/stats_minute',
    '/stats_heure',
    '/get_serie_heure',
    '/get_serie_jour',
    '/get_serie_last_heure',
    '/get_serie_last_jour',
    # '/get_data_animov'
]

# Test d'accès à toutes les routes protégées avec un token valide
def test_protected_routes_with_token(client):
    # Obtenir un token de connexion valide
    response = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    data = json.loads(response.data)
    token = data['token']

    # Itérer sur toutes les routes protégées
    for route in protected_routes:
        response = client.get(route, headers={'x-access-tokens': token})
        # Vérifier que la réponse a un statut 200 OK pour chaque route
        assert response.status_code == 200, f"Echec sur la route {route}"

# Liste des routes GET à tester pour la récupération des données
get_routes = [
    '/sources',
    '/dates',
    '/stats_minute',
    '/stats_heure',
    '/get_serie_heure',
    '/get_serie_jour',
    '/get_serie_last_heure',
    '/get_serie_last_jour',
    '/chevres_heures',
    '/chevres_minutes'
]

# Test de la récupération des données pour toutes les routes GET
def test_get_routes(client):
    # Obtenir un token de connexion valide
    response = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    data = json.loads(response.data)
    token = data['token']

    # Itérer sur toutes les routes GET
    for route in get_routes:
        response = client.get(route, headers={'x-access-tokens': token})
        # Vérifier que la réponse a un statut 200 OK pour chaque route
        assert response.status_code == 200, f"Echec sur la route {route}"
        # Charger la réponse JSON
        data = json.loads(response.data)
        # Vérifier que la réponse est une liste ou un dictionnaire, selon le cas
        assert isinstance(data, (list, dict)), f"La réponse de la route {route} n'est pas du bon type"

# Test de la réception de données Animov
def test_receive_data_animov(client):
    # Préparer des données de test pour l'envoi
    data_to_send = [{
        "source_id": 1,
        "date": ["2024-07-31 13:45:00.000"],
        "detect": [
            [1, 100, 100, 200, 200, 0.9, 1, False, False, False],
            [2, 150, 150, 250, 250, 0.8, 0, False, False, False]
        ]
    }]
    # Envoyer les données de test à la route de réception
    response = client.post('/receive_data_animov', json=data_to_send)
    # Vérifier que la réponse a un statut 200 OK
    assert response.status_code == 200
    # Vérifier que le message de réponse indique que les données ont été reçues
    assert b'Re\xc3\xa7u' in response.data  # Vérification du message de réponse 'Reçu'

# Test de la récupération des données Animov avec différents paramètres
def test_get_data_animov_ch(client):
    # Obtenir un token de connexion valide
    response = client.post('/login', json={
        'username': 'arscg',
        'password': 'arscg'
    })
    data = json.loads(response.data)
    token = data['token']

    # Liste des paramètres à tester
    params_list = [
        {'sources': "1,2,3,4", 'with_images': "Single", 'with_detect': False, 'with_stats': False, 'with_global_stats': True},
        {'sources': "1", 'with_images': "Single", 'with_detect': False, 'with_stats': False, 'with_global_stats': False},
        {'sources': "2", 'with_images': "Single", 'with_detect': False, 'with_stats': False, 'with_global_stats': False},
        {'sources': "3", 'with_images': "Single", 'with_detect': False, 'with_stats': False, 'with_global_stats': False},
        {'sources': "4", 'with_images': "Single", 'with_detect': False, 'with_stats': False, 'with_global_stats': False},
        {'sources': "1", 'with_images': "Single", 'with_detect': True, 'with_stats': False, 'with_global_stats': False},
        {'sources': "2", 'with_images': "Single", 'with_detect': True, 'with_stats': False, 'with_global_stats': False},
        {'sources': "3", 'with_images': "Single", 'with_detect': True, 'with_stats': False, 'with_global_stats': False},
        {'sources': "4", 'with_images': "Single", 'with_detect': True, 'with_stats': False, 'with_global_stats': False},
    ]

    # Itérer sur toutes les combinaisons de paramètres
    for params in params_list:
        response = client.get('/get_data_animov_ch', headers={'x-access-tokens': token}, query_string=params)
        # Vérifier que la réponse a un statut 200 OK pour chaque combinaison de paramètres
        assert response.status_code == 200
        # Charger la réponse JSON
        data = json.loads(response.data)
        # Vérifier que la réponse est un dictionnaire
        assert isinstance(data, dict), "La réponse de la route /get_data_animov_ch n'est pas du bon type"
