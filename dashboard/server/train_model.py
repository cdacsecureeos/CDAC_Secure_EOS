# server/scripts/train_model.py

import pandas as pd
import psycopg2
from server.ml.anomaly_detector import train_model
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def fetch_data():
    conn = psycopg2.connect(DATABASE_URL)
    query = """
        SELECT cpu_percent, mem_percent, virt, res, shr, priority, nice
        FROM cpu_processes
        WHERE timestamp >= now() - interval '7 days'
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    df = fetch_data()
    print(f"Fetched {len(df)} records for training.")
    model = train_model(df)
    print("✅ Model trained and saved.")
