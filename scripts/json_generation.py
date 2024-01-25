import math
import sqlite3
import json
from pathlib import Path

# SQLite database connection
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()


# MATCHES RESULT BY TEAMS
cursor.execute('SELECT DISTINCT team1 FROM matches UNION SELECT DISTINCT team2 FROM matches')
teams = [row[0] for row in cursor.fetchall()]

for team in teams:
    # Sélectionner les matches pour le pays donné
    cursor.execute('''
        SELECT m.date, m.country, m.tournament, m.team1, m.team2, m.original_team1, m.original_team2, t1.flag as flag1, t2.flag as flag2, m.score1, m.score2, m.rating1, m.rating2, m.rating_ev, m.expected_result, m.neutral
        FROM matches m
        LEFT JOIN Teams t1 ON (m.original_team1 = t1.team)
        LEFT JOIN Teams t2 ON (m.original_team2 = t2.team)
        WHERE team1 = ? OR team2 = ?
        ORDER BY date DESC
    ''', (team, team))

    matches_data = cursor.fetchall()

    json_data = {
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
        'win_prob': round((1/(1+math.exp(-((1 if team == team1 else -1)*(expected_result+(0.341 if not neutral else 0)))*2.95)))*100,1)
    } for date, country, tournament, team1, team2, original_team1, original_team2, flag1, flag2, score1, score2, rating1, rating2, rating_ev, expected_result, neutral in matches_data]
    }

    output_file_path = Path(f"data/json/matches/{team}.json")
    
    with open(output_file_path, 'w', encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=2)
        print(f"Data successfully extracted and exported to {output_file_path}.")


# YEARLY RANKINGS
# Execute SQL query to obtain list of current years
cursor.execute("SELECT DISTINCT year FROM Rankings WHERE year IS NOT strftime('%Y', CURRENT_DATE)")
years = cursor.fetchall()

for year in years:
    year = year[0]

    # Execute SQL query to select data for current year
    cursor.execute('''
                   WITH previous_year AS (
                    SELECT r.ranking, r.reference_team, r.points
                    FROM Rankings r
                    LEFT JOIN Teams t ON (r.team = t.team)
                    WHERE year = ? - 1 AND month = 12 AND day = 31
                   )
                    SELECT r.ranking, t.flag, r.team, r.reference_team, r.points, t.confederation, (p.ranking - r.ranking) AS ranking_change, (r.points - p.points) AS points_change
                    FROM Rankings r
                    LEFT JOIN Teams t ON (r.team = t.team)
                    LEFT JOIN previous_year p ON (r.reference_team = p.reference_team)
                    WHERE year = ? AND month = 12 AND day = 31
                    AND r.team NOT LIKE ('Not-Sovereign %')
                    ORDER BY r.ranking
                   ''', (year,year))

    # Data recovery
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    data = [dict(zip(column_names, row)) for row in rows]

    # JSON file name
    json_path = Path(f"data/json/years/{year}Rankings.json")

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)
        print(f"Data successfully extracted and exported to {json_path}.")

'''
    # Check if the file already exists
    if not json_path.exists():
        # Export data to a JSON file
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2)

        print(f"Data successfully extracted and exported to {json_path}.")
    else:
        print(f"The {json_path} file already exists. No action required.")
'''

# Generate last date file
# Execute SQL query to select all table rows
cursor.execute('''
                WITH max_date AS (
                    SELECT MAX(date) as max_date, strftime('%Y', MAX(date)) AS year FROM Rankings
                ),
               previous_year AS (
                    SELECT r.ranking, r.team, r.reference_team, r.points
                    FROM Rankings r
                    LEFT JOIN Teams t ON (r.team = t.team)
                    WHERE year = (SELECT year FROM max_date) - 1 AND month = 12 AND day = 31
                   )
                SELECT r.ranking, t.flag, r.team, r.reference_team, r.points, t.confederation, (p.ranking - r.ranking) AS ranking_change, (r.points - p.points) AS points_change
                FROM Rankings r
                LEFT JOIN previous_year p ON (r.reference_team = p.reference_team)
                LEFT JOIN Teams t ON (r.team = t.team)
                WHERE date = (SELECT MAX(date) FROM Rankings)
                AND r.team NOT LIKE ('Not-Sovereign %')
                ORDER BY r.ranking 
               '''
)

rows = cursor.fetchall()
column_names = [description[0] for description in cursor.description]
data = [dict(zip(column_names, row)) for row in rows]

# Export data to a JSON file
json_path = "data/json/years/LastRankings.json"
with open(json_path, "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, indent=2)

print(f"Data successfully extracted and exported to {json_path}.")

connection.close()
