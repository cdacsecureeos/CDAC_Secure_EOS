from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from server.database import Base

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    pid = Column(Integer)
    username = Column(Text)
    cpu_percent = Column(Float)
    mem_percent = Column(Float)
    command = Column(Text)
    timestamp = Column(DateTime)
    from_ip = Column(Text)
    anomaly_type = Column(String(50))
    anomaly_score = Column(Float)
    model_version = Column(String(10), default="v1")
