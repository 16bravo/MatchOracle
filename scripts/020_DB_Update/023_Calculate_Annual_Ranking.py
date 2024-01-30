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
end_date = today_date if pd.isna(end_date) else end_date

# Generate all the dates to display, all the 31/12 in the date frame
# 'A-DEC' for each December 31st
EOY_dates = pd.date_range(start=start_date, end=end_date, freq='A-DEC')

# Init the Points History Dataframe with all the 31/12 dates
points_history = pd.DataFrame({'date': EOY_dates})

# Adding today date for last date points
# Prevent duplicates : If we're on 31/12, no need to add today date as the following loop will generate data for this day
if not (datetime.now().month == 12 and datetime.now().day == 31):
    points_history = pd.concat([points_history, today], ignore_index=True)

# Add one column for each team (id by its history name name)
points_history = pd.concat([points_history, pd.DataFrame(columns=teams['team'].unique())], axis=1)

# Create the Countries History to list all the countries names in history
countries_history = pd.DataFrame()

# Calculate points for each 31/12 in the date frame defined by start_date + today date if we're not already on 31/12
for index, row in tqdm(points_history.iterrows(), total=len(points_history), desc="Calculating Points History"):
    date = row['date']

    # List of countries to date to get original names at this date
    countries_to_date = teams[((date >= teams['startDate']) | teams['startDate'].isna()) &
                     ((date <= teams['endDate']) | teams['endDate'].isna())]
    # We keep the first value (by priority)
    countries_to_date = countries_to_date.drop_duplicates(subset=['team'])
    countries_to_date['date'] = date

    # Retrieve last points value in matches df to the date
    for reference_team in teams['reference_team'].unique():
        team_matches = matches[((matches['home_team'] == reference_team) | (matches['away_team'] == reference_team)) & (matches['date'] <= date)]
               
        # If this is a match of the team (team_matches is not empty), get data
        if not team_matches.empty:
            last_points_home = team_matches.iloc[-1]['home_points_after'] if team_matches.iloc[-1]['home_team'] == reference_team else 0
            last_points_away = team_matches.iloc[-1]['away_points_after'] if team_matches.iloc[-1]['away_team'] == reference_team else 0
            
            last_points = max(last_points_home, last_points_away)

            team = countries_to_date.loc[countries_to_date['reference_team'] == reference_team, 'team'].values[0] if not countries_to_date.loc[countries_to_date['reference_team'] == reference_team, 'team'].empty else reference_team

            points_history.at[index, team] = last_points

        # If the match was today, we directly get the value points in teams (last value calculated)
        elif date == today_date:
            last_points = teams.loc[teams['reference_team'] == reference_team, 'points'].values[0]
    
            points_history.at[index, reference_team] = last_points

# Transforming df : pivoting points_history
points_history = pd.melt(points_history, id_vars=['date'], var_name='team', value_name='points')
points_history.sort_values(by=['date', 'team'], inplace=True)
# Deleting lines with no value for points (teams does not exist)
points_history = points_history[points_history['points'].notna()]

print('Points History calculated')

# Save the dataset in temp csv file
points_history.to_csv('data/temp/points_history.csv', index=False)

print('Points History data saved in temp file')