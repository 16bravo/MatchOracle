import pandas as pd
from tqdm import tqdm
import math
import numpy as np
import sys

# Retrieve Data from previous steps in csv files
matches = pd.read_csv('data/temp/matches.csv')
teams = pd.read_csv('data/temp/teams.csv')

# Adapting dates for calculation
matches['date'] = pd.to_datetime(matches['date'], errors='coerce')

teams['startDate'] = pd.to_datetime(teams['startDate'], errors='coerce')
teams['startDate'] = teams['startDate'].fillna('01/01/1872')
teams['startDate'] = pd.to_datetime(teams['startDate'], format='%d/%m/%Y')
teams['endDate'] = pd.to_datetime(teams['endDate'], errors='coerce')
teams['endDate'] = teams['endDate'].fillna('31/12/2099')
teams['endDate'] = pd.to_datetime(teams['endDate'], format='%d/%m/%Y')

# Adding a simplified teams dataframe to count the number of match and the live ranking
#reference_teams = pd.DataFrame({'reference_team': teams['reference_team'].unique()})
#reference_teams = teams.groupby('reference_team')['points'].max().reset_index()

#teams_at_time = teams[['team','reference_team','startDate','endDate','points']]

#print(teams_at_time)



## POINTS CALCULATION MATCH BY MATCH

for index, match in  tqdm(matches.iterrows(), total=len(matches), desc="Calculating matches points"):
    
    # Init match values
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

    # Create a team dataframe with teams at the time for ranking
    teams_at_time = teams.query("startDate < @match.date and endDate > @match.date and not team.str.startswith('Not-')", engine='python') #Doesn't work for Not-sovereign countries
    teams_at_time = teams_at_time.sort_values(by='priority')
    teams_at_time = teams_at_time.drop_duplicates(subset='reference_team', keep='first')
    teams_at_time['rank'] = teams_at_time['points'].rank(ascending=False)
    
    home_rank = teams_at_time.loc[teams_at_time['reference_team'] == home_team, 'rank']
    home_rank = home_rank.iloc[0] if not home_rank.empty else np.nan
    away_rank = teams_at_time.loc[teams_at_time['reference_team'] == away_team, 'rank']
    away_rank = away_rank.iloc[0] if not away_rank.empty else np.nan
    
    # Update the values in the match dataframe    
    matches.at[index, 'home_points_before'] = points_home_team
    matches.at[index, 'away_points_before'] = points_away_team
    matches.at[index, 'expected_result'] = expected_result
    matches.at[index, 'calculated_result'] = calculated_result
    matches.at[index, 'home_points_after'] = home_points_after
    matches.at[index, 'away_points_after'] = away_points_after
    matches.at[index, 'home_rank'] = home_rank
    matches.at[index, 'away_rank'] = away_rank

teams = teams.sort_values(by=['points', 'priority'], ascending=[False, True])

teams['ranking'] = range(1, len(teams) + 1)

print('Matches Points Calculated & Teams Data Updated')

# Save the datasets in temp csv files
matches.to_csv('data/temp/matches.csv', index=False)
teams.to_csv('data/temp/teams.csv', index=False)

print('Teams, Matches data saved in temp files')