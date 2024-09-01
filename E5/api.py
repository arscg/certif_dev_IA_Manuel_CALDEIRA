from flask import Flask, request, render_template, jsonify, Response, send_from_directory, render_template_string, redirect
import requests
import time
from datetime import datetime
import socket
import psutil
import os
import signal
import subprocess
import docker
import yaml
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import numpy as np
from io import BytesIO

# Définition des niveaux de log
log_levels = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

WITH_MAIL = False

# Définition des seuils d'alerte pour CPU, mémoire, etc.
seuils = {
    "cpu": {"seuil1": 90, "seuil2": 30, 'state': 0, 'timestamp': None},
    "memory": {"seuil1": 90, "seuil2": 45, 'state': 0, 'timestamp': None},
    "elapse": {"seuil1": 9, "seuil2": 3, 'state': 0, 'timestamp': None},
    "mysql": {'state': 0, 'timestamp': None},
    "demon": {'state': 0, 'timestamp': None},
}

app = Flask(__name__)
data = {"cpu": 0.0, "memory": 0.6, "disk": 0.9}  # Dictionnaire pour représenter les données JSON
last_time_received = None
time_intervals = []  # Stockage des intervalles de temps entre les réceptions de données
ligne_de_vie = 0
elapsed_time = 0

data_list_reception_INRA_animov = {}

client = docker.from_env()  # Connexion au démon Docker

serveur = "localhost"

# Configuration de base du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Définir le niveau de log à DEBUG

# Formatter pour les logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Création d'un FileHandler pour écrire les logs dans un fichier
file_handler = logging.FileHandler('mon_application.log')
file_handler.setLevel(logging.DEBUG)  # Capture tous les niveaux de log
file_handler.setFormatter(formatter)

# Ajout du FileHandler au logger
logger.addHandler(file_handler)

logger.info("Start Flask.")

# Charger la configuration depuis un fichier YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
    container_name_or_id = config["container_name_or_id"]

def send_email(average_rmse):
    # Fonction pour envoyer un email d'alerte
    from_email = "manu@certif.fr"
    to_email = "arscg@certif.fr"
    subject = "Alerte: RMSE moyen élevé"
    body = f"La moyenne des RMSE est supérieure à 25. Valeur actuelle: {average_rmse}"

    smtp_server = "localhost"
    smtp_port = 587
    smtp_user = "mlflow@certif.fr"
    smtp_password = "mlflow"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}")

@app.route('/send_mail', methods=['GET'])
def send_mail(corps="Bonjour, ceci est un message de test envoyé depuis Python.", subject="Sujet de votre email"):
    # Fonction pour envoyer un email manuellement
    from_email = "manu@certif.fr"
    to_email = "arscg@certif.fr"
    subject = "Alerte serveur !!!"

    smtp_server = "localhost"
    smtp_port = 587
    smtp_user = "mlflow@certif.fr"
    smtp_password = "mlflow"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(corps, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        if WITH_MAIL:
            server.sendmail(from_email, to_email, text)
            logger.info(f"Email envoyé avec succès à {to_email} !!!")
        else:
            logger.info(f"Email envoyé SIMULÉ !!!")
        server.quit()
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}")
    
    return 'send mail !!!'

