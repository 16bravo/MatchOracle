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

# Checking if the teams are valid
home_condition = fixtures['home_team'].isin(teams['reference_team'])
away_condition = fixtures['away_team'].isin(teams['reference_team'])

valid_fixtures = home_condition & away_condition
fixtures = fixtures[valid_fixtures]

print(fixtures)

## POINTS CALCULATION MATCH BY MATCH

for index, fixture in  tqdm(fixtures.iterrows(), total=len(fixtures), desc="Calculating fixtures expected results"):
    
    # Init match values
    home_team = fixture['home_team']
    away_team = fixture['away_team']
    
    # Retrieve the points value for home_team and away_team.
    points_home_team = teams.loc[teams['reference_team'] == home_team, 'points'].values[0]
    points_away_team = teams.loc[teams['reference_team'] == away_team, 'points'].values[0]
    points_off_home_team = teams.loc[teams['reference_team'] == home_team, 'points_off'].values[0]
    points_off_away_team = teams.loc[teams['reference_team'] == away_team, 'points_off'].values[0]
    points_def_home_team = teams.loc[teams['reference_team'] == home_team, 'points_def'].values[0]
    points_def_away_team = teams.loc[teams['reference_team'] == away_team, 'points_def'].values[0]

    # Point calculations
    if fixture['tournament'] == "FIFA World Cup":
        match_coef = 60
    elif fixture['tournament'] == "Friendly":
        match_coef = 20
    else:
        match_coef = 40
    home = int(not fixture['neutral'])

    # Expected Results
    # Main ranking
    expected_result = max(-2.5,min(2.5,((1/(1+math.exp(-1*(points_home_team-points_away_team)/850))-0.5)*33-1.25*home)/6.5))
    # Off/Def ranking
    b1 = (points_off_home_team - points_def_away_team + home * 136)
    b2 = (points_off_away_team - points_def_home_team - home * 136)

    if b1 > 0:
        expected_1 = float(np.real_if_close(1.66e-6 * (b1 + 924) ** 1.96))
    else:
        expected_1 = 0.0
    if b2 > 0:
        expected_2 = float(np.real_if_close(1.66e-6 * (b2 + 924) ** 1.96))
    else:
        expected_2 = 0.0

    # Create a team dataframe with teams at the time for ranking
    teams_at_time = teams.query("startDate < @fixture.date and endDate > @fixture.date and not team.str.startswith('Not-')", engine='python') #Doesn't work for Not-sovereign countries
    teams_at_time = teams_at_time.sort_values(by='priority')
    teams_at_time = teams_at_time.drop_duplicates(subset='reference_team', keep='first')
    teams_at_time['rank'] = teams_at_time['points'].rank(ascending=False)
    teams_at_time['rank_off'] = teams_at_time['points_off'].rank(ascending=False)
    teams_at_time['rank_def'] = teams_at_time['points_def'].rank(ascending=False)
    
    # Main ranking
    home_rank = teams_at_time.loc[teams_at_time['reference_team'] == home_team, 'rank']
    home_rank = home_rank.iloc[0] if not home_rank.empty else np.nan
    away_rank = teams_at_time.loc[teams_at_time['reference_team'] == away_team, 'rank']
    away_rank = away_rank.iloc[0] if not away_rank.empty else np.nan
    # Off/Def ranking
    home_rank_off = teams_at_time.loc[teams_at_time['reference_team'] == home_team, 'rank_off']
    home_rank_off = home_rank_off.iloc[0] if not home_rank_off.empty else np.nan
    away_rank_off = teams_at_time.loc[teams_at_time['reference_team'] == away_team, 'rank_off']
    away_rank_off = away_rank_off.iloc[0] if not away_rank_off.empty else np.nan
    home_rank_def = teams_at_time.loc[teams_at_time['reference_team'] == home_team, 'rank_def']
    home_rank_def = home_rank_def.iloc[0] if not home_rank_def.empty else np.nan
    away_rank_def = teams_at_time.loc[teams_at_time['reference_team'] == away_team, 'rank_def']
    away_rank_def = away_rank_def.iloc[0] if not away_rank_def.empty else np.nan
    
    # Update the values in the match dataframe
    # Main ranking   
    fixtures.at[index, 'home_points_before'] = points_home_team
    fixtures.at[index, 'away_points_before'] = points_away_team
    fixtures.at[index, 'expected_result'] = expected_result
    fixtures.at[index, 'home_rank'] = home_rank
    fixtures.at[index, 'away_rank'] = away_rank
    # Off/Def ranking
    fixtures.at[index, 'home_points_off_before'] = points_off_home_team
    fixtures.at[index, 'away_points_off_before'] = points_off_away_team
    fixtures.at[index, 'home_points_def_before'] = points_def_home_team
    fixtures.at[index, 'away_points_def_before'] = points_def_away_team
    fixtures.at[index, 'expected_score_1'] = expected_1
    fixtures.at[index, 'expected_score_2'] = expected_2
    fixtures.at[index, 'home_rank_off'] = home_rank_off
    fixtures.at[index, 'away_rank_off'] = away_rank_off
    fixtures.at[index, 'home_rank_def'] = home_rank_def
    fixtures.at[index, 'away_rank_def'] = away_rank_def

print('Fixtures Points Calculated')

# Save the datasets in temp csv files
fixtures.to_csv('data/temp/fixtures.csv', index=False)

print('Fixtures data saved in temp files')