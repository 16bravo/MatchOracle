import pandas as pd
from tqdm import tqdm
from datetime import datetime

# Chargement des données
matches = pd.read_csv('data/temp/matches.csv')
teams = pd.read_csv('data/temp/teams.csv')
with open('data/temp/last_date.txt', 'r') as file:
    date_str = file.read().strip()
date_format = "%Y-%m-%d %H:%M:%S"
last_date = datetime.strptime(date_str, date_format)

matches['date'] = pd.to_datetime(matches['date'])
teams['startDate'] = pd.to_datetime(teams['startDate'])
teams['endDate'] = pd.to_datetime(teams['endDate'])

today_date = pd.Timestamp(datetime.now())
start_date = matches['date'].min()
end_date = matches['date'].max()
start_date = last_date if pd.isna(start_date) else start_date
last_eoy = pd.Timestamp(year=today_date.year - 1, month=12, day=31)
end_date = max(last_eoy, end_date)

# Génère toutes les fins de mois
EOM_dates = pd.date_range(start=start_date, end=end_date, freq='M')
if today_date.normalize() > EOM_dates.max():
    EOM_dates = EOM_dates.append(pd.to_datetime([today_date.normalize()]))

# Prépare la table (date, team) pour toutes les équipes vivantes à chaque date
all_teams = teams[['team', 'reference_team', 'startDate', 'endDate']].drop_duplicates()
date_team = (
    pd.DataFrame({'date': EOM_dates})
    .assign(key=1)
    .merge(all_teams.assign(key=1), on='key')
    .drop('key', axis=1)
)
date_team = date_team[
    ((date_team['startDate'].isna()) | (date_team['date'] >= date_team['startDate'])) &
    ((date_team['endDate'].isna()) | (date_team['date'] <= date_team['endDate']))
].copy()

# Prépare un DataFrame "long" des matches (une ligne par équipe impliquée)
home = matches.rename(columns={
    'home_team': 'reference_team',
    'home_points_after': 'points',
    'home_points_off_after': 'points_off',
    'home_points_def_after': 'points_def'
})[['date', 'reference_team', 'points', 'points_off', 'points_def']]
away = matches.rename(columns={
    'away_team': 'reference_team',
    'away_points_after': 'points',
    'away_points_off_after': 'points_off',
    'away_points_def_after': 'points_def'
})[['date', 'reference_team', 'points', 'points_off', 'points_def']]
matches_long = pd.concat([home, away], ignore_index=True)
matches_long = matches_long.sort_values(['reference_team', 'date'])

# Pour chaque équipe, merge_asof pour trouver le dernier match avant chaque date
results = []
for ref_team, group in tqdm(date_team.groupby('reference_team'), desc="Calculating Points History (optimized)"):
    team_dates = group[['date', 'team']].sort_values('date')
    team_matches = matches_long[matches_long['reference_team'] == ref_team][['date', 'points', 'points_off', 'points_def']].sort_values('date')
    merged = pd.merge_asof(team_dates, team_matches, on='date', direction='backward')
    merged['reference_team'] = ref_team
    results.append(merged)

points_history_long = pd.concat(results, ignore_index=True)

# Pour today, si pas de match, on prend les points actuels de teams.csv
today_mask = points_history_long['date'] == today_date.normalize()
for idx, row in points_history_long[today_mask].iterrows():
    if pd.isna(row['points']) and pd.isna(row['points_off']) and pd.isna(row['points_def']):
        ref_team = row['reference_team']
        team_row = teams[teams['reference_team'] == ref_team].iloc[-1]
        points_history_long.at[idx, 'points'] = team_row.get('points', None)
        points_history_long.at[idx, 'points_off'] = team_row.get('points_off', None)
        points_history_long.at[idx, 'points_def'] = team_row.get('points_def', None)

# Réorganise les colonnes
points_history_long = points_history_long[['date', 'team', 'points', 'points_off', 'points_def']]

print('Points History (long, one row per team/date) calculated (optimized)')

points_history_long.to_csv('data/temp/points_history.csv', index=False)
print('Points History data saved in temp file')