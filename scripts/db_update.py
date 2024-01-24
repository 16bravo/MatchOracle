import kaggle.cli
import sys
import pandas as pd
from pathlib import Path
from zipfile import ZipFile
from tqdm import tqdm
import math
import numpy as np
from dateutil.relativedelta import relativedelta
from datetime import datetime
import sqlite3

## EXTRACT DATA FROM KAGGLE AND EXCEL

# Download data set
# https://www.kaggle.com/datasets/patateriedata/all-international-football-results
dataset = "patateriedata/all-international-football-results"
sys.argv = [sys.argv[0]] + f"datasets download {dataset}".split(" ")
kaggle.cli.main()

zfile = ZipFile(f"{dataset.split('/')[1]}.zip")

matches = {f.filename:pd.read_csv(zfile.open(f)) for f in zfile.infolist() }["all_matches.csv"]
matches['match_id'] = range(1, len(matches) + 1)
#countries = pd.read_excel('data/countries_names.xlsx')

# Match validity filter
# Load data from CSV files
# matches generated with Kaggle API
teams_db = pd.read_excel('data/teams_db.xlsx')

# replacing old countries' names by the current ones but saving them
matches['history_home_team'] = matches['home_team']
matches['history_away_team'] = matches['away_team']
matches['home_team'] = matches['home_team'].replace(teams_db.set_index('team')['reference_team'])
matches['away_team'] = matches['away_team'].replace(teams_db.set_index('team')['reference_team'])

# Merge DataFrames on home_team and away_team columns
merged_df = pd.merge(matches, teams_db[['team', 'tricode']], how='inner', left_on='home_team', right_on='team')
merged_df = pd.merge(merged_df, teams_db[['team', 'tricode']], how='inner', left_on='away_team', right_on='team')

# Filter lines where both teams are valid (non-empty tricode)
valid_matches = merged_df[(merged_df['tricode_x'].notna()) & (merged_df['tricode_y'].notna())]
matches_filtered = valid_matches[['match_id']]
matches = pd.merge(matches, matches_filtered, how='inner', on='match_id')
matches = matches.sort_values(by='match_id', ascending=True)

## LOAD DATA IF EXISTS

matches['home_points_before'] = None
matches['away_points_before'] = None
matches['expected_result'] = None
matches['calculated_result'] = None
matches['home_points_after'] = None
matches['away_points_after'] = None

database_path = 'data/BravoRanking.db'  
conn = sqlite3.connect(database_path)

# Check if the Rankings table is empty
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM Rankings")
result = cursor.fetchone()

# Create the DataFrame
teams = pd.DataFrame(columns=['team', 'points'])

if result[0] == 0:
    last_date = datetime(1872, 1, 1)
    # Load the DataFrame from the Excel file
    teams_db = pd.read_excel("data/teams_db.xlsx")
    # Excluding non-valid teams (with no tricode)
    teams_db = teams_db[(teams_db['tricode'].notna())]    
    teams['team'] = teams_db['team']
    teams['points'] = teams_db['base']
    matches['date'] = pd.to_datetime(matches['date'])
    
