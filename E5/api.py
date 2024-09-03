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
import json
import traceback
import logging
import numpy as np
from io import BytesIO

log_levels = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

WITH_MAIL= True

seuils = {
    "cpu": {"seuil1": 90, "seuil2": 30, 'state' : 0, 'timestamp': None},
    "memory": {"seuil1": 90, "seuil2": 45, 'state' : 0, 'timestamp': None},
    "elapse": {"seuil1": 9, "seuil2": 3, 'state' : 0, 'timestamp': None},
    "mysql": {'state' : 0, 'timestamp': None},
    "demon": {'state' : 0, 'timestamp': None},
}

app = Flask(__name__)
data = {"cpu": 0.0, "memory": 0.6, "disk": 0.9}  # Utilisez un dictionnaire pour représenter des données JSON
last_time_received = None
time_intervals = []
ligne_de_vie = 0
elapsed_time = 0

data_list_reception_INRA_animov = {}

client = docker.from_env()

serveur = "localhost"

# Configuration de base du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Définir le niveau de logger à DEBUG

# Formatter pour les logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Créer un FileHandler pour écrire les logs dans un fichier
file_handler = logging.FileHandler('mon_application.log')
file_handler.setLevel(logging.DEBUG)  # Assurez-vous que le handler capture tous les niveaux
file_handler.setFormatter(formatter)

temps_modification = os.path.getmtime("config.yaml")

# Ajouter le FileHandler au logger
logger.addHandler(file_handler)

logger.info("Start Flask.")

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)         
    container_name_or_id = config["container_name_or_id"]

def send_email(message, sujet):
    from_email = "serveur_alert@certif.fr"
    to_email = "arscg@certif.fr"
    subject = sujet
    body = message

    # Configurer le serveur SMTP
    smtp_server = "localhost"
    smtp_port =587
    smtp_user = "mlflow@certif.fr"
    smtp_password = "mlflow"

    # Créer le message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Envoyer l'e-mail
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.login(smtp_user, smtp_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

app = Flask(__name__)

@app.route('/send_mail', methods=['GET'])
def send_mail( corps = "Bonjour, ceci est un message de test envoyé depuis Python.", subjet = "Sujet de votre email"):

    send_email(corps, subjet)
    return 'send mail !!!'

@app.route('/receive_data', methods=['POST'])
def receive_data():
    global data, last_time_received, time_intervals, WITH_MAIL, seuils, temps_modification
    current_time = time.time()

    if temps_modification != os.path.getmtime("config.yaml"):
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)

        WITH_MAIL = config['WITH_MAIL']
        seuils = config['seuils']

        temps_modification = os.path.getmtime("config.yaml")

        logger.warning("Update config.")

    try:
        # Calculez la différence de temps si last_time_received n'est pas None
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
        data['time_intervals'] = time_intervals  # Intégrez les intervalles de temps au JSON
        data['running'] = elapsed_time < 10 if last_time_received is not None else False

        data['time_intervals'] = time_intervals  # Intégrez les intervalles de temps au JSON
        data['running'] = elapsed_time < 10 if elapsed_time is not None else False

        process_alarm("cpu")
        process_alarm("memory")

        # process_stop_overmemory()
        
        elapsed_time = round(elapsed_time, 2)
        process_alarm_elapse(elapsed_time)

        return jsonify({"Ok": 'Ok'}), 200    
    except Exception as e:
        print("Erreur rencontrée :", e)
        print(traceback.format_exc())  # Affiche la trace de l'exception
        return jsonify({"error": str(e)}), 500

@app.route('/get_data', methods=['GET'])  # 'GET' en majuscules
def get_data():
    global data, ligne_de_vie
    ligne_de_vie += 1
    ligne_de_vie %= 2
    data['check_up'] = {"ligne_de_vie": ligne_de_vie}
    return jsonify(data)

@app.route('/get_alarm_cpu', methods=['GET'])
def get_alarm_cpu():
    cpu_precedent = None
    for iteration in data["pc_data"]:
        if cpu_precedent is not None and iteration["cpu"] != cpu_precedent:
            # Retourne la première itération où la valeur du CPU change
            return jsonify({"cpu": iteration["cpu"]})
        cpu_precedent = iteration["cpu"]

    return jsonify({"message": "Aucun changement de CPU détecté"})


