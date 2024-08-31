# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 15:05:05 2023

@author: dsite
"""

import os
import pandas as pd
import pickle

class DataFrameStatisticsOutliers:
    def __init__(self, df):
        
        self.df = df
        self.stats = {}
        
    def detect_outliers(self, df):
         
         Q1 = df.quantile(0.25)
         Q3 = df.quantile(0.75)
         IQR = Q3 - Q1
         lower_bound = Q1 - 1.5 * IQR
         upper_bound = Q3 + 1.5 * IQR
     
         return ((df < lower_bound) | (df > upper_bound))
    
    def get_stats(self):
        """
        Récupère les statistiques générées pour le DataFrame.

        Returns:
            dict: Un dictionnaire contenant les statistiques générées pour différentes catégories de colonnes.
        """
        return self.stats
        

class DataFrameStatisticsOutliers_Typr_1(DataFrameStatisticsOutliers):
    
    def find_outliers(self):
        import time
        
        # Enregistrez le moment où la fonction commence à s'exécuter
        temps_debut = time.time()
        
        self.df=self.df.select_dtypes(include=['number', 'bool'])
        self.df = self.df.drop(columns=['frame', 'id','timestamp', 'Abreuvoir', 'Auge', 'Frottoir'])
        
        lst = self.df.apply(self.detect_outliers)
        
        # Affichez combien de temps cela a pris pour traiter tous les fichiers
        print("Detection outlayers : {:.4f} s".format(time.time() - temps_debut))
        
        self.stats = {'Enregistrements': self.df[lst.any(axis=1)] , 'sum': lst.sum()}
     
        return self
    
class DataFrameStatisticsOutliers_Typr_2(DataFrameStatisticsOutliers):
   
    def detect_outliers(self, df):
          lower_bound = 0
          upper_bound = 20
         
          return ((df < lower_bound) | (df > upper_bound))
         
    def find_outliers(self):
        import time
        
        # Enregistrez le moment où la fonction commence à s'exécuter
        temps_debut = time.time()
        
        self.df=self.df.select_dtypes(include=['number', 'bool'])
        self.df = self.df.drop(columns=['timestamp'])
        
        lst = self.df.apply(self.detect_outliers)
        
        # Affichez combien de temps cela a pris pour traiter tous les fichiers
        print("Detection outlayers : {:.4f} s".format(time.time() - temps_debut))
        
        self.stats = {'Enregistrements': self.df[lst.any(axis=1)] , 'sum': lst.sum()}
     
        return self
  
  
  
class DataFrameStatistics_Type:
    """
   Une classe pour analyser et traiter les données d'un DataFrame pandas.

   Attributs:
       df (pandas.DataFrame): DataFrame à analyser.
       columns_qualitatives (pandas.DataFrame): Colonnes qualitatives du DataFrame.
       columns_numériques (pandas.DataFrame): Colonnes numériques du DataFrame.
       columns_datetime (pandas.DataFrame): Colonnes de type date du DataFrame.
       columns_timestamp (pandas.DataFrame): Colonnes de type timestamp du DataFrame.
       stats (dict): Dictionnaire contenant les statistiques sur les données.
   """
    
    def __init__(self, df, path, file):
        """
        Initialisez la classe avec un DataFrame (df), un chemin de fichier (path), et un nom de fichier (file).
       """
       
        # Initialisez la classe avec un DataFrame (df), un chemin de fichier (path), et un nom de fichier (file)
        self.df = df
        
        # Définissez le format d'affichage des nombres à virgule flottante dans le DataFrame
        pd.options.display.float_format = '{:.1f}'.format

    
        if 'timestamp' in self.df.columns:
            # Ajoutez une colonne 'date' au DataFrame en convertissant la colonne 'timestamp' en format de date et heure
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            
        # Séparez les colonnes qualitatives, numériques, de date et de timestamp
        self.columns_qualitatives = self.df.select_dtypes(include=['object'])
        self.columns_numériques = self.df.select_dtypes(include=['number'])
        self.columns_datetime = self.df.select_dtypes(include=['datetime'])
        self.columns_timestamp = self.df.select_dtypes(include=['datetime64'])


        self.stats = {'file': file,
                      'data': self. traitement (),
                      'nb_enregistrement': df.shape[0]}

        # Vérifiez si le répertoire spécifié existe, sinon créez-le
        if not os.path.exists(path):
            os.makedirs(path)

        # Sauvegardez les statistiques dans un fichier pickle dans le répertoire spécifié
        with open(path + "/" + file, 'wb') as file:
            pickle.dump(self.stats, file)
   
    def analyse_descriptive_binaire(self, colonne):
        """
        Analyse une colonne binaire et retourne le nombre d'occurrences de 1 et 0 ainsi que leurs pourcentages.
        
        Args:
            colonne (str): Nom de la colonne binaire à analyser.
            
        Returns:
            pandas.DataFrame: DataFrame contenant le nombre d'occurrences et les pourcentages.
        """
        # Comptez le nombre d'occurrences de 1 et de 0 dans la colonne "Abreuvoir"
        count_1 =  self.columns_numériques[colonne][ self.columns_numériques[colonne] == 0].count()
        count_0 =  self.columns_numériques[colonne][ self.columns_numériques[colonne] == 1].count()
         
        # Calculez les pourcentages
        total_count = count_1 + count_0
        percentage_1 = (count_1 / total_count) * 100
        percentage_0 = (count_0 / total_count) * 100
         
        # Créez un DataFrame pour l'analyse descriptive
        return pd.DataFrame({
              # "Valeur": [1, 0],
              "Nombre d'occurrences": [count_1, count_0],
              "Pourcentage": [percentage_1, percentage_0]
          })
    
    def traitement (self):
        """
       Traitement de base pour la génération des statistiques.
       
       Returns:
           dict: Un dictionnaire vide (peut être étendu pour d'autres traitements).
       """
        return {}
 
     # Créez une fonction pour obtenir les valeurs uniques d'une colonne
    def get_unique_values(self,column):
       return column.unique()
    
    # Créez une fonction pour obtenir le comptage des valeurs uniques d'une colonne
    def get_value_counts(self,column):
        return column.value_counts()
    
    # Créez une fonction pour obtenir le comptage des valeurs uniques en pourcentage d'une colonne
    def get_percentage_value_counts(self,column):
        return column.value_counts(normalize=True) * 100
       
    def get_df(self):
        """
       Récupère le DataFrame d'origine.

       Returns:
           pandas.DataFrame: Le DataFrame d'origine.
       """
        return self.df
    
    def get_colums(self):
        """
       Récupère les noms de colonnes pour différentes catégories de colonnes.

       Returns:
           dict: Un dictionnaire contenant les noms de colonnes pour différentes catégories.
       """
        
        return {'all': self.df.columns,
                'numeric': self.columns_numérics.columns,
                'qualit': self.columns_qualitatives.columns,
                'date': self.columns_timestamp.columns}
    
    def get_stats(self):
        """
        Récupère les statistiques générées pour le DataFrame.

        Returns:
            dict: Un dictionnaire contenant les statistiques générées pour différentes catégories de colonnes.
        """
        return self.stats
    
    def anomalie_champs_numériques(self):
        """
        Détecte les anomalies dans les champs numériques du DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame contenant les statistiques sur les anomalies dans les champs numériques.
        """
        # Calcul des statistiques des champs numériques
        valeur_null_count = self.df[self.columns_numériques.columns].isnull().sum()
        valeur_null_percent = ((self.df[self.columns_numériques.columns].isnull()).mean() * 100).round(2)
        valeur_nan_count = self.df[self.columns_numériques.columns].isna().sum()
        valeur_nan_percent = ((self.df[self.columns_numériques.columns].isna()).mean() * 100).round(2)
        valeur_negatives_count = (self.df[self.columns_numériques.columns] < 0).sum()
        valeur_negatives_percent = ((self.df[self.columns_numériques.columns] < 0).mean() * 100).round(2)

        # Créez un DataFrame contenant les statistiques des champs numériques
        return pd.DataFrame({
            'Null Count': valeur_null_count,
            'Null %': valeur_null_percent,
            'NaN Count': valeur_nan_count,
            'NaN %': valeur_nan_percent,
            'Negative Count': valeur_negatives_count,
            'Negative %': valeur_negatives_percent
        })
    
    def anomalie_champs_date(self):
        """
        Détecte les anomalies dans les champs date du DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame contenant les statistiques sur les anomalies dans les champs date.
        """
        
        # Calcul des statistiques des champs date
        valeur_null_count = self.df[self.columns_datetime.columns].isnull().sum()
        valeur_null_percent = ((self.df[self.columns_datetime.columns].isnull()).mean() * 100).round(2)
        valeur_nan_count = self.df[self.columns_datetime.columns].isna().sum()
        valeur_nan_percent = ((self.df[self.columns_datetime.columns].isna()).mean() * 100).round(2)
        
        # Créez un DataFrame contenant les statistiques des champs date
        return pd.DataFrame({
            'Null Count': valeur_null_count,
            'Null %': valeur_null_percent,
            'NaN Count': valeur_nan_count,
            'NaN %': valeur_nan_percent
        })

        
class DataFrameStatistics_Type_1 (DataFrameStatistics_Type):
    """
  Classe permettant d'effectuer des analyses statistiques et de générer un résumé des données d'un DataFrame.

  Args:
      df (pandas.DataFrame): Le DataFrame contenant les données à analyser.
      path (str): Le chemin vers le répertoire où le résultat sera sauvegardé.
      file (str): Le nom du fichier de sortie pour le résultat.

  Attributes:
      df (pandas.DataFrame): Le DataFrame d'origine.
      columns_qualitatives (pandas.DataFrame): Les colonnes qualitatives du DataFrame.
      columns_numériques (pandas.DataFrame): Les colonnes numériques du DataFrame.
      columns_datetime (pandas.DataFrame): Les colonnes de type datetime du DataFrame.
      columns_timestamp (pandas.DataFrame): Les colonnes de type datetime64 du DataFrame.
      stats (dict): Un dictionnaire contenant les statistiques générées pour différentes catégories de colonnes.
  """
  
    def __init__(self, df, path, file):
        
        
       """
        Initialise une instance de DataFrameStatistics.
        
        Args:
            df (pandas.DataFrame): Le DataFrame contenant les données à analyser.
            path (str): Le chemin vers le répertoire où le résultat sera sauvegardé.
            file (str): Le nom du fichier de sortie pour le résultat.
       """

       super().__init__(df, path, file)
       
    def traitement (self):
        
        # Appliquez la fonction get_value_counts à chaque colonne du DataFrame pour obtenir les comptes de valeurs uniques
        value_counts = self.columns_qualitatives.apply(self.get_value_counts)

        # Appliquez la fonction get_percentage_value_counts à chaque colonne du DataFrame pour obtenir les pourcentages de valeurs uniques
        percentage_value_counts = self.columns_qualitatives.apply(self.get_percentage_value_counts)

        # Concaténez les résultats des comptes de valeurs et des pourcentages de valeurs uniques
        unique_values = pd.concat([value_counts, percentage_value_counts], axis=1)
        unique_values.columns = ['classe_count', 'classe_percent']


        analyse_anomalie_champs_numériques = self.anomalie_champs_numériques()
        analyse_descriptive_champs_date = self.anomalie_champs_date()            

     
        analyse_descriptive_abreuvoir = self.analyse_descriptive_binaire('Abreuvoir')
        analyse_descriptive_auge = self.analyse_descriptive_binaire('Auge')
        analyse_descriptive_frottoire = self.analyse_descriptive_binaire('Frottoir')
      
        # Créez un dictionnaire de statistiques pour différentes catégories de données
        return {"all": self.df.describe(),
                "numeric": {'describ': self.df[self.columns_numériques.columns].describe(),
                            'analyse_anomalies': analyse_anomalie_champs_numériques.transpose(),
                            # 'outliers' : self.info_outliers(self.df),
                            'analyse_descriptive': {'abreuvoir':  analyse_descriptive_abreuvoir.transpose(),
                                                    'auge':  analyse_descriptive_auge.transpose(),
                                                    'frottoire':  analyse_descriptive_frottoire.transpose()}},
                "qualit": {'describ': self.df[self.columns_qualitatives.columns].describe(),
                          'values_distri': unique_values.transpose()},
                "date": {'describ': self.df[self.columns_datetime.columns].describe(),
                            'analyse_anomalies': analyse_descriptive_champs_date.transpose()}}
    
  
        
class DataFrameStatistics_Type_2(DataFrameStatistics_Type):
    def __init__(self, df, path, file):
        super().__init__(df, path, file)

    def traitement (self):
        
        describe_all = self.df.describe()
   
        analyse_anomalie_champs_numériques = self.anomalie_champs_numériques()
        analyse_descriptive_champs_date = self.anomalie_champs_date()
        
        describe = self.df[self.columns_numériques.columns].describe()
        
        # Sélectionner toutes les colonnes numériques
        colonnes_numeriques = self.df.select_dtypes(include=[int, float]).columns
        
        # Supprimer la colonne spécifique de la liste des colonnes à convertir
        colonne_a_ne_pas_convertir = "timestamp"
        if colonne_a_ne_pas_convertir in colonnes_numeriques:
            colonnes_numeriques = colonnes_numeriques.drop(colonne_a_ne_pas_convertir)
        
        # Convertir les colonnes numériques en objets
        self.df[colonnes_numeriques] = self.df[colonnes_numeriques].astype(str)
        
        self.columns_qualitatives = self.df.select_dtypes(include=['object'])
        
        nom_colonne_index = 'occurances effectif'
        # Appliquez la fonction get_value_counts à chaque colonne du DataFrame pour obtenir les comptes de valeurs uniques
        value_counts = self.columns_qualitatives.apply(self.get_value_counts)
        value_counts = value_counts.reset_index().rename(columns={"index": nom_colonne_index})
        value_counts[nom_colonne_index] = value_counts[nom_colonne_index].astype('int')
        value_counts= value_counts.sort_values(by=nom_colonne_index, ascending=True)

        # Créez un dictionnaire de statistiques pour différentes catégories de données
        return {"all": describe_all,
                      "numeric": {'describ':describe,
                                  'analyse_anomalies': analyse_anomalie_champs_numériques.transpose(),
                                  'analyse_descriptive': value_counts
                                  },
                      "date": {'describ': self.df[self.columns_datetime.columns].describe(),
                                  'analyse_anomalies': analyse_descriptive_champs_date.transpose()}}