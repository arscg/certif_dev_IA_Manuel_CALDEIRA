# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:01:50 2024

@author: arsca
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import mean_squared_error
from mlflow import pyfunc

class DataCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        df = X.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['jour'] = df['date'].dt.date
        df['quart_heure'] = df['date'].dt.floor('15T').dt.time
        grouped = df.groupby(['jour', 'quart_heure'])
        df_aggregated = grouped[['Effectif couche', 'Effectif debout']].median().reset_index()
        df_aggregated['ratio_debout'] = (df_aggregated['Effectif debout'] / (df_aggregated['Effectif debout'] + df_aggregated['Effectif couche'])) * 100
        df_aggregated['date'] = pd.to_datetime(df_aggregated['jour'].astype(str) + ' ' + df_aggregated['quart_heure'].astype(str))
        return df_aggregated

class SARIMAXModel(BaseEstimator):
    def __init__(self, order=(3, 1, 3), seasonal_order=(1, 1, 1, 96)):
        self.order = order
        self.seasonal_order = seasonal_order
        self.model_ = None
    
    def fit(self, X, y=None):
        train_ratio = X.set_index('date')['ratio_debout']
        self.model_ = SARIMAX(train_ratio, order=self.order, seasonal_order=self.seasonal_order)
        self.results_ = self.model_.fit(disp=5, maxiter=200)
        return self
    
    def predict(self, X):
        start_date = X['date'].min()
        end_date = X['date'].max()
        predictions = self.results_.predict(start=start_date, end=end_date)
        return predictions
    
    def score(self, X, y):
        predictions = self.predict(X)
        rmse = np.sqrt(mean_squared_error(y, predictions))
        return -rmse

class CustomModel(pyfunc.PythonModel):
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def predict(self, context, model_input):
        return self.pipeline.predict(model_input)
    
# import pandas as pd
# import cupy as cp
# import numpy as np
# from statsmodels.tsa.statespace.sarimax import SARIMAX
# from sklearn.base import BaseEstimator, TransformerMixin
# from sklearn.metrics import mean_squared_error
# from mlflow import pyfunc

# class DataCleaner(BaseEstimator, TransformerMixin):
#     def fit(self, X, y=None):
#         return self
    
#     def transform(self, X, y=None):
#         df = X.copy()
#         df['date'] = pd.to_datetime(df['date'], errors='coerce')
#         df = df.dropna(subset=['date'])
#         df['jour'] = df['date'].dt.date
#         df['quart_heure'] = df['date'].dt.floor('15T').dt.time
#         grouped = df.groupby(['jour', 'quart_heure'])
#         df_aggregated = grouped[['Effectif couche', 'Effectif debout']].median().reset_index()
#         df_aggregated['ratio_debout'] = (df_aggregated['Effectif debout'] / (df_aggregated['Effectif debout'] + df_aggregated['Effectif couche'])) * 100
#         df_aggregated['date'] = pd.to_datetime(df_aggregated['jour'].astype(str) + ' ' + df_aggregated['quart_heure'].astype(str))
#         return df_aggregated

# class SARIMAXModel(BaseEstimator):
#     def __init__(self, order=(3, 1, 3), seasonal_order=(1, 1, 1, 96)):
#         self.order = order
#         self.seasonal_order = seasonal_order
#         self.model_ = None
    
#     def fit(self, X, y=None):
#         train_ratio = X.set_index('date')['ratio_debout']
#         self.model_ = SARIMAX(train_ratio, order=self.order, seasonal_order=self.seasonal_order)
#         self.results_ = self.model_.fit(disp=5, maxiter=200)
#         return self
    
#     def predict(self, X):
#         start_date = X['date'].min()
#         end_date = X['date'].max()
#         predictions = self.results_.predict(start=start_date, end=end_date)
#         return predictions
    
#     def score(self, X, y):
#         predictions = self.predict(X)
#         # Utilisation de CuPy pour le calcul de RMSE
#         rmse = cp.sqrt(cp.mean((cp.array(y.values) - cp.array(predictions.values)) ** 2)).get()
#         return -rmse

# class CustomModel(pyfunc.PythonModel):
#     def __init__(self, pipeline):
#         self.pipeline = pipeline

#     def predict(self, context, model_input):
#         return self.pipeline.predict(model_input)
