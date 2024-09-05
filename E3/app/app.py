# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 10:35:03 2024

@author: dsite
"""

import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import timedelta
import warnings
import json
from sklearn.metrics import mean_squared_error
import numpy as np
import streamlit as st

warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")

@st.experimental_dialog("Alerte modele")
def message(rmse):
    st.write(f"RMSE moyen trop élévée - {rmse} !!")
    st.write(f"Recalculer le modele !!")

def convert_df_to_dict(df):
    df_copy = df.copy()
    for col in df_copy.columns:
        if isinstance(df_copy[col].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].astype(str)
    return df_copy.to_dict(orient='records')

@st.cache_resource
def load_data():
    chemin_pickle = r'../fichier_final.pickle'
    df = pd.read_pickle(chemin_pickle)
    return df

def train(df):
    # Convertir les colonnes numériques en float32 pour réduire l'utilisation de la mémoire
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        try:
            df[col] = df[col].astype('float32')
        except ValueError as e:
            st.error(f"Erreur lors de la conversion de la colonne {col} en float32 : {e}")
            return

    # Convertir le DataFrame en une liste de dictionnaires (format requis)
    data = df.to_dict(orient='records')

    # Vérifier si le jeton est disponible dans la session
    if 'token' not in st.session_state:
        st.error("Veuillez vous authentifier d'abord.")
        return

    headers = {
        'x-access-tokens': st.session_state.token,
        'Content-Type': 'application/json'
    }
    url_train = 'http://localhost:5100/train'
    response_train = requests.post(url_train, headers=headers, json=data)
    
    if response_train.status_code == 200:
        st.success("Entraînement réussi !")

        col1, col2, col3 = st.columns([2,3, 2])
        
        with col2:
            try:
                data_response = response_train.json()
            except ValueError:
                st.error("La réponse n'est pas un JSON valide.")
                return

            if 'predictions' in data_response:
                predictions_json = data_response['predictions']
                
                try:
                    predictions_df = pd.read_json(predictions_json)
                    predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])

                    # Ajouter la colonne ratio
                    try:
                        df['ratio'] = (df['Effectif debout'] / (df['Effectif couche'] + df['Effectif debout'])) * 100
                    except KeyError as e:
                        st.error(f"Erreur lors du calcul du ratio : colonne manquante {e}")
                        return
                    
                    # Conversion en timestamp et mise en index
                    df['timestamp'] = pd.to_datetime(df['date'], errors='coerce')
                    df = df.set_index('timestamp')

                    # Sélection des colonnes numériques et calcul de la médiane sur un échantillonnage de 15 minutes
                    df_numeric = df.select_dtypes(include=[float, int])
                    median_df = df_numeric.resample('15T').median()

                    # Filtrage pour ne garder que les deux derniers jours
                    last_two_days = median_df.loc[median_df.index >= (median_df.index.max() - pd.Timedelta(days=2))]

                    # Tracer les courbes des valeurs et du ratio sur un seul graphique avec matplotlib
                    plt.figure(figsize=(10, 6))

                    # Courbe des valeurs du modèle prédictif
                    plt.plot(predictions_df.set_index('Date').index, predictions_df['Valeurs'], label='Prédiction', color='blue')

                    # Courbe du ratio
                    plt.plot(last_two_days.index, last_two_days['ratio'], label='Verité terrain', color='orange', linestyle='--')

                    # Ajouter le titre et les légendes
                    plt.title('Prédiction et Verité terrain sur le même graphique')
                    plt.xlabel('Date')
                    plt.legend()

                    # Afficher le graphique dans Streamlit
                    st.pyplot(plt)

                except ValueError as e:
                    st.error(f"Erreur lors de la lecture du JSON : {e}")
                    return


def prediction(filtered_df, ratio_df, median_df):
    ratio_df['Ratio debout'] = (ratio_df['Effectif debout'] / (ratio_df['Effectif debout'] + ratio_df['Effectif couche'])) * 100
    ratio_df.reset_index(inplace=True)
    ratio_df = ratio_df[['date', 'Ratio debout']]

    median_df.reset_index(inplace=True)
    median_df['Ratio debout'] = (median_df['Effectif debout'] / (median_df['Effectif debout'] + median_df['Effectif couche'])) * 100

    filtered_df.reset_index(inplace=True)
    filtered_df['date'] = filtered_df['date'].astype(str)
    data = filtered_df.to_dict(orient='records')

    # Vérifier si le jeton est disponible dans la session
    if 'token' not in st.session_state:
        st.error("Veuillez vous authentifier d'abord.")
        return

    headers = {
        'x-access-tokens': st.session_state.token,
        'Content-Type': 'application/json'
    }
    url_predict = 'http://localhost:5100/predict'
    response_predict = requests.post(url_predict, headers=headers, json=data)
    if response_predict.status_code == 200:
        st.success("Requête de prédiction réussie avec succès !")
        col1, col2, col3 = st.columns(3)

        try:
            with col1:
                response_data = response_predict.json()
                data_list = json.loads(response_data['predictions'])
                df_response = pd.DataFrame(data_list)
                df_response['Date'] = pd.to_datetime(df_response['Date'], errors='coerce')
                ratio_df['date'] = pd.to_datetime(ratio_df['date'], errors='coerce')
                merged_df = pd.merge(df_response, ratio_df, left_on='Date', right_on='date')
                rmse = np.sqrt(mean_squared_error(merged_df['Valeurs'], merged_df['Ratio debout']))
                st.write(f"RMSE: {round(rmse,3)}")

                plt.figure(figsize=(10, 6))
                plt.plot(df_response['Date'], df_response['Valeurs'], color='blue', label='Valeurs API')
                plt.plot(ratio_df['date'], ratio_df['Ratio debout'], color='red', label='Ratio debout')
                plt.title('Graphique des données de l\'API et Ratio debout')
                plt.xlabel('Date')
                plt.ylabel('Valeurs')
                plt.ylim(0, 100)
                plt.legend()
                plt.text(0.05, 0.95, f'RMSE: {rmse:.2f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))

                # Sauvegarder le graphique
                plt.savefig('graphique_plot.png')
                plt.show()

                st.pyplot(plt)

            # Lire le fichier image en binaire
            with open('graphique_plot.png', 'rb') as file:
                img_data = file.read()

            ground_truth = ratio_df[['date', 'Ratio debout']].copy()
            ground_truth['date'] = ground_truth['date'].astype(str)
            ground_truth = ground_truth.to_dict(orient='records')

            predictions = df_response[['Date', 'Valeurs']].copy()
            predictions['Date'] = predictions['Date'].astype(str)
            predictions = predictions.to_dict(orient='records')

            url_rmse = 'http://localhost:5100/rmse'
            data_rmse = {
                'rmse': rmse,
                "model": response_data['model'],
                'version': response_data['version'],
                'exec_time': response_data['prediction_time'],
                'graphique': img_data.decode('latin1'),
                'ground_truth': ground_truth,
                'predictions': predictions
            }
            
            # Appel à la route rmse_history pour afficher l'historique des RMSE
            url_rmse_history = 'http://localhost:5100/rmse_history'
            params = {'limit': 5, 'model': response_data['model']+"_V"+str(response_data['version'])}

            with col2: 
                st.write("Model : "+response_data['model']+"_V"+str(response_data['version']))

            response_rmse = requests.post(url_rmse, headers=headers, json=data_rmse)
            if response_rmse.status_code == 200:
                st.success("RMSE, graphique et données envoyés avec succès !")
            else:
                st.error(f"Erreur lors de l'envoi du RMSE: {response_rmse.status_code}")
                st.text(f"Contenu de la réponse brute: {response_rmse.text}")

            response_rmse_history = requests.get(url_rmse_history, headers=headers, params=params)
            if response_rmse_history.status_code == 200:
                st.success("Historique des RMSE récupéré avec succès !")

                with col2: 
                    df = pd.DataFrame(response_rmse_history.json()["rmse_history"])
              
                    # Extraire les valeurs de RMSE et les identifiants des runs
                    rmse_values = [entry["rmse"] for entry in df["metrics"]]

                    # Créer le bar graphe
                    plt.figure(figsize=(10, 6))
                    plt.bar(df["run_id"][::-1], rmse_values[::-1], color='skyblue')
                    plt.xlabel("Run ID")
                    plt.ylabel("RMSE")
                    plt.title("RMSE par Run")
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()

                    st.pyplot(plt)

                with col3:

                    avg_execute_time = response_rmse_history.json()['average_execute_time']

                    st.write(f"Temps moyen d'execution des dernière prédictions : {round(avg_execute_time, 2)} s")

                    df = pd.DataFrame(response_rmse_history.json()["rmse_history"])

                    # Extraire les valeurs de temps et les identifiants des runs
                    temps_exec = [entry["temps_exec"] for entry in df["metrics"]]

                    # Créer la courbe
                    plt.figure(figsize=(10, 6))
                    plt.plot(df["run_id"][::-1], temps_exec[::-1], marker='o', linestyle='-', color='red', linewidth=2.5)
                    plt.xlabel("Run ID")
                    plt.ylabel("Temps d'exec.")
                    plt.title("Temps d'execution des dernières predictions")
                    plt.xticks(rotation=45, ha='right')
                    plt.ylim(0)  # Définit le minimum de l'axe Y à 0
                    plt.grid(True)  # Ajoute une grille pour faciliter la lecture des valeurs
                    plt.tight_layout()

                    # Afficher la courbe dans Streamlit
                    st.pyplot(plt)
            else:
                st.error(f"Erreur lors de la récupération de l'historique des RMSE: {response_rmse_history.status_code}")
                st.text(f"Contenu de la réponse brute: {response_rmse_history.text}")

        except ValueError as e:
            st.error("Erreur lors de la tentative de décoder la réponse en JSON:")
            st.text(e)
            st.text(f"Contenu de la réponse brute: {response_predict.text}")
    else:
        st.error(f"Erreur lors de la requête de prédiction: {response_predict.status_code}")
        st.text(f"Contenu de la réponse brute: {response_predict.text}")

    if response_rmse_history.json()["average_rmse"] > 20:
        message(response_rmse_history.json()["average_rmse"])

def authentication_form():
    st.title("Authentification")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        url_login = 'http://localhost:5100/login'
        auth_data = {'username': username, 'password': password}
        response_login = requests.post(url_login, json=auth_data)
        if response_login.status_code == 200:
            token = response_login.json()['token']
            st.success("Authentification réussie")
            # Stocker le jeton dans la session
            st.session_state.token = token
        else:
            st.error(f"Erreur d'authentification: {response_login.status_code}")
            st.text(f"Contenu de la réponse brute: {response_login.text}")

def training_form():
    st.title(f"Entraînement du modèle au {st.session_state.selected_date}")
    df = load_data()

    # Sélectionner uniquement les colonnes nécessaires
    df = df[['date', 'Effectif debout', 'Effectif couche']]
    
    # S'assurer que la colonne 'date' est au format datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Supprimer les valeurs NaT
    df = df.dropna(subset=['date'])

    if st.button("Entraîner le modèle"):
        # Utiliser la date sélectionnée stockée dans la session
        selected_date = st.session_state.get('selected_date', None)
        if not selected_date:
            st.error("Veuillez sélectionner une date.")
            return
        
        # Filtrer pour inclure seulement les données des 5 premiers jours à partir de selected_date
        day_start = pd.to_datetime(selected_date) - pd.Timedelta(days=3)
        df = df[(df['date'] >= day_start) & (df['date'] < day_start + pd.Timedelta(days=5))]
        
        # Conversion de la colonne 'date' en string pour l'affichage
        df['date'] = df['date'].astype(str)
        
        # Appel à la fonction d'entraînement du modèle
        train(df)
        
        st.write("Modèle entraîné avec les données des 5 premiers jours à partir de", selected_date)

def prediction_form():
    st.title("Prédiction SARIMAX (En production)")
    df = load_data()

    # Sélectionner uniquement les colonnes nécessaires
    df = df[['date', 'Effectif debout', 'Effectif couche']]
    
    # S'assurer que la colonne 'date' est au format datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Supprimer les valeurs NaT
    df = df.dropna(subset=['date'])
    
    # Ajouter une listbox de dates et trier les dates dans l'ordre croissant
    unique_dates = sorted(df['date'].dt.date.unique())
    unique_dates = unique_dates[2:-2]
    selected_date = st.selectbox('Sélectionnez une date pour commencer l\'entraînement', unique_dates, key='training_date')

    if selected_date:
        st.session_state.selected_date = selected_date

    # Utiliser la date stockée dans la session ou demander de sélectionner une nouvelle date
    selected_date = st.session_state.get('selected_date', None)
    if selected_date is None:
        unique_dates = sorted(df['date'].dt.date.unique())
        selected_date = st.selectbox('Sélectionnez une date pour effectuer une prédiction', unique_dates, key='prediction_date')
        if selected_date:
            st.session_state.selected_date = selected_date
    else:
        st.write(f"Date sélectionnée pour la prédiction : {selected_date}")
    
    if st.button("Prédire avec le modèle"):
        # Utiliser la date sélectionnée stockée dans la session
        selected_date = st.session_state.get('selected_date', None)
        if not selected_date:
            st.error("Veuillez sélectionner une date.")
            return
        
        # Définir l'intervalle de prédiction basé sur selected_date
        day_start = pd.to_datetime(selected_date)
        day_end = day_start + pd.Timedelta(days=1)
        
        # Filtrer les données pour l'intervalle de prédiction
        filtered_df_ = df[(df['date'] >= day_start) & (df['date'] <= day_end)]
        filtered_df_.set_index('date', inplace=True)
        filtered_df = filtered_df_.resample('15T').sum()
        
        # Créer des DataFrames pour le ratio et la médiane
        ratio_df = filtered_df.copy()
        median_df = filtered_df_.resample('15T').median()
        
        # Appel à la fonction de prédiction
        prediction(filtered_df, ratio_df, median_df)
        
        # st.write("Prédiction réalisée pour la journée du", selected_date)

def main():
    st.sidebar.title("Navigation")
    option = st.sidebar.radio("Sélectionnez une page", ('Authentification', 'Prédiction', 'Entraînement'))

    if option == 'Authentification':
        authentication_form()
    elif option == 'Entraînement':
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
        else:
            training_form()
    elif option == 'Prédiction':
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
        else:
            prediction_form()

if __name__ == "__main__":
    main()
