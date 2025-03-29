import os
import requests
import json
import sqlite3
from datetime import datetime
from datetime import timezone
import pandas as pd

url = 'https://api.5calls.org/v1/issues'

backup_path = '/home/Projects/fivecallsdatabackup/'

def parse_json_to_db(data, utc_time, db_name="fivecalls.db", table_name="flat_data", backup_path=backup_path):
    os.makedirs("data", exist_ok=True)
    os.makedirs(backup_path, exist_ok=True)
    df = pd.json_normalize(data)
    df['inserted_at_utc'] = utc_time
    df['categories'] = df['categories'].apply(json.dumps)
    df['contactAreas'] = df['contactAreas'].apply(json.dumps)
    df['outcomeModels'] = df['outcomeModels'].apply(json.dumps)
    if 'stats.calls' in df.columns:
        df.rename(columns={'stats.calls': 'calls'}, inplace=True)
    # Write to working directory
    for path in ('data/', backup_path):
        db_name_tmp = os.path.join(path, db_name)
        print(f"Writing to {db_name_tmp}...")
        with sqlite3.connect(db_name_tmp) as conn:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"✅ Appended {len(df)} records to {table_name} in {db_name_tmp}.")

def fetch_and_store(keep_original_data=True, backup_path=backup_path):
    response = requests.get(url)
    utc_time = datetime.now(timezone.utc).isoformat()
    if response.status_code == 200:
        data = response.json()
        parse_json_to_db(data, utc_time)
        if keep_original_data:
            backup_path = os.path.join(backup_path, 'original_data')
            os.makedirs(backup_path, exist_ok=True)
            with open(f'{backup_path}/data_{utc_time}.json', 'w') as f:
                json.dump(data, f)
            print(f"✅ Data saved at {utc_time}")
    else:
        print(f"❌ API Error: {response.status_code}")

if __name__ == "__main__":
    fetch_and_store()
