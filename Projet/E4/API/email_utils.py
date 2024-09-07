# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:02:30 2024

@author: arsca
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(average_rmse):
    from_email = "manu@certif.fr"
    to_email = "arscg@certif.fr"
    subject = "Alerte: RMSE moyen élevé"
    body = f"La moyenne des RMSE est supérieure à 25. Valeur actuelle: {average_rmse}"

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