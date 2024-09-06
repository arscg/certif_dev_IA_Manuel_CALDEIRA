import pymysql
from faker import Faker
import os
from urllib.parse import urlparse
import random

# Configuration
fake = Faker()
mysql_uri = os.getenv('MYSQL_DATABASE_URI')

# Parse the URI
url = urlparse(mysql_uri)

# Extract connection parameters
host = url.hostname
port = url.port
user = url.username
password = url.password
database = 'ANIMOV'  # Nom de la base de données à créer

# Connect to the MySQL server (sans spécifier de base de données)
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password
)

try:
    with conn.cursor() as cursor:
        # Créer la base de données et sélectionner la base
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
        cursor.execute(f"USE {database};")

        # Définir les tables à créer
        table_definitions = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                );
            """,
            'products': """
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price FLOAT NOT NULL
                );
            """,
            'table_chevres_minute_serveur_v2': """
                CREATE TABLE IF NOT EXISTS table_chevres_minute_serveur_v2 (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp BIGINT(20) NOT NULL,
                    source INT(11) NOT NULL,
                    total INT(11) NOT NULL,
                    couche INT(11) NOT NULL,
                    debout INT(11) NOT NULL,
                    max_total INT(11) NOT NULL,
                    max_couche INT(11) NOT NULL,
                    max_debout INT(11) NOT NULL,
                    min_total INT(11) NOT NULL,
                    min_couche INT(11) NOT NULL,
                    min_debout INT(11) NOT NULL,
                    std_total DECIMAL(6, 3) NOT NULL,
                    std_couche DECIMAL(6, 3) NOT NULL,
                    std_debout DECIMAL(6, 3) NOT NULL,
                    Q1_total DECIMAL(6, 3) NOT NULL,
                    Q1_couche DECIMAL(6, 3) NOT NULL,
                    Q1_debout DECIMAL(6, 3) NOT NULL,
                    Q2_total DECIMAL(6, 3) NOT NULL,
                    Q2_couche DECIMAL(6, 3) NOT NULL,
                    Q2_debout DECIMAL(6, 3) NOT NULL,
                    Q3_total DECIMAL(6, 3) NOT NULL,
                    Q3_couche DECIMAL(6, 3) NOT NULL,
                    Q3_debout DECIMAL(6, 3) NOT NULL,
                    mode_total TEXT,
                    mode_couche TEXT,
                    mode_debout TEXT,
                    nb_frames INT(11) NOT NULL
                );
            """,
            'table_chevres_heures': """
                CREATE TABLE IF NOT EXISTS table_chevres_heures (
                    jour DATETIME NOT NULL,
                    source BIGINT(20) NOT NULL,
                    heure BIGINT(20) NOT NULL,
                    brush DOUBLE NOT NULL,
                    drink DOUBLE NOT NULL,
                    eat DOUBLE NOT NULL,
                    class_0 DOUBLE NOT NULL,
                    class_1 DOUBLE NOT NULL
                );
            """,
            'table_chevres_minute': """
                CREATE TABLE IF NOT EXISTS table_chevres_minute (
                    jour DATETIME NOT NULL,
                    source BIGINT(20) NOT NULL,
                    minutes BIGINT(20) NOT NULL,
                    heure BIGINT(20) NOT NULL,
                    brush DOUBLE NOT NULL,
                    drink DOUBLE NOT NULL,
                    eat DOUBLE NOT NULL,
                    class_0 DOUBLE NOT NULL,
                    class_1 DOUBLE NOT NULL
                );
            """,
            'ResultatsConsolides': """
                CREATE TABLE IF NOT EXISTS ResultatsConsolides (
                    source INT(11) NOT NULL,
                    moyenne_total DECIMAL(10,6) NOT NULL,
                    max_total DECIMAL(10,0) NOT NULL,
                    min_total DECIMAL(10,0) NOT NULL,
                    ecart_type_total DECIMAL(10,6) NOT NULL,
                    moyenne_debout DECIMAL(10,6) NOT NULL,
                    max_debout DECIMAL(10,0) NOT NULL,
                    min_debout DECIMAL(10,0) NOT NULL,
                    ecart_type_debout DECIMAL(10,6) NOT NULL,
                    moyenne_couche DECIMAL(10,6) NOT NULL,
                    max_couche DECIMAL(10,0) NOT NULL,
                    min_couche DECIMAL(10,0) NOT NULL,
                    ecart_type_couche DECIMAL(10,6) NOT NULL
                );
            """
        }

        # Créer les tables
        for table_sql in table_definitions.values():
            cursor.execute(table_sql)

        # Peupler les tables `users` et `products` avec des données factices
        users_data = [(fake.user_name(), fake.password()) for _ in range(10)]
        users_data.append(('arscg', 'arscg'))
        cursor.executemany("INSERT INTO users (username, password) VALUES (%s, %s)", users_data)

        products_data = [(fake.word(), fake.random_number(digits=2)) for _ in range(10)]
        cursor.executemany("INSERT INTO products (name, price) VALUES (%s, %s)", products_data)

        # Peupler la table `table_chevres_minute_serveur_v2` avec des données factices
        chevres_minute_serveur_data = []
        for _ in range(100):
            total = random.randint(0, 100)
            couche = random.randint(0, total)
            debout = total - couche

            chevres_minute_serveur_data.append((
                fake.unix_time(), random.randint(1, 4), total, couche, debout,
                random.randint(total, total + 10), random.randint(couche, couche + 5), random.randint(debout, debout + 5),
                random.randint(total - 10, total), random.randint(couche - 5, couche), random.randint(debout - 5, debout),
                round(random.uniform(0, 10), 3), round(random.uniform(0, 10), 3), round(random.uniform(0, 10), 3),
                round(random.uniform(0, total / 4), 3), round(random.uniform(0, couche / 4), 3), round(random.uniform(0, debout / 4), 3),
                round(random.uniform(total / 4, total / 2), 3), round(random.uniform(couche / 4, couche / 2), 3), round(random.uniform(debout / 4, debout / 2), 3),
                round(random.uniform(total / 2, 3 * total / 4), 3), round(random.uniform(couche / 2, 3 * couche / 4), 3), round(random.uniform(debout / 2, 3 * debout / 4), 3),
                str(fake.random_elements(elements=('A', 'B', 'C'), length=3)),
                str(fake.random_elements(elements=('X', 'Y', 'Z'), length=3)),
                str(fake.random_elements(elements=('L', 'M', 'N'), length=3)),
                random.randint(1, 1000)
            ))

        cursor.executemany("""
            INSERT INTO table_chevres_minute_serveur_v2 (
                timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                min_total, min_couche, min_debout, std_total, std_couche, std_debout, 
                Q1_total, Q1_couche, Q1_debout, Q2_total, Q2_couche, Q2_debout, 
                Q3_total, Q3_couche, Q3_debout, mode_total, mode_couche, mode_debout, nb_frames
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chevres_minute_serveur_data)

        # Peupler les tables `table_chevres_heures` et `table_chevres_minute` avec des données factices
        chevres_heures_data = [
            (fake.date_time_this_year(), random.randint(1, 4), random.randint(0, 23), random.random() * 10,
             random.random() * 10, random.random() * 10, random.random() * 10, random.random() * 10)
            for _ in range(10)
        ]
        cursor.executemany("""
            INSERT INTO table_chevres_heures (jour, source, heure, brush, drink, eat, class_0, class_1)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, chevres_heures_data)

        chevres_minute_data = [
            (fake.date_time_this_year(), random.randint(1, 4), random.randint(0, 59), random.randint(0, 23), 
             random.random() * 10, random.random() * 10, random.random() * 10, random.random() * 10, random.random() * 10)
            for _ in range(10)
        ]
        cursor.executemany("""
            INSERT INTO table_chevres_minute (jour, source, minutes, heure, brush, drink, eat, class_0, class_1)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chevres_minute_data)

        # Création des vues
        views_definitions = {
            'vue_chevres_derniere_minute_v2': """
                CREATE OR REPLACE VIEW vue_chevres_derniere_minute_v2 AS
                SELECT 
                    timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                    min_total, min_couche, min_debout, std_total, std_couche, std_debout, 
                    Q1_total, Q1_couche, Q1_debout, Q2_total, Q2_couche, Q2_debout, 
                    Q3_total, Q3_couche, Q3_debout, mode_total, mode_couche, mode_debout, nb_frames
                FROM table_chevres_minute_serveur_v2
                WHERE timestamp = (SELECT MAX(timestamp) FROM table_chevres_minute_serveur_v2);
            """,
            'vue_chevre_derniere_heure_last': """
                CREATE OR REPLACE VIEW vue_chevre_derniere_heure_last AS
                SELECT 
                    id, timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                    min_total, min_couche, min_debout, std_total, std_couche, std_debout, 
                    Q1_total, Q1_couche, Q1_debout, Q2_total, Q2_couche, Q2_debout, 
                    Q3_total, Q3_couche, Q3_debout, mode_total, mode_couche, mode_debout
                FROM table_chevres_minute_serveur_v2
                WHERE timestamp = (SELECT MAX(timestamp) FROM table_chevres_minute_serveur_v2);
            """,
            'vue_chevres_serie_heure': """
                CREATE OR REPLACE VIEW vue_chevres_serie_heure AS
                SELECT 
                    id, timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                    min_total, min_couche, min_debout, std_total, std_couche, std_debout, 
                    Q1_total, Q1_couche, Q1_debout, Q2_total, Q2_couche, Q2_debout, 
                    Q3_total, Q3_couche, Q3_debout, mode_total, mode_couche, mode_debout, nb_frames
                FROM table_chevres_minute_serveur_v2
                WHERE HOUR(FROM_UNIXTIME(timestamp)) = HOUR(NOW());
            """,
            'vue_chevre_derniere_jour_last': """
                CREATE OR REPLACE VIEW vue_chevre_derniere_jour_last AS
                SELECT 
                    timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                    min_total, min_couche, min_debout, nb_frames
                FROM table_chevres_minute_serveur_v2
                WHERE DATE(FROM_UNIXTIME(timestamp)) = (
                    SELECT MAX(DATE(FROM_UNIXTIME(timestamp))) 
                    FROM table_chevres_minute_serveur_v2
                );
            """,
            'vue_chevres_serie_jour': """
                CREATE OR REPLACE VIEW vue_chevres_serie_jour AS
                SELECT 
                    timestamp, source, total, couche, debout, max_total, max_couche, max_debout, 
                    min_total, min_couche, min_debout, nb_frames
                FROM table_chevres_minute_serveur_v2
                WHERE DATE(FROM_UNIXTIME(timestamp)) = CURDATE();
            """
        }

        # Créer les vues
        for view_sql in views_definitions.values():
            cursor.execute(view_sql)

        # Peupler la table `ResultatsConsolides` avec des données factices
        resultats_consolides_data = []
        for _ in range(100):
            resultats_consolides_data.append((
                random.randint(1, 4),
                round(random.uniform(0, 100), 6), random.randint(50, 150), random.randint(0, 50), round(random.uniform(0, 10), 6),
                round(random.uniform(0, 100), 6), random.randint(50, 150), random.randint(0, 50), round(random.uniform(0, 10), 6),
                round(random.uniform(0, 100), 6), random.randint(50, 150), random.randint(0, 50), round(random.uniform(0, 10), 6)
            ))

        cursor.executemany("""
            INSERT INTO ResultatsConsolides (
                source, moyenne_total, max_total, min_total, ecart_type_total,
                moyenne_debout, max_debout, min_debout, ecart_type_debout,
                moyenne_couche, max_couche, min_couche, ecart_type_couche
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, resultats_consolides_data)

        # Commit the changes
        conn.commit()

finally:
    conn.close()
