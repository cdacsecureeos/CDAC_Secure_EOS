# server/models/cpu.py

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from server.database import Base

class CpuAuditEvent(Base):
    __tablename__ = "cpu_audit_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(128), index=True)
    from_ip = Column(String(64))
    pid = Column(Integer, index=True)
    ppid = Column(Integer, index=True)
    name = Column(Text)
    username = Column(Text)
    cpu_percent = Column(Float)
    mem_percent = Column(Float)
    virt = Column(Integer)
    res = Column(Integer)
    shr = Column(Integer)
    nice = Column(Integer)
    threads = Column(Integer)
    status = Column(String(32))
    cmdline = Column(Text)
    tty = Column(String(32))
    timestamp = Column(DateTime, index=True, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "from_ip": self.from_ip,
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "username": self.username,
            "cpu_percent": self.cpu_percent,
            "mem_percent": self.mem_percent,
            "virt": self.virt,
            "res": self.res,
            "shr": self.shr,
            "nice": self.nice,
            "threads": self.threads,
            "status": self.status,
            "cmdline": self.cmdline,
            "tty": self.tty,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
