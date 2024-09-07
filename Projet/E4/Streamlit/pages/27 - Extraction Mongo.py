# -*- coding: utf-8 -*-
"""
Created on Sat Apr 20 12:04:54 2024

@author: Utilisateur
"""

import streamlit as st
from pymongo import MongoClient
import pandas as pd
import base64
from PIL import Image
import io

# END_POINT = '172.24.240.193:27017'
END_POINT = 'localhost:27017'

# Connexion à MongoDB
client = MongoClient(f'mongodb://admin:admin@{END_POINT}/')
db = client['ANIMOV']
collection = db['chevres']

# Obtenir le nombre total d'enregistrements dans la collection
total_enregistrements = collection.count_documents({})

# Ajouter un slider pour sélectionner l'indice de l'enregistrement
n = st.sidebar.slider('Sélectionner l\'indice de l\'enregistrement:', 0, total_enregistrements - 1, 0)

options = list(range(4))
selected_option = st.sidebar.selectbox("Source :", options)

# Extraction du n-ième enregistrement de la collection
n_ieme_enregistrement = collection.find().skip(n).limit(1).next()

st.title(f"Frame {n} de la source {selected_option}.")

col1, col2= st.columns(2)

# Vérification de la présence de 'data' et extraction de 'data.detect'
if 'data' in n_ieme_enregistrement and n_ieme_enregistrement['data']:
    detect_data = n_ieme_enregistrement['data'][selected_option].get('detect', None)
    if detect_data is not None:
        # Créer un DataFrame à partir de la liste de listes dans 'data.detect'

        with col1:
            df = pd.DataFrame(detect_data)

            new_column_names = {
                0: 'Id', 
                1: 'X1', 
                2: 'Y1', 
                3: 'X2', 
                4: 'Y2', 
                5: 'Confiance', 
                6: 'Debout-Couche', 
                7: 'Auge', 
                8: 'Abreuvoir', 
                9: 'Grooming'
            }

            df = df.rename(columns=new_column_names)

            st.write("Detections :")
            st.write(df)
        
        with col2:
            # Extraction et affichage de l'image frame
            frame_data = n_ieme_enregistrement['data'][selected_option].get('frame', None)
            if frame_data:
                # Décoder les données base64 de 'frame'
                image_data = base64.b64decode(frame_data)
                # Conversion des données binaires en image et affichage
                image = Image.open(io.BytesIO(image_data))

                st.write("Frame :")
                # Afficher l'image dans Streamlit
                st.image(image, caption=f'Frame {n}.')
    else:
        st.error("Le champ 'detect' est absent du premier élément de 'data'.")
else:
    st.error("Le champ 'data' est absent ou vide.")

# Création d'une case à cocher pour demander à l'utilisateur s'il souhaite voir le code
agree = st.sidebar.checkbox('Afficher le code Python')

if agree:
    # Si l'utilisateur coche la case, le fichier Python est lu et affiché
    file_path = r'./pages/27 - Extraction Mongo.py'  # Spécifiez le chemin correct vers le fichier Python
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        st.code(code, language='python')  # Affiche le code dans un format adapté à Python
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
