"""
Configuração de Logging do Sistema
"""

import logging
import logging.handlers
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """Configurar sistema de logging"""
    
    # Criar diretório de logs
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mapear formatos nomeados para strings de formato reais
    format_map = {
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
        "simple": "%(levelname)s:%(name)s:%(message)s"
    }
    fmt = settings.LOG_FORMAT
    if fmt in format_map:
        fmt_str = format_map[fmt]
    else:
        fmt_str = fmt  # assumir que já é um formato válido
    
    # Configurar formato
    formatter = logging.Formatter(fmt_str)
    
    # Logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    
    # Evitar handlers duplicados em reconfigurações
    if root_logger.handlers:
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo (rotativo)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "training_system.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Logger específico para jobs
    job_logger = logging.getLogger("jobs")
    job_file_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "jobs.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    job_file_handler.setFormatter(formatter)
    job_logger.addHandler(job_file_handler)
    
    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)
    
    logging.info("✅ Sistema de logging configurado")