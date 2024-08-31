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

    # # Configuration de l'email
    # sender_email = "manu@certif.fr"
    # receiver_email = "arscg@certif.fr"
    # subject = "Test Email de totol"
    # body = "Ceci est un email de test."
    
    # # Création du message
    # message = MIMEMultipart()
    # message["From"] = sender_email
    # message["To"] = receiver_email
    # message["Subject"] = subject
    # message.attach(MIMEText(body, "plain"))
    
    # # Connexion au serveur SMTP
    # try:
    #     server = smtplib.SMTP("localhost", 587)
    #     server.set_debuglevel(1)  # Activer le mode débogage pour plus de détails
    
    #     # Authentification sans STARTTLS
    #     server.ehlo()
    #     server.login(sender_email, "manu")  # Remplacez "manu" par le mot de passe correct
    #     server.sendmail(sender_email, receiver_email, message.as_string())
    #     server.quit()
    #     print("Email envoyé avec succès.")
    # except smtplib.SMTPAuthenticationError as e:
    #     print(f"Erreur lors de l'authentification: {e.smtp_code} - {e.smtp_error.decode('utf-8')}")
    # except Exception as e:
    #     print(f"Erreur lors de l'envoi de l'email: {e}")
    
    #     print(f"Erreur lors de l'envoi de l'email: {e}")
    # # send_email(100)