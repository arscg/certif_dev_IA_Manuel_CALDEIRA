import streamlit as st
from model.model import segment_video
import os
from page.page import Analytics
import requests
import plotly.graph_objects as go
import pandas as pd

# Configuration de la page Streamlit pour un affichage large
st.set_page_config(layout="wide")

END_POINT = 'localhost:5500'

class VideoAnalytics(Analytics):
    def __init__(self):
        super().__init__()
        
        # Initialiser les informations de segmentation vidéo
        info = segment_video()

        # Durée totale de la vidéo en secondes
        self.duree_totale = 50  
        # Obtenir et trier les segments vidéo
        self.segments = sorted(os.listdir(info))
        # Segment vidéo actuel
        self.segment_actuel = 0
        # Obtenir les données des chèvres par minute
        self.chevres_minutes = self.query_get_chevres_minutes()

    def render_slider(self):
        """
        Affiche un slider dans la barre latérale pour contrôler la position de la vidéo.
        """
        return st.sidebar.slider("Position de la vidéo", 10, self.duree_totale, 0, key='position')

    def navigate_segments(self, position):
        """
        Détermine quel segment vidéo jouer en fonction de la position du slider.
        """
        segment_index = int(position / 10)
        if self.segment_actuel != len(self.segments) - 1:
            self.segment_actuel += 1
        return self.segments[segment_index]

    def play_video(self, chemin_segment):
        """
        Joue le segment vidéo spécifié.
        """
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.video(chemin_segment)

    def query_get_chevres_minutes(self):
        """
        Récupère les données des chèvres par minute depuis l'API.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }
        
        url = f'http://{END_POINT}/chevres_minutes'
        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            df['jour'] = pd.to_datetime(df['jour'], format='%a, %d %b %Y %H:%M:%S GMT')
            return df

        except requests.exceptions.HTTPError as http_err:
            print(f"Erreur HTTP : {http_err}, URL : {url}")
        except requests.exceptions.RequestException as err:
            print(f"Erreur de requête : {err}, URL : {url}")
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"Erreur de décodage JSON : {json_err}, Réponse : {response.text}")

        return None
        
    def display_graph(self, position):
        """
        Affiche un graphique de l'évolution moyenne du nombre de chèvres par minute pour toutes les sources.
        """
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            fig = go.Figure()

            for src in [1, 2, 3, 4]:
                query_result = self.chevres_minutes

                # Filtrer les résultats pour la source et la plage de temps
                filtered_query_result = query_result[
                    (query_result['minutes'] >= position) & 
                    (query_result['minutes'] < position + 10) &
                    (query_result['source'] == int(src))
                ]

                filtered_query_result['somme_classes'] = filtered_query_result['class_0'] + filtered_query_result['class_1']
                average_per_minute = filtered_query_result.groupby('minutes', as_index=False).mean()
                is_visible = True if src == 1 else 'legendonly'

                # Ajouter un tracé à la figure pour la source actuelle
                fig.add_trace(
                    go.Scatter(
                        x=average_per_minute['minutes'], 
                        y=average_per_minute['somme_classes'], 
                        mode='lines',
                        name=f'Source {src}',
                        visible=is_visible
                    )
                )

            # Mise à jour du layout du graphique
            fig.update_layout(
                title='Evolution moyenne du nombre de chèvres par minute pour toutes les sources',
                xaxis_title='Minutes',
                yaxis_title='Nombre moyen de chèvres'
            )

            config = {
                'displayModeBar': True,
                'scrollZoom': True,
                'staticPlot': False,
                'modeBarButtonsToRemove': ['select2d', 'lasso2d']
            }

            # Afficher le graphique avec Streamlit
            st.plotly_chart(fig, use_container_width=True, config=config)

    def run(self):
        """
        Point d'entrée principal pour exécuter l'application Streamlit.
        """
        # Afficher le slider pour contrôler la position de la vidéo
        position = self.render_slider()
        # Obtenir le segment vidéo correspondant à la position du slider
        segment = self.navigate_segments(position)
        chemin_segment = os.path.join(segment_video(), segment)
        # Jouer le segment vidéo
        self.play_video(chemin_segment)
        # Afficher le graphique des données des chèvres
        self.display_graph(position)

if __name__ == "__main__":
    app = VideoAnalytics()
    app.run()
