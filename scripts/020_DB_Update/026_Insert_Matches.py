import pandas as pd
import sqlite3

database_path = 'data/BravoRanking.db' 

# Retrieve Data from previous steps in csv files
matches = pd.read_csv('data/temp/matches.csv')
# Convert the date in datetime format
date_format = "%Y-%m-%d"
matches['date'] = pd.to_datetime(matches['date'], format = date_format)

## DATABASE INSERTION
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# Insert matches data into SQLite table
matches['date'] = matches['date'].dt.strftime('%Y-%m-%d')
for index, row in matches.iterrows():
    cursor.execute('''
        INSERT INTO matches (date, country, tournament, team1, team2, original_team1, original_team2, score1, score2, rating1, rating2, rating_ev, expected_result, neutral)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row['date'], row['country'], row['tournament'], row['home_team'], row['away_team'], row['history_home_team'], row['history_away_team'], row['home_score'], row['away_score'],
          row['home_points_after'], row['away_points_after'],
          row['home_points_after'] - row['home_points_before'],
          row['expected_result'], row['neutral']
          ))

# Delete duplicates    
cursor.execute('''
    DELETE FROM Matches
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM Matches
        GROUP BY date, country, tournament, team1, team2, score1, score2
    );
''')

conn.commit()
conn.close()

print('Matches data updated in database '+database_path)