@app.route('/get_alarm_memory', methods=['GET'])
def get_alarm_memory():
    memory_precedent = None
    for iteration in data["pc_data"]:
        if memory_precedent is not None and iteration["memory"] != memory_precedent:
            # Retourne la première itération où la valeur du CPU change
            return jsonify({"memory": iteration["memory"]})
        memory_precedent = iteration["memory"]

    return jsonify({"message": "Aucun changement de memoire détecté"})

@app.route('/get_alarm_time_inteval', methods=['GET'])
def get_alarm_time_inteval():
    return jsonify({"elapse":time_intervals[0]})

@app.route('/get_check_port', methods=['GET'])  # 'GET' en majuscules
def get_check_port():
    # Passer seulement l'adresse IP à scan_ports
    ports = scan_ports('localhost')
    print("Ports ouverts:", ports)
    return jsonify({"list_port": ports})

@app.route('/get_check_demon', methods=['GET'])  # 'GET' en majuscules
def get_check_demon():
    running = is_process_running('demon.py')
    if running.get("running") is False:
        if seuils["demon"]["state"] == 0:
            logger.error("Erreur connection demon.")
            seuils["demon"]["state"] = 1
            send_mail("Erreur connection demon.", "Serveur defaut")
    else:
        if seuils["demon"]["state"] == 1:
            logger.warning("Reconnection demon.")
            seuils["demon"]["state"] = 0
            send_mail("Reconnection demon.", "Serveur defaut")
         
    return jsonify(running)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
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
    logs = lire_logs_get('mon_application.log')
    
    logs_json = {"logs": list(logs)}  # Convertit le générateur en liste si nécessaire
    return jsonify(logs_json)

def start_data_animov():

    chemin_actuel = os.getcwd()
    print("Chemin actuel                                 :", chemin_actuel)

    subprocess.Popen(["bash", "../../data_animov.sh"])

    logger.info("Start test_data_animov.")

def stop_data_animov(value = 0):
    
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        # logger.warning(f"{process.info['name']} - {process.info['cmdline']}")
        
        if process.info['name'] == 'python' or process.info['name'] == 'python3':  
            try:  
                if any('test_data_animov.py' in cmd for cmd in process.info['cmdline']):
                    print (process.info['name'], process.info['cmdline'], process.info['pid'])
                    os.kill(process.info['pid'], signal.SIGTERM)
            except:
                pass

    logger.info(f"Stop test_data_animov : {value} %")

def start_demon():
    script_path = 'demon.py'
    subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print ("start demon")
    logger.info("Start demon.")

def stop_demon():
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.info['name'] == 'python.exe' or process.info['name'] == 'pythonw.exe':
            if process.info['cmdline'] and any('demon.py' in cmd for cmd in process.info['cmdline']):
                print('kill', 'pid', process.info['pid'])
                try:
                    process.terminate()  # Utilisation de psutil pour terminer le processus
                    process.wait(timeout=5)  # Attendre que le processus se termine
                except psutil.NoSuchProcess:
                    print(f"Le processus avec PID {process.info['pid']} n'existe pas.")
                except psutil.AccessDenied:
                    print(f"Accès refusé pour terminer le processus avec PID {process.info['pid']}.")
                except psutil.TimeoutExpired:
                    print(f"Le processus avec PID {process.info['pid']} n'a pas pu être terminé dans le délai imparti.")
    print("Stop demon")
                
def start_mysql():
    try:
        control=0
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
            control = config.get("mysql_control", False)
            print(control)
        if control:
            container = client.containers.get(container_name_or_id)
            container.start()
            print("start MySQL")
            logger.info("Demarrage de MySQL.")
        else:

            print("Dont start MySQL")
            logger.info("Le demarrage de MySQL est omis.")

    except docker.errors.NotFound:
        print(f"Conteneur {container_name_or_id} non trouvé.")
        logger.error(f"Conteneur {container_name_or_id} non trouvé.")
    except Exception as e:
        print(f"Erreur lors du démarrage du conteneur: {e}")
        logger.error(f"Erreur lors du demarrage du conteneur: {e}")
    
