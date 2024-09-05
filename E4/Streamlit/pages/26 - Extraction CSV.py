import streamlit as st
import pandas as pd
import glob
import os
import warnings
from sqlalchemy import create_engine, text
import pymysql

# Configuration initiale
st.set_page_config(layout="wide")
warnings.filterwarnings('ignore')

k= 1

# Fonction pour vérifier et créer la base de données si elle n'existe pas
def create_database_if_not_exists(database_url, db_name):
    # Se connecter sans spécifier de base de données
    engine = create_engine(database_url.replace(f"/{db_name}", ""))
    conn = engine.connect()

    # Utiliser SQLAlchemy text() pour exécuter la requête SQL
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
    conn.close()

# Fonction pour le traitement et le transfert des données
def data_traitement(chemin_dossier, base_de_donnees_url, source, db_name):
    global k

    # Vérifier et créer la base de données si nécessaire
    create_database_if_not_exists(base_de_donnees_url, db_name)
    
    # Création de l'engine de la base de données
    engine = create_engine(base_de_donnees_url)
    
    # Dictionnaire pour stocker les résultats des DataFrames concaténés
    resultats = {}

    # Pour les types de fichiers -1.csv et -2.csv
    for type_fichier in ['-1.csv', '-2.csv']:
        # Recherche des fichiers CSV correspondant dans le dossier
        fichiers_csv = glob.glob(os.path.join(chemin_dossier, f'*{type_fichier}'))
        
        # Lecture des fichiers CSV et ajout d'une colonne "fichier" pour chaque fichier
        dataframes = []
        for fichier in fichiers_csv:
            df = pd.read_csv(fichier)
            df['fichier'] = os.path.basename(fichier)  # Ajout du nom du fichier comme nouvelle colonne
            dataframes.append(df)
        
        if dataframes:
            # Concaténation des DataFrames si la liste n'est pas vide
            df_final = pd.concat(dataframes, ignore_index=True)

            # Renommer la colonne id_ en num_chevre
            df_final.rename(columns={'id': 'num_chevre'}, inplace=True)
            
            # Ajout de la colonne "Source" avec la valeur fournie
            df_final['Source'] = source
            
            # Ajout d'une colonne 'id' comme index auto-incrémenté
            df_final['id'] = range(k, k + len(df_final))
    
            k+=len(df_final) + 1
            
            # Nom de la table en fonction du type de fichier
            table_name = 'final' if '-1' in type_fichier else 'final_2'
            
            # Insertion dans la base de données avec l'option 'append'
            df_final.to_sql(table_name, engine, if_exists='append', index=False)

            try:
                # Ajouter la contrainte de clé primaire après l'insertion
                with engine.connect() as conn:
                    conn.execute(text(f"""
                        ALTER TABLE {table_name} 
                        ADD PRIMARY KEY (id);
                    """))
            except:
                pass
            
            # Stockage du DataFrame dans le dictionnaire de résultats
            resultats[type_fichier] = df_final
        else:
            # Si aucun fichier n'a été trouvé, un DataFrame vide est enregistré
            resultats[type_fichier] = pd.DataFrame()

        try:

            if '-1' in type_fichier:
                # Modification des types de colonnes après insertion dans la table MySQL
                with engine.connect() as connection:
                    connection.execute(text(f"""
                        ALTER TABLE {table_name}
                        MODIFY COLUMN num_chevre INT,
                        MODIFY COLUMN frame INT,
                        MODIFY COLUMN classe VARCHAR(255),
                        MODIFY COLUMN Source VARCHAR(255),
                        MODIFY COLUMN fichier VARCHAR(255),
                        MODIFY COLUMN Abreuvoir int,
                        MODIFY COLUMN Auge int,
                        MODIFY COLUMN Frottoir int,
                        MODIFY COLUMN date datetime;
                    """))
        except:
            pass

    # Retourne les DataFrames concaténés
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
db_name = "ANIMOV_CSV_data_"
base_de_donnees_url = f"mysql+pymysql://root:admin@localhost:3306/{db_name}"

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

