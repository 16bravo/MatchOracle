import pandas as pd
from tqdm import tqdm
import math
import numpy as np
import sys

# Retrieve Data from previous steps in csv files
fixtures = pd.read_csv('data/source/fixtures.csv')
teams = pd.read_csv('data/temp/teams.csv')

# Adapting dates for calculation
fixtures['date'] = pd.to_datetime(fixtures['date'], errors='coerce')

teams['startDate'] = pd.to_datetime(teams['startDate'], errors='coerce')
teams['startDate'] = teams['startDate'].fillna('01/01/1872')
teams['startDate'] = pd.to_datetime(teams['startDate'], format='%d/%m/%Y')
teams['endDate'] = pd.to_datetime(teams['endDate'], errors='coerce')
teams['endDate'] = teams['endDate'].fillna('31/12/2099')
teams['endDate'] = pd.to_datetime(teams['endDate'], format='%d/%m/%Y')


## POINTS CALCULATION MATCH BY MATCH

for index, fixture in  tqdm(fixtures.iterrows(), total=len(fixtures), desc="Calculating fixtures expected results"):
    
    # Init match values
    home_team = fixture['home_team']
    away_team = fixture['away_team']
    
    # Retrieve the points value for home_team and away_team.
    points_home_team = teams.loc[teams['reference_team'] == home_team, 'points'].values[0]
    points_away_team = teams.loc[teams['reference_team'] == away_team, 'points'].values[0]

    # Point calculations
    if fixture['tournament'] == "FIFA World Cup":
        match_coef = 60
    elif fixture['tournament'] == "Friendly":
        match_coef = 20
    else:
        match_coef = 40

    expected_result = max(-2.5,min(2.5,((1/(1+math.exp(-1*(points_home_team-points_away_team)/850))-0.5)*33-1.25*int(not fixture['neutral']))/6.5))

    # Create a team dataframe with teams at the time for ranking
    teams_at_time = teams.query("startDate < @fixture.date and endDate > @fixture.date and not team.str.startswith('Not-')", engine='python') #Doesn't work for Not-sovereign countries
    teams_at_time = teams_at_time.sort_values(by='priority')
    teams_at_time = teams_at_time.drop_duplicates(subset='reference_team', keep='first')
    teams_at_time['rank'] = teams_at_time['points'].rank(ascending=False)
    
    home_rank = teams_at_time.loc[teams_at_time['reference_team'] == home_team, 'rank']
    home_rank = home_rank.iloc[0] if not home_rank.empty else np.nan
    away_rank = teams_at_time.loc[teams_at_time['reference_team'] == away_team, 'rank']
    away_rank = away_rank.iloc[0] if not away_rank.empty else np.nan
    
    # Update the values in the match dataframe    
    fixtures.at[index, 'home_points_before'] = points_home_team
    fixtures.at[index, 'away_points_before'] = points_away_team
    fixtures.at[index, 'expected_result'] = expected_result
    fixtures.at[index, 'home_rank'] = home_rank
    fixtures.at[index, 'away_rank'] = away_rank

print('Fixtures Points Calculated')

# Save the datasets in temp csv files
fixtures.to_csv('data/temp/fixtures.csv', index=False)

print('Fixtures data saved in temp files')