def stop_mysql():
    try:
        container = client.containers.get(container_name_or_id)
        container.stop()
        logger.info("Stop mysql.")
        print(f"Conteneur {container_name_or_id} arrêté avec succès.")
    except docker.errors.NotFound:
        print(f"Conteneur {container_name_or_id} non trouvé.")
        logger.error(f"Conteneur {container_name_or_id} non trouvé.")
    except Exception as e:
        print(f"Erreur lors de l'arrêt du conteneur: {e}")
        logger.error(f"Erreur lors de l'arrêt du conteneur: {e}")
        
def send_data_to_server(data_to_send):
    url = "http://localhost:5002/receive_data"
    requests.post(url, json=data_to_send)


def scan_ports(host):
    global seuils
    open_ports = {}
    for service, port in {"Flask":5100, "Mysql": 3306, "Mysql2": 3303}.items():
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
        if seuils["mysql"]["state"] == 1 :
            logger.warning("Reconnection mysql.")
            seuils["mysql"]["state"] = 0
            send_mail("Reconnection mysql.", "Serveur defaut")
         
    return open_ports

def is_process_running(process_name):
    """
    Vérifie si un processus spécifique est en cours d'exécution.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and process_name in cmdline:
                return {'demon':{"running": True, "pid": proc.info['pid']}}
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return {'demon':{"running": False}}

def lire_logs(fichier_log):
    with open(fichier_log, 'rb') as file:
        file.seek(0, 2)  # Aller à la fin du fichier
        position = file.tell()
        ligne = bytearray()
        while position >= 0:
            file.seek(position)
            position -= 1
            caractere = file.read(1)
            if caractere == b'\n':
                # Ignorer le saut de ligne en début de fichier
                if ligne:
                    yield ligne.decode('utf-8')[::-1]
                ligne = bytearray()
            else:
                ligne.extend(caractere)
        # N'oubliez pas de renvoyer la dernière ligne
        yield ligne.decode('utf-8')[::-1]
        
def parse_log_line(line):
    # Utiliser une expression régulière pour séparer les composants du log
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\S+) - (\S+) - (.+)$", line)
    if match:
        date_time_str, module, level, message = match.groups()
        # Convertir la date et l'heure en un objet datetime pour le tri
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S,%f')
        level_num = log_levels.get(level, 0)
        
        return {
            'date_time': date_time,
            'module': module,
            'level': level,
            'level_num': level_num,
            'message': message.rstrip('\n')  # Enlever le retour à la ligne
        }
    else:
        return None  # ou lever une exception si le format est toujours attendu
        
def lire_logs_get(fichier_log):
    logs = []
    with open(fichier_log, 'r', encoding='ISO-8859-1') as file:
        for line in file:
            log_entry = parse_log_line(line)
            if log_entry:
                logs.append(log_entry)
    # Trier les logs par date et heure, du plus récent au plus ancien
    logs.sort(key=lambda entry: entry['date_time'], reverse=True)
    # Convertir les objets datetime en chaînes pour la sérialisation JSON
    for entry in logs:
        entry['date_time'] = entry['date_time'].strftime('%Y-%m-%d %H:%M:%S,%f')
    return logs

def process_alarm(device):
    global data, seuils
    sll = data['pc_data'][0][device]

    if sll > seuils[device]["seuil1"] and seuils[device]["state"] == 0:
        logger.info(f"Alerte {device} {sll} %.")
        seuils[device]["state"]=1
        send_mail(f"Alerte {device} {sll} %.", "Serveur en surcharge")
    elif sll < seuils[device]["seuil2"] and seuils[device]["state"] == 1:
        logger.info(f"Fin d'alerte {device} {sll} %.")
        seuils[device]["state"]=0
        send_mail(f"Fin d'alerte {device} {sll} %.", "Fin serveur en surcharge")

def process_alarm_elapse( delay, device = "elapse"):
    global data, seuils

    if delay > seuils[device]["seuil1"] and seuils[device]["state"] == 0:
        logger.info(f"Alerte reponce demon {delay} s.")
        seuils[device]["state"]=1
        send_mail(f"Alerte reponce demon {delay} s.", "Demon réponce !")
    elif delay < seuils[device]["seuil2"] and seuils[device]["state"] == 1:
        logger.info(f"Fin d'alerte reponce demon  {delay} s.")
        seuils[device]["state"]=0
        send_mail(f"Fin d'alerte reponce demon {delay} s.", "Demon réponce !")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= '5002', debug=False)
