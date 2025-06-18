import pandas as pd
from tqdm import tqdm
from datetime import datetime
import sys

# Retrieve Data from previous steps in csv files
matches = pd.read_csv('data/temp/matches.csv')
teams = pd.read_csv('data/temp/teams.csv')
# Retrieve the last date variable in txt file
with open('data/temp/last_date.txt', 'r') as file:
    date_str = file.read().strip()
date_format = "%Y-%m-%d %H:%M:%S"
last_date = datetime.strptime(date_str, date_format)

# Convert the date in datetime format
matches['date'] = pd.to_datetime(matches['date'])
teams['startDate'] = pd.to_datetime(teams['startDate'])
teams['endDate'] = pd.to_datetime(teams['endDate'])

## GET POINTS YEAR BY YEAR AND TODAY
# Get today date
today_date = pd.Timestamp(datetime.now())
today = pd.DataFrame({'date': [today_date]})

# Get time frame : from first to last date in matches df
start_date = matches['date'].min()
end_date = matches['date'].max()
start_date = last_date if pd.isna(start_date) else start_date
last_eoy = pd.Timestamp(year=today_date.year - 1, month=12, day=31)
end_date = max(last_eoy, end_date)

# Generates all month-ends with matches
EOM_dates = pd.date_range(start=start_date, end=end_date, freq='ME')
if today_date.normalize() > EOM_dates.max():
    EOM_dates = EOM_dates.append(pd.to_datetime([today_date.normalize()]))

# Prepare column list
cols = ['date']
for col_type in ["points", "points_off", "points_def"]:
    for team in teams['team'].unique():
        cols.append(f"{team}_{col_type}")

# Creates the DataFrame with all columns set to None
points_history = pd.DataFrame(columns=cols)
points_history['date'] = EOM_dates

# Adds today's date if not already end of month
if today_date.normalize() not in EOM_dates:
    points_history = pd.concat([points_history, pd.DataFrame({'date': [today_date.normalize()]})], ignore_index=True)

# Add one column for each team (id by its history name name)
for col_type in ["points", "points_off", "points_def"]:
    for team in teams['team'].unique():
        points_history[f"{team}_{col_type}"] = None

# Create the Countries History to list all the countries names in history
countries_history = pd.DataFrame()

# Calculate points for each 31/12 in the date frame defined by start_date + today date if we're not already on 31/12
for index, row in tqdm(points_history.iterrows(), total=len(points_history), desc="Calculating Points History"):
    date = row['date']
    countries_to_date = teams[((date >= teams['startDate']) | teams['startDate'].isna()) &
                     ((date <= teams['endDate']) | teams['endDate'].isna())]
    countries_to_date = countries_to_date.drop_duplicates(subset=['team'])
    countries_to_date['date'] = date

    for reference_team in teams['reference_team'].unique():
        team_matches = matches[((matches['home_team'] == reference_team) | (matches['away_team'] == reference_team)) & (matches['date'] <= date)]
        if not team_matches.empty:
            last_match = team_matches.iloc[-1]
            # Main Points
            last_points_home = last_match['home_points_after'] if last_match['home_team'] == reference_team else None
            last_points_away = last_match['away_points_after'] if last_match['away_team'] == reference_team else None
            last_points = last_points_home if last_points_home is not None else last_points_away

            # Points off
            last_points_off_home = last_match['home_points_off_after'] if last_match['home_team'] == reference_team else None
            last_points_off_away = last_match['away_points_off_after'] if last_match['away_team'] == reference_team else None
            last_points_off = last_points_off_home if last_points_off_home is not None else last_points_off_away

            # Points def
            last_points_def_home = last_match['home_points_def_after'] if last_match['home_team'] == reference_team else None
            last_points_def_away = last_match['away_points_def_after'] if last_match['away_team'] == reference_team else None
            last_points_def = last_points_def_home if last_points_def_home is not None else last_points_def_away

            team = countries_to_date.loc[countries_to_date['reference_team'] == reference_team, 'team'].values[0] if not countries_to_date.loc[countries_to_date['reference_team'] == reference_team, 'team'].empty else reference_team

            points_history.at[index, f"{team}_points"] = last_points
            points_history.at[index, f"{team}_points_off"] = last_points_off
            points_history.at[index, f"{team}_points_def"] = last_points_def

        elif date == today_date:
            last_points = teams.loc[teams['reference_team'] == reference_team, 'points'].values[0]
            last_points_off = teams.loc[teams['reference_team'] == reference_team, 'points_off'].values[0]
            last_points_def = teams.loc[teams['reference_team'] == reference_team, 'points_def'].values[0]

            points_history.at[index, f"{reference_team}_points"] = last_points
            points_history.at[index, f"{reference_team}_points_off"] = last_points_off
            points_history.at[index, f"{reference_team}_points_def"] = last_points_def

records = []
for index, row in points_history.iterrows():
    date = row['date']
    for team in teams['team'].unique():
        points = row.get(f"{team}_points", None)
        points_off = row.get(f"{team}_points_off", None)
        points_def = row.get(f"{team}_points_def", None)
        # On ne garde que si au moins un des points existe (évite les lignes vides)
        if pd.notna(points) or pd.notna(points_off) or pd.notna(points_def):
            records.append({
                'date': date,
                'team': team,
                'points': points,
                'points_off': points_off,
                'points_def': points_def
            })

points_history_long = pd.DataFrame(records)
points_history_long = points_history_long.dropna(subset=['points', 'points_off', 'points_def'], how='all')

print('Points History (long, one row per team/date) calculated')

points_history_long.to_csv('data/temp/points_history.csv', index=False)

print('Points History data saved in temp file')