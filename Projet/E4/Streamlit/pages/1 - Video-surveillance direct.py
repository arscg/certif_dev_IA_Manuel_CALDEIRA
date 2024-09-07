import streamlit as st
from page.page import Analytics
import requests
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import time
import warnings

# Configuration de la page Streamlit
st.set_page_config(layout="wide")
warnings.filterwarnings('ignore')

END_POINT = 'localhost:5500'

# Initialisation de la variable d'état pour la réinitialisation du formulaire, si elle n'existe pas
if 'reset_form' not in st.session_state:
    st.session_state['reset_form'] = False

# Fonction pour réinitialiser le formulaire
def reset_form():
    st.session_state['reset_form'] = True
    st.experimental_rerun()

class RealTime(Analytics):
    def __init__(self):
        super().__init__()
        
    def display_cam(self, source, frame, data, data2, df_stats=None):
        """
        Affiche l'image de la caméra avec les statistiques et annotations.
        """
        image = self.extract_image(frame)  # Extraire l'image de la frame encodée en base64

        hauteur_image = image.height
        taille_police = hauteur_image // 20  # Déterminer la taille de la police en fonction de la hauteur de l'image

        font = ImageFont.load_default().font_variant(size=taille_police)
        draw = ImageDraw.Draw(image)

        # Position et affichage des statistiques de la frame
        position = (10, 10)
        if data2.loc['total'] >= 0:
            texte = 'Statistiques de la frame:\n' f"Total : {data2.loc['total']}\nDebout : {data2.loc['debout']}\nCouche : {data2.loc['couche']}"
            draw.text(position, texte, fill="Green", font=font)

        # Position et affichage des statistiques moyennes sur la dernière minute
        position = (10, 200)
        if data2.loc['total'] >= 0:
            texte = 'Statistiques\nmoyennes sur\nla dernière minute:\n' + f"Total : {(df_stats.loc['total'] / df_stats.loc['nb_frames']).round(2)}\nDebout : {(df_stats.loc['debout'] / df_stats.loc['nb_frames']).round(2)}\nCouche : {(df_stats.loc['couche'] / df_stats.loc['nb_frames']).round(2)}"
            draw.text(position, texte, fill="Maroon", font=font)

        # Position et affichage de la source de l'image
        position = (image.width - 170, 10)
        texte = f"Source : {source}"
        draw.text(position, texte, fill="White", font=font)

        st.image(image)  # Afficher l'image dans Streamlit

    def extract_image(self, frame):
        """
        Extraire l'image de la frame encodée en base64.
        """
        image_data = base64.b64decode(frame)
        image = Image.open(io.BytesIO(image_data))
        return image.resize((1280, 720))

    def extract_global_stats(self, stats):
        """
        Extraire les statistiques globales des données.
        """
        dfs = []
        for item in stats:
            data_dict = {}
            for key, value in item.items():
                data_dict[key] = value
                dfs.append(pd.DataFrame.from_dict(data_dict, orient='index'))

        df = pd.concat(dfs)
        return df
    
    def extract_frame_stats_chevres(self, stats):
        """
        Extraire les statistiques par frame pour les chèvres.
        """
        dfs = []
        for stt in stats:
            try:
                data_dict = {f"source_{stt['source_id']}": {'total': stt['stats']['count'],
                                                            'debout': stt['stats']['debout'],
                                                            'couche': stt['stats']['couche']}}
                dfs.append(pd.DataFrame.from_dict(data_dict, orient='index'))
            except:
                data_dict = {f"source_{stt['source_id']}": {'total': -1,
                                                            'debout': -1,
                                                            'couche': -1}}
                dfs.append(pd.DataFrame.from_dict(data_dict, orient='index'))

        df = pd.concat(dfs)
        return df
    
    def display(self, source, response, k, df, df_, df_stats, df_stats_heure):
        """
        Affiche les données et statistiques dans les différents onglets de l'interface.
        """
        if (not df.empty) and (not df_.empty) and (not df_stats.empty) and (not df_stats_heure.empty):

            tab11, tab12, tab13 = st.tabs(["Cams", "Stats minute", "Stats heure"])

            with tab12:
                # Affichage des statistiques par minute
                df_stats_source = df_stats.loc[f'source_{source}']

                indices = ['Moyenne', 'Max', 'Min', 'Écart Type', 'Q1', 'Q2', 'Q3', 'Mode']

                df_donnees_couche = pd.DataFrame([
                    (df_stats_source.loc['couche'] / df_stats_source.loc['nb_frames']).round(3),
                    df_stats_source.loc['max_couche'],
                    df_stats_source.loc['min_couche'],
                    df_stats_source.loc['std_couche'],
                    df_stats_source.loc['Q1_couche'],
                    df_stats_source.loc['Q2_couche'],
                    df_stats_source.loc['Q3_couche'],
                    df_stats_source.loc['mode_couche'],
                ],
                    columns=['couche'],
                    index=indices
                )

                df_donnees_debout = pd.DataFrame([
                    (df_stats_source.loc['debout'] / df_stats_source.loc['nb_frames']).round(3),
                    df_stats_source.loc['max_debout'],
                    df_stats_source.loc['min_debout'],
                    df_stats_source.loc['std_debout'],
                    df_stats_source.loc['Q1_debout'],
                    df_stats_source.loc['Q2_debout'],
                    df_stats_source.loc['Q3_debout'],
                    df_stats_source.loc['mode_debout'],
                ],
                    columns=['debout'],
                    index=indices
                )

                df_donnees_total = pd.DataFrame([
                    (df_stats_source.loc['total'] / df_stats_source.loc['nb_frames']).round(3),
                    df_stats_source.loc['max_total'],
                    df_stats_source.loc['min_total'],
                    df_stats_source.loc['std_total'],
                    df_stats_source.loc['Q1_total'],
                    df_stats_source.loc['Q2_total'],
                    df_stats_source.loc['Q3_total'],
                    df_stats_source.loc['mode_total'],
                ],
                    columns=['total'],
                    index=indices
                )

                col11, col12, col13 = st.columns([2, 5, 2])
                with col12:
                    df_concatene = pd.concat([df_donnees_couche, df_donnees_debout, df_donnees_total], axis=1)
                    st.dataframe(df_concatene.T)

            with tab13:
                # Affichage des statistiques par heure
                col11, col12, col13 = st.columns([2, 5, 2])
                with col12:
                    df_stats_source = df_stats_heure.loc[f'source_{source}']

                    indices = ['Moyenne', 'Max', 'Min', 'Écart Type']

                    df_donnees_couche = pd.DataFrame([
                        (df_stats_source.loc['moyenne_couche']).round(3),
                        df_stats_source.loc['max_couche'],
                        df_stats_source.loc['min_couche'],
                        df_stats_source.loc['ecart_type_couche']
                    ],
                        columns=['couche'],
                        index=indices
                    )

                    df_donnees_debout = pd.DataFrame([
                        (df_stats_source.loc['moyenne_debout']).round(3),
                        df_stats_source.loc['max_debout'],
                        df_stats_source.loc['min_debout'],
                        df_stats_source.loc['ecart_type_debout']
                    ],
                        columns=['debout'],
                        index=indices
                    )

                    df_donnees_total = pd.DataFrame([
                        (df_stats_source.loc['moyenne_total']).round(3),
                        df_stats_source.loc['max_total'],
                        df_stats_source.loc['min_total'],
                        df_stats_source.loc['ecart_type_total']
                    ],
                        columns=['total'],
                        index=indices
                    )

                    df_concatene = pd.concat([df_donnees_couche, df_donnees_debout, df_donnees_total], axis=1)
                    st.dataframe(df_concatene.T)

            if df.empty and df_.empty:
                # Affichage de l'image sans statistiques si les données sont vides
                self.display_cam(source,
                                 response['data'][k]['frame'],
                                 None,
                                 None,
                                 df_stats.loc[f'source_{source}'],
                                 )
            elif df.empty:
                # Affichage de l'image avec les statistiques globales uniquement
                self.display_cam(source,
                                 response['data'][k]['frame'],
                                 None,
                                 df_.loc[f'source_{source}'],
                                 df_stats.loc[f'source_{source}'],
                                 )
            elif df_.empty:
                # Affichage de l'image avec les statistiques de la frame uniquement
                self.display_cam(source,
                                 response['data'][k]['frame'],
                                 df.loc[f'source_{source}'],
                                 None,
                                 df_stats.loc[f'source_{source}'],
                                 )
            else:
                # Affichage de l'image avec les deux types de statistiques
                self.display_cam(source,
                                 response['data'][k]['frame'],
                                 df.loc[f'source_{source}'],
                                 df_.loc[f'source_{source}'],
                                 df_stats.loc[f'source_{source}'],
                                 )
        else:
            # Affichage d'un message d'erreur si le flux de données est interrompu
            image = self.extract_image(response['data'][k - 1]['frame'])

            hauteur_image = image.height
            taille_police = hauteur_image // 20

            position = (image.width - 170, 10)
            font = ImageFont.load_default().font_variant(size=taille_police)
            draw = ImageDraw.Draw(image)

            texte = f"Source : {source}"
            draw.text(position, texte, fill="White", font=font)

            position = (10, 10)
            texte = "Flux de données interrompu."
            draw.text(position, texte, fill="red", font=font)

            st.image(image)

    def get_api_animov(self, sources, mode_images, with_detect, with_stats, with_global_stats, on):
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

        on_display_stats = False

        if on:
            on_display_stats = st.sidebar.toggle('Avec affichage stats RT', value=True)

        if on_display_stats:
            with_stats = "Lite"
        else:
            with_stats = "False"

        ROUTE = f'get_data_animov_ch?sources={sources}&with_images={mode_images}&with_detect={with_detect}&with_stats={with_stats}&with_global_stats={with_global_stats}'
        # st.write(ROUTE)
        url = f'http://{END_POINT}/{ROUTE}'

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response = response.json()
            try:
                df = self.extract_global_stats(response['_general_stats'])
            except:
                df = pd.DataFrame()

            df_ = self.extract_frame_stats_chevres(response['data'])

            return response, df, df_

        return None, None, None

    def get_api_stats(self, type='minute'):
        """
        Récupère les statistiques de l'API pour le type spécifié (minute ou heure).
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        if type == 'minute':
            ROUTE = 'stats_minute'
        else:
            ROUTE = 'stats_heure'

        url = f'http://{END_POINT}/{ROUTE}'

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response = response.json()
            df = pd.DataFrame(response)

            if not df.empty:
                df = df.set_index('source')
                df.index = ['source_' + str(idx) for idx in df.index]

                try:
                    df = df.drop(columns=['timestamp'])
                    df['mode_total'] = df['mode_total'].astype(object)
                    df['mode_couche'] = df['mode_couche'].astype(object)
                    df['mode_debout'] = df['mode_debout'].astype(object)
                    df['Q1_total'] = df['Q1_total'].astype(int)
                    df['Q2_total'] = df['Q2_total'].astype(int)
                    df['Q3_total'] = df['Q3_total'].astype(int)
                    df['Q1_debout'] = df['Q1_debout'].astype(int)
                    df['Q2_debout'] = df['Q2_debout'].astype(int)
                    df['Q3_debout'] = df['Q3_debout'].astype(int)
                    df['Q1_couche'] = df['Q1_couche'].astype(int)
                    df['Q2_couche'] = df['Q2_couche'].astype(int)
                    df['Q3_couche'] = df['Q3_couche'].astype(int)
                except:
                    pass

            return df

        return pd.DataFrame()
    
    def run(self):
        """
        Point d'entrée principal pour exécuter l'application Streamlit.
        """
        sources = '1,2,3,4'
        mode_images = 'Single'
        with_detect = 'False'
        with_stats = 'Lite'
        with_global_stats = 'True'

        on = st.sidebar.toggle('Activation RT')

        response, df, df_ = self.get_api_animov(sources, mode_images, with_detect, with_stats, with_global_stats, on)

        df_stats_minute = self.get_api_stats()
        df_stats_heure = self.get_api_stats(type='heure')

        col1, col2 = st.columns([1, 1])
        k = -1
        with col1:
            k += 1
            try:
                self.display('1', response, k, df, df_, df_stats_minute, df_stats_heure)
            except:
                pass

            try:
                k += 1
                self.display('2', response, k, df, df_, df_stats_minute, df_stats_heure)
            except:
                pass

        with col2:
            try:
                k += 1
                self.display('3', response, k, df, df_, df_stats_minute, df_stats_heure)
            except:
                pass

            try:
                k += 1
                self.display('4', response, k, df, df_, df_stats_minute, df_stats_heure)
            except:
                pass

        if on:
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    app = RealTime()
    try:
        app.run()
    except:
        pass
