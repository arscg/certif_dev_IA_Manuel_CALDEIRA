from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pandas as pd
import json
import yaml
from itertools import permutations
import numpy as np
import sqlalchemy
from sqlalchemy.engine.url import URL
from sqlalchemy import Table, Column, Integer, BigInteger, MetaData, Index, Text, DECIMAL, text
import statistics
import tracemalloc
import logging
from db_utils import add_user, authenticate_user
from functools import wraps
import sqlite3
import jwt
from collections import defaultdict
from flasgger import Swagger  # Importation de flasgger

# Création d'une instance de l'application Flask.
app = Flask(__name__)

# Configuration de flasgger
swagger = Swagger(app)

# Configuration de la clé secrète et de la base de données
app.config['SECRET_KEY'] = 'd3a6e8b45f8e4c73a9a4f6e7a9c1b2d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0'
DATABASE = 'tokens.db'

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO)

# Ajout d'un utilisateur de test, gestion des exceptions
try:
    add_user('arscg', 'arscg')
except Exception as e:
    logging.error(f"Error adding user: {e}")

@app.route('/login', methods=['POST'])
def login():
    """
    Authentification de l'utilisateur
    ---
    tags:
      - Authentification
    parameters:
      - in: body
        name: auth
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: arscg
            password:
              type: string
              example: arscg
    responses:
      200:
        description: Token généré avec succès
        schema:
          type: object
          properties:
            token:
              type: string
              description: Token JWT
      401:
        description: Authentification échouée
    """
    auth = request.json
    if auth:
        token = authenticate_user(auth['username'], auth['password'], app.config['SECRET_KEY'])
        if token:
            return jsonify({'token': token})
    return jsonify({'message': 'Authentification échouée'}), 401

