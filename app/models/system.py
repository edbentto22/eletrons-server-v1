"""
Modelos de dados para sistema e recursos
Baseado no PRD - Seção 5: Monitoramento de Recursos
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GPUInfo(BaseModel):
    """Informações da GPU"""
    id: int
    name: str
    memory_total: int  # MB
    memory_used: int   # MB
    memory_free: int   # MB
    utilization: float  # Percentual 0-100
    temperature: Optional[float] = None  # Celsius
    power_draw: Optional[float] = None   # Watts
    available: bool = True
    
    @property
    def memory_usage_percent(self) -> float:
        """Percentual de uso da memória"""
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 0,
                "name": "NVIDIA GeForce RTX 4090",
                "memory_total": 24576,
                "memory_used": 8192,
                "memory_free": 16384,
                "utilization": 75.5,
                "temperature": 68.0,
                "power_draw": 350.0,
                "available": True
            }
        }
    }


class CPUInfo(BaseModel):
    """Informações da CPU"""
    cores: int
    threads: int
    usage_percent: float
    frequency: Optional[float] = None  # MHz
    temperature: Optional[float] = None  # Celsius
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cores": 8,
                "threads": 16,
                "usage_percent": 45.2,
                "frequency": 3200.0,
                "temperature": 55.0
            }
        }
    }


class MemoryInfo(BaseModel):
    """Informações da memória RAM"""
    total: int  # MB
    used: int   # MB
    free: int   # MB
    available: int  # MB
    usage_percent: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 32768,
                "used": 16384,
                "free": 8192,
                "available": 16384,
                "usage_percent": 50.0
            }
        }
    }


class DiskInfo(BaseModel):
    """Informações do disco"""
    path: str
    total: int  # MB
    used: int   # MB
    free: int   # MB
    usage_percent: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "path": "/",
                "total": 1048576,
                "used": 524288,
                "free": 524288,
                "usage_percent": 50.0
            }
        }
    }


class SystemResources(BaseModel):
    """Recursos do sistema"""
    timestamp: datetime
    cpu: CPUInfo
    memory: MemoryInfo
    gpu: Optional[List[GPUInfo]] = None
    disk: Optional[List[DiskInfo]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2024-01-15T10:30:00Z",
                "cpu": {
                    "cores": 8,
                    "threads": 16,
                    "usage_percent": 45.2,
                    "frequency": 3200.0
                },
                "memory": {
                    "total": 32768,
                    "used": 16384,
                    "free": 8192,
                    "available": 16384,
                    "usage_percent": 50.0
                },
                "gpu": [
                    {
                        "id": 0,
                        "name": "NVIDIA GeForce RTX 4090",
                        "memory_total": 24576,
                        "memory_used": 8192,
                        "memory_free": 16384,
                        "utilization": 75.5,
                        "available": True
                    }
                ]
            }
        }
    }


class SystemStatus(BaseModel):
    """Status geral do sistema"""
    status: str  # "healthy", "warning", "critical"
    uptime: float  # segundos
    load_average: Optional[List[float]] = None  # 1min, 5min, 15min
    active_jobs: int
    total_jobs: int
    gpu_available: bool
    warnings: List[str] = []
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "uptime": 86400.0,
                "load_average": [1.2, 1.5, 1.8],
                "active_jobs": 2,
                "total_jobs": 15,
                "gpu_available": True,
                "warnings": []
            }
        }
    }


class ModelInfo(BaseModel):
    """Informações de modelo"""
    name: str
    path: str
    size: int  # bytes
    type: str  # "yolov8", "yolov9", "yolov10"
    version: str
    classes: Optional[List[str]] = None
    input_size: Optional[int] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "yolov8n.pt",
                "path": "/data/models/yolov8n.pt",
                "size": 6234567,
                "type": "yolov8",
                "version": "8.0.0",
                "classes": ["person", "bicycle", "car"],
                "input_size": 640,
                "created_at": "2024-01-15T10:00:00Z",
                "last_used": "2024-01-15T10:30:00Z"
            }
        }
    }


class DatasetInfo(BaseModel):
    """Informações de dataset"""
    name: str
    path: str
    format: str  # "yolo", "coco", "pascal"
    classes: List[str]
    train_images: int
    val_images: int
    test_images: Optional[int] = None
    total_size: int  # bytes
    created_at: datetime
    last_used: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "custom_dataset",
                "path": "/data/datasets/custom_dataset",
                "format": "yolo",
                "classes": ["person", "car", "bicycle"],
                "train_images": 5000,
                "val_images": 1000,
                "test_images": 500,
                "total_size": 1073741824,
                "created_at": "2024-01-15T09:00:00Z",
                "last_used": "2024-01-15T10:30:00Z"
            }
        }
    }