import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import os
import numpy as np

# Define the directory name
DATA_DIR = 'data'
file1 = os.path.join(DATA_DIR, 'pstk.csv')
file2 = os.path.join(DATA_DIR, 'synz.csv')

def find_elite_recruits_refined(filepath):
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return None

    df_original = pd.read_csv(filepath)
    required_cols = ['Member', 'Power', 'Kills', 'Level']
    
    # Data cleaning step 1: Drop rows with any missing required values
    df = df_original.dropna(subset=required_cols)
    
    # Data cleaning step 2: Filter out players below Level 30
    df = df[df['Level'] >= 30].copy()
    
    original_count_after_filter = len(df)

    if df.empty:
        print(f"Error: No data remains in file '{filepath}' after applying Level 30+ filter and cleaning missing values.")
        return None
    
    # Select the numerical features and scale them
    features_to_scale = df[['Power', 'Kills', 'Level']]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_to_scale)
    
    # --- Apply Isolation Forest for Outlier Detection on the filtered dataset ---
    # The 'contamination' is recalculated based on the new, smaller, filtered group.
    # We maintain 5% of the remaining *high-level* players.
    contamination_rate = 0.05
    iso_forest = IsolationForest(contamination=contamination_rate, random_state=42)
    df['is_elite_recruit'] = iso_forest.fit_predict(scaled_features)

    # 4. Print results
    filename = filepath.split(os.sep)[-1]
    print(f"\n=============================================")
    print(f"  Isolation Forest Results for {filename} (Lvl 30+ Filter, Top 5% Identified)")
    print(f"=============================================\n")
    
    # Filter for the elite players (marked as -1)
    elite_players = df[df['is_elite_recruit'] == -1].sort_values(by=['Power', 'Kills'], ascending=False)
    average_players = df[df['is_elite_recruit'] == 1]
    
    print(f"--- Identified Potential Elite Recruits ({len(elite_players)} players) ---")
    print(elite_players[['Member', 'Power', 'Kills', 'Level']].to_markdown(index=False))
    
    print(f"\n--- Remaining Players (Lvl 30+) ({len(average_players)} players) ---")
    print(average_players[['Member', 'Power', 'Kills', 'Level']].head(50).to_markdown(index=False))
    print("[...rest of players omitted for brevity...]")

    return df

# Process both files with the new approach
# df_pstk = find_elite_recruits_refined(file1)
df_synz = find_elite_recruits_refined(file2)