@app.route('/receive_data', methods=['POST'])
def receive_data():
    # Route pour recevoir les données et les traiter
    global data, last_time_received, time_intervals, WITH_MAIL, seuils, temps_modification
    current_time = time.time()

    # Vérifier si le fichier de configuration a été modifié
    if temps_modification != os.path.getmtime("config.yaml"):
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)

        WITH_MAIL = config['WITH_MAIL']
        seuils = config['seuils']
        temps_modification = os.path.getmtime("config.yaml")
        logger.warning("Update config.")

    try:
        if last_time_received is not None:
            elapsed_time = current_time - last_time_received
            timestamp = datetime.now().isoformat()  # Obtenez la date et l'heure actuelles
            interval_data = {"interval": elapsed_time, "timestamp": timestamp}

            time_intervals.insert(0, interval_data) 

            # Conservez seulement les 100 derniers enregistrements
            if len(time_intervals) > 100:
                time_intervals.pop()
        else:
            elapsed_time = None

        last_time_received = current_time

        data = request.json
        data['time_intervals'] = time_intervals  # Intégration des intervalles de temps au JSON
        data['running'] = elapsed_time < 10 if last_time_received is not None else False

        process_alarm("cpu")

        elapsed_time = round(elapsed_time, 2)
        process_alarm_elapse(elapsed_time)

        return jsonify({"Ok": 'Ok'}), 200    
    except Exception as e:
        logger.error(f"Erreur rencontrée : {e}")
        logger.error(traceback.format_exc())  # Affiche la trace de l'exception
        return jsonify({"error": str(e)}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    # Route pour obtenir les données actuelles
    global data, ligne_de_vie
    ligne_de_vie += 1
    ligne_de_vie %= 2
    data['check_up'] = {"ligne_de_vie": ligne_de_vie}
    return jsonify(data)

@app.route('/get_alarm_cpu', methods=['GET'])
def get_alarm_cpu():
    # Route pour obtenir une alarme CPU si le CPU change
    cpu_precedent = None
    for iteration in data["pc_data"]:
        if cpu_precedent is not None and iteration["cpu"] != cpu_precedent:
            return jsonify({"cpu": iteration["cpu"]})
        cpu_precedent = iteration["cpu"]
    return jsonify({"message": "Aucun changement de CPU détecté"})

@app.route('/get_alarm_memory', methods=['GET'])
def get_alarm_memory():
    # Route pour obtenir une alarme mémoire si la mémoire change
    memory_precedent = None
    for iteration in data["pc_data"]:
        if memory_precedent is not None and iteration["memory"] != memory_precedent:
            return jsonify({"memory": iteration["memory"]})
        memory_precedent = iteration["memory"]
    return jsonify({"message": "Aucun changement de mémoire détecté"})

@app.route('/get_alarm_time_inteval', methods=['GET'])
def get_alarm_time_inteval():
    # Route pour obtenir une alarme sur l'intervalle de temps
    return jsonify({"elapse": time_intervals[0]})

@app.route('/get_check_port', methods=['GET'])
def get_check_port():
    # Route pour vérifier les ports ouverts
    ports = scan_ports('localhost')
    return jsonify({"list_port": ports})

@app.route('/get_check_demon', methods=['GET'])
def get_check_demon():
    # Route pour vérifier si le démon est en cours d'exécution
    running = is_process_running('demon.py')
    if running.get("running") is False:
        if seuils["demon"]["state"] == 0:
            logger.error("Erreur connection demon.")
            seuils["demon"]["state"] = 1
    else:
        if seuils["demon"]["state"] == 1:
            logger.warning("Reconnection demon.")
            seuils["demon"]["state"] = 0
    return jsonify(running)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    # Route pour gérer le démarrage et l'arrêt des services
    if request.method == 'POST':
        if 'demon' in request.form:
            if request.form['demon'] == 'Marche':
                start_demon()
                send_mail("Start demon.", "Serveur defaut")
            elif request.form['demon'] == 'Arret':
                stop_demon()
                send_mail("Stop demon.", "Serveur defaut")
                            
        elif 'mysql' in request.form:
            if request.form['mysql'] == 'Marche':
               start_mysql()
               send_mail("Start database.", "Serveur defaut")
            elif request.form['mysql'] == 'Arret':
                stop_mysql()
                send_mail("Stop database.", "Serveur defaut")
                
        elif 'all' in request.form:
            if request.form['all'] == 'Marche':
                start_demon()
                start_data_animov()
                start_mysql()
                send_mail("Start database & demon.", "Serveur defaut")
            elif request.form['all'] == 'Arret':
                stop_demon()
                stop_data_animov()
                stop_mysql()
                send_mail("Stop database, flask data animov & demon.", "Serveur defaut")
        
    return render_template('managing.html')

@app.route('/get_logs', methods=['GET'])
def get_logs():
    # Route pour obtenir les logs
    logs = lire_logs_get('mon_application.log')
    logs_json = {"logs": list(logs)}  # Convertit le générateur en liste si nécessaire
    return jsonify(logs_json)

def start_data_animov():
    # Fonction pour démarrer le script data_animov
    chemin_actuel = os.getcwd()
    subprocess.Popen(["bash", "../../data_animov.sh"])
    logger.info("Start test_data_animov.")

def stop_data_animov(value=0):
    # Fonction pour arrêter le script data_animov
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.info['name'] == 'python' or process.info['name'] == 'python3':
            try:
                if any('test_data_animov.py' in cmd for cmd in process.info['cmdline']):
                    os.kill(process.info['pid'], signal.SIGTERM)
            except:
                pass
    logger.info(f"Stop test_data_animov : {value} %")

def start_demon():
    # Fonction pour démarrer le démon
    script_path = 'demon.py'
    subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info("Start demon.")

def stop_demon():
    # Fonction pour arrêter le démon
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.info['name'] == 'python.exe' or process.info['name'] == 'pythonw.exe':
            if process.info['cmdline'] and any('demon.py' in cmd for cmd in process.info['cmdline']):
                try:
                    process.terminate()  # Utilisation de psutil pour terminer le processus
                    process.wait(timeout=5)  # Attendre que le processus se termine
                except psutil.NoSuchProcess:
                    logger.error(f"Le processus avec PID {process.info['pid']} n'existe pas.")
                except psutil.AccessDenied:
                    logger.error(f"Accès refusé pour terminer le processus avec PID {process.info['pid']}.")
                except psutil.TimeoutExpired:
                    logger.error(f"Le processus avec PID {process.info['pid']} n'a pas pu être terminé dans le délai imparti.")
    logger.info("Stop demon")

def start_mysql():
    # Fonction pour démarrer MySQL
    try:
        control = 0
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
            control = config.get("mysql_control", False)
        if control:
            container = client.containers.get(container_name_or_id)
            container.start()
            logger.info("Demarrage de MySQL.")
        else:
            logger.info("Le demarrage de MySQL est omis.")
    except docker.errors.NotFound:
        logger.error(f"Conteneur {container_name_or_id} non trouvé.")
    except Exception as e:
        logger.error(f"Erreur lors du demarrage du conteneur: {e}")

def stop_mysql():
    # Fonction pour arrêter MySQL
    try:
        container = client.containers.get(container_name_or_id)
        container.stop()
        logger.info("Stop mysql.")
    except docker.errors.NotFound:
        logger.error(f"Conteneur {container_name_or_id} non trouvé.")
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt du conteneur: {e}")

def send_data_to_server(data_to_send):
    # Fonction pour envoyer les données au serveur
    url = "http://localhost:5002/receive_data"
    requests.post(url, json=data_to_send)

def scan_ports(host):
    # Fonction pour scanner les ports ouverts
    global seuils
    open_ports = {}
    for service, port in {"Flask": 5100, "Mysql": 3306, "Mysql2": 3303}.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        open_ports[service] = result == 0
        sock.close()
        
    if not open_ports.get("Mysql", False):
        if seuils["mysql"]["state"] == 0:
            logger.error("Erreur serveur MySQL.")
            seuils["mysql"]["state"] = 1 
            send_mail("Erreur serveur MySQL.", "Serveur defaut")

            with open("config.yaml", "r") as file:
                config = yaml.safe_load(file)
                if config["auto_start"]:
                    start_mysql()
    else:
        if seuils["mysql"]["state"] == 1:
            logger.warning("Reconnection mysql.")
            seuils["mysql"]["state"] = 0
            send_mail("Reconnection mysql.", "Serveur defaut")
         
    return open_ports

def is_process_running(process_name):
    # Fonction pour vérifier si un processus spécifique est en cours d'exécution
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and process_name in cmdline:
                return {'demon': {"running": True, "pid": proc.info['pid']}}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return {'demon': {"running": False}}

def lire_logs(fichier_log):
    # Fonction pour lire les logs
    with open(fichier_log, 'rb') as file:
        file.seek(0, 2)  # Aller à la fin du fichier
        position = file.tell()
        ligne = bytearray()
        while position >= 0:
            file.seek(position)
            position -= 1
            caractere = file.read(1)
            if caractere == b'\n':
                if ligne:
                    yield ligne.decode('utf-8')[::-1]
                ligne = bytearray()
            else:
                ligne.extend(caractere)
        yield ligne.decode('utf-8')[::-1]
        
def parse_log_line(line):
    # Fonction pour parser une ligne de log
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\S+) - (\S+) - (.+)$", line)
    if match:
        date_time_str, module, level, message = match.groups()
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S,%f')
        level_num = log_levels.get(level, 0)
        return {
            'date_time': date_time,
            'module': module,
            'level': level,
            'level_num': level_num,
            'message': message.rstrip('\n')
        }
    else:
        return None
        
