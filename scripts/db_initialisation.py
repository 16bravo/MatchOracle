import sqlite3
import pandas as pd

database_path = 'data/BravoRanking.db'

# Database connection
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# Tables creations 
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team VARCHAR(50) NOT NULL,
        reference_team VARCHAR(50),
        tricode VARCHAR(3),
        flag VARCHAR(25),
        confederation VARCHAR(10),
        startDate DATE,
        endDate DATE,
        member BOOLEAN NOT NULL,
        base INTEGER,
        priority INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rankings (
        ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        day INTEGER NOR NULL,
        team VARCHAR(50) NOT NULL,
        reference_team VARCHAR(50) NULL,
        points INTEGER NOT NULL,
        ranking INTEGER NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        country VARCHAR(50) NULL,
        tournament VARCHAR(60) NULL,
        team1 VARCHAR(50) NOT NULL,
        team2 VARCHAR(50) NOT NULL,
        original_team1 VARCHAR(50) NOT NULL,
        original_team2 VARCHAR(50) NOT NULL,
        score1 INTEGER NOT NULL,
        score2 INTEGER NOT NULL,
        rating1 INTEGER NOT NULL,
        rating2 INTEGER NOT NULL,
        rating_ev INTEGER NOT NULL,
        expected_result FLOAT NULL,
        neutral BOOLEAN NOT NULL
    );
''')


# Load Teams data from Excel to Table
excel_file_path = 'data/teams_db.xlsx'
df_teams = pd.read_excel(excel_file_path)
df_teams.to_sql('Teams', conn, index=False, if_exists='replace')

# Validez et fermez la connexion à la base de données
conn.commit()
conn.close()