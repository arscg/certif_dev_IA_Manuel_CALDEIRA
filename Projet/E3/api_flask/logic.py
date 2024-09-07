import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import mlflow
import os
import time
import logging
from email_utils import send_email
from models import DataCleaner, SARIMAXModel, CustomModel

# Fonction pour récupérer l'historique des RMSE (Root Mean Squared Error)
def get_rmse_history(client, experiment_id, limit, version, include_artifacts):
    all_runs = []  # Liste pour stocker tous les runs
    next_page_token = None

    # Boucle pour récupérer tous les runs pour un ID d'expérience donné
    while True:
        runs = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string="",
            run_view_type=mlflow.entities.ViewType.ACTIVE_ONLY,
            max_results=100,
            page_token=next_page_token
        )
        all_runs.extend(runs)
        if runs.token:
            next_page_token = runs.token  # Passe à la page suivante s'il y en a une
        else:
            break

    # Filtre les runs par version de modèle si spécifié
    if version:
        all_runs = [run for run in all_runs if run.data.params.get('model_version') == version]

    # Trie les runs par ordre décroissant de temps de début
    all_runs.sort(key=lambda x: x.info.start_time, reverse=True)
    all_runs = all_runs[:limit]  # Limite le nombre de runs
        
    rmse_values = []  # Liste pour stocker les valeurs de RMSE
    time_values = []  # Liste pour stocker les valeurs de temps d'execution
    rmse_history = []  # Liste pour stocker l'historique de RMSE
    for run in all_runs:
        run_data = {
            "run_id": run.info.run_id,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time,
            "metrics": run.data.metrics,
            "params": run.data.params,
            "artifacts": {}
        }

        # Ajoute la valeur RMSE si elle est disponible
        if "rmse" in run.data.metrics:
            rmse_values.append(run.data.metrics["rmse"])
        
        # Ajoute la valeur RMSE si elle est disponible
        if "temps_exec" in run.data.metrics:
            time_values.append(run.data.metrics["temps_exec"])

        # Inclut les artefacts si demandé
        if include_artifacts:
            def list_all_artifacts(run_id, path=""):
                artifacts = []
                for artifact in client.list_artifacts(run_id, path):
                    if artifact.is_dir:
                        artifacts += list_all_artifacts(run_id, artifact.path)  # Récursion pour lister les artefacts dans les sous-dossiers
                    else:
                        artifacts.append(artifact)
                return artifacts

            artifact_list = list_all_artifacts(run.info.run_id)
            for artifact in artifact_list:
                if artifact.path.endswith('ground_truth.csv') or artifact.path.endswith('predictions.csv'):
                    artifact_uri = client.download_artifacts(run.info.run_id, artifact.path)
                    artifact_df = pd.read_csv(artifact_uri)
                    run_data["artifacts"][artifact.path] = artifact_df.to_dict(orient='records')

        rmse_history.append(run_data)

    # Calcule la moyenne des RMSE
    average_rmse = sum(rmse_values) / len(rmse_values) if rmse_values else None

    average_time_values = sum(time_values) / len(time_values) if time_values else None

    warning = 'None'

    # Envoie un email d'alerte si le RMSE moyen dépasse 25
    if average_rmse and average_rmse > 25:
        send_email(average_rmse)
        warning = "RMSE_ALARM - send mail"

    return {
        "warning": warning,
        "rmse_history": rmse_history,
        "average_rmse": average_rmse,
        "execute_time": time_values,
        "average_execute_time": average_time_values
    }

