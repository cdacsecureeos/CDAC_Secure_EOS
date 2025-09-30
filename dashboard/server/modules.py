from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CpuProcess(BaseModel):
    pid: int
    ppid: int
    username: str
    cpu_percent: float
    mem_percent: float
    time_used: str
    command: str
    virt: int
    res: int
    shr: int
    priority: int
    nice: int
    state: str
    from_ip: str
    timestamp:  str



"""class AuditEvent(BaseModel):
    pid: int
    ppid: int
    username: str
    cpu_percent: float
    mem_percent: float
    command: str
    virt: int
    res: int
    shr: int
    priority: int
    nice: int
    tty: str
    level: str
    from_ip: str
    timestamp: datetime"""


class SessionEvent(BaseModel):
    session_id: str 
    username: str
    tty: str
    from_ip: str
    event: str
    login_time: str
    idle: str
    jcpu: str
    pcpu: str
    command: str = "-bash"  # optional fallback if needed
    timestamp: str


class CommandHistoryEntry(BaseModel):
    username: str
    from_ip: str 
    commands: str
    session_id: str  # ✅ Newly added
    timestamp: str   # also string format from client

class FileChange(BaseModel):
    from_ip: str
    file_path: str
    checksum: str
    change_type: str
    timestamp: datetime  # correct: datetime object

class SecurityEvent(BaseModel):
    source_ip: str
    event_type: str  # e.g., "SSH_LOGIN", "BRUTE_FORCE"
    username: str
    tty: str = "-"
    description: str
    timestamp: str  # client-side ISO format
    received_at: str = None  # filled by backend on receive

# --------------------------------------------
# 🛡️ CVE Scan Result Log
# --------------------------------------------
'''class CVEScanResult(BaseModel):
    host: str
    cve_id: str
    severity: str  # e.g., "HIGH", "CRITICAL"
    description: str
    package: str
    fixed_version: str = "-"
    current_version: str
    timestamp: str  # from client
    received_at: str = None  # filled by backend
'''


class SecurityLogEntry(BaseModel):
    username: str
    from_ip: str
    event: str
    description: str
    received_at: str = None 



class AgentEnrollmentPayload(BaseModel):
  
    hostname: str
    ip_address: Optional[str] = None
    os_name: str 

class AlertPayload(BaseModel):
    agent_uuid: str
    alert_type: str
    value: str
    source: str
    


