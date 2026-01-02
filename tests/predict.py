import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os # Import the os library

# Define the directory name
DATA_DIR = 'data'

# Define file names using the directory path
file1 = os.path.join(DATA_DIR, 'pstk.csv')
file2 = os.path.join(DATA_DIR, 'synz.csv')

# Function to load and process data from a CSV file
def process_guild_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        # Print current working directory to help debugging if path is wrong
        print(f"Current working directory: {os.getcwd()}")
        return None

    # 1. Load data from the CSV file into a pandas DataFrame
    df = pd.read_csv(filepath)

    # Ensure required columns exist
    required_cols = ['Member', 'Power', 'Kills', 'Level']
    if not all(col in df.columns for col in required_cols):
        print(f"Error: Missing one of the required columns {required_cols} in file '{filepath}'.")
        return None
    
    # Drop rows with missing values in required columns
    df = df.dropna(subset=required_cols)
    
    # 2. Prepare features for clustering (Assuming the user wants the same weighting scheme)
    df['Level_Weighted'] = df['Level'] * 100
    df['Kills_Weighted'] = df['Kills'] * 20
    features = df[['Power', 'Kills_Weighted', 'Level_Weighted']]

    # 3. Apply KMeans Clustering to group players (3 clusters)
    # Using a fixed random_state for reproducibility
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(features)

    # 4. Print all clusters for this file
    print(f"\n=============================================")
    print(f"  Clustering Results for {filepath.split(os.sep)[-1]} (from {DATA_DIR}/)")
    print(f"=============================================\n")
    for cluster_id in sorted(df['Cluster'].unique()):
        print(f"--- Players in Cluster {cluster_id} ---")
        cluster_players = df[df['Cluster'] == cluster_id].sort_values(by='Power', ascending=False)
        # Using to_markdown for a clean table output, including all features
        print(cluster_players[['Member', 'Power', 'Kills', 'Level', 'Cluster']].to_markdown(index=False))
        print("\n")
    
    return df

# Process both files
# df_pstk = process_guild_data(file1)
df_synz = process_guild_data(file2)

# Optional: You can add further analysis or combined processing here if needed
if df_synz is not None:
    print("\nSuccessfully processed both files.")