else:
    # Retrieve the last line and filter the dataset from here
    query_last_match_info = '''
        SELECT date, team1 AS home_team, team2 AS away_team, score1 AS home_score, score2 AS away_score, tournament, country
        FROM Matches
        ORDER BY match_id DESC
        LIMIT 1;
    '''

    last_match_info_in_db = pd.read_sql_query(query_last_match_info, conn)

    last_match_id = matches[
        (matches['date'] == last_match_info_in_db['date'].iloc[0]) &
        (matches['home_team'] == last_match_info_in_db['home_team'].iloc[0]) &
        (matches['away_team'] == last_match_info_in_db['away_team'].iloc[0]) &
        (matches['home_score'] == last_match_info_in_db['home_score'].iloc[0]) &
        (matches['away_score'] == last_match_info_in_db['away_score'].iloc[0]) &
        (matches['tournament'] == last_match_info_in_db['tournament'].iloc[0]) &
        (matches['country'] == last_match_info_in_db['country'].iloc[0])
    ]['match_id'].iloc[0]

    matches = matches[matches['match_id'] > last_match_id]
    matches['date'] = pd.to_datetime(matches['date'])

    # Retrieve the maximum date from the Rankings table to get the last ratings
    last_date_query = "SELECT strftime('%Y-%m-%d',MAX(date)) FROM Rankings"
    last_date = pd.read_sql(last_date_query, conn).iloc[0, 0]
    last_date = datetime.strptime(last_date, "%Y-%m-%d")
    last_year = last_date.year
    last_month = last_date.month
    last_day = last_date.day
    # Load DataFrame from database
    teams_query = f"SELECT r.team, r.points, t.startDate, t.endDate FROM Rankings r LEFT JOIN Teams t ON (r.team = t.team) WHERE year = {last_year} AND month = {last_month} AND day = {last_day}"
    teams_db = pd.read_sql(teams_query, conn)
    teams_db['startDate'] = pd.to_datetime(teams_db['startDate'])
    teams_db['endDate'] = pd.to_datetime(teams_db['endDate'])
    teams['team'] = teams_db['team']
    teams['points'] = teams_db['points']

conn.close()

## POINTS CALCULATION MATCH BY MATCH

#matches['date'] = pd.to_datetime(matches['date'])
#matches = matches[matches['date'] > last_date]

for index, match in  tqdm(matches.iterrows(), total=len(matches), desc="Calculating matches points"):
    
    home_team = match['home_team']
    away_team = match['away_team']
    home_score = match['home_score']
    away_score = match['away_score']
    
    # Retrieve the points value for home_team and away_team.
    points_home_team = teams.loc[teams['team'] == home_team, 'points'].values[0]
    points_away_team = teams.loc[teams['team'] == away_team, 'points'].values[0]

    # Point calculations
    if match['tournament'] == "FIFA World Cup":
        match_coef = 60
    elif match['tournament'] == "Friendly":
        match_coef = 20
    else:
        match_coef = 40

    expected_result = ((1/(1+math.exp(-1*(points_home_team-points_away_team)/850))-0.5)*33-1.25*int(not match['neutral']))/6.5
    calculated_result = ((1/(1+math.exp(-1*(home_score-away_score)/5))-0.5)*21-int(not match['neutral']))/3

    home_points_after = points_home_team + (calculated_result-expected_result) * match_coef
    away_points_after = points_away_team - (calculated_result-expected_result) * match_coef

    teams.loc[teams['team'] == home_team, 'points'] = home_points_after
    teams.loc[teams['team'] == away_team, 'points'] = away_points_after
        
    matches.at[index, 'home_points_before'] = points_home_team
    matches.at[index, 'away_points_before'] = points_away_team
    matches.at[index, 'expected_result'] = expected_result
    matches.at[index, 'calculated_result'] = calculated_result
    matches.at[index, 'home_points_after'] = home_points_after
    matches.at[index, 'away_points_after'] = away_points_after


teams = teams.sort_values(by='points', ascending=False)

teams['ranking'] = range(1, len(teams) + 1)

#matches.to_excel('matches.xlsx', index=False)

#sys.exit()

## GET POINTS YEAR BY YEAR AND TODAY

today_date = pd.Timestamp(datetime.now())
today = pd.DataFrame({'date': [today_date]})

start_date = matches['date'].min()
end_date = matches['date'].max()

start_date = last_date if pd.isna(start_date) else start_date
end_date = today_date if pd.isna(end_date) else end_date

EOY_dates = pd.date_range(start=start_date, end=end_date, freq='A-DEC') # 'A-DEC' for each December 31st

historical_points = pd.DataFrame({'date': EOY_dates})

if not (datetime.now().month == 12 and datetime.now().day == 31):
    historical_points = pd.concat([historical_points, today], ignore_index=True)

historical_points = pd.concat([historical_points, pd.DataFrame(columns=teams['team'].unique())], axis=1)

historical_countries = pd.DataFrame()