def lire_logs_get(fichier_log):
    # Fonction pour obtenir les logs sous forme de liste
    logs = []
    with open(fichier_log, 'r', encoding='ISO-8859-1') as file:
        for line in file:
            log_entry = parse_log_line(line)
            if log_entry:
                logs.append(log_entry)
    logs.sort(key=lambda entry: entry['date_time'], reverse=True)
    for entry in logs:
        entry['date_time'] = entry['date_time'].strftime('%Y-%m-%d %H:%M:%S,%f')
    return logs

def process_alarm(device):
    # Fonction pour déclencher une alarme si une valeur dépasse un seuil
    global data, seuils
    sll = data['pc_data'][0][device]

    if sll > seuils[device]["seuil1"] and seuils[device]["state"] == 0:
        logger.info(f"Alerte {device} {sll} %.")
        seuils[device]["state"] = 1
        send_mail(f"Alerte {device} {sll} %.", "Serveur en surcharge")
    elif sll < seuils[device]["seuil2"] and seuils[device]["state"] == 1:
        logger.info(f"Fin d'alerte {device} {sll} %.")
        seuils[device]["state"] = 0
        send_mail(f"Fin d'alerte {device} {sll} %.", "Fin serveur en surcharge")

def process_alarm_elapse(delay, device="elapse"):
    # Fonction pour déclencher une alarme si le délai dépasse un seuil
    global data, seuils

    if delay > seuils[device]["seuil1"] and seuils[device]["state"] == 0:
        logger.info(f"Alerte reponce demon {delay} s.")
        seuils[device]["state"] = 1
        send_mail(f"Alerte reponce demon {delay} s.", "Demon réponse !")
    elif delay < seuils[device]["seuil2"] and seuils[device]["state"] == 1:
        logger.info(f"Fin d'alerte reponce demon  {delay} s.")
        seuils[device]["state"] = 0
        send_mail(f"Fin d'alerte reponce demon {delay} s.", "Demon réponse !")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5002', debug=False)
