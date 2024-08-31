import streamlit as st
from page.page import Analytics
import requests
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import time
from datetime import timedelta
import plotly.graph_objects as go

# Configuration de la page Streamlit pour un affichage large
st.set_page_config(layout="wide")

END_POINT = 'localhost:5500'

class VideoAnalytics(Analytics):
    def __init__(self):
        super().__init__()
        # Initialisation de la classe parent Analytics

    def get_api_animov(self, sources, with_global_stats):
        """
        Récupère les données de l'API animov pour les sources spécifiées.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        # Construction de l'URL de l'API avec les paramètres
        ROUTE = f'get_data_animov_ch?sources={sources}&with_images=Single&with_detect=False&with_stats=False&with_global_stats={with_global_stats}'
        # st.write(ROUTE)
        url = f'http://{END_POINT}/{ROUTE}'

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response = response.json()
            return response
        
        return None

    def query_get_chevres_serie_jour(self, source, mode='normal'):
        """
        Récupère les données de la série de chèvres par jour pour la source spécifiée.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        # URL de l'API pour les données par jour
        if mode == 'degrade':
            url = f'http://{END_POINT}/get_serie_last_jour'
        else:
            url = f'http://{END_POINT}/get_serie_last_jour'

        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)

            # Filtrer les données pour la source spécifiée
            filtered_df = df[df['source'] == source]

            return filtered_df

        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'Other error occurred: {err}')
        
        return pd.DataFrame()

    def extract_image(self, message, detect, with_id=False, with_score=False):
        """
        Extrait l'image à partir du message et ajoute des annotations si nécessaire.
        """
        image_data = base64.b64decode(message['data'][0]['frame'])
        image = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(image)

        if detect:
            df_detect = pd.DataFrame(message['data'][0]['detect'], columns=['id', 'x_min', 'y_min', 'x_max', 'y_max', 'score', 'classe', '0', '1', '2'])

            for index, row in df_detect.iterrows():
                top_left = (row['x_min'], row['y_min'])
                bottom_right = (row['x_max'], row['y_max'])

                hauteur_image = image.height
                taille_police = hauteur_image // 40
                font = ImageFont.load_default().font_variant(size=taille_police)

                if with_score:
                    position = (row['x_max'] + 5, row['y_min'] + 5)
                    texte = f"{round(row['score'], 3)}"
                    draw.text(position, texte, fill="yellow", font=font)

                if with_id:
                    position = (row['x_min'] + 5, row['y_min'] + 5)
                    texte = f"{int(row['id'])}"
                    draw.text(position, texte, fill="white", font=font)

                # Dessiner un rectangle autour de la détection
                if row['classe'] == 0:
                    draw.rectangle([top_left, bottom_right], outline="green", width=3)
                else:
                    draw.rectangle([top_left, bottom_right], outline="red", width=3)

        return image.resize((1280, 720)), draw

    def display_graph(self, df):
        """
        Affiche les graphiques basés sur les données fournies.
        """
        def axe_x(premier_timestamp):
            """
            Calcule les axes x pour les graphiques.
            """
            timestamp_fin = premier_timestamp + timedelta(days=1)
            debut_axe_x = premier_timestamp.strftime('%Y-%m-%d %H:%M')
            fin_axe_x = timestamp_fin.strftime('%Y-%m-%d %H:%M')
            return debut_axe_x, fin_axe_x

        # Création des onglets pour afficher les données sous différentes formes
        tabh1, tabh2, tabh3 = st.tabs(["Courbe sur une journée", "Proportion debout/couché", "Données"])

        df['timestamp'] = pd.to_datetime(df['timestamp'])  # Conversion des timestamps en format datetime

        with tabh1:
            # Calculer les moyennes par frame
            df['total'] = df['total'] / df['nb_frames']
            df['couche'] = df['couche'] / df['nb_frames']
            df['debout'] = df['debout'] / df['nb_frames']

            # Préparer les données pour le graphique
            df_melted = df.melt(id_vars=['timestamp'], value_vars=['debout', 'couche', 'total'], 
                                var_name='État', value_name='Moyenne jour du nombre de chèvres')

            fig = go.Figure()
            display_type = st.toggle('Ligne')
            mode = 'lines' if display_type else 'markers'

            for etat in df_melted['État'].unique():
                df_filtre = df_melted[df_melted['État'] == etat]
                if etat == 'total':
                    fig.add_trace(go.Scatter(x=df_filtre['timestamp'], y=df_filtre['Moyenne jour du nombre de chèvres'],
                                            mode=mode, name=etat,
                                            line=dict(width=5, dash='dash'),
                                            marker=dict(size=5)))
                else:
                    fig.add_trace(go.Scatter(x=df_filtre['timestamp'], y=df_filtre['Moyenne jour du nombre de chèvres'],
                                            mode=mode, name=etat,
                                            marker=dict(size=5)))

            fig.update_layout(
                title='Activité moyenne des chèvres.',
                xaxis_title='Date et Heure',
                yaxis_title='Nombre moyen de chèvres',
                margin=dict(l=0, r=0)
            )

            debut_axe_x, fin_axe_x = axe_x(df_filtre['timestamp'].min())
            fig.update_xaxes(range=[debut_axe_x, fin_axe_x])
            st.plotly_chart(fig, use_container_width=True)

        with tabh3:
            df_ = df.set_index('timestamp')
            st.dataframe(df_)

        with tabh2:
            df['% debout'] = (df['debout'] / (df['debout'] + df['couche'])) * 100
            df['% couche'] = (df['couche'] / (df['debout'] + df['couche'])) * 100

            df_melted = df.melt(id_vars=['timestamp'], value_vars=['% debout', '% couche'], 
                                var_name='État', value_name='Moyenne jour du nombre de chèvres')

            fig = go.Figure()
            for etat in df_melted['État'].unique():
                df_filtre = df_melted[df_melted['État'] == etat]
                fig.add_trace(go.Bar(x=df_filtre['timestamp'].dt.strftime('%Y-%m-%d %H:%M'), 
                                    y=df_filtre['Moyenne jour du nombre de chèvres'],
                                    name=etat))

            fig.update_layout(
                title='Répartition debout/couché sur une journée par quart-heures.',
                xaxis_title='Date et Heure',
                yaxis_title='% de chèvres',
                margin=dict(l=0, r=0),
            )

            fig.update_layout(barmode='stack')
            fig.update_yaxes(range=[0, 100])
            debut_axe_x, fin_axe_x = axe_x(df_filtre['timestamp'].min())

            fig.update_xaxes(range=[debut_axe_x, fin_axe_x])
            fig.add_hline(y=50, line_dash="dot", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

    def query_get_sources(self):
        """
        Récupère les sources disponibles à partir de l'API.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        url = f'http://{END_POINT}/sources'
        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            return df

        except requests.exceptions.HTTPError as http_err:
            print(f"Erreur HTTP : {http_err}, URL : {url}")
        except requests.exceptions.RequestException as err:
            print(f"Erreur de requête : {err}, URL : {url}")
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"Erreur de décodage JSON : {json_err}, Réponse : {response.text}")

        return None

    def setup_radio_sources(self):
        """
        Crée une interface de sélection de source avec les options disponibles.
        """
        query_result = self.query_get_sources()

        # Crée une liste de sources à partir du résultat de la requête
        source_list = [str(source) for source in query_result['source'] if source is not None]

        # Utilise st.sidebar.radio pour permettre à l'utilisateur de sélectionner une seule source
        selected_source = st.sidebar.radio("Sources", source_list, key="source_selection")

        return selected_source

    def run(self):
        """
        Point d'entrée principal pour exécuter l'application Streamlit.
        """
        detect = st.sidebar.toggle('Avec detections')
        if detect:
            with_id = st.sidebar.toggle('Avec Id')
            with_score = st.sidebar.toggle('Avec score')
        else:
            with_id = False
            with_score = False

        selected_source = self.setup_radio_sources()

        message = self.get_api_animov(selected_source, 'False')

        df = self.query_get_chevres_serie_jour(int(selected_source))

        on_line = True

        if df.empty:
            df = self.query_get_chevres_serie_jour(int(selected_source), 'degrade')
            on_line = False

        col21, col22, col23 = st.columns([1, 7, 1])
        with col22:
            image, draw = self.extract_image(message, detect, with_id, with_score)

            if not on_line:
                hauteur_image = image.height
                taille_police = hauteur_image // 20
                position = (10, 10)
                font = ImageFont.load_default().font_variant(size=taille_police)
                texte = "Flux de données interrompu."
                draw.text(position, texte, fill="red", font=font)

            st.image(image)

        self.display_graph(df)

        if on_line:
            on = st.sidebar.toggle('Activation RT')

            if on:
                time.sleep(5)
                st.rerun()

if __name__ == "__main__":
    app = VideoAnalytics()
    try:
        app.run()
    except:
        pass
