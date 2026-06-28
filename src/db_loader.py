import os
import json
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv('DB_NAME'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "host": os.getenv('DB_HOST'),
    "port": os.getenv('DB_PORT')
}

def extract_lake_data(base_dir="data/raw/telegram_messages"):
    all_records = []
    json_files = glob.glob(os.path.join(base_dir, "**", "*.json"), recursive=True)
    
    for file_path in json_files:
        channel_name = os.path.basename(file_path).replace(".json", "")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                messages = json.load(f)
                for msg in messages:
                    msg["_extracted_channel_name"] = channel_name
                    all_records.append(msg)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    return all_records

def main():
    raw_messages = extract_lake_data()
    if not raw_messages:
        print("No raw data found in data lake folder paths.")
        return

    print(f"Extracted {len(raw_messages)} raw entries. Flattening structural keys...")
    
    flattened = []
    for m in raw_messages:
        flattened.append({
            "message_id": m.get("id"),
            "channel_name": m.get("_extracted_channel_name"),
            "date": m.get("date"),
            "message_text": m.get("message"),
            "views": m.get("views"),
            "forwards": m.get("forwards"),
            "media_type": m.get("media", {}).get("_") if m.get("media") else None
        })

    df = pd.DataFrame(flattened)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id BIGINT,
            channel_name VARCHAR(255),
            date VARCHAR(100),
            message_text TEXT,
            views INTEGER,
            forwards INTEGER,
            media_type VARCHAR(255)
        );
    """)
    
    cur.execute("TRUNCATE TABLE raw.telegram_messages;")
    
    query = """
        INSERT INTO raw.telegram_messages (message_id, channel_name, date, message_text, views, forwards, media_type)
        VALUES %s
    """
    values = [tuple(x) for x in df.to_numpy()]
    execute_values(cur, query, values)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Successfully populated raw.telegram_messages table!")

if __name__ == "__main__":
    main()