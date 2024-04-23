import sqlite3

# Database connection
database_path = 'data/BravoRanking.db'
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# Table creation
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Fixtures (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        country VARCHAR(50),
        tournament VARCHAR(60),
        team1 VARCHAR(50) NOT NULL,
        team2 VARCHAR(50) NOT NULL,
        original_team1 VARCHAR(50) NOT NULL,
        original_team2 VARCHAR(50) NOT NULL,
        rating1 INTEGER,
        rating2 INTEGER,
        rank1 INTEGER,
        rank2 INTEGER,
        expected_result FLOAT,
        neutral BOOLEAN NOT NULL
    );
''')

conn.commit()
conn.close()

print('Fixtures Table Created')