@app.route('/')
def index():
    return render_template('login.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tokens WHERE token=?", (token,))
                token_data = cursor.fetchone()
                if not token_data:
                    return jsonify({'message': 'Token invalide'}), 401
                expiration = token_data[3]
                if isinstance(expiration, str):
                    expiration = datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S.%f')
                if expiration < datetime.utcnow():
                    return jsonify({'message': 'Token expiré'}), 401
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated

# Lecture du fichier JSON et chargement des données dans une variable.
with open('test.json', 'r') as fichier:
    data_list_reception_INRA_animov = json.load(fichier)
              
# Fonction pour calculer et envoyer les statistiques globales.
def global_stats_data_animov_send(json_, sources):
    try:
        sources = sources.split(',')
    except:
        sources = list(set([item["source_id"] for item in data_list_reception_INRA_animov]))

    colonnes = ['count', 'couche', 'debout', 'mean_score', 'std_score', 'source_id']
    df = pd.DataFrame(columns=colonnes)

    if isinstance(json_, list):
        for item in json_:
            if isinstance(item, dict) and 'stats' in item:
                try:
                    nouvelle_ligne = {
                        'count': item['stats']['count'],
                        'couche': item['stats']['couche'],
                        'debout': item['stats']['debout'],
                        'mean_score': item['stats']['mean']['score'],
                        'std_score': item['stats']['std']['score'],
                        'source_id': item['source_id']
                    }
                except:
                    nouvelle_ligne = {
                        'count': item['stats']['count'],
                        'couche': item['stats']['couche'],
                        'debout': item['stats']['debout'],
                        'mean_score': np.NaN,
                        'std_score': np.NaN,
                        'source_id': item['source_id']
                    }
                df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

    df['count'] = pd.to_numeric(df['count'], errors='coerce')
    df['couche'] = pd.to_numeric(df['couche'], errors='coerce')
    df['debout'] = pd.to_numeric(df['debout'], errors='coerce')

    lst = []

    for src in sources:
        df_filter = df[df['source_id'] == int(src)]
        df_filter = df_filter.describe()

        try:
            _general_stats = {
                'avg_count': df_filter['count'].iloc[1].round(3),
                'std_count': df_filter['count'].iloc[2].round(3),
                'avg_couche': df_filter['couche'].iloc[1].round(3),
                'std_couche': df_filter['couche'].iloc[2].round(3),
                'avg_debout': df_filter['debout'].iloc[1].round(3),
                'std_debout': df_filter['debout'].iloc[2].round(3),
                'avg_all_score': df_filter['mean_score'].iloc[1].round(3),
                'std_mean_all_score': df_filter['std_score'].iloc[1].round(3),
            }
        except:
            _general_stats = {
                'avg_count': df_filter['count'].iloc[1].round(3),
                'std_count': df_filter['count'].iloc[2].round(3),
                'avg_couche': df_filter['couche'].iloc[1].round(3),
                'std_couche': df_filter['couche'].iloc[2].round(3),
                'avg_debout': df_filter['debout'].iloc[1].round(3),
                'std_debout': df_filter['debout'].iloc[2].round(3),
            }

        lst.append({f'source_{src}': _general_stats})

    return lst

# Fonction pour calculer les statistiques des données d'animation des cadres.
def stats_data_animov_frames(json_):
    if isinstance(json_, list):
        for item in json_:
            if isinstance(item, dict) and 'detect' in item:
                df = pd.DataFrame(item['detect'], columns=['id', 'x_min', 'y_min', 'x_max', 'y_max', 'score', 'classe', 'brush', 'eat', 'drink'])
                count_classe_1 = df[df['classe'] == 0].shape[0]
                count_classe_0 = df[df['classe'] == 1].shape[0]

                df['x_min'] = df['x_min'].astype(int)
                df['y_min'] = df['y_min'].astype(int)
                df['x_max'] = df['x_max'].astype(int)
                df['y_max'] = df['y_max'].astype(int)
                df['score'] = df['score'].round(3)

                df = df.drop(columns=['id', 'brush', 'eat', 'drink'])
                df = df.describe()
                df = df.transpose()
                df['std'] = df['std'].round(3)
                df['mean'] = df['mean'].round(3)
                df['25%'] = df['25%'].round(3)
                df['50%'] = df['50%'].round(3)
                df['75%'] = df['75%'].round(3)
                df['count'] = df['count'].astype(int)

                if not df.empty:
                    try:
                        item['stats'] = df.to_dict()
                        cnt = item['stats']['count']['classe']
                        item['stats'].pop("count")
                        item['stats']["count"] = cnt
                        item['stats']["debout"] = count_classe_1
                        item['stats']["couche"] = count_classe_0
                    except:
                        item['stats']["count"] = np.NaN
                        item['stats']["debout"] = np.NaN
                        item['stats']["couche"] = np.NaN

    return json_

def stats_data_animov_frames_lite(json_):
    if isinstance(json_, list):
        for item in json_:
            if isinstance(item, dict) and 'detect' in item:
                df = pd.DataFrame(item['detect'], columns=['id', 'x_min', 'y_min', 'x_max', 'y_max', 'score', 'classe', 'brush', 'eat', 'drink'])
                count_classe_1 = df[df['classe'] == 0].shape[0]
                count_classe_0 = df[df['classe'] == 1].shape[0]

                if not df.empty:
                    try:
                        item['stats'] = {}
                        item['stats']["count"] = count_classe_1 + count_classe_0
                        item['stats']["debout"] = count_classe_1
                        item['stats']["couche"] = count_classe_0
                    except:
                        item['stats']["count"] = np.NaN
                        item['stats']["debout"] = np.NaN
                        item['stats']["couche"] = np.NaN

    return json_

# Fonction pour filtrer les données en fonction des sources spécifiées.
def filter_data_anomov(sources):
    global data_list_reception_INRA_animov
    try:
        sources = sources.split(',')
    except:
        sources = list(set([item["source_id"] for item in data_list_reception_INRA_animov]))

    filtered_data = []

    for src in sources:
        for data in data_list_reception_INRA_animov:
            if sources is not None and data.get('source_id') != int(src):
                continue
            filtered_data.append(data)

    return filtered_data

# Fonction pour obtenir la minute actuelle à partir d'un timestamp
def get_minute(timestamp):
    date_from_timestamp = datetime.fromtimestamp(timestamp)
    return date_from_timestamp.minute

# Initialisation d'un dictionnaire pour stocker les agrégations
dict_resultat = defaultdict(lambda: {
                                        'total': 0, 
                                        'couche': 0, 
                                        'debout': 0, 
                                        'nb_frames': 0, 
                                        'max_total' : 0,
                                        'max_couche' : 0,
                                        'max_debout' : 0,
                                        'min_total' : 10000,
                                        'min_couche' : 10000,
                                        'min_debout' : 10000,
                                        'std_total' : 0,
                                        'std_couche' : 0,
                                        'std_debout' : 0,
                                    })

# Variable pour garder la trace de la dernière minute traitée
last_minute = None

lst_dict_resultat = []

database = None

# Lecture de la clé secrète et de la configuration de la base de données
with open("config.yaml", "r") as file:
  config = yaml.safe_load(file)
  if config["SECRET_KEY"]:         
    app.config['SECRET_KEY'] = config["SECRET_KEY"]
    database = config['database']["database_name"]

# Classe pour la gestion de la base de données
class DatabaseManager:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(self.connection())

    def connection(self):
        with open('config.yaml', 'r') as file:
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
        
        print("------------------------------------->", connection_url)
        
        return connection_url
    
    def query_get_sources(self):
        
        sql_query = f"""
        select source from {database}.table_chevres_heures group by source
        """        
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        
        return df

    def query_get_dates(self):

        sql_query = f"""
        select jour as dates from {database}.table_chevres_heures group by jour
        """        
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)

        return df

    def query_get_chevres_heure(self):
        sql_query = f"""
        SELECT jour, source, heure, avg(brush) as brush, avg(drink) as drink, avg(eat) as eat, avg(class_0) as class_0, avg(class_1) as class_1
        FROM {database}.table_chevres_heures 
        group by jour, source, heure
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df

    def query_get_chevres_minutes(self):
        sql_query = f"""
        SELECT jour, source, minutes, heure, avg(brush) as brush, avg(drink) as drink, avg(eat) as eat, avg(class_0) as class_0, avg(class_1) as class_1
        FROM {database}.table_chevres_minute 
        group by jour, source, minutes, heure
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df
    
    def query_set_stat_minutes(self, data):

        metadata = MetaData()

        ma_table_stats = Table('table_chevres_minute_serveur_v2', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('timestamp', BigInteger, nullable=False),
            Column('source', Integer, nullable=False),
            Column('total', Integer, nullable=False),
            Column('couche', Integer, nullable=False),
            Column('debout', Integer, nullable=False),

            Column('max_total', Integer, nullable=False),
            Column('max_couche', Integer, nullable=False),
            Column('max_debout', Integer, nullable=False),

            Column('min_total', Integer, nullable=False),
            Column('min_couche', Integer, nullable=False),
            Column('min_debout', Integer, nullable=False),

            Column('std_total', DECIMAL(6, 3), nullable=False),
            Column('std_couche', DECIMAL(6, 3), nullable=False),
            Column('std_debout', DECIMAL(6, 3), nullable=False),

            Column('Q1_total', Integer, nullable=False),
            Column('Q1_couche', Integer, nullable=False),
            Column('Q1_debout', Integer, nullable=False),

            Column('Q2_total', Integer, nullable=False),
            Column('Q2_couche', Integer, nullable=False),
            Column('Q2_debout', Integer, nullable=False),

            Column('Q3_total', Integer, nullable=False),
            Column('Q3_couche', Integer, nullable=False),
            Column('Q3_debout', Integer, nullable=False),

            Column('mode_total', Text, nullable=True),
            Column('mode_couche', Text, nullable=True),
            Column('mode_debout', Text, nullable=True),

            Column('nb_frames', Integer, nullable=False)
        )

        Index('idx_timestamp', ma_table_stats.c.timestamp)
        Index('idx_source', ma_table_stats.c.source)

        metadata.create_all(self.engine)

        timestamp_entier = int(data['timestamp'])

        insert_data = {
            'timestamp': timestamp_entier,
            'source': data['source'],
            'total': data['result']['total'],
            'couche': data['result']['couche'],
            'debout': data['result']['debout'],

            'max_total': data['result']['max_total'],
            'max_couche': data['result']['max_couche'],
            'max_debout': data['result']['max_debout'],

            'min_total': data['result']['min_total'],
            'min_couche': data['result']['min_couche'],
            'min_debout': data['result']['min_debout'],

            'std_total': data['result']['std_total'],
            'std_couche': data['result']['std_couche'],
            'std_debout': data['result']['std_debout'],

            'Q1_total': data['result']['quartiles_total'][0],
            'Q1_couche': data['result']['quartiles_couche'][0],
            'Q1_debout': data['result']['quartiles_debout'][0],
            
            'Q2_total': data['result']['quartiles_total'][1],
            'Q2_couche': data['result']['quartiles_couche'][1],
            'Q2_debout': data['result']['quartiles_debout'][1],

            'Q3_total': data['result']['quartiles_total'][2],
            'Q3_couche': data['result']['quartiles_couche'][2],
            'Q3_debout': data['result']['quartiles_debout'][2],

            'mode_total': json.dumps(data['result']['mode_total']) if data['result']['mode_total'] is not None else json.dumps([]),
            'mode_couche': json.dumps(data['result']['mode_couche']) if data['result']['mode_couche'] is not None else json.dumps([]),
            'mode_debout': json.dumps(data['result']['mode_debout']) if data['result']['mode_debout'] is not None else json.dumps([]),
        
            'nb_frames': data['result']['nb_frames']
        }

        with self.engine.connect() as connection:
            connection.execute(ma_table_stats.insert(), insert_data)
            connection.commit()
            print(f"Send data minutes source {data['source']}!!!")

    
    def query_set_stat_hours(self, data):
        
        metadata = MetaData()

        ma_table_stats = Table('table_chevres_minute_serveur', metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('timestamp', BigInteger, nullable=False),
            Column('source', Integer, nullable=False),
            Column('total', Integer, nullable=False),
            Column('couche', Integer, nullable=False),
            Column('debout', Integer, nullable=False),
            Column('nb_frames', Integer, nullable=False)
        )

        Index('idx_timestamp', ma_table_stats.c.timestamp)
        Index('idx_source', ma_table_stats.c.source)

        metadata.create_all(self.engine)

        timestamp_entier = int(data['timestamp'])

        insert_data = {
            'timestamp': timestamp_entier,
            'source': data['source'],
            'total': data['result']['total'],
            'couche': data['result']['couche'],
            'debout': data['result']['debout'],
            'nb_frames': data['result']['nb_frames']
        }

        with self.engine.connect() as connection:
            connection.execute(ma_table_stats.insert(), insert_data)
            connection.commit()
            print(f"Send data minutes source {data['source']}!!!")

    def query_get_stats_minute(self):
        sql_query = """
        select * from ANIMOV.vue_chevres_derniere_minute_v2 vcdh
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df
    
    def query_get_stats_heure(self):
        sql_query_procedure = text("CALL `ANIMOV`.`ConsoliderResultatsEcartType`();")
        try:
            with self.engine.begin() as conn:
                conn.execute(sql_query_procedure)
        except Exception as e:
            print(f"Erreur lors de l'exécution de la procédure stockée: {e}")
            return pd.DataFrame()
        
        sql_query_results = "SELECT * FROM `ANIMOV`.`ResultatsConsolides`;"
        df = pd.read_sql(sql_query_results, self.engine)
        
        return df
    
    def query_get_serie_jour(self):
        sql_query = """
        select * from ANIMOV.vue_chevres_serie_jour
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df
    
    def query_get_serie_heure(self):
        sql_query = """
        select * from ANIMOV.vue_chevres_serie_heure
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df
    
    def query_get_serie_last_jour(self):
        sql_query = """
        select * from ANIMOV.vue_chevre_derniere_jour_last
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df
    
    def query_get_serie_last_heure(self):
        sql_query = """
        select * from ANIMOV.vue_chevre_derniere_heure_last
        """
        with self.engine.connect() as connection:
            df = pd.read_sql(sql_query, connection)
        return df

