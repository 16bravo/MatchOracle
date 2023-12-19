#!/usr/bin/env python
# coding: utf-8


# # Import des librairies
import kaggle.cli
import sys
import pandas as pd
from pathlib import Path
from zipfile import ZipFile
from tqdm import tqdm
import math
import numpy as np
import sqlite3


# # Import des données

# ## Extraction du jeu de données sur Kaggle

# Téléchargement du jeu de données
# https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017/?select=results.csv
dataset = "martj42/international-football-results-from-1872-to-2017"
sys.argv = [sys.argv[0]] + f"datasets download {dataset}".split(" ")
kaggle.cli.main()

zfile = ZipFile(f"{dataset.split('/')[1]}.zip")

matches = {f.filename:pd.read_csv(zfile.open(f)) for f in zfile.infolist() }["results.csv"]

# Ajout d'une colonne d'identifiant unique pour chaque ligne dans le DataFrame matches
matches['match_id'] = range(1, len(matches) + 1)

# matches.head(15)


# ## Nettoyage des données

#Filtre sur la validité des matches
# Chargement des données depuis les fichiers CSV
# matches a été généré avec l'API Kaggle
teams_db = pd.read_excel('./data/teams_db.xlsx')

# Fusion des DataFrames sur les colonnes home_team et away_team
merged_df = pd.merge(matches, teams_db[['team', 'tricode']], how='inner', left_on='home_team', right_on='team')
merged_df = pd.merge(merged_df, teams_db[['team', 'tricode']], how='inner', left_on='away_team', right_on='team')

# print(merged_df)

# Filtre sur les lignes où les deux équipes sont valides (tricode non vide)
valid_matches = merged_df[(merged_df['tricode_x'].notna()) & (merged_df['tricode_y'].notna())]

# Sélection des colonnes souhaitées dans le DataFrame final
matches_filtered = valid_matches[['match_id']]

# print(matches_filtered)
# matches_filtered.to_csv('matches_filtered.csv', index=False)

# Fusion des DataFrames matches et matches_filtered sur match_id
matches = pd.merge(matches, matches_filtered, how='inner', on='match_id')
matches = matches.sort_values(by='match_id', ascending=True)
# matches.head(15)


# # Transformation des données

# ## Calcul des points match par match

# Ajout de colonnes
matches['home_points'] = None
matches['away_points'] = None
matches['calculated_result'] = None
matches['home_points_after'] = None
matches['away_points_after'] = None

# Création du DataFrame "teams" avec deux colonnes "team" et "points"
teams = pd.DataFrame(columns=['team', 'points'])

# Boucle sur chaque ligne du DataFrame "matches"
for index, match in  tqdm(matches.iterrows(), total=len(matches), desc="Calculating matches points"):
    # Vérification si la valeur dans la colonne home_team existe dans le DataFrame "teams"
    if match['home_team'] not in teams['team'].values:
        if match['away_team'] not in teams['team'].values:
            new_team_row = pd.DataFrame({'team': [match['home_team']], 'points': [2000]})
        else:
            new_team_row = pd.DataFrame({'team': [match['home_team']], 'points': [teams.loc[teams['team'] == match['away_team'], 'points'].values[0]]})
        teams = pd.concat([teams, new_team_row], ignore_index=True)

    # Vérification pour la colonne away_team
    if match['away_team'] not in teams['team'].values:
        if match['home_team'] not in teams['team'].values:
            new_team_row = pd.DataFrame({'team': [match['away_team']], 'points': [2000]})
        else:
            new_team_row = pd.DataFrame({'team': [match['away_team']], 'points': [teams.loc[teams['team'] == match['home_team'], 'points'].values[0]]})
        teams = pd.concat([teams, new_team_row], ignore_index=True)
        
    # Valeur de points pour home_team et away_team
    points_home_team = teams.loc[teams['team'] == match['home_team'], 'points'].values[0]
    points_away_team = teams.loc[teams['team'] == match['away_team'], 'points'].values[0]

    #Calcul du coef pour accentuer l'écart entre les équipes si même niveau exact (souvent cas du premier match)
    if points_home_team == points_away_team:
        coef = 1
    else :
        coef = 0.1
    
    # Calculs sur les points

    calculated_result = (1/(1+math.exp(-1*(match['home_score']-match['away_score'])/5))-0.5)*21-int(not match['neutral'])

    match_level = teams.loc[teams['team'] == match['home_team'], 'points'].values[0]*0.5+teams.loc[teams['team'] == match['away_team'], 'points'].values[0]*0.5
    teams.loc[teams['team'] == match['home_team'], 'points'] = points_home_team*(1-coef) + (match_level + calculated_result*200)*coef
    teams.loc[teams['team'] == match['away_team'], 'points'] = points_away_team*(1-coef) + (match_level - calculated_result*200)*coef
    
    # Colonnes supplémentaires
    matches.at[index, 'home_points'] = points_home_team
    matches.at[index, 'away_points'] = points_away_team
    matches.at[index, 'calculated_result'] = calculated_result*200
    matches.at[index, 'home_points_after'] = teams.loc[teams['team'] == match['home_team'], 'points'].values[0]
    matches.at[index, 'away_points_after'] = teams.loc[teams['team'] == match['away_team'], 'points'].values[0]


