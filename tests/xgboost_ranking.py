"""
XGBoost-based Player Retention Ranking System

This script ranks players by predicted value using Gradient Boosting,
with secondary filtering for inactive outliers via Isolation Forest.

Features:
- Composite value score based on Power, Kills, Level, Prof Lvl, Gift Lvl
- XGBoost regression to predict and rank player value
- Isolation Forest to flag suspicious players (high level/power but low activity)
- Output: Ranked retention list with activity flags
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import os
import argparse
from sklearn.model_selection import train_test_split


def create_value_score(df):
    """
    Create a composite 'Player Value Score' based on weighted metrics.
    
    Weighting:
    - Power: 40% (raw strength indicator)
    - Kills: 35% (activity/engagement indicator)
    - Level: 15% (progression investment)
    - Prof Lvl: 10% (specialization depth)
    """
    # Normalize each metric to 0-1 scale
    power_norm = (df['Power'] - df['Power'].min()) / (df['Power'].max() - df['Power'].min() + 1e-6)
    kills_norm = (df['Kills'] - df['Kills'].min()) / (df['Kills'].max() - df['Kills'].min() + 1e-6)
    level_norm = (df['Level'] - df['Level'].min()) / (df['Level'].max() - df['Level'].min() + 1e-6)
    prof_norm = (df['Prof Lvl'] - df['Prof Lvl'].min()) / (df['Prof Lvl'].max() - df['Prof Lvl'].min() + 1e-6)
    
    # Weighted composite score (0-100 scale)
    value_score = (
        power_norm * 0.40 +
        kills_norm * 0.35 +
        level_norm * 0.15 +
        prof_norm * 0.10
    ) * 100
    
    return value_score


def detect_alt_accounts(df):
    """
    Detect likely alternative/inactive accounts using strict heuristics.
    These patterns indicate abandoned or low-activity accounts:
    
    1. Very low kills (<0.3) regardless of other stats - clear abandonment
    2. Level 30+ with Power <100 - abandoned high-level (not actively played)
    3. Level 30+ with Kills <0.5 with Power <180 - level-up only, zero combat engagement
    4. Low effort accounts: Prof Lvl and Gift Lvl are statistical outliers (below Q1 - 1.5*IQR)
    """
    # Pattern 1: Near-zero kills = clearly inactive
    zero_kills = df['Kills'] < 0.3
    
    # Pattern 2: High level but tiny power (level-boosted but not developed)
    abandoned_high_level = (df['Level'] >= 30) & (df['Power'] < 100)
    
    # Pattern 3: Multiple high-level accounts with minimal kills (farm/alts)
    minimal_combat = (df['Level'] >= 30) & (df['Kills'] < 0.5) & (df['Power'] < 180)
    
    # Pattern 4: Low effort accounts - use IQR-based outlier detection
    # Calculate outlier thresholds for Prof Lvl and Gift Lvl
    prof_q1 = df['Prof Lvl'].quantile(0.25)
    prof_iqr = df['Prof Lvl'].quantile(0.75) - prof_q1
    prof_threshold = prof_q1 - 1.5 * prof_iqr
    
    gift_q1 = df['Gift Lvl'].quantile(0.25)
    gift_iqr = df['Gift Lvl'].quantile(0.75) - gift_q1
    gift_threshold = gift_q1 - 1.5 * gift_iqr
    
    # Flag accounts where BOTH Prof Lvl and Gift Lvl are statistical outliers (very low)
    low_effort = (df['Prof Lvl'] <= prof_threshold) & (df['Gift Lvl'] <= gift_threshold)
    
    # Combine: flag if ANY pattern matches
    alt_mask = zero_kills | abandoned_high_level | minimal_combat | low_effort
    
    return alt_mask


def rank_players_xgboost(filepath, alliance_filter=None, blocklist=None):
    """
    Rank players by predicted value using XGBoost + Isolation Forest.
    
    Args:
        filepath: Path to CSV file
        alliance_filter: Optional alliance name to filter by
    
    Returns:
        DataFrame with rankings and activity flags
    """
    
    # --- 1. LOAD AND CLEAN DATA ---
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return None
    
    df = pd.read_csv(filepath)
    
    # Rename columns for consistency
    df = df.rename(columns={'Power (m)': 'Power', 'Kills (m)': 'Kills'})
    
    # Filter by alliance if specified
    if alliance_filter:
        df = df[df['Alliance'] == alliance_filter].copy()
    
    # Drop rows with missing core stats
    df = df.dropna(subset=['Member', 'Power', 'Kills', 'Level', 'Prof Lvl'])
    
    if df.empty:
        print(f"Error: No valid data after filtering.")
        return None
    
    print(f"\n{'='*60}")
    print(f"  XGBoost Player Retention Ranking")
    print(f"  File: {os.path.basename(filepath)}")
    if alliance_filter:
        print(f"  Alliance: {alliance_filter}")
    print(f"  Total Players: {len(df)}")
    print(f"{'='*60}\n")
    
    # --- 2. FEATURE ENGINEERING ---
    # Create target: Player Value Score
    df['Value_Score'] = create_value_score(df)
    
    # Engineer additional features
    df['Power_to_Level'] = df['Power'] / (df['Level'] + 1)  # Efficiency metric
    df['Kills_to_Power'] = df['Kills'] / (df['Power'] + 0.1)  # Activity intensity
    df['Prof_to_Level'] = df['Prof Lvl'] / (df['Level'] + 1)  # Specialization ratio
    
    # Select features for modeling
    feature_cols = ['Power', 'Kills', 'Level', 'Prof Lvl', 'Gift Lvl',
                    'Power_to_Level', 'Kills_to_Power', 'Prof_to_Level']
    
    X = df[feature_cols].copy()
    y = df['Value_Score'].copy()
    
    # Scale features for better XGBoost performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=X.index)
    
    # --- 3. TRAIN XGBOOST MODEL ---
    # Split data for training/validation
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    
    # Train XGBoost regressor
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    xgb_model.fit(X_train, y_train)
    
    # Predict value scores for all players
    df['Predicted_Value'] = xgb_model.predict(X_scaled)
    
    # Calculate model performance
    train_score = xgb_model.score(X_train, y_train)
    test_score = xgb_model.score(X_test, y_test)
    print(f"Model Performance:")
    print(f"  Training R² Score: {train_score:.4f}")
    print(f"  Testing R² Score:  {test_score:.4f}\n")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': xgb_model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("Feature Importance (Top 5):")
    for idx, row in feature_importance.head(5).iterrows():
        print(f"  {row['Feature']}: {row['Importance']:.4f}")
    print()
    
    # --- 4. ANOMALY DETECTION: HEURISTIC-BASED INACTIVE DETECTION ONLY ---
    # DO NOT use Isolation Forest - it flags high-kill players as outliers
    # Instead, use explicit heuristics to catch abandoned/alt accounts
    
    # Add heuristic-based alt account detection
    df['Is_Anomaly'] = detect_alt_accounts(df)
    
    # --- 5. RANK AND OUTPUT ---
    # Sort by predicted value (descending)
    df_ranked = df.sort_values('Predicted_Value', ascending=False).reset_index(drop=True)
    df_ranked['Retention_Rank'] = range(1, len(df_ranked) + 1)
    
    # Create output columns
    output_df = df_ranked[[
        'Retention_Rank', 'Member', 'Level', 'Power', 'Kills', 
        'Prof Lvl', 'Predicted_Value', 'Is_Anomaly'
    ]].copy()
    
    output_df['Retention_Rank'] = output_df['Retention_Rank'].astype(int)
    output_df['Predicted_Value'] = output_df['Predicted_Value'].round(2)
    output_df['Anomaly_Status'] = output_df['Is_Anomaly'].map(
        {True: '⚠️  INACTIVE', False: '✓ ACTIVE'}
    )
    
    # Display results
    print("\n" + "="*120)
    print("RETENTION RANKING (Top 25 Players by Predicted Value)")
    print("="*120)
    print(output_df.head(25)[['Retention_Rank', 'Member', 'Level', 'Power', 'Kills', 
                               'Predicted_Value', 'Anomaly_Status']].to_string(index=False))
    
    # Summary statistics
    active_count = (~df_ranked['Is_Anomaly']).sum()
    anomaly_count = df_ranked['Is_Anomaly'].sum()
    avg_value = df_ranked['Predicted_Value'].mean()
    
    print("\n" + "="*120)
    print("SUMMARY STATISTICS")
    print("="*120)
    print(f"Total Players Analyzed:     {len(df_ranked)}")
    print(f"Active Players:             {active_count} ({100*active_count/len(df_ranked):.1f}%)")
    print(f"Flagged Inactive/Anomaly:   {anomaly_count} ({100*anomaly_count/len(df_ranked):.1f}%)")
    print(f"Average Predicted Value:    {avg_value:.2f}")
    print(f"Value Range:                {df_ranked['Predicted_Value'].min():.2f} - {df_ranked['Predicted_Value'].max():.2f}\n")
    
    # Anomaly breakdown
    if anomaly_count > 0:
        print("⚠️  FLAGGED PLAYERS (Potential Inactive Accounts):")
        anomalies = df_ranked[df_ranked['Is_Anomaly']][['Member', 'Level', 'Power', 'Kills', 'Prof Lvl', 'Gift Lvl', 'Predicted_Value']]
        print(anomalies.to_string(index=False))
        print()
    
    return df_ranked


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Rank players for retention using XGBoost')
    parser.add_argument('--alliance', type=str, help='Filter by alliance name (e.g., SYNZ, pstk)')
    parser.add_argument('--file', type=str, default='../data/synz.csv', help='CSV file path')
    
    args = parser.parse_args()
    
    # Construct full file path
    csv_path = os.path.join(os.path.dirname(__file__), args.file)
    
    # Run ranking
    result_df = rank_players_xgboost(csv_path, alliance_filter=args.alliance)
    
    if result_df is not None:
        print("\n✓ Ranking complete. Use --alliance flag to filter by specific alliance.")
