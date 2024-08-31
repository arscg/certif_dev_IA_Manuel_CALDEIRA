# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 11:48:20 2023

@author: dsite
"""

import pandas as pd
# import atoti as tt
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base
import streamlit as st
import yaml
from flask import Flask
from threading import Thread
from sqlalchemy.orm import Session as session_orm
from sqlalchemy import text
import random
import math
import logging

# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

allow = None

class DataSource:
    def __init__(self, database_url, table_name):
        self.engine = create_engine(database_url)
        self.table_name = table_name

    def get_table_data(self):
        query = f"SELECT * FROM {self.table_name} LIMIT 100"
        return pd.read_sql_query(query, self.engine)
        
    def get_size_db(self):
        query = f"SELECT COUNT(*) AS total FROM {self.table_name}"
        return pd.read_sql_query(query, self.engine)
    
    def get_min_max_db(self):
        query = f"SELECT MIN(id), MAX(id) FROM {self.table_name}"
        return pd.read_sql_query(query, self.engine)

    def create_samples_db(self):
        
        population = self.calculer_taille_echantillon(self.get_min_max_db()['MAX(id)'].iloc[0], 3.29, 0.5, 0.005)
     
        id_range = self.get_min_max_db()
        
        random_ids = random.sample(range(id_range['MIN(id)'].iloc[0], id_range['MAX(id)'].iloc[0]), population)
        
        drop_query = f"DROP TABLE IF EXISTS {self.table_name}_samples_analyse"
        with self.engine.connect() as connection:
            connection.execute(text(drop_query))
            
        # Create the new table
        create_query = f"""CREATE TABLE {self.table_name}_samples_analyse AS 
                           SELECT * FROM {self.table_name} 
                           WHERE id IN {tuple(random_ids)}"""
       
        with self.engine.connect() as connection:
            connection.execute(text(create_query))
        
    def get_samples_db(self):
        query = f"SELECT * FROM {self.table_name}_samples_analyse"
        return pd.read_sql_query(query, self.engine)

    # Fonction pour calculer la taille de l'échantillon avec correction pour population finie
    def calculer_taille_echantillon(self, N, z_score, p, e):
        """
        Calcule la taille de l'échantillon nécessaire avec correction pour population finie.
        
        :param N: Taille de la population
        :param z_score: Valeur z correspondant au niveau de confiance souhaité
        :param p: Proportion attendue dans la population
        :param e: Marge d'erreur souhaitée
        :return: Taille de l'échantillon nécessaire arrondie au nombre entier supérieur
        """
        # Calculateur du numérateur et du dénominateur selon la formule
        numerateur = N * (z_score**2) * p * (1 - p)
        denominateur = (N - 1) * (e**2) + (z_score**2) * p * (1 - p)
        
        # Calcul de n sans arrondi
        n_non_arrondi = numerateur / denominateur
        
        # Arrondi au nombre entier supérieur
        n = math.ceil(n_non_arrondi)
        
        return n


class Cube_Atoti:
    def __init__(self, db_url, port=65055):
            
        # self.session = tt.Session()
        self.engine = create_engine(db_url)
        self.df = self.create_df()
        self.cube = self.create_atoti_cube()
        # print(self.session.link)

    def create_df(self):
        query = "SELECT x.* FROM animov_stats.table_semple_detection x"
        self.df = pd.read_sql(query, self.engine)
        return self.df

def connection():
    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)
           
    db_info = config['database']
    
    connection_url = URL.create(
    drivername=f"{db_info['type']}+{db_info['driver']}",
    username=db_info['username'],
    password=db_info['password'],
    host=db_info['host'],
    port=db_info['port'],
    database=db_info['database_name']
    )
    
    connection_url_with_password = f"{connection_url.__to_string__(hide_password=False)}"
    
    print("------------------------------------->", connection_url)
    # exit(0)
    
    return connection_url_with_password

@st.cache_resource
def stats_creation():     
    stats = DataSource(str(connection()), 'table_detection_sans_doublons')
    return stats
        
@st.cache_resource
def segment_video():
    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)
           
    return config['repertoire_segments']

# Fonction pour démarrer Flask dans un thread séparé
# @st.cache(allow_output_mutation=True)
@st.cache_resource
def start_flask():
    def run_app():
        app = Flask(__name__)

        @app.route('/')
        def hello_world():
            return 'Hello, World!'

        app.run(port=5000, debug=False)  # Choisissez un port approprié

    flask_thread = Thread(target=run_app)
    flask_thread.start()