if st.session_state.button_pressed:
    st.write('Processing...')
    for tab, dossier in zip(tabs, sous_dossiers):
        chemin_dossier = os.path.join(dossier_parent, dossier)
        with tab:
            resultats = data_traitement(chemin_dossier, base_de_donnees_url, dossier, db_name)
            for key, df in resultats.items():
                st.write(f"Traitement fichiers *{key}")
                st.dataframe(df)

    engine = create_engine(base_de_donnees_url)

    # Créer la table 'source' si elle n'existe pas déjà
    create_table_query = """
    CREATE TABLE IF NOT EXISTS source (
        id INT AUTO_INCREMENT PRIMARY KEY,  -- Clé primaire auto-incrémentée
        source VARCHAR(255) NOT NULL, 
        fichier VARCHAR(255) NOT NULL
    )
    SELECT DISTINCT source, fichier
    FROM final;
    """
    # Exécuter la requête pour créer la table
    with engine.connect() as connection:
        connection.execute(text(create_table_query))
        st.write("Table 'source' créée avec succès.")

    # Créer la table 'chevres' si elle n'existe pas déjà
    create_table_query = """
    CREATE TABLE IF NOT EXISTS chevres (
        id INT AUTO_INCREMENT PRIMARY KEY,  -- Clé primaire auto-incrémentée
        num_chevre int NOT NULL,
        nom VARCHAR(255) NOT NULL, 
        identifiant VARCHAR(255) NOT NULL, 
        Source VARCHAR(255) NOT NULL
    )
    select num_chevre, "nom" as nom, "123456A" as identifiant, Source 
    from final
    group by num_chevre, Source 
    """
    # Exécuter la requête pour créer la table
    with engine.connect() as connection:
        connection.execute(text(create_table_query))
        st.write("Table 'chevres' créée avec succès.")

    # Ajouter un index composite sur les colonnes num_chevre et Source
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE INDEX chevres_num_chevre_IDX ON chevres (num_chevre, Source);
        """))
    st.write("Index 'chevres_num_chevre_IDX' ajouté avec succès sur les colonnes num_chevre et Source.")

    # Créer la table 'chevres_sources' si elle n'existe pas déjà
    create_table_query = """
    CREATE TABLE IF NOT EXISTS chevres_sources (
            id INT AUTO_INCREMENT PRIMARY KEY,  -- Clé primaire auto-incrémentée
            id_source int NOT NULL,
            id_chevre int NOT NULL,
            FOREIGN KEY (id_source) REFERENCES source(id),  -- Clé étrangère sur 'source'
            FOREIGN KEY (id_chevre) REFERENCES chevres(id)  -- Clé étrangère sur 'chevre'
        )
    select id_source, s.id as id_chevre 
    from (SELECT num_chevre, s.id as id_source, s.source as video
                FROM final f
                INNER JOIN source s
                ON f.source = s.source AND f.fichier = s.fichier
                group by num_chevre, s.source, id_source) as c
    INNER JOIN chevres s
    ON c.video  = s.Source  AND c.num_chevre  = s.num_chevre 
    """
    # Exécuter la requête pour créer la table
    with engine.connect() as connection:
        connection.execute(text(create_table_query))
        st.write("Table 'chevres_sources' créée avec succès.")

    # Créer la table 'frames' si elle n'existe pas déjà
    create_table_query = """
    CREATE TABLE IF NOT EXISTS frames (
            id INT AUTO_INCREMENT PRIMARY KEY,  -- Clé primaire auto-incrémentée
            frame int NOT NULL,
            `date` datetime NOT NULL,
            FOREIGN KEY (id_source) REFERENCES source(id)  -- Clé étrangère sur 'source'
        )
    select frame, date, s.id as id_source  
    from (select frame, `date`,Source , fichier 
            from ANIMOV_CSV_data.`final`
            group by frame, `date`,Source , fichier) as f
    INNER JOIN source s
    On f.source = s.source AND f.fichier = s.fichier 
    """
    # Exécuter la requête pour créer la table
    with engine.connect() as connection:
        connection.execute(text(create_table_query))
        st.write("Table 'frames' créée avec succès.")

    # Ajouter un index composite sur les colonnes date et frame
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE INDEX frames_date_IDX ON frames (date, frame);
        """))
    st.write("Index 'frames_date_IDX' ajouté avec succès sur les colonnes num_chevre et Source.")


 # Créer la table 'detection' si elle n'existe pas déjà
    create_table_query = """
    CREATE TABLE IF NOT EXISTS detection (
        id INT AUTO_INCREMENT PRIMARY KEY,  -- Clé primaire auto-incrémentée
        id_chevres int NOT NULL,
        id_frame int NOT NULL,
        bb_left bigint NOT NULL,
        bb_top bigint NOT NULL,
        bb_width double NOT NULL,
        bb_height double NOT NULL,
        classe VARCHAR(255) NOT NULL,
        Abreuvoir int NOT NULL,
        Auge int NOT NULL,
        Frottoir int NOT NULL,
        FOREIGN KEY (id_chevres) REFERENCES chevres(id),  -- Clé étrangère sur 'source'
        FOREIGN KEY (id_frame) REFERENCES frames(id)  -- Clé étrangère sur 'source'
    )
    select ch.id as  id_chevres, fs.id_frame as id_frame,f.bb_left as bb_left, f.bb_top as bb_top, 
            f.bb_width as  bb_width,  f.bb_height as bb_height, f.classe as classe, 
            f.Abreuvoir as Abreuvoir, f.Auge as Auge, f.Frottoir as Frottoir
    from (select f.id as id_frame, date as dte, source as src, fichier as fch
            from frames f
            INNER JOIN source s
            on s.id = f.id_source)  as fs,
    final f, 
    chevres ch
    where ch.num_chevre = f.num_chevre and ch.Source = f.Source and fs.dte = f.`date` 
            and fs.src = f.Source and fs.fch = f.fichier
    limit 1000000
    """

    # Exécuter la requête pour créer la table
    with engine.connect() as connection:
        connection.execute(text(create_table_query))
        st.write("Table 'detection' créée avec succès.")

    # Ajouter un index composite sur les colonnes num_chevre et Source
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE INDEX final_Source_IDX ON final (num_chevre, Source);
        """))
        connection.execute(text("""
            CREATE INDEX final_frame_IDX ON final (frame, date);
        """))
    st.write("Index pour final créés avec succès.")




        




