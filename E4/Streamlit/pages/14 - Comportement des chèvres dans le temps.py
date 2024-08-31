import streamlit as st
from page.page import Analytics
import plotly.graph_objects as go
import matplotlib.colors as mcolors
from plotly.subplots import make_subplots
import seaborn as sns
import pandas as pd
import requests

# Configuration de la page Streamlit pour un affichage large
st.set_page_config(layout="wide")

END_POINT = 'localhost:5500'

class VideoAnalytics_3_(Analytics):
    def __init__(self):
        super().__init__()

        # Récupération des données initiales pour les sources, dates et données de chèvres
        self.sources = self.query_get_sources()
        self.dates = self.query_get_dates()
        self.chevres_heure = self.query_get_chevres_heure()
        self.chevres_minutes = self.query_get_chevres_minutes()

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

    def query_get_dates(self):
        """
        Récupère les dates disponibles à partir de l'API.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        url = f'http://{END_POINT}/dates'
        response = requests.get(url, headers=headers)

        try:
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            df['dates'] = pd.to_datetime(df['dates'], format='%a, %d %b %Y %H:%M:%S GMT')
            return df

        except requests.exceptions.HTTPError as http_err:
            print(f"Erreur HTTP : {http_err}, URL : {url}")
        except requests.exceptions.RequestException as err:
            print(f"Erreur de requête : {err}, URL : {url}")
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"Erreur de décodage JSON : {json_err}, Réponse : {response.text}")

        return None

    def query_get_chevres_heure(self):
        """
        Récupère les données horaires des chèvres à partir de l'API.
        """
        # Vérifier si le jeton est disponible dans la session
        if 'token' not in st.session_state:
            st.error("Veuillez vous authentifier d'abord.")
            return

        headers = {
            'x-access-tokens': st.session_state.token,
            'Content-Type': 'application/json'
        }

        url = f'http://{END_POINT}/chevres_heures'
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

    def query_get_chevres_minutes(self):
        """
        Récupère les données minutaires des chèvres à partir de l'API.
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

    def setup_checkbox_sources(self):
        """
        Affiche les cases à cocher pour la sélection des sources.
        """
        query_result = self.query_get_sources()
        selected_sources = []
        source_list = [str(source) for source in query_result['source'] if source is not None]

        for idx, source in enumerate(source_list):
            if st.sidebar.checkbox(source, key=f"source_{idx}"):
                selected_sources.append(source)

        return selected_sources

    def setup_checkbox_date(self):
        """
        Affiche les cases à cocher pour la sélection des dates.
        """
        query_result = self.query_get_dates()
        selected_sources = []
        source_list = [date.strftime('%Y-%m-%d') for date in query_result['dates'] if date is not None]

        for idx, source in enumerate(source_list):
            if st.sidebar.checkbox(source, key=f"jour_{idx}"):
                selected_sources.append(source)

        return selected_sources

    def comportement_chevres_acceuil(self, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH, scale='heures', MODE_GRAPH='lines'):
        """
        Affiche les graphiques de comportement des chèvres pour les états couchées ou debout.
        """
        st.title('Chèvres couchées ou debout évolution temporelle.')

        if scale == 'minutes':
            query_result = self.chevres_minutes
        elif scale == 'heures':
            query_result = self.chevres_heure
        else:
            query_result = self.chevres_heure
            scale = 'heures'

        sources = [1, 2, 3, 4]

        first_debout = True
        first_couche = True
        first_total = True

        # Créer une figure avec des sous-graphiques (4 rangées, 1 colonne)
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=[f'Source {src}' for src in sources])
        # Création de la palette de couleurs
        palette = sns.color_palette("Paired", 10)
        colors = [mcolors.to_hex(rgb) for rgb in palette]

        # Pour chaque source, ajouter les données correspondantes à la figure
        for i, src in enumerate(sources, start=1):
            query_result_source = query_result[query_result['source'] == src]

            if scale == 'minutes':
                query_result_source['datetime'] = pd.to_datetime(
                    query_result_source['jour'].astype(str) + ' ' +
                    query_result_source['heure'].astype(str) + ':' +
                    query_result_source['minutes'].astype(str)
                )
            elif scale == 'heures':
                query_result_source['datetime'] = pd.to_datetime(query_result_source['jour'].astype(str) + ' ' + query_result_source['heure'].astype(str) + ':00')

            query_result_source.sort_values('datetime', inplace=True)
            query_result_source['sum'] = query_result_source['class_0'] + query_result_source['class_1']

            show_legend_debout = first_debout
            show_legend_couche = first_couche
            show_legend_total = first_total

            # Ajouter les tracés pour 'Couché', 'Debout', et 'Total' pour chaque source
            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['class_0'], name='Couché', line=dict(color=colors[0]), mode=MODE_GRAPH, showlegend=show_legend_couche, legendgroup='Couché'), row=i, col=1)
            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['class_1'], name='Debouts', line=dict(color=colors[1]), mode=MODE_GRAPH, showlegend=show_legend_debout, legendgroup='Debouts'), row=i, col=1)
            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['sum'], name='Total', line=dict(color=colors[LINE_TOTAL_COLOR], width=LINE_TOTAL_WIDTH, dash=LINE_TOTAL_DASH), mode=MODE_GRAPH, showlegend=show_legend_total, legendgroup='Total'), row=i, col=1)

            if first_debout:
                first_debout = False
            if first_couche:
                first_couche = False
            if first_total:
                first_total = False

            # Ajouter une ligne horizontale à chaque sous-graphique
            if scale == 'minutes':
                fig.add_hline(y=20, line_width=2, line_dash="dash", line_color="red", row=i, col=1)

            # Mise à jour de la disposition du graphique
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="black",
                    font_size=16,
                    font_family="Rockwell"
                ),
                legend=dict(
                    font_size=16,
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=1200,  # Hauteur totale du graphique
                width=800,    # Largeur du graphique
                xaxis=dict(
                    tickformat='%d/%m %Hh',  # Format de la date et de l'heure pour le dernier sous-graphique
                    dtick=3600000  # Interval d'une heure sur l'axe des x (en millisecondes)
                )
            )

            # Mise à jour des axes x pour tous les sous-graphiques, sauf le dernier
            for j in range(1, 4):
                fig.update_xaxes(showticklabels=False, row=j, col=1)

        # Affichage du graphique avec Streamlit
        st.plotly_chart(fig, use_container_width=True)

    def comportement_chevres_couche_debout(self, dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH):
        """
        Affiche les données des chèvres pour les états couchées ou debout par heure.
        """
        palette = sns.color_palette("Paired", 10)
        colors = [mcolors.to_hex(rgb) for rgb in palette]

        query_result = self.chevres_heure

        fig = make_subplots(rows=len(dates), cols=len(sources),
                            subplot_titles=[f'Source {src} - {date}' for date in dates for src in sources])

        first_debout = True
        first_couche = True
        first_total = True

        st.title('Moyenne de chèvres couchées ou debout dans une heure.')

        for row, date in enumerate(dates):
            for col, src in enumerate(sources):
                query_result_date = query_result[(query_result['jour'] == date) & (query_result['source'] == int(src))]

                query_result_date['sum'] = query_result_date['class_0'] + query_result_date['class_1']

                show_legend_debout = first_debout
                show_legend_couche = first_couche
                show_legend_total = first_total

                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['class_0'], name='Couché', line=dict(color=colors[0]),
                                         showlegend=show_legend_couche, legendgroup='Couché'), row=row + 1, col=col + 1)
                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['class_1'], name='Debouts', line=dict(color=colors[1]),
                                         showlegend=show_legend_debout, legendgroup='Debout'), row=row + 1, col=col + 1)
                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['sum'], name='Total', line=dict(color=colors[LINE_TOTAL_COLOR], width=LINE_TOTAL_WIDTH, dash=LINE_TOTAL_DASH),
                                         showlegend=show_legend_total, legendgroup='Total'), row=row + 1, col=col + 1)

                if first_debout:
                    first_debout = False
                if first_couche:
                    first_couche = False
                if first_total:
                    first_total = False

        # Mise à jour de la disposition du graphique
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="black",
                font_size=16,
                font_family="Rockwell"
            ),
            legend=dict(
                font_size=16,
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=1200,  # Hauteur totale du graphique
            width=800,    # Largeur du graphique
            xaxis=dict(
                tickformat='%d/%m %Hh',  # Format de la date et de l'heure pour le dernier sous-graphique
                dtick=3600000  # Interval d'une heure sur l'axe des x (en millisecondes)
            )
        )

        # Update x-axis range if needed
        fig.update_xaxes(range=[0, 23])

        if len(dates) == 1 and len(sources) == 1:
            fig.update_layout(height=600 * (len(dates) * 1.5), width=800)
        else:
            fig.update_layout(height=600 * (len(dates) if len(dates) == 1 else len(dates) * 0.75), width=800)

        # Display the figure with Streamlit
        st.plotly_chart(fig, use_container_width=True)

    def comportement_chevres_couche_debout_etat(self, dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH):
        """
        Affiche les pourcentages de chèvres couchées ou debout.
        """
        palette = sns.color_palette("Paired", 10)
        colors = [mcolors.to_hex(rgb) for rgb in palette]

        query_result = self.chevres_heure

        st.title('% de chèvres couchées ou debout.')
        fig = make_subplots(rows=len(dates), cols=len(sources),
                            subplot_titles=[f'Source {src} - {date}' for date in dates for src in sources])

        first_debout = True
        first_couche = True

        for row, date in enumerate(dates):
            for col, src in enumerate(sources):
                query_result_date_source = query_result[(query_result['jour'] == date) & (query_result['source'] == int(src))]

                show_legend_debout = first_debout
                show_legend_couche = first_couche

                query_result['0_normalized'] = query_result_date_source['class_0'] / (query_result_date_source['class_0'] + query_result_date_source['class_1'])
                query_result['1_normalized'] = query_result_date_source['class_1'] / (query_result_date_source['class_0'] + query_result_date_source['class_1'])

                fig.add_trace(
                    go.Bar(x=query_result['heure'], y=query_result['1_normalized'], name='Debout', marker_color=colors[1],
                           showlegend=show_legend_debout, legendgroup='Debout'),
                    row=row + 1, col=col + 1
                )

                fig.add_trace(
                    go.Bar(x=query_result['heure'], y=query_result['0_normalized'], name='Couché', marker_color=colors[0],
                           showlegend=show_legend_couche, legendgroup='Couche'),
                    row=row + 1, col=col + 1
                )

                fig.update_yaxes(tickformat='.0%', row=row + 1, col=col + 1)

                if first_debout:
                    first_debout = False
                if first_couche:
                    first_couche = False

        # Mise à jour des layouts si nécessaire
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="black",
                font_size=16,  # Augmente la taille de la police pour l'info-bulle
                font_family="Rockwell"
            ),
            barmode='stack',
            legend=dict(
                font_size=16
            )
        )

        # Update x-axis range if needed
        fig.update_xaxes(range=[-1, 24])

        # Update height depending on the number of rows
        if len(dates) == 1 and len(sources) == 1:
            fig.update_layout(height=600 * (len(dates) * 1.5), width=800)
        else:
            fig.update_layout(height=600 * (len(dates) if len(dates) == 1 else len(dates) * 0.75), width=800)

        st.plotly_chart(fig, use_container_width=True)

    def comportement_chevres_couche_debout_table(self, dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH):
        """
        Affiche les données des chèvres sous forme de tableau.
        """
        query_result = self.chevres_heure

        st.title('Table de données.')
        st.dataframe(query_result, hide_index=True)

    def comportement_chevres_acceuil_2(self, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH):
        """
        Affiche les graphiques pour les comportements des chèvres (abreuvoir, auge, frottoir).
        """
        st.title("Chèvres à l'abreuvoir, à l'auge ou au frottoir évolution temporelle (Heures).")

        query_result = self.chevres_heure

        sources = [1, 2, 3, 4]

        first_brush = True
        first_drink = True
        first_eat = True
        legend_total = True

        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=[f'Source {src}' for src in sources])
        # Création de la palette de couleurs

        for i, src in enumerate(sources, start=1):
            palette = sns.color_palette("dark", 10)
            colors = [mcolors.to_hex(rgb) for rgb in palette]

            query_result_source = query_result[query_result['source'] == src]
            query_result_source['datetime'] = pd.to_datetime(query_result_source['jour'].astype(str) + ' ' + query_result_source['heure'].astype(str) + ':00')
            query_result_source.sort_values('datetime', inplace=True)

            query_result_source['sum'] = query_result_source['class_0'] + query_result_source['class_1']

            show_legend_brush = first_brush
            show_legend_drink = first_drink
            show_legend_eat = first_eat
            show_legend_total = legend_total

            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['brush'], name='Brush', line=dict(color=colors[1]), showlegend=show_legend_brush, legendgroup='Brush'), row=i, col=1)
            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['drink'], name='Drink', line=dict(color=colors[3]), showlegend=show_legend_drink, legendgroup='Drink'), row=i, col=1)
            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['eat'], name='Eat', line=dict(color=colors[2]), showlegend=show_legend_eat, legendgroup='Eat'), row=i, col=1)

            palette = sns.color_palette("Paired", 10)
            colors = [mcolors.to_hex(rgb) for rgb in palette]

            fig.add_trace(go.Scatter(x=query_result_source['datetime'], y=query_result_source['sum'], name='Total', line=dict(color=colors[LINE_TOTAL_COLOR], width=LINE_TOTAL_WIDTH, dash=LINE_TOTAL_DASH), showlegend=show_legend_total, legendgroup='Total'), row=i, col=1)

            if first_brush:
                first_brush = False
            if first_drink:
                first_drink = False
            if first_eat:
                first_eat = False
            if legend_total:
                legend_total = False

            # Mise à jour de la disposition du graphique
            fig.update_layout(
                hoverlabel=dict(
                    bgcolor="black",
                    font_size=16,
                    font_family="Rockwell"
                ),
                legend=dict(
                    font_size=16,
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=1200,  # Hauteur totale du graphique
                width=800,    # Largeur du graphique
                xaxis=dict(
                    tickformat='%d/%m %Hh',  # Format de la date et de l'heure pour le dernier sous-graphique
                    dtick=3600000  # Interval d'une heure sur l'axe des x (en millisecondes)
                )
            )

            for j in range(1, 4):
                fig.update_xaxes(showticklabels=False, row=j, col=1)

        st.plotly_chart(fig, use_container_width=True)

    def comportement_chevres_abreuvoir_auge_frottoir(self, dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH):
        """
        Affiche les comportements des chèvres (abreuvoir, auge, frottoir) pour les dates et sources sélectionnées.
        """
        query_result = self.chevres_heure

        fig = make_subplots(rows=len(dates), cols=len(sources),
                            subplot_titles=[f'Source {src} - {date}' for date in dates for src in sources])

        first_brush = True
        first_drink = True
        first_eat = True
        legend_total = True

        st.title("Chèvres à l'abreuvoir, à l'auge ou au frottoir évolution temporelle (Heures).")

        for row, date in enumerate(dates):
            for col, src in enumerate(sources):
                palette = sns.color_palette("dark", 10)
                colors = [mcolors.to_hex(rgb) for rgb in palette]
                query_result_date = query_result[(query_result['jour'] == date) & (query_result['source'] == int(src))]

                query_result_date['sum'] = query_result_date['class_0'] + query_result_date['class_1']

                show_legend_brush = first_brush
                show_legend_drink = first_drink
                show_legend_eat = first_eat
                show_legend_total = legend_total

                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['brush'], name='Brush', line=dict(color=colors[1]),
                                         showlegend=show_legend_brush, legendgroup='Brush'), row=row + 1, col=col + 1)
                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['drink'], name='Drink', line=dict(color=colors[3]),
                                         showlegend=show_legend_drink, legendgroup='Drink'), row=row + 1, col=col + 1)
                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['eat'], name='Eat', line=dict(color=colors[2]),
                                         showlegend=show_legend_eat, legendgroup='Eat'), row=row + 1, col=col + 1)

                palette = sns.color_palette("Paired", 10)
                colors = [mcolors.to_hex(rgb) for rgb in palette]

                fig.add_trace(go.Scatter(x=query_result_date['heure'], y=query_result_date['sum'], name='Total', line=dict(color=colors[LINE_TOTAL_COLOR], width=LINE_TOTAL_WIDTH, dash=LINE_TOTAL_DASH),
                                         showlegend=show_legend_total, legendgroup='Total'), row=row + 1, col=col + 1)

                if first_brush:
                    first_brush = False
                if first_drink:
                    first_drink = False
                if first_eat:
                    first_eat = False
                if legend_total:
                    legend_total = False

        # Mise à jour de la disposition du graphique
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="black",
                font_size=16,
                font_family="Rockwell"
            ),
            legend=dict(
                font_size=16,
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=1200,  # Hauteur totale du graphique
            width=800,    # Largeur du graphique
            xaxis=dict(
                tickformat='%d/%m %Hh',  # Format de la date et de l'heure pour le dernier sous-graphique
                dtick=3600000  # Interval d'une heure sur l'axe des x (en millisecondes)
            )
        )

        # Update x-axis range if needed
        fig.update_xaxes(range=[0, 23])

        if len(dates) == 1 and len(sources) == 1:
            fig.update_layout(height=600 * (len(dates) * 1.5), width=800)
        else:
            fig.update_layout(height=600 * (len(dates) if len(dates) == 1 else len(dates) * 0.75), width=800)

        st.plotly_chart(fig, use_container_width=True)

    def display_graph(self, sources, dates):
        """
        Gère l'affichage des graphiques en fonction des sources et des dates sélectionnées.
        """
        LINE_TOTAL_WIDTH = 5
        LINE_TOTAL_DASH = 'dash'
        LINE_TOTAL_COLOR = 8

        col1, col2, col3 = st.columns([2, 2, 1])

        if not (len(sources) != 0 and len(dates) != 0):
            self.comportement_chevres_acceuil(LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)
        else:
            tab1, tab2, tab3 = st.tabs(["État chèvres (par heures)", "État chèvres (en %)", "Tables de données"])

            with tab1:
                self.comportement_chevres_couche_debout(dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)

            with tab2:
                self.comportement_chevres_couche_debout_etat(dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)

            with tab3:
                self.comportement_chevres_couche_debout_table(dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)

    def display_graph_2(self, sources, dates):
        """
        Gère l'affichage des graphiques pour les comportements (abreuvoir, auge, frottoir) en fonction des sources et des dates sélectionnées.
        """
        LINE_TOTAL_WIDTH = 5
        LINE_TOTAL_DASH = 'dash'
        LINE_TOTAL_COLOR = 8

        if not (len(sources) != 0 and len(dates) != 0):
            self.comportement_chevres_acceuil_2(LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)
        else:
            self.comportement_chevres_abreuvoir_auge_frottoir(dates, sources, LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH)

    def display_graph_3(self):
        """
        Affiche le graphique des chèvres couchées/debout en temps réel (par minutes).
        """
        LINE_TOTAL_WIDTH = 5
        LINE_TOTAL_DASH = 'dash'
        LINE_TOTAL_COLOR = 8

        if st.sidebar.toggle("lignes"):
            self.comportement_chevres_acceuil(LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH, 'minutes', 'lines')
        else:
            self.comportement_chevres_acceuil(LINE_TOTAL_COLOR, LINE_TOTAL_DASH, LINE_TOTAL_WIDTH, 'minutes', 'markers')

    def run(self):
        """
        Point d'entrée principal pour exécuter l'application Streamlit.
        """
        graph_type = st.sidebar.radio(
            "Type de données :",
            ["Couchées/Debout", "Abreuvoir/Auge/Frottoir", "Debouts/Couchées minutes"])

        if graph_type != "Debouts/Couchées minutes":
            st.sidebar.markdown('#### Sources')
            selected_source = self.setup_checkbox_sources()
            st.sidebar.markdown("---")
            st.sidebar.markdown('#### Jours')
            selected_date = self.setup_checkbox_date()
            st.sidebar.markdown("---")

            if graph_type == "Couchées/Debout":
                self.display_graph(selected_source, selected_date)
            elif graph_type == "Abreuvoir/Auge/Frottoir":
                self.display_graph_2(selected_source, selected_date)
        else:
            self.display_graph_3()

if __name__ == "__main__":
    app = VideoAnalytics_3_()
    app.run()