db_manager = DatabaseManager()

# Définition d'une route Flask '/receive_data_animov' avec la méthode POST.
@app.route('/receive_data_animov', methods=['POST'])
def receive_data_animov():
   
    global data_list_reception_INRA_animov  # Référence à la variable globale.
    global last_minute, lst_dict_resultat

    timestamp = datetime.now().isoformat()
    data_list_reception_INRA_animov = request.json

    for frm in data_list_reception_INRA_animov:
        if 'date' in frm:
            datehour = datetime.strptime(frm['date'][0], "%Y-%m-%d %H:%M:%S.%f")
            timestamp = datehour.timestamp()

            current_minute = get_minute(timestamp)

            id = frm['source_id']
            smm = sum(int(chv[6]) for chv in frm['detect'])
            total = len(frm['detect'])
            
            if 'lst_totals' not in dict_resultat[id]:
                dict_resultat[id]['lst_totals'] = []
            if 'lst_couches' not in dict_resultat[id]:
                dict_resultat[id]['lst_couches'] = []
            if 'lst_debouts' not in dict_resultat[id]:
                dict_resultat[id]['lst_debouts'] = []

            dict_resultat[id]['lst_totals'].append(total)
            dict_resultat[id]['lst_couches'].append(smm)
            dict_resultat[id]['lst_debouts'].append(total - smm)

            if last_minute is not None and current_minute != last_minute:    
                for key in dict_resultat.keys():
                    
                    try:
                        ecart_type_total = statistics.stdev(dict_resultat[key]['lst_totals'])
                        ecart_type_couche = statistics.stdev(dict_resultat[key]['lst_couches'])
                        ecart_type_debout = statistics.stdev(dict_resultat[key]['lst_debouts'])
                        quartiles_total = statistics.quantiles(dict_resultat[key]['lst_totals'], n=4, method='inclusive')
                        quartiles_couche = statistics.quantiles(dict_resultat[key]['lst_couches'], n=4, method='inclusive')
                        quartiles_debout = statistics.quantiles(dict_resultat[key]['lst_debouts'], n=4, method='inclusive')
                        mode_total = statistics.multimode(dict_resultat[key]['lst_totals'])
                        mode_couche = statistics.multimode(dict_resultat[key]['lst_couches'])
                        mode_debout = statistics.multimode(dict_resultat[key]['lst_debouts'])
                    except:
                        ecart_type_total = 0
                        ecart_type_couche = 0
                        ecart_type_debout = 0
                        quartiles_total = [0, 0, 0]
                        quartiles_couche = [0, 0, 0]
                        quartiles_debout = [0, 0, 0]
                        mode_total = None
                        mode_couche = None
                        mode_debout = None

                        if 'lst_totals' not in dict_resultat[id]:
                            dict_resultat[id]['lst_totals'] = []
                        if 'lst_couches' not in dict_resultat[id]:
                            dict_resultat[id]['lst_couches'] = []
                        if 'lst_debouts' not in dict_resultat[id]:
                            dict_resultat[id]['lst_debouts'] = []

                    print(ecart_type_total, ecart_type_couche, ecart_type_debout)

                    dict_resultat[key]['std_total'] = ecart_type_total
                    dict_resultat[key]['std_couche'] = ecart_type_couche
                    dict_resultat[key]['std_debout'] = ecart_type_debout

                    dict_resultat[key]['quartiles_total'] = quartiles_total
                    dict_resultat[key]['quartiles_couche'] = quartiles_couche
                    dict_resultat[key]['quartiles_debout'] = quartiles_debout

                    dict_resultat[key]['mode_total'] = mode_total
                    dict_resultat[key]['mode_couche'] = mode_couche
                    dict_resultat[key]['mode_debout'] = mode_debout
                         
                    db_manager.query_set_stat_minutes({'timestamp':timestamp, 'source': key, 'result':dict_resultat[key]})
                    
                    print()

                    dict_resultat[key]['lst_totals'] = []
                    dict_resultat[key]['lst_couches'] = []
                    dict_resultat[key]['lst_debouts'] = []

                    dict_resultat[key] = {
                                            'total': 0, 
                                            'couche': 0, 
                                            'debout': 0, 
                                            'nb_frames': 0, 
                                            'max_total' : 0,
                                            'max_couche' : 0,
                                            'max_debout' : 0,
                                            'min_total' : 10000,
                                            'min_couche' : 10000,
                                            'min_debout' : 10000,
                                            'std_total' : 0,
                                            'std_couche' : 0,
                                            'std_debout' : 0,
                                          }

            dict_resultat[id]['total'] += total
            dict_resultat[id]['couche'] += smm
            dict_resultat[id]['debout'] += total - smm
            dict_resultat[id]['nb_frames'] += 1
            dict_resultat[id]['max_total'] = max(dict_resultat[id]['max_total'], total)
            dict_resultat[id]['max_couche'] = max(dict_resultat[id]['max_couche'], smm)
            dict_resultat[id]['max_debout'] = max(dict_resultat[id]['max_debout'], total - smm)
            dict_resultat[id]['min_total'] = min(dict_resultat[id]['min_total'], total)
            dict_resultat[id]['min_couche'] = min(dict_resultat[id]['min_couche'], smm)
            dict_resultat[id]['min_debout'] = min(dict_resultat[id]['min_debout'], total - smm)
            
            last_minute = current_minute

        else:
            print("Champ 'timestamp' manquant dans l'un des éléments de la liste.")
            # Gestion d'erreur ou logique alternative ici

    return f'Reçu {timestamp}!!'

