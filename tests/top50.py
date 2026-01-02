import pandas as pd
import os
import numpy as np

# Define the directory name
DATA_DIR = 'data'
file1 = os.path.join(DATA_DIR, 'pstk.csv')
file2 = os.path.join(DATA_DIR, 'synz.csv')

def select_top_recruits_by_rank(filepath, top_n=100):
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return None

    df_original = pd.read_csv(filepath)
    # Alliance is a required column now for the counts
    required_cols_for_processing = ['Member', 'Power', 'Kills', 'Level', 'Alliance']
    
    # Data cleaning steps: drop NaNs for essential columns
    df = df_original.dropna(subset=required_cols_for_processing)
    
    # Filter: Ensure players are Level 30+
    df = df[df['Level'] >= 30].copy()
    
    if df.empty:
        print(f"Error: No data remains in file '{filepath}' after cleaning/filtering.")
        return None

    # Sort by Level (desc), then Kills (desc), then Power (desc)
    df_sorted = df.sort_values(
        by=['Level', 'Kills', 'Power'],
        ascending=[False, False, False]
    )
    
    # Select the top N players
    top_recruits = df_sorted.head(top_n)
    
    # Calculate the aggregate power for the selected top players
    total_power_aggregate = top_recruits['Power'].sum()

    # Calculate the counts for each alliance present in the top recruits list
    alliance_counts = top_recruits['Alliance'].value_counts()
    
    # 4. Print results
    filename = filepath.split(os.sep)[-1]
    print(f"\n=============================================")
    print(f"  Report for {filename}")
    print(f"=============================================\n")
    
    print(f"  >>> AGGREGATE TOTAL POWER (Top {len(top_recruits)} members): {total_power_aggregate:,.0f} <<<")
    
    print("\n--- Alliance Counts within Top Recruits ---")
    # Using to_markdown for a clean table output of the counts
    print(alliance_counts.reset_index().rename(columns={'index': 'Alliance', 'Alliance': 'Count'}).to_markdown(index=False))

    print(f"\n--- Top {len(top_recruits)} Members Details ---")

    # Add a rank column for clarity in the output
    top_recruits = top_recruits.copy()
    top_recruits['Rank'] = range(1, len(top_recruits) + 1)

    # Include 'Alliance' in the final output table
    cols_to_display = ['Rank', 'Alliance', 'Member', 'Power', 'Kills', 'Level']
    final_columns = [col for col in cols_to_display if col in top_recruits.columns]
    
    print(top_recruits[final_columns].to_markdown(index=False))
    
    if len(df) > top_n:
         print(f"\n[...{len(df) - len(top_recruits)} remaining eligible players not shown...]")
    else:
         print(f"\n[...All eligible players listed above...]")

    return top_recruits

# Process both files with the new approach
# df_pstk_recruits = select_top_recruits_by_rank(file1, top_n=100)
df_synz_recruits = select_top_recruits_by_rank(file2, top_n=100)
