import pandas as pd
import os
# from ydata_profiling import ProfileReport
from glob import glob

PARQUET_PATH = "raw/merged_data.parquet"
PROCESSED_PATH = "raw/processed_files.txt"
RAW_DIR = "data"

def load_incremental_data():
    """
    Loads and processes new Excel files from a raw data directory incrementally.

    This function identifies unprocessed `.xlsx` files in the RAW_DIR, reads them,
    standardizes string columns, adds a `source_file` column, and appends them to an existing
    dataset stored in PARQUET_PATH. It maintains a log of processed filenames in PROCESSED_PATH
    to avoid duplication. New data is merged, deduplicated, and stored back as a Parquet file.

    To reset the dataset, delete content inside processed_files and merged_data.parquet, this function is applied everytime main.py started looking for new files.

    Returns:
        pd.DataFrame: A DataFrame containing the full dataset after merging new files.
    """
    all_files = glob(os.path.join(RAW_DIR, "*.xlsx"))
    if os.path.exists(PROCESSED_PATH):
        with open(PROCESSED_PATH, "r") as f:
            processed = set(f.read().splitlines())
    else:
        processed = set()

    new_files = [f for f in all_files if os.path.basename(f) not in processed]
    if not new_files:
        print("No new files, current :", len(processed))
        return pd.read_parquet(PARQUET_PATH)

    dfs = []
    for file in new_files:
        try:
            df = pd.read_excel(file, parse_dates=["Date"])
            for col in df.select_dtypes(include="object").columns:
                df[col] = df[col].astype(str)
            df["source_file"] = os.path.basename(file)
            dfs.append(df)
        except Exception as e:
            print(f"Failed: {file}")

    df_connected = pd.concat(dfs, ignore_index=True)
    df_clean = df_connected.dropna(axis=1, how="all")

    if os.path.exists(PARQUET_PATH):
        df_old = pd.read_parquet(PARQUET_PATH)
        df_all = pd.concat([df_old, df_clean], ignore_index=True)
    else:
        df_all = df_clean

    df_all = df_all.drop_duplicates()
    df_all.to_parquet(PARQUET_PATH, index=False)

    with open(PROCESSED_PATH, "a") as f:
        for fpath in new_files:
            f.write(os.path.basename(fpath) + "\n")

    print(f"Updated: {len(df_clean)} rows added")
    return df_all