# Fonction pour entraîner un modèle
def train_model(data):
    df = pd.DataFrame(data)  # Convertit les données en DataFrame
    
    cleaner = DataCleaner()  # Initialise le nettoyeur de données
    df_cleaned = cleaner.transform(df)  # Nettoie les données
    
    max_date = df_cleaned['date'].max()  # Trouve la date maximale dans les données nettoyées
    cutoff_date = max_date - pd.Timedelta(days=2)  # Définit la date de coupure pour séparer les données de formation et de validation
    train_data = df_cleaned[df_cleaned['date'] <= cutoff_date]  # Données de formation
    validation_data = df_cleaned[df_cleaned['date'] > cutoff_date]  # Données de validation
    
    num_days_train = (train_data['date'].max() - train_data['date'].min()).days  # Nombre de jours dans les données de formation
    num_days_test = (validation_data['date'].max() - validation_data['date'].min()).days  # Nombre de jours dans les données de validation
    
    sarimax_model = SARIMAXModel()  # Initialise le modèle SARIMAX
    pipeline = Pipeline([('cleaner', cleaner), ('sarimax', sarimax_model)], verbose=True)  # Crée un pipeline avec le nettoyeur et le modèle SARIMAX
    
    pipeline.fit(train_data)  # Entraîne le pipeline sur les données de formation

    custom_model = CustomModel(pipeline)  # Crée un modèle personnalisé avec le pipeline
    
    
    predictions = sarimax_model.predict(validation_data)  # Fait des prédictions sur les données de validation
    actuals = validation_data.set_index('date')['ratio_debout']  # Obtient les valeurs réelles pour comparer
    
    validation_rmse = np.sqrt(mean_squared_error(actuals, predictions))  # Calcule le RMSE pour la validation
    
    # Crée un graphique des résultats
    plt.figure(figsize=(14, 7))
    plt.plot(train_data['date'], train_data['ratio_debout'], color='blue', label='Entraînement (5 jours)')
    plt.plot(validation_data['date'], actuals, color='green', label='Vérité Terrain (jours 6 et 7)')
    plt.plot(validation_data['date'], predictions, color='yellow', label='Prédictions (jours 6 et 7)')
    plt.xlabel('Date et Heure')
    plt.ylabel('Ratio Debout (%)')
    plt.title('Prédictions SARIMAX du Ratio Debout')
    plt.legend()
    plt.grid(True)
        
    plot_file = 'predictions_plot.png'
    plt.savefig(plot_file)  # Sauvegarde le graphique
    plt.close()
    
    train_data_file = 'train_data.csv'
    validation_data_file = 'validation_data.csv'
    train_data.to_csv(train_data_file, index=False)  # Sauvegarde les données d'entraînement
    validation_data.to_csv(validation_data_file, index=False)  # Sauvegarde les données de validation

    with mlflow.start_run() as run:  # Démarre un nouveau run MLflow
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=custom_model
        )
        
        # Logue les paramètres et les métriques du modèle
        mlflow.log_param("order", sarimax_model.order)
        mlflow.log_param("seasonal_order", sarimax_model.seasonal_order)
        mlflow.log_param("num_data_points", len(df_cleaned))
        mlflow.log_param("num_days_train", num_days_train)
        mlflow.log_param("num_days_test", num_days_test + 1)
        mlflow.log_metric("train_rmse", -sarimax_model.score(train_data, train_data['ratio_debout']))
        mlflow.log_metric("validation_rmse", validation_rmse)
        
        mlflow.log_artifact(plot_file)  # Logue le fichier du graphique
        mlflow.log_artifact(train_data_file)  # Logue les données d'entraînement
        mlflow.log_artifact(validation_data_file)  # Logue les données de validation
        
        run_id = run.info.run_id  # Récupère l'ID du run
        mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/model",
            name="SARIMAXModel"
        )
    
    # Supprime les fichiers temporaires créés
    if os.path.exists(plot_file):
        os.remove(plot_file)
    if os.path.exists(train_data_file):
        os.remove(train_data_file)
    if os.path.exists(validation_data_file):
        os.remove(validation_data_file)
    
    try:
        print(validation_data)    
            
        predictions_df = validation_data[["date", 'ratio_debout']]
        predictions_df.reset_index(inplace=True)
        print(predictions_df.columns)  # Cela montrera ['index', 'date', 'ratio_debout']
        predictions_df.columns = ['Index', 'Date', 'Valeurs']
        predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])
        predictions_json = predictions_df.to_json(orient='records', date_format='iso')  # Convertit les prédictions en JSON

    except Exception as e:    
        logging.error(f"Error during training: {e}")  # Logue l'erreur si elle se produit

    return predictions_json, validation_rmse, run_id  # Retourne les prédictions, le RMSE et l'ID du run