for index, row in tqdm(historical_points.iterrows(), total=len(historical_points), desc="Calculating Historical Points"):
    date = row['date']

    #valid_data = merged_data[((merged_data['date'] >= merged_data['startDate']) | merged_data['startDate'].isna()) &
    #                         ((merged_data['date'] <= merged_data['endDate']) | merged_data['endDate'].isna())]

    #List of countries to date to get original names
    countries_to_date = teams_db[((date >= teams_db['startDate']) | teams_db['startDate'].isna()) &
                     ((date <= teams_db['endDate']) | teams_db['endDate'].isna())]
    countries_to_date = countries_to_date.drop_duplicates(subset=['team'])
    countries_to_date['date'] = date

    #historical_countries = pd.concat([historical_countries,countries_to_date], ignore_index=True)

    for team in teams['team'].unique():
        team_matches = matches[((matches['home_team'] == team) | (matches['away_team'] == team)) & (matches['date'] <= date)]
        #new_team_name = countries_to_date.loc[countries_to_date['current_name'] == team]['original_name'].values[0] if not countries_to_date.loc[countries_to_date['current_name'] == team]['original_name'].empty else team

        if not team_matches.empty:
            last_points_home = team_matches.iloc[-1]['home_points_after'] if team_matches.iloc[-1]['home_team'] == team else 0
            last_points_away = team_matches.iloc[-1]['away_points_after'] if team_matches.iloc[-1]['away_team'] == team else 0

            last_points = max(last_points_home, last_points_away)

            original_name = countries_to_date.loc[countries_to_date['reference_team'] == team, 'team'].values[0] if not countries_to_date.loc[countries_to_date['reference_team'] == team, 'team'].empty else team

            historical_points.at[index, original_name] = last_points
        elif date == today_date:
            last_points = teams.loc[teams['team'] == team, 'points'].values[0]
    
            historical_points.at[index, team] = last_points

#historical_points.to_excel('histpoints.xlsx')

## DATA CLEANSING

melted_points = pd.melt(historical_points, id_vars=['date'], var_name='team', value_name='points')
melted_points.sort_values(by=['date', 'team'], inplace=True)

# Deleting empty lines
melted_points = melted_points[melted_points['points'].notna()]

melted_points['date'] = pd.to_datetime(melted_points['date'])

#melted_points = pd.merge(melted_points, historical_countries, left_on=['date','team'], right_on=['date','original_name'])
#melted_points = melted_points.drop(['team','current_name','start_date','end_date','priority'], axis=1)
#melted_points = melted_points.rename(columns={'original_name': 'team'})

teams_db['startDate'] = pd.to_datetime(teams_db['startDate'])
teams_db['endDate'] = pd.to_datetime(teams_db['endDate'])

merged_data = pd.merge(melted_points, teams_db[['team','reference_team','startDate','endDate']], on='team')
valid_data = merged_data[((merged_data['date'] >= merged_data['startDate']) | merged_data['startDate'].isna()) &
                         ((merged_data['date'] <= merged_data['endDate']) | merged_data['endDate'].isna())]

ranking_df = valid_data[['date', 'team', 'points']]

ranking_df = ranking_df.drop_duplicates()

ranking_df.loc[:, 'ranking'] = ranking_df.groupby('date')['points'].rank(ascending=False, method='min')

ranking_df.sort_values(by=['date', 'ranking'], inplace=True)

ranking_df['year'] = ranking_df['date'].dt.year
ranking_df['month'] = ranking_df['date'].dt.month
ranking_df['day'] = ranking_df['date'].dt.day
ranking_df['points'] = ranking_df['points'].astype(int)
ranking_df['ranking'] = ranking_df['ranking'].astype(int)

ranking_df = pd.merge(ranking_df, teams_db[['team','reference_team']], left_on='team', right_on='team')
#ranking_df = ranking_df.rename(columns={'reference_team': 'reference_team'})

ranking_df = ranking_df[['date', 'year', 'month', 'day', 'team', 'reference_team', 'points', 'ranking']]
ranking_df = ranking_df.drop_duplicates()
#ranking_df.to_excel('ranking_df.xlsx')

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

# Insert rankings into SQLite table
ranking_df.to_sql('Rankings', conn, index=False, if_exists='append')

conn.commit()
conn.close()
