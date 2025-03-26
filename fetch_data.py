import os
import requests
import json
import sqlite3
from datetime import datetime
from datetime import timezone
import pandas as pd

url = 'https://api.5calls.org/v1/issues'

def parse_json_to_db(data, utc_time, db_name="data/fivecalls.db", table_name="flat_data"):
    os.makedirs("data", exist_ok=True)
    df = pd.json_normalize(data)
    df['inserted_at_utc'] = utc_time
    df['categories'] = df['categories'].apply(json.dumps)
    df['contactAreas'] = df['contactAreas'].apply(json.dumps)
    df['outcomeModels'] = df['outcomeModels'].apply(json.dumps)
    if 'stats.calls' in df.columns:
        df.rename(columns={'stats.calls': 'calls'}, inplace=True)
    with sqlite3.connect(db_name) as conn:
        df.to_sql(table_name, conn, if_exists='append', index=False)
    print(f"✅ Appended {len(df)} records to {table_name} in {db_name}.")

def fetch_and_store(keep_original_data=False):
    response = requests.get(url)
    utc_time = datetime.now(timezone.utc).isoformat()
    if response.status_code == 200:
        data = response.json()
        parse_json_to_db(data, utc_time)
        if keep_original_data:
            os.makedirs("original_data", exist_ok=True)
            with open(f'original_data/data_{utc_time}.json', 'w') as f:
                json.dump(data, f)
            print(f"✅ Data saved at {utc_time}")
    else:
        print(f"❌ API Error: {response.status_code}")

if __name__ == "__main__":
    fetch_and_store()
