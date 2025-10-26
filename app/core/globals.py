"""
Instâncias globais dos serviços
Evita importação circular entre main.py e roteadores
"""

from app.services.job_manager import JobManager
from app.services.system_monitor import SystemMonitor
from app.services.sse_manager import SSEManager

# Instâncias globais dos serviços
job_manager = JobManager()
system_monitor = SystemMonitor()
sse_manager = SSEManager()