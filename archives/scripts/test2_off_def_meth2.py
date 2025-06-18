import pandas as pd
import numpy as np
from collections import defaultdict

def run_bidir_iterations(df, iterations=10, multi=14, ceil=5, limit=2.9, save_path="initial_ratings_meth2.csv"):
    df_sorted_asc = df.sort_values("date")
    df_sorted_desc = df.sort_values("date", ascending=False)
    
    ratings = defaultdict(dict)
    result_df = None

    for i in range(iterations):
        direction = "asc" if i % 2 == 0 else "desc"
        current_df = df_sorted_asc if direction == "asc" else df_sorted_desc

        for _, row in current_df.iterrows():
            t1, t2 = row["team1"], row["team2"]
            score1, score2 = row["score1"], row["score2"]
            r1, r2 = row["rating1"], row["rating2"]
            home = row["home"]

            off_1 = ratings[t1].get("off", r1)
            def_1 = ratings[t1].get("def", r1)
            off_2 = ratings[t2].get("off", r2)
            def_2 = ratings[t2].get("def", r2)

            b1 = (off_1 - def_2 + home * 136)
            b2 = (off_2 - def_1 - home * 136)

            if b1 > 0:
                expected_1 = float(np.real_if_close(1.66e-6 * ((off_1 - def_2 + home * 136) + 924) ** 1.96))
            else:
                expected_1 = 0.0
            if b2 > 0:
                expected_2 = float(np.real_if_close(1.66e-6 * ((off_2 - def_1 - home * 136) + 924) ** 1.96))
            else:
                expected_2 = 0.0

            diff_1 = score1 - expected_1
            diff_2 = score2 - expected_2

            mm_1 = np.sign(diff_1) * ((ceil * abs(diff_1)) / (limit + abs(diff_1)))
            mm_2 = np.sign(diff_2) * ((ceil * abs(diff_2)) / (limit + abs(diff_2)))

            new_off_1 = off_1 + (mm_1 * multi)
            new_off_2 = off_2 + (mm_2 * multi)
            new_def_1 = def_1 - (mm_2 * multi)
            new_def_2 = def_2 - (mm_1 * multi)

            ratings[t1]["off"] = new_off_1
            ratings[t1]["def"] = new_def_1
            ratings[t2]["off"] = new_off_2
            ratings[t2]["def"] = new_def_2

        if i == iterations - 1:
            initial_values = {
                team: {"off": vals["off"], "def": vals["def"]}
                for team, vals in ratings.items()
            }
            initial_df = pd.DataFrame.from_dict(initial_values, orient="index").reset_index()
            initial_df.columns = ["team", "init_off", "init_def"]
            initial_df.to_csv(save_path, index=False)

    # Final pass
    final_results = []
    for _, row in df_sorted_asc.iterrows():
        t1, t2 = row["team1"], row["team2"]
        score1, score2 = row["score1"], row["score2"]
        r1, r2 = row["rating1"], row["rating2"]
        home = row["home"]

        off_1 = ratings[t1].get("off", r1)
        def_1 = ratings[t1].get("def", r1)
        off_2 = ratings[t2].get("off", r2)
        def_2 = ratings[t2].get("def", r2)

        b1 = (off_1 - def_2 + home * 136)
        b2 = (off_2 - def_1 - home * 136)

        if b1 > 0:
            expected_1 = float(np.real_if_close(1.66e-6 * ((off_1 - def_2 + home * 136) + 924) ** 1.96))
        else:
            expected_1 = 0.0
        if b2 > 0:
            expected_2 = float(np.real_if_close(1.66e-6 * ((off_2 - def_1 - home * 136) + 924) ** 1.96))
        else:
            expected_2 = 0.0

        diff_1 = score1 - expected_1
        diff_2 = score2 - expected_2

        mm_1 = np.sign(diff_1) * ((ceil * abs(diff_1)) / (limit + abs(diff_1)))
        mm_2 = np.sign(diff_2) * ((ceil * abs(diff_2)) / (limit + abs(diff_2)))

        new_off_1 = off_1 + (mm_1 * multi)
        new_off_2 = off_2 + (mm_2 * multi)
        new_def_1 = def_1 - (mm_2 * multi)
        new_def_2 = def_2 - (mm_1 * multi)

        ratings[t1]["off"] = new_off_1
        ratings[t1]["def"] = new_def_1
        ratings[t2]["off"] = new_off_2
        ratings[t2]["def"] = new_def_2

        error = abs(score1 - expected_1) + abs(score2 - expected_2)

        final_results.append({
            "date": row["date"],
            "team1": t1, "team2": t2,
            "score1": score1, "score2": score2,
            "expected_1": expected_1, "expected_2": expected_2,
            "error": error
        })

    final_df = pd.DataFrame(final_results)
    mean_error = final_df["error"].mean()
    print(f"Final Mean Error (after 11th pass): {mean_error:.4f}")
    return final_df

# Utilisation
df = pd.read_csv("results_off_def.csv", delimiter=";")
df["score1"] = pd.to_numeric(df["score1"], errors="coerce")
df["score2"] = pd.to_numeric(df["score2"], errors="coerce")
df["rating1"] = pd.to_numeric(df["rating1"], errors="coerce")
df["rating2"] = pd.to_numeric(df["rating2"], errors="coerce")
df["home"] = pd.to_numeric(df["home"], errors="coerce")
final_df = run_bidir_iterations(df, iterations=10, multi=14, ceil=5, limit=2.9, save_path="initial_ratings_meth2.csv")