@app.route('/get_data_animov_ch_minutes', methods=['GET'])
@token_required
def get_data_animov_ch_minutes():
    global data_list_reception_INRA_animov

# Définition d'une route Flask pour obtenir des données spécifiques avec la méthode HTTP GET.
@app.route('/get_data_animov_ch', methods=['GET'])
@token_required
def get_data_animov_ch():
    """
Exemple d'endpoint qui renvoie des données détaillées sur les activités avec des scores et statistiques.
---
tags:
  - Activités
responses:
  200:
    description: Une liste de données d'activités avec des scores et des statistiques détaillées.
    content: 
    schema:
      type: object
      properties:
        _general_stats:
          type: array
          items:
            type: object
            properties:
              source_1:
                type: object
                properties:
                  avg_all_score:
                    type: number
                    format: double
                    description: Score d'inférence moyenne globale.
                    example: 0.847
                  avg_couche:
                    type: number
                    format: double
                    description: Moyenne du nombre de chèvres couchés.
                    example: 5.667
                  avg_count:
                    type: number
                    format: double
                    description: Moyenne du comptages des chèvres.
                    example: 12.667
                  avg_debout:
                    type: number
                    format: double
                    description: Moyenne du nombre de chèvres debout.
                    example: 7.0
                  std_couche:
                    type: number
                    format: double
                    description: Écart type du nombre de chèvres couchés.
                    example: 0.577
                  std_count:
                    type: number
                    format: double
                    description: Écart type des comptages de chèvres.
                    example: 0.577
                  std_debout:
                    type: number
                    format: double
                    description: Écart type du nombre de chèvres debout.
                    example: 0.0
                  std_mean_all_score:
                    type: number
                    format: double
                    description: Écart type des inférences du score moyen global.
                    example: 0.124
        _send_date:
          type: string
          format: date-time
          description: Date d'envoi des données.
          example: "2024-08-01 17:18:46"
        data:
          type: array
          items:
            type: object
            properties:
              date:
                type: array
                items:
                  type: string
                  format: date-time
                  description: Date de l'enregistrement.
                  example: "2024-02-19 09:28:09.703"
              detect:
                type: array
                items:
                  type: array
                  items:
                    type: number
                    description: Détails de la détection (ID, coordonnées, score, etc.).
                    example: [0,911.098,201.100,1104.898,379.823,0.945821,0.0,0,0,0]
              frame:
                type: string
                type: number
                description: image de video surveillance.
                example: "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/2wBDA..."
              frame_id:
                type: integer
                description: ID du frame.
                example: 3004169
              source_id:
                type: integer
                description: Numéro de la source.
                example: 1
              stats:
                type: object
                properties:
                  25%:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe 25e percentile.
                        example: 0.0
                      score:
                        type: number
                        format: double
                        description: Score 25e percentile.
                        example: 0.86
                      x_max:
                        type: number
                        format: double
                        description: x_max 25e percentile.
                        example: 719.25
                      x_min:
                        type: number
                        format: double
                        description: x_min 25e percentile.
                        example: 639.5
                      y_max:
                        type: number
                        format: double
                        description: y_max 25e percentile.
                        example: 357.75
                      y_min:
                        type: number
                        format: double
                        description: y_min 25e percentile.
                        example: 197.5
                  50%:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe 50e percentile.
                        example: 0.0
                      score:
                        type: number
                        format: double
                        description: Score 50e percentile.
                        example: 0.913
                      x_max:
                        type: number
                        format: double
                        description: x_max 50e percentile.
                        example: 765.5
                      x_min:
                        type: number
                        format: double
                        description: x_min 50e percentile.
                        example: 668.0
                      y_max:
                        type: number
                        format: double
                        description: y_max 50e percentile.
                        example: 409.0
                      y_min:
                        type: number
                        format: double
                        description: y_min 50e percentile.
                        example: 322.0
                  75%:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe 75e percentile.
                        example: 1.0
                      score:
                        type: number
                        format: double
                        description: Score 75e percentile.
                        example: 0.926
                      x_max:
                        type: number
                        format: double
                        description: x_max 75e percentile.
                        example: 897.5
                      x_min:
                        type: number
                        format: double
                        description: x_min 75e percentile.
                        example: 792.5
                      y_max:
                        type: number
                        format: double
                        description: y_max 75e percentile.
                        example: 626.75
                      y_min:
                        type: number
                        format: double
                        description: y_min 75e percentile.
                        example: 526.75
                  couche:
                    type: integer
                    description: Nombre de fois couché.
                    example: 5
                  count:
                    type: integer
                    description: Nombre total de détections.
                    example: 12
                  debout:
                    type: integer
                    description: Nombre de fois debout.
                    example: 7
                  max:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe maximale.
                        example: 1.0
                      score:
                        type: number
                        format: double
                        description: Score maximal.
                        example: 0.946
                      x_max:
                        type: number
                        format: double
                        description: x_max maximal.
                        example: 1326.0
                      x_min:
                        type: number
                        format: double
                        description: x_min maximal.
                        example: 1243.0
                      y_max:
                        type: number
                        format: double
                        description: y_max maximal.
                        example: 1060.0
                      y_min:
                        type: number
                        format: double
                        description: y_min maximal.
                        example: 801.0
                  mean:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe moyenne.
                        example: 0.417
                      score:
                        type: number
                        format: double
                        description: Score moyen.
                        example: 0.885
                      x_max:
                        type: number
                        format: double
                        description: x_max moyen.
                        example: 844.75
                      x_min:
                        type: number
                        format: double
                        description: x_min moyen.
                        example: 736.583
                      y_max:
                        type: number
                        format: double
                        description: y_max moyen.
                        example: 499.417
                      y_min:
                        type: number
                        format: double
                        description: y_min moyen.
                        example: 364.25
                  min:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Classe minimale.
                        example: 0.0
                      score:
                        type: number
                        format: double
                        description: Score minimal.
                        example: 0.733
                      x_max:
                        type: number
                        format: double
                        description: x_max minimal.
                        example: 606.0
                      x_min:
                        type: number
                        format: double
                        description: x_min minimal.
                        example: 531.0
                      y_max:
                        type: number
                        format: double
                        description: y_max minimal.
                        example: 112.0
                      y_min:
                        type: number
                        format: double
                        description: y_min minimal.
                        example: 0.0
                  std:
                    type: object
                    properties:
                      classe:
                        type: number
                        format: double
                        description: Écart type des classes.
                        example: 0.515
                      score:
                        type: number
                        format: double
                        description: Écart type des scores.
                        example: 0.063
                      x_max:
                        type: number
                        format: double
                        description: Écart type x_max.
                        example: 207.512
                      x_min:
                        type: number
                        format: double
                        description: Écart type x_min.
                        example: 195.134
                      y_max:
                        type: number
                        format: double
                        description: Écart type y_max.
                        example: 267.017
                      y_min:
                        type: number
                        format: double
                        description: Écart type y_min.
                        example: 237.496
"""

    global data_list_reception_INRA_animov  # Référence à la variable globale pour les données.

    required_params = ['sources', 'with_images', 'with_detect', 'with_stats', 'with_global_stats']
    params_present = all(param in request.args for param in required_params)

    if not params_present:
        return jsonify({'error': 'Certains paramètres requis sont manquants dans la requête'}), 400
    else:
        pass

    valid_values = {
        'with_images': ['True', 'False','Single'],
        'with_detect': ['True', 'False'],
        'with_stats': ['True', 'False', 'Lite'],
        'with_global_stats': ['True', 'False']
    }

    if not all(param in request.args for param in required_params):
        return jsonify({'error': 'Certains paramètres requis sont manquants dans la requête'}), 400

    for param, values in valid_values.items():
        if param in request.args and request.args[param] not in values:
            return jsonify({'error': f'La valeur du paramètre {param} est invalide'}), 400
        
    sources_possibles = ['1', '2', '3', '4']
    all_permutations = []
    for r in range(1, len(sources_possibles) + 1):
        for perm in permutations(sources_possibles, r):
            all_permutations.append(perm)
    all_permutations_strings = [','.join(perm) for perm in all_permutations]

    try:
        sources_list = request.args.get('sources')
        numbers_list = [int(num) for num in sources_list.split(',')]
        numbers_list = sorted(numbers_list)
        numbers_list = list(set(numbers_list))
        sorted_permutations = ','.join([str(num) for num in numbers_list])

        if sorted_permutations not in all_permutations_strings:
            return jsonify({'error': 'La requête ne contient aucune combinaison valide de sources'}), 400
    except:
        return jsonify({'error': "Le champs sources de la requête n'est la valide"}), 400
    
    json_ = filter_data_anomov(sorted_permutations)
    
    if request.args.get('with_stats')=='Lite':
        json_ = stats_data_animov_frames_lite(json_)
    elif request.args.get('with_stats')=='True':   
        json_ = stats_data_animov_frames(json_)
    
    if request.args.get('with_global_stats') == 'True':
        json_g_stats = global_stats_data_animov_send(json_, sorted_permutations)

    if request.args.get('with_stats') == 'False':
        for entry in json_:
            if "stats" in entry:
                del entry["stats"]

    if request.args.get('with_images') != 'True' and request.args.get('with_images') != 'Single':
        for entry in json_:
            if "frame" in entry:
                del entry["frame"]
    else:
        for entry in json_:
            try:
                if entry['frame'] == None:
                    del entry["frame"]
                    del entry["frame_id"]
                    del entry["source_id"]
                    del entry["date"]
                    try:
                        del entry["detect"]
                    except:
                        pass
            except:
                pass
        for json_data in reversed(json_):
            if json_data == {}:
                json_.remove(json_data)
        try:
            if request.args.get('with_images') == 'Single' :
                filtered_data = {}
                for entry in json_:
                    try:
                        filtered_data[entry['source_id']] = entry
                    except:
                        pass
                json_ = list(filtered_data.values())
        except:
            return jsonify({'erreur':'error !!!!' , 'json':json_}), 200 
            pass
    
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        if request.args.get('with_images') == 'False' and request.args.get('with_stats') == 'False' and request.args.get('with_detect') == 'False':
            del entry["data"]
    except:
        try:
            return jsonify({"_general_stats": json_g_stats, '_send_date': current_date}), 200
        except:
            return jsonify({'_send_date': current_date}), 200
   
    try:
        return jsonify({"data": json_, '_general_stats': json_g_stats, '_send_date': current_date}), 200 
    except:
        try:
            return jsonify({"_general_stats": json_g_stats, '_send_date': current_date}), 200 
        except:
            return jsonify({"data": json_, '_send_date': current_date}), 200 

