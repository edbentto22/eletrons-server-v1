"""
Modelos de dados para treinamento
Baseado no PRD - Seção 6: Estrutura de Dados
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Status dos jobs de treinamento"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(str, Enum):
    """Tipos de modelo YOLO suportados"""
    YOLOV8N = "yolov8n.pt"
    YOLOV8S = "yolov8s.pt"
    YOLOV8M = "yolov8m.pt"
    YOLOV8L = "yolov8l.pt"
    YOLOV8X = "yolov8x.pt"
    YOLOV9C = "yolov9c.pt"
    YOLOV9E = "yolov9e.pt"
    YOLOV10N = "yolov10n.pt"
    YOLOV10S = "yolov10s.pt"
    YOLOV10M = "yolov10m.pt"
    YOLOV10B = "yolov10b.pt"
    YOLOV10L = "yolov10l.pt"
    YOLOV10X = "yolov10x.pt"


class TrainingMetrics(BaseModel):
    """Métricas de treinamento"""
    epoch: int
    total_epochs: int
    train_loss: float
    val_loss: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    learning_rate: float
    eta: Optional[str] = None  # Tempo estimado restante
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "epoch": 50,
                "total_epochs": 100,
                "train_loss": 0.0234,
                "val_loss": 0.0456,
                "precision": 0.892,
                "recall": 0.845,
                "map50": 0.923,
                "map50_95": 0.678,
                "learning_rate": 0.001,
                "eta": "1h 23m"
            }
        }
    }


class TrainingConfig(BaseModel):
    """Configuração de treinamento"""
    base_model: ModelType = ModelType.YOLOV8N
    epochs: int = Field(default=100, ge=1, le=1000)
    batch_size: int = Field(default=16, ge=1, le=128)
    image_size: int = Field(default=640, ge=320, le=1280)
    learning_rate: float = Field(default=0.01, gt=0, le=1)
    optimizer: str = Field(default="AdamW")
    device: Optional[str] = None  # Auto-detect
    workers: int = Field(default=8, ge=1, le=32)
    patience: int = Field(default=50, ge=1)
    save_period: int = Field(default=10, ge=1)
    
    # Augmentação
    augment: bool = True
    mosaic: float = Field(default=1.0, ge=0, le=1)
    mixup: float = Field(default=0.0, ge=0, le=1)
    copy_paste: float = Field(default=0.0, ge=0, le=1)
    
    @validator("image_size")
    def validate_image_size(cls, v):
        """Validar que image_size é múltiplo de 32"""
        if v % 32 != 0:
            raise ValueError("image_size deve ser múltiplo de 32")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "base_model": "yolov8n.pt",
                "epochs": 100,
                "batch_size": 16,
                "image_size": 640,
                "learning_rate": 0.01,
                "optimizer": "AdamW",
                "workers": 8,
                "patience": 50,
                "save_period": 10,
                "augment": True,
                "mosaic": 1.0,
                "mixup": 0.0,
                "copy_paste": 0.0
            }
        }
    }


class DatasetInfo(BaseModel):
    """Informações do dataset"""
    name: str
    path: str
    classes: List[str]
    train_images: int
    val_images: int
    test_images: Optional[int] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "custom_dataset",
                "path": "/data/datasets/custom_dataset",
                "classes": ["person", "car", "bicycle"],
                "train_images": 1000,
                "val_images": 200,
                "test_images": 100
            }
        }
    }


class TrainingJob(BaseModel):
    """Job de treinamento"""
    id: str
    name: str
    status: JobStatus = JobStatus.PENDING
    config: TrainingConfig
    dataset: DatasetInfo
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progresso
    current_epoch: int = 0
    progress_percent: float = 0.0
    
    # Métricas
    metrics: Optional[TrainingMetrics] = None
    best_metrics: Optional[Dict[str, float]] = None
    
    # Arquivos
    model_path: Optional[str] = None
    weights_path: Optional[str] = None
    logs_path: Optional[str] = None
    
    # Erro (se houver)
    error_message: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "job_123456",
                "name": "Treinamento Detecção Pessoas",
                "status": "running",
                "config": {
                    "base_model": "yolov8n.pt",
                    "epochs": 100,
                    "batch_size": 16,
                    "image_size": 640
                },
                "dataset": {
                    "name": "pessoas_dataset",
                    "path": "/data/datasets/pessoas",
                    "classes": ["person"],
                    "train_images": 5000,
                    "val_images": 1000
                },
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:31:00Z",
                "current_epoch": 45,
                "progress_percent": 45.0,
                "metrics": {
                    "epoch": 45,
                    "total_epochs": 100,
                    "train_loss": 0.0234,
                    "val_loss": 0.0456,
                    "map50": 0.923,
                    "eta": "1h 23m"
                }
            }
        }
    }


class JobCreateRequest(BaseModel):
    """Request para criar novo job"""
    name: str = Field(..., min_length=1, max_length=100)
    dataset_path: str = Field(..., min_length=1)
    config: TrainingConfig
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Novo Treinamento",
                "dataset_path": "/data/datasets/my_dataset",
                "config": {
                    "base_model": "yolov8n.pt",
                    "epochs": 100,
                    "batch_size": 16,
                    "image_size": 640
                }
            }
        }
    }


class JobUpdateRequest(BaseModel):
    """Request para atualizar job"""
    name: Optional[str] = None
    status: Optional[JobStatus] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Novo Nome do Job",
                "status": "cancelled"
            }
        }
    }


class ProgressUpdate(BaseModel):
    """Atualização de progresso via SSE"""
    job_id: str
    event_type: str  # "progress", "metrics", "completed", "error"
    data: Dict[str, Any]
    timestamp: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "job_123456",
                "event_type": "metrics",
                "data": {
                    "epoch": 45,
                    "train_loss": 0.0234,
                    "val_loss": 0.0456,
                    "map50": 0.923
                },
                "timestamp": "2024-01-15T10:45:00Z"
            }
        }
    }