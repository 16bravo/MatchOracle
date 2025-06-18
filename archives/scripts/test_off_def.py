import pandas as pd
import numpy as np

def compute_ratings_with_error(df, evoRate=0.01):
    ratings = {}
    history = []

    for _, row in df.iterrows():
        t1, t2 = row["original_team1"], row["original_team2"]
        score1, score2 = row["score1"], row["score2"]
        r1, r2 = row["rating1"], row["rating2"]
        home = row["home"]

        off_1 = ratings.get((t1, "off"), r1)
        def_1 = ratings.get((t1, "def"), r1)
        off_2 = ratings.get((t2, "off"), r2)
        def_2 = ratings.get((t2, "def"), r2)

        try:
            expected_1 = float(np.real_if_close(1.66e-6 * ((off_1 - def_2 + home * 136) + 924) ** 1.96))
        except:
            expected_1 = 0.0
        try:
            expected_2 = float(np.real_if_close(1.66e-6 * ((off_2 - def_1 - home * 136) + 924) ** 1.96))
        except:
            expected_2 = 0.0

        level_1 = (off_1 + def_2) / 2
        level_2 = (off_2 + def_1) / 2

        try:
            theoGap_1 = float(np.real_if_close((score1 / 1.66e-6) ** (1 / 1.96) - 924 - home * 136))
        except:
            theoGap_1 = 0.0
        try:
            theoGap_2 = float(np.real_if_close((score2 / 1.66e-6) ** (1 / 1.96) - 924 + home * 136))
        except:
            theoGap_2 = 0.0

        post_off_1 = level_1 + theoGap_1
        post_off_2 = level_2 - theoGap_2
        post_def_1 = level_2 + theoGap_2
        post_def_2 = level_1 - theoGap_1

        # Blocage des progressions illogiques
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

        ratings[(t1, "off")] = new_off_1
        ratings[(t1, "def")] = new_def_1
        ratings[(t2, "off")] = new_off_2
        ratings[(t2, "def")] = new_def_2

        error = abs(score1 - expected_1) + abs(score2 - expected_2)

        history.append({
            "date": row["date"],
            "team1": t1, "team2": t2,
            "score1": score1, "score2": score2,
            "expected_1": expected_1, "expected_2": expected_2,
            "off_1": off_1, "def_1": def_1,
            "off_2": off_2, "def_2": def_2,
            "new_off_1": new_off_1, "new_def_1": new_def_1,
            "new_off_2": new_off_2, "new_def_2": new_def_2,
            "error": error
        })

    result_df = pd.DataFrame(history)
    mean_error = result_df["error"].mean()
    print(f"Mean error: {mean_error:.4f}")
    return result_df

# Exemple d'utilisation
df = pd.read_csv("results_off_def.csv", delimiter=";")
df["score1"] = pd.to_numeric(df["score1"], errors="coerce")
df["score2"] = pd.to_numeric(df["score2"], errors="coerce")
df["rating1"] = pd.to_numeric(df["rating1"], errors="coerce")
df["rating2"] = pd.to_numeric(df["rating2"], errors="coerce")
df["home"] = pd.to_numeric(df["home"], errors="coerce")
results = compute_ratings_with_error(df.sort_values("date"), evoRate=0.0125)

