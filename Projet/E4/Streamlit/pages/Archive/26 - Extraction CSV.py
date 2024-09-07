import streamlit as st
import pandas as pd
import glob
import os
import warnings
from sqlalchemy import create_engine

# Configuration initiale
st.set_page_config(layout="wide")
warnings.filterwarnings('ignore')

# Fonction pour le traitement et le transfert des données
def data_traitement(chemin_dossier, base_de_donnees_url, source):
    engine = create_engine(base_de_donnees_url)
    resultats = {}
    
    # Pour les types de fichiers -1.csv et -2.csv
    for type_fichier in ['-1.csv', '-2.csv']:
        fichiers_csv = glob.glob(os.path.join(chemin_dossier, f'*{type_fichier}'))
        dataframes = [pd.read_csv(fichier) for fichier in fichiers_csv]
        if dataframes:
            df_final = pd.concat(dataframes, ignore_index=True)
            df_final['Source'] = source 
            # Nom de la table en fonction du type de fichier
            table_name = 'final' if '-1' in type_fichier else 'final_2'
            df_final.to_sql(table_name, engine, if_exists='append', index=False)
            resultats[type_fichier] = df_final
        else:
            resultats[type_fichier] = pd.DataFrame()
    
    return resultats

# Création d'une case à cocher pour demander à l'utilisateur s'il souhaite voir le code
agree = st.sidebar.checkbox('Afficher le code Python')

if agree:
    # Si l'utilisateur coche la case, le fichier Python est lu et affiché
    file_path = r'./pages/26 - Extraction CSV.py'  # Spécifiez le chemin correct vers le fichier Python
    try:
        with open(file_path, 'r') as file:
            code = file.read()
        st.code(code, language='python')  # Affiche le code dans un format adapté à Python
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")

# Paramètres de la base de données pour MySQL
base_de_donnees_url = "mysql+pymysql://root:admin@localhost:3306/ANIMOV_CSV_data"

# Localisation du dossier parent et recherche des sous-dossiers
dossier_parent = '../../lusignan_14-01_20-01'
sous_dossiers = [d for d in os.listdir(dossier_parent) if os.path.isdir(os.path.join(dossier_parent, d))]

# Configuration des onglets pour différents ensembles de données
tabs = st.tabs([f"Fichiers {d}" for d in sous_dossiers])


# Initialisation de la variable de session pour suivre l'état du bouton
if 'button_pressed' not in st.session_state:
    st.session_state.button_pressed = False

# Affichage du bouton
button_label = 'Lancer extraction !'
extract = st.button(button_label, key='extract_button', use_container_width=True, disabled=st.session_state.button_pressed)

# Vérifier si le bouton a été pressé
if extract:
    # Mettre à jour l'état du bouton dans la variable de session
    st.session_state.button_pressed = True


if not st.session_state.button_pressed :
    st.write('Prossessing')
    for tab, dossier in zip(tabs, sous_dossiers):
        chemin_dossier = os.path.join(dossier_parent, dossier)
        with tab:
            resultats = data_traitement(chemin_dossier, base_de_donnees_url, dossier)
            for key, df in resultats.items():
                st.write(f"Traitement fichiers *{key}")
                st.dataframe(df)
