# server/database.py

import os
from dotenv import load_dotenv

import psycopg  # for lightweight raw access
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔹 Load .env credentials
load_dotenv()

# 🔹 Raw psycopg connection (used by most modules)
def get_conn():
    return psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

