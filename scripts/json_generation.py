import sqlite3
import json

# Connexion à la base de données SQLite
database_path = "data/BravoRanking.db"
connection = sqlite3.connect(database_path)
cursor = connection.cursor()

# Exécution de la requête SQL pour sélectionner toutes les lignes de la table
cursor.execute('''
                SELECT r.ranking, t.tricode || '.png' AS flag, r.team, r.points, t.confederation
                FROM Rankings r
                LEFT JOIN Teams t ON (r.team = t.team)
                WHERE date = (SELECT MAX(date) FROM Rankings)
               '''
)

# Récupération de toutes les lignes sous forme de liste de tuples
rows = cursor.fetchall()

# Obtention des noms des colonnes
column_names = [description[0] for description in cursor.description]

# Création d'une liste de dictionnaires pour chaque ligne
data = [dict(zip(column_names, row)) for row in rows]

# Fermeture de la connexion à la base de données
connection.close()

# Exportation des données vers un fichier JSON
json_path = "data/LastMonthRanking.json"
with open(json_path, "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, indent=2)

print(f"Données extraites avec succès et exportées vers {json_path}.")