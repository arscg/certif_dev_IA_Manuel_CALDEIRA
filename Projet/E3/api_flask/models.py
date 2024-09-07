import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import mean_squared_error
from mlflow import pyfunc

# Classe pour nettoyer et transformer les données
class DataCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self  # La méthode fit ne fait rien ici, car il n'y a pas de paramètres à ajuster
    
    def transform(self, X, y=None):
        df = X.copy()  # Crée une copie des données pour éviter de modifier l'original
        df['date'] = pd.to_datetime(df['date'], errors='coerce')  # Convertit la colonne 'date' en datetime
        df = df.dropna(subset=['date'])  # Supprime les lignes où la date n'a pas pu être convertie
        df['jour'] = df['date'].dt.date  # Extrait la date sans l'heure
        df['quart_heure'] = df['date'].dt.floor('15T').dt.time  # Regroupe par quart d'heure

        # Regroupe les données par jour et quart d'heure et calcule la médiane
        grouped = df.groupby(['jour', 'quart_heure'])
        df_aggregated = grouped[['Effectif couche', 'Effectif debout']].median().reset_index()

        # Calcule le ratio des personnes debout par rapport à la somme des personnes couchées et debout
        df_aggregated['ratio_debout'] = (df_aggregated['Effectif debout'] / 
                                         (df_aggregated['Effectif debout'] + df_aggregated['Effectif couche'])) * 100

        # Reconstruit la colonne 'date' en combinant le jour et le quart d'heure
        df_aggregated['date'] = pd.to_datetime(df_aggregated['jour'].astype(str) + ' ' + df_aggregated['quart_heure'].astype(str))
        return df_aggregated  # Retourne le DataFrame transformé

# Classe pour le modèle SARIMAX
class SARIMAXModel(BaseEstimator):
    def __init__(self, order=(3, 1, 3), seasonal_order=(1, 1, 1, 96)):
        self.order = order  # Paramètres pour le modèle SARIMA (ordre non saisonnier)
        self.seasonal_order = seasonal_order  # Paramètres pour le modèle saisonnier
        self.model_ = None  # Variable pour stocker le modèle SARIMAX ajusté
    
    def fit(self, X, y=None):
        # Extrait la série temporelle de 'ratio_debout' et la définit comme indexée par la date
        train_ratio = X.set_index('date')['ratio_debout']

        # Crée un modèle SARIMAX avec les ordres spécifiés
        self.model_ = SARIMAX(train_ratio, order=self.order, seasonal_order=self.seasonal_order)

        # Ajuste le modèle aux données
        self.results_ = self.model_.fit(disp=5, maxiter=200)
        
        return self  # Retourne l'objet ajusté
    
    def predict(self, X):
        start_date = X['date'].min()  # Date de début des prédictions
        end_date = X['date'].max()  # Date de fin des prédictions
        predictions = self.results_.predict(start=start_date, end=end_date)  # Fait les prédictions
        return predictions  # Retourne les prédictions
    
    def score(self, X, y):
        predictions = self.predict(X)  # Fait les prédictions sur les données X
        rmse = np.sqrt(mean_squared_error(y, predictions))  # Calcule le RMSE entre les valeurs réelles et les prédictions
        return -rmse  # Retourne le RMSE négatif (car dans sklearn un score plus élevé est meilleur, donc RMSE négatif pour minimisation)

# Classe pour encapsuler le modèle dans MLflow
class CustomModel(pyfunc.PythonModel):
    def __init__(self, pipeline):
        self.pipeline = pipeline  # Pipeline de traitement de données et modèle
    
    def predict(self, context, model_input):
        return self.pipeline.predict(model_input)  # Utilise le pipeline pour faire des prédictions sur les nouvelles données
