# -*- coding: utf-8 -*-
"""
Created on Sat Apr 20 12:04:54 2024

@author: Utilisateur
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL de la page à scraper
url = 'https://rnm.franceagrimer.fr/prix?CHEVRE'
# url = 'https://rnm.franceagrimer.fr/prix?MUNSTER'

st.title("Cours du jour (rnm.franceagrimer.fr)")

try:
    # Envoyer une requête HTTP à l'URL
    response = requests.get(url)
    response.raise_for_status()  # Lève une exception pour les codes d'état 4xx/5xx

    # Analyser le contenu HTML de la page avec BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Rechercher tous les éléments avec la classe 'sta5'
    elements_sta5 = soup.find_all(class_='sta5')
    
    # Création d'une liste pour stocker les données
    data = []

    # Extraire les informations nécessaires de chaque élément et les ajouter à la liste
    for element in elements_sta5:
        product_name = element.find('a').text.strip()
        product_price = element.find('strong').text.strip()
        product_variation = element.find_all('td')[0].text.strip()
        
        # Convertir le prix en valeur numérique si possible, sinon ignorer cet élément
        try:
            product_price = float(product_price.replace(',', '.'))
            # Ajouter un dictionnaire pour chaque produit dans la liste
            data.append({
                "Produit": product_name,
                "Prix": product_price,
                "Variation": product_variation
            })

        except ValueError:

            # Si le prix n'est pas convertible en float, commencer une nouvelle section de données
            if data:  # Vérifie si la liste n'est pas vide

                st.write("France :")
                # Création d'un DataFrame à partir des données collectées jusqu'à présent
                df = pd.DataFrame(data)
                # Affichage du DataFrame dans Streamlit
                st.write(df)
                # Réinitialiser la liste pour une nouvelle section de données
                data = []
                
            continue

    # Vérifier et afficher les données restantes à la fin de la boucle
    if data:
        st.write("MIN de Rungis :")
        df = pd.DataFrame(data)
        st.write(df)

except requests.RequestException as e:
    st.error(f"Erreur lors de la récupération de la page : {e}")

# Création d'une case à cocher pour demander à l'utilisateur s'il souhaite voir le code
agree = st.sidebar.checkbox('Afficher le code Python')

if agree:
    # Si l'utilisateur coche la case, le fichier Python est lu et affiché
    file_path = r'./pages/28 - Scraping.py'  # Spécifiez le chemin correct vers le fichier Python
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        st.code(code, language='python')  # Affiche le code dans un format adapté à Python
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