@app.route('/chevres_heures', methods=['GET'])
# @token_required
def get_chevres_heures():
    """
Exemple d'endpoint qui renvoie des données d'activités à haute précision.
---
tags:
  - Activités
responses:
  200:
    description: Une liste de données sur les activités avec des valeurs à haute précision.
    content:
    schema:
      type: array
      items:
        type: object
        properties:
          brush:
            type: number
            format: double
            description: Nombre chèvres en moyenne à la brosse.
            example: 0.0
          class_0:
            type: number
            format: double
            description: Nombre de chèvres en moyenne de classe 0.
            example: 18.93543878976774
          class_1:
            type: number
            format: double
            description: Nombre de chèvres en moyenne classe 1.
            example: 4.5
          drink:
            type: number
            format: double
            description: Nombre de chèvres en moyenne à l'abrevoire.
            example: 0.0
          eat:
            type: number
            format: double
            description: Nombre de chèvres en moyenne à manger, en haute précision.
            example: 0.354837896774193
          heure:
            type: integer
            description: Heure de l'inférence, en format 24 heures.
            example: 9
          jour:
            type: string
            description: Jour de l'enregistrement des données.
            example: "Wed, 27 Sep 2023 00:00:00 GMT"
          source:
            type: integer
            description: Numéro de la source des video.
            example: 1
"""

    df = db_manager.query_get_chevres_heure()
    return jsonify(df.to_dict(orient='records'))

