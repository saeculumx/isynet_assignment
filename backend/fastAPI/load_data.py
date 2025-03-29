import pandas as pd
import os
from glob import glob
from fuzzywuzzy import process

PARQUET_PATH = "raw/merged_data.parquet"
PROCESSED_PATH = "raw/processed_files.txt"
RAW_DIR = "data"

# Top 50 Indian cities
india_cities = [
    "MUMBAI", "DELHI", "NAVI MUMBAI", "BANGALORE", "CHENNAI", "HYDERABAD", "KOLKATA",
    "PUNE", "AHMEDABAD", "NOIDA", "THANE", "JAIPUR", "GURGAON", "FARIDABAD", "LUCKNOW",
    "NAGPUR", "VISAKHAPATNAM", "INDORE", "BHOPAL", "PATNA", "CHANDIGARH", "KANPUR",
    "SURAT", "VADODARA", "RAJKOT", "LUDHIANA", "AGRA", "RANCHI", "COIMBATORE", "GUWAHATI",
    "JAMSHEDPUR", "DEHRADUN", "JODHPUR", "MANGALORE", "ALLAHABAD", "TIRUPATI",
    "AMRITSAR", "TRIVANDRUM", "VIJAYAWADA", "MADURAI", "VARANASI", "AURANGABAD",
    "BHIWANDI", "HUBLI", "KOTA", "NASHIK", "SALEM", "GHAZIABAD", "RAIPUR", "SRINAGAR"
]

# Top 50 Global cities
global_cities = [
    "NEW YORK", "LONDON", "DUBAI", "SINGAPORE", "HONG KONG", "SHANGHAI", "LOS ANGELES",
    "TOKYO", "PARIS", "CHICAGO", "TORONTO", "BERLIN", "BANGKOK", "SEOUL", "SYDNEY",
    "AMSTERDAM", "FRANKFURT", "SAN FRANCISCO", "MUNICH", "KUALA LUMPUR", "HAMBURG",
    "BEIJING", "JAKARTA", "ROME", "ZURICH", "MOSCOW", "ISTANBUL", "BRUSSELS", "BARCELONA",
    "CAPE TOWN", "MEXICO CITY", "SAO PAULO", "DOHA", "MELBOURNE", "MIAMI", "STOCKHOLM",
    "VIENNA", "COPENHAGEN", "BOSTON", "WARSAW", "AUCKLAND", "OSLO", "MILAN", "MANILA",
    "LAGOS", "ABU DHABI", "HELSINKI", "HOUSTON", "GENEVA", "PRAGUE"
]

standard_cities = india_cities + global_cities

def normalize_city(city, choices=standard_cities, threshold=90):
    if pd.isna(city):
        return city
    match, score = process.extractOne(str(city).upper(), choices)
    return match if score >= threshold else city

def load_incremental_data():
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

            if "City" in df.columns:
                df["City_normalized"] = df["City"].apply(normalize_city)

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
