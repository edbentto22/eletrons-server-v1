"""
Configurações do Sistema de Treinamento YOLO
Baseado no PRD - Seção 4: Especificações Técnicas
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Segurança
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    API_SECRET: str = os.getenv("API_SECRET", "change-me-api-secret")
    CALLBACK_SECRET: str = os.getenv("CALLBACK_SECRET", "change-me-callback-secret")
    
    # Diretórios
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = DATA_DIR / "models"
    DATASETS_DIR: Path = DATA_DIR / "datasets"
    OUTPUTS_DIR: Path = DATA_DIR / "outputs"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # YOLO/Ultralytics
    DEFAULT_MODEL: str = "yolov8n.pt"
    SUPPORTED_MODELS: List[str] = [
        "yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt",
        "yolov9c.pt", "yolov9e.pt",
        "yolov10n.pt", "yolov10s.pt", "yolov10m.pt", "yolov10b.pt", "yolov10l.pt", "yolov10x.pt"
    ]
    
    # Treinamento
    MAX_CONCURRENT_JOBS: int = 2
    DEFAULT_EPOCHS: int = 100
    DEFAULT_BATCH_SIZE: int = 16
    DEFAULT_IMAGE_SIZE: int = 640
    
    # Sistema
    GPU_MEMORY_THRESHOLD: float = 0.9  # 90% de uso máximo
    CPU_CORES: Optional[int] = None  # Auto-detect
    
    # Monitoramento
    SYSTEM_MONITOR_INTERVAL: int = 5  # segundos
    JOB_UPDATE_INTERVAL: int = 1  # segundos
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configuração do Pydantic v2 / pydantic-settings
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
    @field_validator("DATA_DIR", "MODELS_DIR", "DATASETS_DIR", "OUTPUTS_DIR", "LOGS_DIR", mode="after")
    def create_directories(cls, v: Path):
        """Criar diretórios se não existirem"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_origins(cls, v):
        """Parse das origens permitidas"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Instância global das configurações
settings = Settings()

# Criar diretórios necessários
for directory in [settings.DATA_DIR, settings.MODELS_DIR, settings.DATASETS_DIR, 
                 settings.OUTPUTS_DIR, settings.LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)