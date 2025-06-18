import sqlite3
import json
from pathlib import Path

# SQLite database connection
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# YEARLY RANKINGS
# HISTORICAL RANKINGS FROM 1872
# Retrieves all month-end dates in Rankings
cursor.execute("""
    SELECT DISTINCT strftime('%Y', date) as year, strftime('%m', date) as month
    FROM Rankings
    WHERE date IS NOT NULL
    ORDER BY year, month
""")
months = cursor.fetchall()

for year, month in months:
    # Last date of the month
    cursor.execute("""
        SELECT MAX(date) FROM Rankings
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
    """, (year, month))
    latest_date = [row[0] for row in cursor.fetchall()]

    # Retrieves ranking data for this date
    cursor.execute("""
        WITH previous_month AS (
            SELECT r.ranking, r.reference_team, r.points
            FROM Rankings r
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        )
        SELECT r.ranking, t.flag, r.team, r.reference_team, r.points, t.confederation,
               (p.ranking - r.ranking) AS ranking_change,
               (r.points - p.points) AS points_change
        FROM Rankings r
        LEFT JOIN Teams t ON (
            r.team = t.team
            AND (t.startDate IS NULL OR r.date >= t.startDate)
            AND (t.endDate IS NULL OR r.date <= t.endDate)
        )
        LEFT JOIN previous_month p ON (r.reference_team = p.reference_team)
        WHERE date = (SELECT MAX(date) FROM Rankings WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?)
          AND r.team NOT LIKE ('Not-Sovereign %')
        ORDER BY r.ranking
    """, (year, str(int(month)-1).zfill(2), year, month))

    month_data_sql = cursor.fetchall()

    # Generates JSON
    month_data = {
        'year': int(year),
        'month': int(month),
        'latest_date': latest_date,
        'rankings': [{
            'ranking': ranking,
            'flag': flag,
            'team': team,
            'reference_team': reference_team,
            'points': points,
            'confederation': confederation,
            'ranking_change': ranking_change if ranking_change is not None else 0,
            'points_change': points_change if points_change is not None else 0
        } for ranking, flag, team, reference_team, points, confederation, ranking_change, points_change in month_data_sql]
    }

    # File name
    month_path = Path(f"data/json/rankings/{year}{month}Rankings.json")
    with open(month_path, "w", encoding="utf-8") as month_file:
        json.dump(month_data, month_file, indent=2)
        print(f"Data successfully extracted and exported to {month_path}.")

connection.close()