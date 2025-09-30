# server/init_db.py
from server.database import engine, Base
import server.models.cpu as cpu_model
import server.models.anomaly as anomaly_model

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init()
