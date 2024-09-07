import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import cv2
from PIL import Image
from ultralytics import YOLO
import os


st.set_page_config(layout="wide")

chemin_repertoire = os.getcwd() +"//Videos_Test"
chemin_repertoire_models = os.getcwd() + "//run//train"

@st.cache_resource
def load_model(model_selection):
    st.session_state.tab1 = None
    st.session_state.tab2 = None
    model = YOLO(model_selection)
    return model

def liste_models(chemin_repertoire):
    # Liste pour stocker les noms des répertoires
    noms_repertoires = []

    # Parcourir les éléments dans le chemin spécifié
    for nom in os.listdir(chemin_repertoire):
        # Construire le chemin complet
        chemin_complet = os.path.join(chemin_repertoire, nom)
        
        # Vérifier si l'élément est un répertoire
        if os.path.isdir(chemin_complet):
            noms_repertoires.append(nom)
    
    return noms_repertoires

frame_num = st.sidebar.slider(
    'Sélectionnez une minute',  # Le texte affiché à côté du slider
    min_value=0,   # La valeur minimale du slider
    max_value=90, # La valeur maximale du slider
    value=0,      # La valeur par défaut du slider
    step=1         # Le pas d'incrémentation entre les valeurs du slider
)

col1, col2 = st.columns(2)

cap = cv2.VideoCapture(r"output_video_D02_20220602013531.MP4")
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num * 60 * 25)

if cap.isOpened():

    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        # try:

        model_selection = st.sidebar.selectbox("Sélectionnez un model", liste_models(chemin_repertoire_models))
        # except:
        #     pass
        
        frame_cof = st.sidebar.slider(
            'Degré de confience',  
            min_value=0.1,
            max_value=1.0, 
            value=0.5, 
            step=0.02
        )

        model = load_model(os.path.join(chemin_repertoire_models, model_selection) + "//weights//best.pt")                    
        results = model(frame, conf=frame_cof, iou=0.5 , device= 'cpu', augment=True, agnostic_nms=True, classes= None)

        # Visualiser les résultats
        annotated_frame = results[0].plot()     
        
        # Afficher l'image avec streamlit
        st.image(annotated_frame, caption=f'minute {frame_num}')

        nouvelles_lignes = []
        predictions_df = pd.DataFrame()

        for i, res in enumerate(results):  
            boxes = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            cls_ids = res.boxes.cls.cpu().numpy()

            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                x1, y1, x2, y2 = box
                
                x1 = int(x1)#f"{x1:.0f}"
                y1 = int(y1)#f"{y1:.0f}"
                x2 = int(x2)#f"{x2:.0f}"
                y2 = int(y2)#f"{y2:.0f}"
                conf = f"{conf:.3f}"
            
                # Pour cls_id, si c'est un entier, pas besoin de formatage pour les décimales
                cls_id = int(cls_id)
                    
                nouvelles_lignes.append({
                    'frame': cap.get(cv2.CAP_PROP_POS_FRAMES),
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2,
                    'confiance': conf,
                    'id_classe': cls_id
                })

            if nouvelles_lignes:  # Vérifie s'il y a des nouvelles lignes à ajouter
                predictions_df = pd.concat([predictions_df, pd.DataFrame(nouvelles_lignes)], ignore_index=True)
    
            st.write("Prédiction Image courante")
            st.write(predictions_df)

# Fermer le captureur de vidéo
cap.release()
