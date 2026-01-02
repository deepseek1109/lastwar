import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 1. Load all data including 'Power', 'Kills', and 'Level' into a pandas DataFrame
data = {
    'Member': ['SAMHAIN13', 'Monztrous', 'Pewpewpewwwwwww', 'Tony595595', 'Gaily Waily', 'Spork', 'Thomster', 'Fort Graves', 'unknown tree', 'Johns Deere', 'Buff Master Griz', 'Cbolicious', 'The1whoknox', 'Taiqi', 'Troop Meek', 'DeepseekR2', 'Deepsea325', 'FemShep', 'DEWstruction', 'Savagelina8228', 'Qusqo', 'Timbo8013', 'Captain cold', 'The 1 and Only Dude', 'Geocrat', 'Ct561', 'Explosive78'],
    'Power': [199, 192, 188, 181, 180, 177, 173, 164, 161, 154, 153, 151, 150, 149, 148, 146, 144, 143, 143, 142, 140, 139, 138, 110, 110, 108, 108],
    'Kills': [15.16, 3.12, 4.04, 0.75, 0.15, 0.75, 0.19, 0.64, 1.15, 1.61, 1.56, 0.26, 1.43, 1.53, 0.60, 1.64, 0.57, 1.34, 0.64, 0.14, 0.19, 0.36, 0.85, 0.58, 0.27, 0.24, 0.37],
    'Level': [31, 30, 33, 32, 31, 31, 30, 30, 31, 30, 31, 30, 30, 32, 30, 33, 30, 31, 30, 30, 31, 28, 30, 27, 30, 27, 29]
}
df = pd.DataFrame(data)

# Features for clustering (Power, Kills, and Level)
df['Level_Weighted'] = df['Level'] * 100
df['Kills_Weighted'] = df['Kills'] * 20
features = df[['Power', 'Kills_Weighted', 'Level_Weighted']]

# features = df[['Power', 'Kills', 'Level']]

# 2. Apply KMeans Clustering to group players (3 clusters)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Cluster'] = kmeans.fit_predict(features)

# 3. Print all clusters
for cluster_id in sorted(df['Cluster'].unique()):
    print(f"\n--- Players in Cluster {cluster_id} ---")
    cluster_players = df[df['Cluster'] == cluster_id].sort_values(by='Power', ascending=False)
    # Using to_markdown for a clean table output, including all features
    print(cluster_players[['Member', 'Power', 'Kills', 'Level', 'Cluster']].to_markdown(index=False))
