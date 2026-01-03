import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import os
import numpy as np

# Define the directory name
DATA_DIR = 'data'
file1 = os.path.join(DATA_DIR, 'pstk.csv')
file2 = os.path.join(DATA_DIR, 'synz.csv')

def find_elite_recruits_weighted(filepath):
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return None

    df_original = pd.read_csv(filepath)
    required_cols = ['Member', 'Power', 'Kills', 'Level']
    
    # Data cleaning steps: drop NaNs and filter Level 30+
    df = df_original.dropna(subset=required_cols)
    df = df[df['Level'] >= 30].copy()
    
    if df.empty:
        print(f"Error: No data remains in file '{filepath}' after cleaning/filtering.")
        return None

    # --- Feature Engineering: Apply weights to prioritize Level and Kills ---
    # We will use explicit weights to guide the definition of "elite"
    df['Level_Weighted'] = df['Level'] * 3
    df['Kills_Weighted'] = df['Kills'] * 2
    # Power will keep its default scale

    # Select the *new* weighted features for modeling
    features_to_model = df[['Power', 'Kills_Weighted', 'Level_Weighted']]

    # Scale the features so the Isolation Forest uses the weights correctly but in a standardized range
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_to_model)
    
    # --- Apply Isolation Forest for Outlier Detection ---
    # We keep contamination at 5%
    contamination_rate = 0.05 
    iso_forest = IsolationForest(contamination=contamination_rate, random_state=42)
    df['is_elite_recruit'] = iso_forest.fit_predict(scaled_features)

    # 4. Print results
    filename = filepath.split(os.sep)[-1]
    print(f"\n=============================================")
    print(f"  Isolation Forest Results for {filename} (Weighted Features, Lvl 30+)")
    print(f"=============================================\n")
    
    # Filter for the elite players (marked as -1)
    elite_players = df[df['is_elite_recruit'] == -1].sort_values(by=['Level', 'Power'], ascending=False)
    average_players = df[df['is_elite_recruit'] == 1]
    
    print(f"--- Identified Potential Elite Recruits ({len(elite_players)} players) ---")
    # Displaying original columns for clarity
    print(elite_players[['Member', 'Power', 'Kills', 'Level']].to_markdown(index=False))
    
    print(f"\n--- Remaining Players (Lvl 30+) ({len(average_players)} players) ---")
    print(average_players[['Member', 'Power', 'Kills', 'Level']].head(50).to_markdown(index=False))
    print("[...rest of players omitted for brevity...]")

    return df

# Process both files with the new approach
# df_pstk = find_elite_recruits_weighted(file1)
df_synz = find_elite_recruits_weighted(file2)