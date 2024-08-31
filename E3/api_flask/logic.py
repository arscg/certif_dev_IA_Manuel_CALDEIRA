# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 13:47:14 2024

@author: arsca
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error
import mlflow
import os
import logging
from email_utils import send_email
from models import DataCleaner, SARIMAXModel, CustomModel


def get_rmse_history(client, experiment_id, limit, version, include_artifacts):
    all_runs = []
    next_page_token = None

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
            next_page_token = runs.token
        else:
            break

    if version:
        all_runs = [run for run in all_runs if run.data.params.get('model_version') == version]

    all_runs.sort(key=lambda x: x.info.start_time, reverse=True)
    all_runs = all_runs[:limit]

    rmse_values = []
    rmse_history = []
    for run in all_runs:
        run_data = {
            "run_id": run.info.run_id,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time,
            "metrics": run.data.metrics,
            "params": run.data.params,
            "artifacts": {}
        }

        if "rmse" in run.data.metrics:
            rmse_values.append(run.data.metrics["rmse"])

        if include_artifacts:
            def list_all_artifacts(run_id, path=""):
                artifacts = []
                for artifact in client.list_artifacts(run_id, path):
                    if artifact.is_dir:
                        artifacts += list_all_artifacts(run_id, artifact.path)
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

    average_rmse = sum(rmse_values) / len(rmse_values) if rmse_values else None

    warning = 'None'

    if average_rmse and average_rmse > 25:
        send_email(average_rmse)
        warning = "RMSE_ALARM - send mail"

    return {
        "warning": warning,
        "rmse_history": rmse_history,
        "average_rmse": average_rmse
    }

def train_model(data):
    df = pd.DataFrame(data)
    
    cleaner = DataCleaner()
    df_cleaned = cleaner.transform(df)
    
    max_date = df_cleaned['date'].max()
    cutoff_date = max_date - pd.Timedelta(days=2)
    train_data = df_cleaned[df_cleaned['date'] <= cutoff_date]
    validation_data = df_cleaned[df_cleaned['date'] > cutoff_date]
    
    num_days_train = (train_data['date'].max() - train_data['date'].min()).days
    num_days_test = (validation_data['date'].max() - validation_data['date'].min()).days
    
    sarimax_model = SARIMAXModel()
    pipeline = Pipeline([('cleaner', cleaner), ('sarimax', sarimax_model)], verbose=True)
    
    pipeline.fit(train_data)

    custom_model = CustomModel(pipeline)
    
    predictions = sarimax_model.predict(validation_data)
    actuals = validation_data.set_index('date')['ratio_debout']
    
    validation_rmse = np.sqrt(mean_squared_error(actuals, predictions))
    
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
    plt.savefig(plot_file)
    plt.close()
    
    train_data_file = 'train_data.csv'
    validation_data_file = 'validation_data.csv'
    train_data.to_csv(train_data_file, index=False)
    validation_data.to_csv(validation_data_file, index=False)

    with mlflow.start_run() as run:
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=custom_model
        )
        
        mlflow.log_param("order", sarimax_model.order)
        mlflow.log_param("seasonal_order", sarimax_model.seasonal_order)
        mlflow.log_param("num_data_points", len(df_cleaned))
        mlflow.log_param("num_days_train", num_days_train)
        mlflow.log_param("num_days_test", num_days_test + 1)
        mlflow.log_metric("train_rmse", -sarimax_model.score(train_data, train_data['ratio_debout']))
        mlflow.log_metric("validation_rmse", validation_rmse)
        
        mlflow.log_artifact(plot_file)
        mlflow.log_artifact(train_data_file)
        mlflow.log_artifact(validation_data_file)
        
        run_id = run.info.run_id
        mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/model",
            name="SARIMAXModel"
        )
    
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
        predictions_json = predictions_df.to_json(orient='records', date_format='iso')

    except Exception as e:    
        logging.error(f"Error during training: {e}")

    return predictions_json,validation_rmse, run_id

def predict_model(data):
    df = pd.DataFrame(data)

    cleaner = DataCleaner()
    df_cleaned = cleaner.transform(df)
    
    model_name = 'SARIMAXModel'
    client = mlflow.tracking.MlflowClient()
    logged_model = f"models:/{model_name}/Production"
    
    model = mlflow.pyfunc.load_model(logged_model)
    
    with mlflow.start_run() as run:
        model_version = client.get_latest_versions(model_name, stages=["Production"])[0].version
        predictions = model.predict(df_cleaned)
        
        predictions_df = predictions.to_frame(name='Valeurs')
        predictions_df.reset_index(inplace=True)
        predictions_df.columns = ['Date', 'Valeurs']
        predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])
        predictions_json = predictions_df.to_json(orient='records', date_format='iso')
        
        mlflow.log_param("num_data_points", len(df_cleaned))
    
    return predictions_json, model_name, model_version

def log_rmse(data):
    rmse_value = data.get('rmse', None)
    model_name = data.get('model', None)
    model_version = data.get('version', None)
    ground_truth = data.get('ground_truth', [])
    predictions = data.get('predictions', [])

    if rmse_value is None:
        raise ValueError("RMSE value not provided")

    model_version_param = f"{model_name}_V{model_version}"

    experiment_name = "predict_experience"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    
    with mlflow.start_run(experiment_id=experiment_id, run_name="rmse_artifact_run"):
        mlflow.log_metric("rmse", rmse_value)
        mlflow.log_param("model_version", model_version_param)

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

        graphique_data = data.get('graphique', None)
        if graphique_data:
            graphique_file = 'graphique_plot.png'
            with open(graphique_file, 'wb') as f:
                f.write(graphique_data.encode('latin1'))
            mlflow.log_artifact(graphique_file)
            os.remove(graphique_file)

    return {"message": "RMSE, graphique et datasets logués avec succès"}

def fetch_rmse_history(client, experiment_id, limit, version, include_artifacts):
    return get_rmse_history(client, experiment_id, limit, version, include_artifacts)

