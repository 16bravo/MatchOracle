import pandas as pd
from tqdm import tqdm
import math
import sys

# Retrieve Data from previous steps in csv files
matches = pd.read_csv('data/temp/matches.csv')
teams = pd.read_csv('data/temp/teams.csv')

# Adding a simplified teams dataframe to count the number of match and the live ranking
reference_teams = pd.DataFrame({'reference_team': teams['reference_team'].unique()})
reference_teams['nb_matches'] = 0

## POINTS CALCULATION MATCH BY MATCH

for index, match in  tqdm(matches.iterrows(), total=len(matches), desc="Calculating matches points"):
    
    home_team = match['home_team']
    away_team = match['away_team']
    home_score = match['home_score']
    away_score = match['away_score']
    
    # Retrieve the points value for home_team and away_team.
    points_home_team = teams.loc[teams['reference_team'] == home_team, 'points'].values[0]
    points_away_team = teams.loc[teams['reference_team'] == away_team, 'points'].values[0]

    # Point calculations
    if match['tournament'] == "FIFA World Cup":
        match_coef = 60
    elif match['tournament'] == "Friendly":
        match_coef = 20
    else:
        match_coef = 40

    expected_result = max(-2.5,min(2.5,((1/(1+math.exp(-1*(points_home_team-points_away_team)/850))-0.5)*33-1.25*int(not match['neutral']))/6.5))
    calculated_result = max(-2.5,min(2.5,((1/(1+math.exp(-1*(home_score-away_score)/5))-0.5)*21-int(not match['neutral']))/3))

    home_points_after = round(points_home_team + (calculated_result-expected_result) * match_coef)
    away_points_after = round(points_away_team - (calculated_result-expected_result) * match_coef)

    teams.loc[teams['reference_team'] == home_team, 'points'] = home_points_after
    teams.loc[teams['reference_team'] == away_team, 'points'] = away_points_after

    reference_teams.loc[reference_teams['reference_team'] == home_team, 'nb_matches'] += 1
    reference_teams.loc[reference_teams['reference_team'] == away_team, 'nb_matches'] += 1
    reference_teams.loc[reference_teams['reference_team'] == home_team, 'points'] = home_points_after
    reference_teams.loc[reference_teams['reference_team'] == away_team, 'points'] = away_points_after

    reference_teams['rank'] = reference_teams['points'].rank(ascending=False)
    home_rank = reference_teams.loc[reference_teams['reference_team'] == home_team, 'rank']
    away_rank = reference_teams.loc[reference_teams['reference_team'] == away_team, 'rank']
        
    matches.at[index, 'home_points_before'] = points_home_team
    matches.at[index, 'away_points_before'] = points_away_team
    matches.at[index, 'expected_result'] = expected_result
    matches.at[index, 'calculated_result'] = calculated_result
    matches.at[index, 'home_points_after'] = home_points_after
    matches.at[index, 'away_points_after'] = away_points_after
    matches.at[index, 'home_rank'] = home_rank
    matches.at[index, 'away_rank'] = away_rank

teams = teams.sort_values(by='points', ascending=False)

teams['ranking'] = range(1, len(teams) + 1)

print('Matches Points Calculated & Teams Data Updated')

# Save the datasets in temp csv files
matches.to_csv('data/temp/matches.csv', index=False)
teams.to_csv('data/temp/teams.csv', index=False)

print('Teams, Matches data saved in temp files')