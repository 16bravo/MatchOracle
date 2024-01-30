import sqlite3
import json
from pathlib import Path

# SQLite database connection
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# YEARLY RANKINGS
# HISTORICAL RANKINGS FROM 1872
# Execute SQL query to obtain list of current years
cursor.execute("SELECT DISTINCT year FROM Rankings WHERE year IS NOT strftime('%Y', CURRENT_DATE)")
years = cursor.fetchall()

for year in years:
    year = year[0]

    cursor.execute("SELECT max(date) FROM Matches WHERE strftime('%Y', date) = '"+str(year)+"'")
    last_date = [row[0] for row in cursor.fetchall()]

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
    years_data_sql = cursor.fetchall()

    years_data = {
    'year': year,
    'last_date': last_date,
    'rankings': [{
        'ranking': ranking,
        'flag' : flag,
        'team' : team,
        'reference_team': reference_team,
        'points': points,
        'confederation': confederation,
        'ranking_change': ranking_change,
        'points_change': points_change
    } for ranking, flag, team, reference_team, points, confederation, ranking_change, points_change in years_data_sql]
    }

    # JSON file name
    years_path = Path(f"data/json/rankings/{year}Rankings.json")

    with open(years_path, "w", encoding="utf-8") as years_file:
        json.dump(years_data, years_file, indent=2)
        print(f"Data successfully extracted and exported to {years_path}.")

connection.close()