"""
Compare multiple ML methods for detecting alternative/inactive accounts.
Tests: XGBoost heuristics, Isolation Forest, Local Outlier Factor, K-means clustering, Z-score.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import KMeans
from scipy import stats
import os
import argparse


def detect_alt_heuristic(df):
    """Pattern-based heuristic detection (current XGBoost method)"""
    # Pattern 1: Near-zero kills
    zero_kills = df['Kills'] < 0.3
    
    # Pattern 2: High level but tiny power
    abandoned_high_level = (df['Level'] >= 30) & (df['Power'] < 100)
    
    # Pattern 3: Minimal combat with high level
    minimal_combat = (df['Level'] >= 30) & (df['Kills'] < 0.5) & (df['Power'] < 180)
    
    # Pattern 4: Low effort - IQR-based outliers on Prof Lvl and Gift Lvl
    prof_q1 = df['Prof Lvl'].quantile(0.25)
    prof_iqr = df['Prof Lvl'].quantile(0.75) - prof_q1
    prof_threshold = prof_q1 - 1.5 * prof_iqr
    
    gift_q1 = df['Gift Lvl'].quantile(0.25)
    gift_iqr = df['Gift Lvl'].quantile(0.75) - gift_q1
    gift_threshold = gift_q1 - 1.5 * gift_iqr
    
    low_effort = (df['Prof Lvl'] <= prof_threshold) & (df['Gift Lvl'] <= gift_threshold)
    
    alt_mask = zero_kills | abandoned_high_level | minimal_combat | low_effort
    return alt_mask.astype(int)


def detect_alt_isolation_forest(df):
    """Isolation Forest on key features"""
    features = ['Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl']
    X = df[features].copy()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    predictions = iso_forest.fit_predict(X_scaled)
    
    # Convert: -1 (anomaly) to 1, 1 (normal) to 0
    return (predictions == -1).astype(int)


def detect_alt_lof(df):
    """Local Outlier Factor"""
    features = ['Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl']
    X = df[features].copy()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
    predictions = lof.fit_predict(X_scaled)
    
    # Convert: -1 (anomaly) to 1, 1 (normal) to 0
    return (predictions == -1).astype(int)


def detect_alt_zscore(df):
    """Z-score based outlier detection on composite low-effort metrics"""
    features = ['Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl']
    X = df[features].copy()
    
    # Calculate z-scores
    z_scores = np.abs(stats.zscore(X, nan_policy='omit'))
    
    # Flag if any metric is >3 standard deviations away (or Prof/Gift Lvl are both <-1.5)
    prof_zscore = stats.zscore(df['Prof Lvl'], nan_policy='omit')
    gift_zscore = stats.zscore(df['Gift Lvl'], nan_policy='omit')
    
    # Flag if Prof and Gift are both low (negative z-scores < -1.5)
    low_investment = (prof_zscore < -1.5) & (gift_zscore < -1.5)
    
    # Flag if any stat is extreme outlier
    extreme_outlier = (z_scores > 3).any(axis=1)
    
    return (low_investment | extreme_outlier).astype(int)


def detect_alt_kmeans(df):
    """K-means clustering to find isolated small clusters"""
    features = ['Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl']
    X = df[features].copy()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Use k=3 to separate active/moderate/inactive players
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Find the cluster with lowest average engagement (Kills + Prof Lvl + Gift Lvl)
    df_temp = df.copy()
    df_temp['Cluster'] = clusters
    
    cluster_engagement = df_temp.groupby('Cluster')[['Kills', 'Prof Lvl', 'Gift Lvl']].mean().sum(axis=1)
    low_engagement_cluster = cluster_engagement.idxmin()
    
    # Flag players in low-engagement cluster
    return (clusters == low_engagement_cluster).astype(int)


def compare_methods(filepath, alliance_filter=None):
    """Compare all detection methods"""
    
    # Load data
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return None
    
    df = pd.read_csv(filepath)
    df = df.rename(columns={'Power (m)': 'Power', 'Kills (m)': 'Kills'})
    
    if alliance_filter:
        df = df[df['Alliance'] == alliance_filter].copy()
    
    df = df.dropna(subset=['Member', 'Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl'])
    
    if df.empty:
        print("Error: No valid data.")
        return None
    
    print(f"\n{'='*100}")
    print(f"ALTERNATIVE ACCOUNT DETECTION COMPARISON")
    print(f"{'='*100}")
    print(f"Total Players: {len(df)}\n")
    
    # Apply all detection methods
    df['Heuristic'] = detect_alt_heuristic(df)
    df['IsolationForest'] = detect_alt_isolation_forest(df)
    df['LOF'] = detect_alt_lof(df)
    df['ZScore'] = detect_alt_zscore(df)
    df['KMeans'] = detect_alt_kmeans(df)
    
    # Count flags by method
    detection_cols = ['Heuristic', 'IsolationForest', 'LOF', 'ZScore', 'KMeans']
    df['Flags'] = df[detection_cols].sum(axis=1)  # How many methods flagged this player
    
    # Print summary statistics
    print("Detection Method Summary:")
    for method in detection_cols:
        count = df[method].sum()
        pct = 100 * count / len(df)
        print(f"  {method:20s}: {count:4d} players ({pct:5.1f}%)")
    
    print(f"\nConsensus Detection (flagged by 3+ methods):")
    consensus = (df['Flags'] >= 3)
    print(f"  Players: {consensus.sum()} ({100*consensus.sum()/len(df):.1f}%)")
    
    # Show "Teddyyh" if present
    print(f"\n{'='*100}")
    print("LOOKUP: Searching for 'Teddyyh'...")
    teddyyh = df[df['Member'].str.contains('Teddyyh', case=False, na=False)]
    if not teddyyh.empty:
        print(f"{'='*100}")
        print(f"Found: Teddyyh")
        print(teddyyh[['Member', 'Level', 'Power', 'Kills', 'Prof Lvl', 'Gift Lvl', 
                       'Heuristic', 'IsolationForest', 'LOF', 'ZScore', 'KMeans', 'Flags']].to_string(index=False))
        
        flags = teddyyh['Flags'].values[0]
        methods_flagged = teddyyh[detection_cols].values[0]
        flagged_by = [detection_cols[i] for i in range(len(detection_cols)) if methods_flagged[i] == 1]
        print(f"\nTeddyyh flagged by {flags}/5 methods: {', '.join(flagged_by)}")
    else:
        print("Not found in dataset")
    
    # Show top flagged players (consensus)
    print(f"\n{'='*100}")
    print("TOP FLAGGED PLAYERS (by consensus - 4+ method agreement)")
    print(f"{'='*100}")
    top_flagged = df[df['Flags'] >= 4].sort_values('Flags', ascending=False)
    if not top_flagged.empty:
        print(top_flagged[['Member', 'Level', 'Power', 'Kills', 'Prof Lvl', 'Gift Lvl', 'Flags']].head(20).to_string(index=False))
    else:
        print("No players flagged by 4+ methods")
    
    # Show moderate consensus
    print(f"\n{'='*100}")
    print("MODERATE FLAGGED PLAYERS (by 3 method agreement)")
    print(f"{'='*100}")
    moderate_flagged = df[(df['Flags'] == 3)].sort_values('Flags', ascending=False)
    if not moderate_flagged.empty:
        print(moderate_flagged[['Member', 'Level', 'Power', 'Kills', 'Prof Lvl', 'Gift Lvl', 'Flags']].head(20).to_string(index=False))
    else:
        print("No players flagged by exactly 3 methods")
    
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare ML methods for alt account detection')
    parser.add_argument('--alliance', type=str, help='Filter by alliance name')
    parser.add_argument('--file', type=str, default='../data/synz.csv', help='CSV file path')
    
    args = parser.parse_args()
    csv_path = os.path.join(os.path.dirname(__file__), args.file)
    
    result_df = compare_methods(csv_path, alliance_filter=args.alliance)