@app.route('/chevres_minutes', methods=['GET'])
@token_required
def get_chevres_minutes():
    """
Exemple d'endpoint qui renvoie des données détaillées sur des activités à différentes heures.
---
tags:
  - Activités
responses:
  200:
    description: Une liste de données sur les activités.
    content: 
    schema:
      type: array
      items:
        type: object
        properties:
          brush:
            type: number
            format: double
            description: Nombre chèvres en moyenne à la brosse.
            example: 0.0
          class_0:
            type: number
            format: double
            description: Nombre de chèvres en moyenne de classe 0.
            example: 18.93543878976774
          class_1:
            type: number
            format: double
            description: Nombre de chèvres en moyenne classe 1.
            example: 4.5
          drink:
            type: number
            format: double
            description: Nombre de chèvres en moyenne à l'abrevoire.
            example: 0.0
          eat:
            type: number
            format: double
            description: Nombre de chèvres en moyenne à manger, en haute précision.
            example: 0.354837896774193
          heure:
            type: integer
            description: Heure de l'inférence, en format 24 heures.
            example: 9
          jour:
            type: string
            description: Jour de l'enregistrement des données.
            example: "Wed, 27 Sep 2023 00:00:00 GMT"
          source:
            type: integer
            description: Numéro de la source des video.
            example: 1
"""

    df = db_manager.query_get_chevres_minutes()
    return jsonify(df.to_dict(orient='records'))

