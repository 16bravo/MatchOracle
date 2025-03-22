import pandas as pd
from tqdm import tqdm
from datetime import datetime
import sys

# Load data from CSV files
matches = pd.read_csv('data/temp/matches.csv')
teams = pd.read_csv('data/temp/teams.csv')

# Retrieve the last date from a text file
with open('data/temp/last_date.txt', 'r') as file:
    date_str = file.read().strip()
date_format = "%Y-%m-%d %H:%M:%S"
last_date = datetime.strptime(date_str, date_format)

# Convert date columns to datetime format
matches['date'] = pd.to_datetime(matches['date'])
teams['startDate'] = pd.to_datetime(teams['startDate'])
teams['endDate'] = pd.to_datetime(teams['endDate'])

# Get today's date
today_date = pd.Timestamp(datetime.now())
today = pd.DataFrame({'date': [today_date]})

# Define the timeframe from the first to the last match date
start_date = matches['date'].min()
end_date = matches['date'].max()
start_date = last_date if pd.isna(start_date) else start_date
end_date = max(end_date, pd.Timestamp("2024-12-31")) if pd.isna(end_date) else end_date

# Generate end-of-year dates within the timeframe
EOY_dates = pd.date_range(start=start_date, end=end_date, freq='A-DEC')

# Initialize points history dataframe
points_history = pd.DataFrame({'date': EOY_dates})

# Add today's date if it's not already December 31st
if not (today_date.month == 12 and today_date.day == 31):
    points_history = pd.concat([points_history, today], ignore_index=True)

# Add a column for each team
points_history = pd.concat([points_history, pd.DataFrame(columns=teams['team'].unique())], axis=1)

# Iterate through each date to calculate points
for index, row in tqdm(points_history.iterrows(), total=len(points_history), desc="Calculating Points History"):
    date = row['date']

    # Get active teams at the current date
    active_teams = teams[((date >= teams['startDate']) | teams['startDate'].isna()) &
                          ((date <= teams['endDate']) | teams['endDate'].isna())]
    active_teams = active_teams.drop_duplicates(subset=['team'])
    active_teams['date'] = date

    # Retrieve the last points value from matches data
    for reference_team in teams['reference_team'].unique():
        team_matches = matches[((matches['home_team'] == reference_team) | (matches['away_team'] == reference_team)) & (matches['date'] <= date)]

        if not team_matches.empty:
            last_match = team_matches.iloc[-1]
            last_points = last_match['home_points_after'] if last_match['home_team'] == reference_team else last_match['away_points_after']
        else:
            last_points = teams.loc[teams['reference_team'] == reference_team, 'points'].values[0] if date == today_date else 0

        team_name = active_teams.loc[active_teams['reference_team'] == reference_team, 'team'].values[0] if not active_teams.loc[active_teams['reference_team'] == reference_team, 'team'].empty else reference_team
        points_history.at[index, team_name] = last_points

# Reshape the dataframe
points_history = pd.melt(points_history, id_vars=['date'], var_name='team', value_name='points')
points_history.sort_values(by=['date', 'team'], inplace=True)

# Remove rows with missing points values
points_history = points_history[points_history['points'].notna()]

print('Points History calculated successfully')

# Save the processed data
points_history.to_csv('data/temp/points_history.csv', index=False)

print('Points History data saved successfully')
