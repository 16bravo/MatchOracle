import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# --- PARAMÈTRES ---
evoRate = 0.0065
match_file = "results_off_def.csv"
initial_rating_file = "initial_ratings.csv"

# --- CHARGEMENT DES DONNÉES ---
df = pd.read_csv(match_file, delimiter=";")
df["score1"] = pd.to_numeric(df["score1"], errors="coerce")
df["score2"] = pd.to_numeric(df["score2"], errors="coerce")
df["rating1"] = pd.to_numeric(df["rating1"], errors="coerce")
df["rating2"] = pd.to_numeric(df["rating2"], errors="coerce")
df["home"] = pd.to_numeric(df["home"], errors="coerce")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

initial_df = pd.read_csv(initial_rating_file)
initial_ratings = {row["team"]: {"off": row["init_off"], "def": row["init_def"]} for _, row in initial_df.iterrows()}

# --- TRAITEMENT D'UNE SEULE ITERATION ---
ratings = initial_ratings.copy()
history = []

for _, row in df.iterrows():
    date = row["date"]
    t1, t2 = row["team1"], row["team2"]
    score1, score2 = row["score1"], row["score2"]
    r1, r2 = row["rating1"], row["rating2"]
    home = row["home"]

    off_1 = ratings.get(t1, {}).get("off", r1)
    def_1 = ratings.get(t1, {}).get("def", r1)
    off_2 = ratings.get(t2, {}).get("off", r2)
    def_2 = ratings.get(t2, {}).get("def", r2)

    try:
        theoGap_1 = (score1 / 1.66e-6) ** (1 / 1.96) - 924 - home * 136
    except:
        theoGap_1 = 0.0
    try:
        theoGap_2 = (score2 / 1.66e-6) ** (1 / 1.96) - 924 + home * 136
    except:
        theoGap_2 = 0.0

    level_1 = (off_1 + def_2) / 2
    level_2 = (off_2 + def_1) / 2

    post_off_1 = level_1 + theoGap_1
    post_off_2 = level_2 - theoGap_2
    post_def_1 = level_2 + theoGap_2
    post_def_2 = level_1 - theoGap_1

    if score1 == 0 and post_off_1 > off_1:
        post_off_1 = off_1
    if score2 == 0 and post_off_2 > off_2:
        post_off_2 = off_2
    if score2 == 0 and post_def_1 < def_1:
        post_def_1 = def_1
    if score1 == 0 and post_def_2 < def_2:
        post_def_2 = def_2

    new_off_1 = off_1 * (1 - evoRate) + post_off_1 * evoRate
    new_off_2 = off_2 * (1 - evoRate) + post_off_2 * evoRate
    new_def_1 = def_1 * (1 - evoRate) + post_def_1 * evoRate
    new_def_2 = def_2 * (1 - evoRate) + post_def_2 * evoRate

    ratings[t1] = {"off": new_off_1, "def": new_def_1}
    ratings[t2] = {"off": new_off_2, "def": new_def_2}

    history.append({"date": date, "team": t1, "off": new_off_1, "def": new_def_1})
    history.append({"date": date, "team": t2, "off": new_off_2, "def": new_def_2})

history_df = pd.DataFrame(history)
history_df = history_df.sort_values("date")

# --- INTERFACE STREAMLIT ---
st.title("Évolution des Ratings Off/Def par Équipe")
team = st.selectbox("Sélectionner une équipe :", sorted(history_df["team"].unique()))
team_data = history_df[history_df["team"] == team]

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(team_data["date"], team_data["off"], label="Offensive Rating")
ax.plot(team_data["date"], team_data["def"], label="Defensive Rating")
ax.set_title(f"Évolution des ratings pour {team}")
ax.set_xlabel("Date")
ax.set_ylabel("Rating")
ax.legend()
ax.grid(True)
st.pyplot(fig)