@app.route('/sources', methods=['GET'])
@token_required
def get_sources():
    """
    Exemple d'endpoint qui renvoie une liste de sources.
    ---
    tags:
      - Sources
    responses:
      200:
        description: Une liste des sources disponibles.
        content:
        schema:
          type: array
          items:
            type: object
            properties:
              source:
                type: integer
                description: L'identifiant de la source.
                example: 1
    """

    df = db_manager.query_get_sources()
    return jsonify(df.to_dict(orient='records'))

@app.route('/dates', methods=['GET'])
@token_required
def get_dates():
    """
    Exemple d'endpoint qui renvoie une liste de dates.
    ---
    tags:
      - Dates
    responses:
      200:
        description: Une liste de dates.
        content:
        schema:
          type: array
          items:
            type: object
            properties:
              dates:
                type: string
                description: Date et heure en format GMT.
                example: "Wed, 27 Sep 2023 00:00:00 GMT"
    """

    df = db_manager.query_get_dates()
    return jsonify(df.to_dict(orient='records'))

@app.route('/stats_minute', methods=['GET'])
@token_required
def get_stats_minute():
    df = db_manager.query_get_stats_minute()
    return jsonify(df.to_dict(orient='records'))

@app.route('/stats_heure', methods=['GET'])
@token_required
def get_stats_heure():
    df = db_manager.query_get_stats_heure()
    return jsonify(df.to_dict(orient='records'))

@app.route('/get_serie_heure', methods=['GET'])
@token_required
def get_serie_heure():
    """
    Exemple d'endpoint qui renvoie les données sur les chèvres heures.
    ---
    tags:
      - Chevres Heures
    responses:
      200:
        description: Une liste de données sur les chèvres heures.
        content: 
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: L'ID de la donnée.
                example: 1
              Q1_couche:
                type: number
                description: Q1 de la distribution des chévres en position couchée.
                example: 4.0
              Q1_debout:
                type: number
                description:  Q1 de la distribution des chévres en position debout.
                example: 1.0
              Q1_total:
                type: number
                description:  Q1 de la distribution du nombre totale des chèvres .
                example: 3.0
              Q2_couche:
                type: number
                description: Médianne de la distribution des chévres en position couchée.
                example: 5.0
              Q2_debout:
                type: number
                description: Médianne de la distribution des chévres en position debout.
                example: 2.0
              Q2_total:
                type: number
                description: Médianne de la distribution du nombre totale des chèvres .
                example: 7.0
              Q3_couche:
                type: number
                description: Q3 de la distribution des chévres en position couchée.
                example: 6.0
              Q3_debout:
                type: number
                description: Q3 de la distribution des chévres en position debout.
                example: 1.0
              Q3_total:
                type: number
                description: Q3 de la distribution du nombre totale des chèvres .
                example: 7.0
              couche:
                type: number
                description: Total en position couchée.
                example: 152.6
              debout:
                type: number
                description: Total en position debout.
                example: 2466
              max_couche:
                type: number
                description: Nombre maximum en position couchée.
                example: 8
              max_debout:
                type: number
                description: Nombre maximum en position debout.
                example: 12
              min_couche:
                type: number
                description: Nombre minimum en position couchée.
                example: 2
              min_debout:
                type: number
                description: Nombre minimum en position debout.
                example: 4
              mode_couche:
                type: integer
                description: Mode en position couchée.
                example: 6
              mode_debout:
                type: integer
                description: Mode en position debout.
                example: 9
              nb_frames:
                type: integer
                description: Nombre de frames analysées.
                example: 300
              source:
                type: integer
                description: Numéro de la donnée, videosurveillance.
                example: 1
              std_couche:
                type: number
                description: Écart type pour la position couchée.
                example: 1.374
              std_debout:
                type: number
                description: Écart type pour la position debout.
                example: 1.205
              std_total:
                type: number
                description: Écart type total.
                example: 1.653
              timestamp:
                type: integer
                description: Timestamp de la donnée.
                example: 1712994000
              total:
                type: integer
                description: Comptage total mesuré.
                example: 4218
   """
    df = db_manager.query_get_serie_heure()
    return jsonify(df.to_dict(orient='records'))

