# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 10:32:32 2023

@author: dsite
"""
import streamlit as st
import logging
import warnings
from PIL import Image
import requests

# Configuration du niveau de journalisation pour réduire les messages de l'API "atoti"
logging.getLogger("atoti").setLevel(logging.ERROR)

# Ignorer les avertissements dans le flux de travail
warnings.filterwarnings('ignore')

def authentication_form():
    """
    Affiche le formulaire d'authentification pour l'utilisateur.
    """
    st.title("Authentification")
    username = st.text_input("Nom d'utilisateur")  # Champ pour le nom d'utilisateur
    password = st.text_input("Mot de passe", type="password")  # Champ pour le mot de passe, masqué

    if st.button("Se connecter"):
        # URL de l'API pour la connexion
        url_login = 'http://localhost:5500/login'
        auth_data = {'username': username, 'password': password}  # Données de connexion
        response_login = requests.post(url_login, json=auth_data)  # Envoi de la requête de connexion

        if response_login.status_code == 200:
            token = response_login.json()['token']  # Récupération du jeton si la connexion est réussie
            st.success("Authentification réussie")
            # Stockage du jeton dans la session Streamlit
            st.session_state.token = token
        else:
            st.error(f"Erreur d'authentification: {response_login.status_code}")
            st.text(f"Contenu de la réponse brute: {response_login.text}")

# Création de la mise en page de la page avec trois colonnes
col1, col2, col3 = st.columns([2, 5, 2])

with col2:
    # Chargement de l'image principale
    image = Image.open('./images/chevre.png')
    # Affichage de l'image en utilisant toute la largeur de la colonne
    st.image(image, use_column_width='always')
    
    # Ajout de logos dans des sous-colonnes
    col11, col12, col13, col14 = st.columns([5, 1, 1, 0.9])
    
    with col14:
        image = Image.open('./images/logo_thumb.png')
        st.image(image)  # Affichage du logo

    with col13:
        image = Image.open('./images/tekin.png')
        st.image(image)  # Affichage du logo

    with col12:
        image = Image.open('./images/logo_acticom.png')
        st.image(image)  # Affichage du logo
    
    # Affichage du formulaire d'authentification
    authentication_form()
