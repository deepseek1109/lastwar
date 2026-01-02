import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 1. Load the data into a pandas DataFrame (replace with your actual data source)
# This data represents the "Power (m)" and "Kills (m)" from the image.
data = {
    'Member': ['SAMHAIN13', 'Monztrous', 'Pewpewpewwwwwww', 'Tony595595', 'Gaily Waily', 'Spork', 'Thomster', 'Fort Graves', 'unknown tree', 'Johns Deere', 'Buff Master Griz', 'Cbolicious', 'The1whoknox', 'Taiqi', 'Troop Meek', 'DeepseekR2', 'Deepsea325', 'FemShep', 'DEWstruction', 'Savagelina8228', 'Qusqo', 'Timbo8013', 'Captain cold', 'The 1 and Only Dude', 'Geocrat', 'Ct561', 'Explosive78'],
    'Power': [199, 192, 188, 181, 180, 177, 173, 164, 161, 154, 153, 151, 150, 149, 148, 146, 144, 143, 143, 142, 140, 139, 138, 110, 110, 108, 108],
    'Kills': [15.16, 3.12, 4.04, 0.75, 0.15, 0.75, 0.19, 0.64, 1.15, 1.61, 1.56, 0.26, 1.43, 1.53, 0.60, 1.64, 0.57, 1.34, 0.64, 0.14, 0.19, 0.36, 0.85, 0.58, 0.27, 0.24, 0.37]
}
df = pd.DataFrame(data)

# Features for clustering
features = df[['Power', 'Kills']]

# 2. Apply KMeans Clustering to group players (e.g., 3 clusters)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Cluster'] = kmeans.fit_predict(features)

# 3. Identify and print top players in the highest-performing cluster
# Cluster 0 is likely the highest based on typical data distribution in this dataset
best_cluster_id = df.groupby('Cluster')['Power'].mean().idxmax()
best_players = df[df['Cluster'] == best_cluster_id].sort_values(by='Power', ascending=False)

print("--- Top Players to Recruit (Highest Potential Cluster) ---")
print(best_players[['Member', 'Power', 'Kills', 'Cluster']].to_markdown(index=False))

# Optional: Visualize the clusters
# plt.scatter(df['Power'], df['Kills'], c=df['Cluster'], cmap='viridis')
# plt.xlabel('Power (m)')
# plt.ylabel('Kills (m)')
# plt.title('Player Clusters (Power vs Kills)')
# plt.show()
