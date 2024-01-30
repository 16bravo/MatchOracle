import os

folder_path = 'data/temp/'

files_to_delete = ['last_date.txt','matches.csv','points_history.csv','ranking.csv','teams.csv']

for file in files_to_delete:
    full_path = os.path.join(folder_path, file)

    if os.path.exists(full_path):
        os.remove(full_path)
        print(f"File {file} deleted.")
    else:
        print(f"File {file} does not exist.")

os.remove('all-international-football-results.zip')