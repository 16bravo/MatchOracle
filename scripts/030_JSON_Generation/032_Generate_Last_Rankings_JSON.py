import sqlite3
import json

# SQLite database connection
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# YEARLY RANKINGS
# LAST DATE (last)
# Generate last date file
cursor.execute("SELECT max(date) FROM Matches")
last_last_date = [row[0] for row in cursor.fetchall()]

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

# Data recovery
last_data_sql = cursor.fetchall()

years_data = {
'year': 'last',
'last_date': last_last_date,
'rankings': [{
    'ranking': ranking,
    'flag' : flag,
    'team' : team,
    'reference_team': reference_team,
    'points': points,
    'confederation': confederation,
    'ranking_change': ranking_change,
    'points_change': points_change
} for ranking, flag, team, reference_team, points, confederation, ranking_change, points_change in last_data_sql]
}

# Export data to JSON file
years_path = "data/json/rankings/LastRankings.json"
with open(years_path, "w", encoding="utf-8") as years_file:
    json.dump(years_data, years_file, indent=2)

print(f"Data successfully extracted and exported to {years_path}.")

connection.close()