# Fonction pour prédire à partir d'un modèle existant
def predict_model(data):

    start_time = time.time()  # Démarre le chronomètre
    
    df = pd.DataFrame(data)  # Convertit les données en DataFrame

    cleaner = DataCleaner()  # Initialise le nettoyeur de données
    df_cleaned = cleaner.transform(df)  # Nettoie les données
    
    model_name = 'SARIMAXModel'  # Nom du modèle enregistré
    client = mlflow.tracking.MlflowClient()
    logged_model = f"models:/{model_name}/Production"  # Récupère le modèle en production
    
    model = mlflow.pyfunc.load_model(logged_model)  # Charge le modèle
    
    with mlflow.start_run() as run:  # Démarre un nouveau run MLflow
        model_version = client.get_latest_versions(model_name, stages=["Production"])[0].version  # Récupère la version du modèle
        
        predictions = model.predict(df_cleaned)  # Fait des prédictions sur les nouvelles données
        
        predictions_df = predictions.to_frame(name='Valeurs')  # Crée un DataFrame des prédictions
        predictions_df.reset_index(inplace=True)
        predictions_df.columns = ['Date', 'Valeurs']
        predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])
        predictions_json = predictions_df.to_json(orient='records', date_format='iso')  # Convertit les prédictions en JSON
        
        end_time = time.time()  # Arrête le chronomètre
        prediction_time = end_time - start_time  # Calcule le temps de prédiction

        mlflow.log_param("num_data_points", len(df_cleaned))  # Logue le nombre de points de données
        mlflow.log_metric("prediction_time", prediction_time)  # Logue le temps de prédiction
    
    return predictions_json, model_name, model_version, prediction_time  # Retourne les prédictions, le nom du modèle, la version et le temps de prédiction

# Fonction pour loguer le RMSE
def log_rmse(data):
    rmse_value = data.get('rmse', None)  # Récupère la valeur du RMSE
    model_name = data.get('model', None)  # Récupère le nom du modèle
    model_version = data.get('version', None)  # Récupère la version du modèle
    ground_truth = data.get('ground_truth', [])  # Récupère les valeurs réelles
    predictions = data.get('predictions', [])  # Récupère les prédictions
    prediction_time = data.get('exec_time', [])  # Récupère les temps d'executtion prédiction

    if rmse_value is None:
        raise ValueError("RMSE value not provided")  # Lève une erreur si le RMSE n'est pas fourni

    model_version_param = f"{model_name}_V{model_version}"  # Formate la version du modèle

    experiment_name = "predict_experience"  # Nom de l'expérience MLflow
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)  # Crée une nouvelle expérience si elle n'existe pas
    else:
        experiment_id = experiment.experiment_id  # Récupère l'ID de l'expérience existante
    
    with mlflow.start_run(experiment_id=experiment_id, run_name="rmse_artifact_run"):
        mlflow.log_metric("rmse", rmse_value)  # Logue la métrique RMSE
        mlflow.log_param("model_version", model_version_param)  # Logue la version du modèle
        mlflow.log_metric("temps_exec", prediction_time)  # Logue la métrique RMSE

        # Logue les fichiers CSV pour les vérités terrain et les prédictions si fournis
        if ground_truth:
            ground_truth_df = pd.DataFrame(ground_truth)
            ground_truth_df['date'] = pd.to_datetime(ground_truth_df['date'])
            ground_truth_file = 'ground_truth.csv'
            ground_truth_df.to_csv(ground_truth_file, index=False)
            mlflow.log_artifact(ground_truth_file, artifact_path='datasets')
            os.remove(ground_truth_file)
        
        if predictions:
            predictions_df = pd.DataFrame(predictions)
            predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])
            predictions_file = 'predictions.csv'
            predictions_df.to_csv(predictions_file, index=False)
            mlflow.log_artifact(predictions_file, artifact_path='datasets')
            os.remove(predictions_file)

        # Logue le graphique si fourni
        graphique_data = data.get('graphique', None)
        if graphique_data:
            graphique_file = 'graphique_plot.png'
            with open(graphique_file, 'wb') as f:
                f.write(graphique_data.encode('latin1'))
            mlflow.log_artifact(graphique_file)
            os.remove(graphique_file)

    return {"message": "RMSE, graphique et datasets logués avec succès"}

# Fonction pour récupérer l'historique des RMSE (Alias de get_rmse_history)
def fetch_rmse_history(client, experiment_id, limit, version, include_artifacts):
    return get_rmse_history(client, experiment_id, limit, version, include_artifacts)
