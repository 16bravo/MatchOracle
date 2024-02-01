import math
import sqlite3
import json
import pandas as pd
from pathlib import Path

# SQLite database connection
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# MATCHES RESULT BY TEAMS
cursor.execute('SELECT DISTINCT team1 FROM matches UNION SELECT DISTINCT team2 FROM matches')
teams = [row[0] for row in cursor.fetchall()]

for team in teams:
    cursor.execute('''
        SELECT m.date, m.country, m.tournament, m.team1, m.team2, m.original_team1, m.original_team2, t1.flag as flag1, t2.flag as flag2, m.score1, m.score2, m.rating1, m.rating2, m.rating_ev, m.rank1, m.rank2, m.expected_result, m.neutral
        FROM matches m
        LEFT JOIN Teams t1 ON (m.original_team1 = t1.team)
        LEFT JOIN Teams t2 ON (m.original_team2 = t2.team)
        WHERE team1 = ? OR team2 = ?
        ORDER BY date DESC
    ''', (team, team))

    matches_data_sql = cursor.fetchall()

    matches_data = {
    'team': team,
    'matches': [{
        'date': date,
        'country' : country,
        'tournament' : tournament,
        'team1': team1 if team == team1 else team2,
        'team2': team2 if team == team1 else team1,
        'original_team1': original_team1 if team == team1 else original_team2,
        'original_team2': original_team2 if team == team1 else original_team1,
        'flag1': flag1 if team == team1 else flag2,
        'flag2': flag2 if team == team1 else flag1,
        'score1': score1 if team == team1 else score2,
        'score2': score2 if team == team1 else score1,
        'rating1': rating1 if team == team1 else rating2,
        'rating2': rating2 if team == team1 else rating1,
        'rating_ev': (1 if team == team1 else -1) * rating_ev,
        'rank' : int(rank1 if team == team1 else rank2) if not pd.isna(rank1 if team == team1 else rank2) else '-',
        'win_prob': round((1/(1+math.exp(-((1 if team == team1 else -1)*(expected_result+(0.341 if not neutral else 0)))*2.95)))*100,1)
    } for date, country, tournament, team1, team2, original_team1, original_team2, flag1, flag2, score1, score2, rating1, rating2, rating_ev, rank1, rank2, expected_result, neutral in matches_data_sql]
    }

    matches_path = Path(f"data/json/matches/{team}.json")
    
    with open(matches_path, 'w', encoding="utf-8") as matches_file:
        json.dump(matches_data, matches_file, indent=2)
        print(f"Data successfully extracted and exported to {matches_path}.")

connection.close()
