   
import psutil
import requests
import time
from datetime import datetime
import random
import math
import yaml
import logging

# Configuration du logger
logging.basicConfig(filename='demon.log', filemode='a', level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

logging.warning("Demarage.")

#163.172.167.26
serveur = "localhost"
    
def get_system_info(cpu_factor):
    cpu = psutil.cpu_percent(interval=1)*cpu_factor
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    timestamp = datetime.now().isoformat()  # Conversion de datetime en chaîne ISO 8601
    logging.info("Informations système collectées")
    return {"cpu": cpu, "memory": memory, "disk": disk, "timestamp": timestamp}

def send_data_to_grafana():
    url = f"http://{serveur}:3000/d/ec216634-47fd-4828-a686-5f84772dfc9d/test-2"
    logging.info("Consulter grafana")
    
    try:
        response = requests.post(url)
        logging.info("Consulté.")
        return response
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de consultations : %s", e)
        return None

def send_data_to_server(data):
    url = f"http://{serveur}:5002/receive_data"
    wrapped_data = {"pc_data": data}
    logging.info("Envoi des données au serveur")
    
    try:
        response = requests.post(url, json=wrapped_data)
        logging.info("Données envoyées avec succès.")
        return response
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de l'envoi des données : %s", e)
        return None
    
data_storage = []  
randomization_factor = None
cpu_factor = None

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)
    logging.info("Fichier de configuration lu")

send_data_to_grafana()

while True:
# for k in range(50000):
    
    if randomization_factor != config["randomization_factor"]:
        randomization_factor = config["randomization_factor"]
        logging.info("Facteur de randomisation mis à jour : %s", randomization_factor)

    if cpu_factor != config["cpu_factor"]:
        cpu_factor = config["cpu_factor"]
        logging.info("Facteur CPU mis à jour : %s", cpu_factor)
    
    system_info = get_system_info(cpu_factor)
    
    data_storage.insert(0, system_info)

    if len(data_storage) > 100:
        data_storage.pop()
        logging.info("Taille maximale de stockage atteinte. Suppression du dernier élément.")
    
   
    random_value = random.uniform(0.01, 1)  
    logarithmic_delay = math.log(random_value) / math.log(0.01) * randomization_factor
    time.sleep(logarithmic_delay)
    
    # Envoyer l'intégralité du tableau nommé 'pc_data'
    print(send_data_to_server(data_storage))