@app.route('/get_serie_jour', methods=['GET'])
@token_required
def get_serie_jour():
    """
   tags:
     - Chevres Heures
   responses:
     200:
       description: Une time série sur la dernière journée enregistrée dans la base de données concernant les chèvres.
       schema:
         type: array
         items:
           type: object
           properties:
             couche:
               type: number
               description: Total en position couchée.
               example: 152.6
             debout:
               type: number
               description: Total en position debout.
               example: 2466
             max_couche:
               type: number
               description: Nombre maximum en position couchée.
               example: 8
             max_debout:
               type: number
               description: Nombre maximum en position debout.
               example: 12
             min_couche:
               type: number
               description: Nombre minimum en position couchée.
               example: 2
             min_debout:
               type: number
               description: Nombre minimum en position debout.
               example: 4
             mode_couche:
               type: integer
               description: Mode en position couchée.
               example: 6
             mode_debout:
               type: integer
               description: Mode en position debout.
               example: 9
             nb_frames:
               type: integer
               description: Nombre de frames analysées.
               example: 300
             source:
               type: integer
               description: Numéro de la donnée, videosurveillance.
               example: 1
             std_couche:
               type: number
               description: Écart type pour la position couchée.
               example: 1.374
             std_debout:
               type: number
               description: Écart type pour la position debout.
               example: 1.205
             std_total:
               type: number
               description: Écart type total.
               example: 1.653
             timestamp:
               type: integer
               description: Timestamp de la donnée.
               example: 1712994000
             total:
               type: integer
               description: Comptage total mesuré.
               example: 4218
   """
    df = db_manager.query_get_serie_jour()
    return jsonify(df.to_dict(orient='records'))

@app.route('/get_serie_last_heure', methods=['GET'])
@token_required
def get_serie_last_heure():
    """
    Exemple d'endpoint qui renvoie les données sur les chèvres heures.
    ---
    tags:
      - Chevres Heures
    responses:
      200:
        description: Une liste de données sur les chèvres heures.
        content:      
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: L'ID de la donnée.
                example: 1
              Q1_couche:
                type: number
                description: Q1 de la distribution des chévres en position couchée.
                example: 4.0
              Q1_debout:
                type: number
                description:  Q1 de la distribution des chévres en position debout.
                example: 1.0
              Q1_total:
                type: number
                description:  Q1 de la distribution du nombre totale des chèvres .
                example: 3.0
              Q2_couche:
                type: number
                description: Médianne de la distribution des chévres en position couchée.
                example: 5.0
              Q2_debout:
                type: number
                description: Médianne de la distribution des chévres en position debout.
                example: 2.0
              Q2_total:
                type: number
                description: Médianne de la distribution du nombre totale des chèvres .
                example: 7.0
              Q3_couche:
                type: number
                description: Q3 de la distribution des chévres en position couchée.
                example: 6.0
              Q3_debout:
                type: number
                description: Q3 de la distribution des chévres en position debout.
                example: 1.0
              Q3_total:
                type: number
                description: Q3 de la distribution du nombre totale des chèvres .
                example: 7.0
              couche:
                type: number
                description: Total en position couchée.
                example: 152.6
              debout:
                type: number
                description: Total en position debout.
                example: 2466
              max_couche:
                type: number
                description: Nombre maximum en position couchée.
                example: 8
              max_debout:
                type: number
                description: Nombre maximum en position debout.
                example: 12
              min_couche:
                type: number
                description: Nombre minimum en position couchée.
                example: 2
              min_debout:
                type: number
                description: Nombre minimum en position debout.
                example: 4
              mode_couche:
                type: integer
                description: Mode en position couchée.
                example: 6
              mode_debout:
                type: integer
                description: Mode en position debout.
                example: 9
              nb_frames:
                type: integer
                description: Nombre de frames analysées.
                example: 300
              source:
                type: integer
                description: Numéro de la donnée, videosurveillance.
                example: 1
              std_couche:
                type: number
                description: Écart type pour la position couchée.
                example: 1.374
              std_debout:
                type: number
                description: Écart type pour la position debout.
                example: 1.205
              std_total:
                type: number
                description: Écart type total.
                example: 1.653
              timestamp:
                type: integer
                description: Timestamp de la donnée.
                example: 1712994000
              total:
                type: integer
                description: Comptage total mesuré.
                example: 4218
   """

    df = db_manager.query_get_serie_last_heure()
    return jsonify(df.to_dict(orient='records'))

@app.route('/get_serie_last_jour', methods=['GET'])
@token_required
def get_serie_last_jour():
    """
tags:
  - Chevres Heures
responses:
  200:
    description: Une time série sur la dernière journée enregistrée dans la base de données concernant les chèvres.
    content:
    schema:
      type: array
      items:
        type: object
        properties:
          couche:
            type: number
            description: Total en position couchée.
            example: 152.6
          debout:
            type: number
            description: Total en position debout.
            example: 2466
          max_couche:
            type: number
            description: Nombre maximum en position couchée.
            example: 8
          max_debout:
            type: number
            description: Nombre maximum en position debout.
            example: 12
          min_couche:
            type: number
            description: Nombre minimum en position couchée.
            example: 2
          min_debout:
            type: number
            description: Nombre minimum en position debout.
            example: 4
          mode_couche:
            type: integer
            description: Mode en position couchée.
            example: 6
          mode_debout:
            type: integer
            description: Mode en position debout.
            example: 9
          nb_frames:
            type: integer
            description: Nombre de frames analysées.
            example: 300
          source:
            type: integer
            description: Numéro de la donnée, videosurveillance.
            example: 1
          std_couche:
            type: number
            description: Écart type pour la position couchée.
            example: 1.374
          std_debout:
            type: number
            description: Écart type pour la position debout.
            example: 1.205
          std_total:
            type: number
            description: Écart type total.
            example: 1.653
          timestamp:
            type: integer
            description: Timestamp de la donnée.
            example: 1712994000
          total:
            type: integer
            description: Comptage total mesuré.
            example: 4218
"""

    df = db_manager.query_get_serie_last_jour()
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5500', debug=False)
