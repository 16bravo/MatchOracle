import pandas as pd
import sys

# Retrieve Data from previous steps in csv files
points_history = pd.read_csv('data/temp/points_history.csv')
teams = pd.read_csv('data/temp/teams.csv')

# Convert the date in datetime format
points_history['date'] = pd.to_datetime(points_history['date'])
teams['startDate'] = pd.to_datetime(teams['startDate'])
teams['endDate'] = pd.to_datetime(teams['endDate'])

## DATA CLEANSING
# Renaming the teams with their old names
points_history = pd.merge(points_history, teams[['team','reference_team','startDate','endDate']], on='team')
valid_data = points_history[((points_history['date'] >= points_history['startDate']) | points_history['startDate'].isna()) &
                         ((points_history['date'] <= points_history['endDate']) | points_history['endDate'].isna())]

ranking_df = valid_data[['date', 'team', 'points']]

ranking_df = ranking_df.drop_duplicates()

ranking_df.loc[:, 'ranking'] = ranking_df.groupby('date')['points'].rank(ascending=False, method='min')

ranking_df.sort_values(by=['date', 'ranking'], inplace=True)

ranking_df['year'] = ranking_df['date'].dt.year
ranking_df['month'] = ranking_df['date'].dt.month
ranking_df['day'] = ranking_df['date'].dt.day
ranking_df['points'] = ranking_df['points'].astype(int)
ranking_df['ranking'] = ranking_df['ranking'].astype(int)

ranking_df = pd.merge(ranking_df, teams[['team','reference_team']], left_on='team', right_on='team')

ranking_df = ranking_df[['date', 'year', 'month', 'day', 'team', 'reference_team', 'points', 'ranking']]
ranking_df = ranking_df.drop_duplicates()
ranking_df['date'] = ranking_df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
ranking_df.sort_values(by=['date', 'ranking'], inplace=True)

print('Ranking Data is clean')

# Save the dataset in temp csv file
ranking_df.to_csv('data/temp/ranking.csv', index=False)

print('Ranking data saved in temp file')