# ## Calcul des points historiques mois par mois pour chaque équipe

# Conversion de la colonne "date" du DataFrame "matches" en objet de type Timestamp
matches['date'] = pd.to_datetime(matches['date'])

# Génération de la liste des premiers jours de chaque mois
start_date = matches['date'].min()
end_date = matches['date'].max()
monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')  # 'MS' pour le premier jour de chaque mois

# Création du DataFrame "historical_points" avec les colonnes "date" et toutes les valeurs uniques de la colonne "team" de "teams"
historical_points = pd.DataFrame({'date': monthly_dates})
historical_points = pd.concat([historical_points, pd.DataFrame(columns=teams['team'].unique())], axis=1)

# Boucle sur chaque ligne du DataFrame "historical_points" avec une barre de progression
for index, row in tqdm(historical_points.iterrows(), total=len(historical_points), desc="Calculating Historical Points"):
    date = row['date']

    # Boucle sur chaque équipe présente dans la colonne "team" de "teams"
    for team in teams['team'].unique():
        # Sélection des lignes correspondant à l'équipe pour la date donnée
        team_matches = matches[((matches['home_team'] == team) | (matches['away_team'] == team)) & (matches['date'] <= date)]

        # Si des matchs existent pour cette équipe à cette date, récupération de la dernière valeur de points
        if not team_matches.empty:
            last_points_home = team_matches.iloc[-1]['home_points_after'] if team_matches.iloc[-1]['home_team'] == team else 0
            last_points_away = team_matches.iloc[-1]['away_points_after'] if team_matches.iloc[-1]['away_team'] == team else 0

            # Sélection de la valeur maximale entre home_points_after et away_points_after
            last_points = max(last_points_home, last_points_away)

            # Valeur dans le DataFrame "historical_points".
            historical_points.at[index, team] = last_points


# ## Préparation des données

# Dépivot des colonnes teams
melted_points = pd.melt(historical_points, id_vars=['date'], var_name='team', value_name='points')

# Tri du DataFrame résultant par date et team si nécessaire
melted_points.sort_values(by=['date', 'team'], inplace=True)


# ## Nettoyage des données : suppression des anciens pays

# Suppression des lignes vides
melted_points = melted_points[melted_points['points'].notna()]

# Conversion des colonnes de dates en objets datetime
melted_points['date'] = pd.to_datetime(melted_points['date'])
teams_db['startDate'] = pd.to_datetime(teams_db['startDate'])
teams_db['endDate'] = pd.to_datetime(teams_db['endDate'])

# Fusion de melted_points avec teams_db sur la colonne team
merged_data = pd.merge(melted_points, teams_db[['team','startDate','endDate']], on='team')

# Filtre des lignes où la date est comprise entre startDate et endDate, ou si startDate et endDate sont NaT
valid_data = merged_data[((merged_data['date'] >= merged_data['startDate']) | merged_data['startDate'].isna()) &
                         ((merged_data['date'] <= merged_data['endDate']) | merged_data['endDate'].isna())]

# Sélection des colonnes souhaitées dans le DataFrame final
ranking_df = valid_data[['date', 'team', 'points']]

# Ajout de la colonne de classement partitionnée par la date
# ranking_df['ranking'] = ranking_df.groupby('date')['points'].rank(ascending=False, method='min')
ranking_df.loc[:, 'ranking'] = ranking_df.groupby('date')['points'].rank(ascending=False, method='min')

# Tri du DataFrame par date et classement
ranking_df.sort_values(by=['date', 'ranking'], inplace=True)

# Extraction de l'année et du mois dans de nouvelles colonnes
ranking_df['year'] = ranking_df['date'].dt.year
ranking_df['month'] = ranking_df['date'].dt.month

# Suppression de la colonne de dates si nécessaire
ranking_df.drop('date', axis=1, inplace=True)

# Conversion des colonnes 'points' et 'classement' en entiers
ranking_df['points'] = ranking_df['points'].astype(int)
ranking_df['ranking'] = ranking_df['ranking'].astype(int)

ranking_df = ranking_df[['year', 'month', 'team', 'points', 'ranking']]


# # Création de la base de données

# ## Création de la base et des tables

# Chemin et nom de la base de données
database_path = './data/BravoRanking.db'

# Connexion à la base de données (la base sera créée si elle n'existe pas)
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# Création de la table Teams
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team VARCHAR(50) NOT NULL,
        tricode VARCHAR(3),
        confederation VARCHAR(10),
        startDate DATE,
        endDate DATE,
        member BOOLEAN NOT NULL
    )
''')

# Création de la table Rankings
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rankings (
        ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        team VARCHAR(50) NOT NULL,
        points INTEGER NOT NULL,
        ranking INTEGER NOT NULL
    );
''')

# Chargement des données Excel dans un DataFrame pandas
#excel_file_path = 'teams_db.xlsx'
#df_teams = pd.read_excel(excel_file_path)

# Insértion des données dans les tables
teams_db.to_sql('Teams', conn, index=False, if_exists='replace')
ranking_df.to_sql('Rankings', conn, index=False, if_exists='append')

# Validez et fermez la connexion à la base de données
conn.commit()
conn.close()