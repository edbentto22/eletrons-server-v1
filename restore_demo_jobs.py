#!/usr/bin/env python3
"""
Script para restaurar jobs de demonstração no sistema de treinamento YOLO
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

# Caminho do arquivo jobs.json
JOBS_FILE = Path("/Volumes/SSD NVME - Backup/TRAINING SYSTEM YOLO/data/jobs.json")

# Dados dos jobs de demonstração
demo_jobs = [
    {
        "id": "job_abc12345",
        "name": "Treinamento YOLOv8n - Dataset COCO",
        "status": "completed",
        "config": {
            "base_model": "yolov8n.pt",
            "epochs": 100,
            "batch_size": 16,
            "image_size": 640,
            "learning_rate": 0.01,
            "optimizer": "AdamW",
            "device": "0",
            "workers": 8,
            "patience": 50,
            "save_period": 10,
            "augment": True,
            "mosaic": 1.0,
            "mixup": 0.0,
            "copy_paste": 0.0
        },
        "dataset": {
            "name": "coco",
            "path": "/datasets/coco",
            "classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"],
            "train_images": 117266,
            "val_images": 4952,
            "test_images": 4069
        },
        "current_epoch": 100,
        "progress_percent": 100.0,
        "metrics": {
            "epoch": 100,
            "total_epochs": 100,
            "train_loss": 2.134,
            "val_loss": 2.089,
            "precision": 0.492,
            "recall": 0.587,
            "map50": 0.543,
            "map50_95": 0.367,
            "learning_rate": 0.001,
            "eta": "0h 0m"
        },
        "best_metrics": {
            "precision": 0.512,
            "recall": 0.601,
            "map50": 0.567,
            "map50_95": 0.389
        },
        "model_path": "/runs/train/yolov8n_coco_100ep",
        "weights_path": "/runs/train/yolov8n_coco_100ep/weights/best.pt",
        "logs_path": "/runs/train/yolov8n_coco_100ep/logs",
        "created_at": "2024-01-15T10:30:00",
        "started_at": "2024-01-15T10:32:15",
        "completed_at": "2024-01-15T13:05:15",
        "error_message": None
    },
    {
        "id": "job_def67890",
        "name": "Treinamento YOLOv8s - Dataset Customizado",
        "status": "running",
        "config": {
            "base_model": "yolov8s.pt",
            "epochs": 50,
            "batch_size": 8,
            "image_size": 640,
            "learning_rate": 0.01,
            "optimizer": "AdamW",
            "device": "0",
            "workers": 4,
            "patience": 25,
            "save_period": 5,
            "augment": True,
            "mosaic": 1.0,
            "mixup": 0.1,
            "copy_paste": 0.1
        },
        "dataset": {
            "name": "custom-objects",
            "path": "/datasets/custom-objects",
            "classes": ["product_a", "product_b", "product_c", "defect_type_1", "defect_type_2"],
            "train_images": 1000,
            "val_images": 200,
            "test_images": 50
        },
        "current_epoch": 25,
        "progress_percent": 50.0,
        "metrics": {
            "epoch": 25,
            "total_epochs": 50,
            "train_loss": 1.845,
            "val_loss": 1.912,
            "precision": 0.723,
            "recall": 0.681,
            "map50": 0.712,
            "map50_95": 0.489,
            "learning_rate": 0.005,
            "eta": "1h 15m"
        },
        "best_metrics": {
            "precision": 0.735,
            "recall": 0.695,
            "map50": 0.725,
            "map50_95": 0.501
        },
        "model_path": "/runs/train/yolov8s_custom_50ep",
        "weights_path": "/runs/train/yolov8s_custom_50ep/weights/last.pt",
        "logs_path": "/runs/train/yolov8s_custom_50ep/logs",
        "created_at": "2024-01-16T14:20:00",
        "started_at": "2024-01-16T14:22:30",
        "completed_at": None,
        "error_message": None
    },
    {
        "id": "job_ghi13579",
        "name": "Validação YOLOv8m - Dataset VOC",
        "status": "pending",
        "config": {
            "base_model": "yolov8m.pt",
            "epochs": 1,
            "batch_size": 16,
            "image_size": 640,
            "learning_rate": 0.001,
            "optimizer": "AdamW",
            "device": "0",
            "workers": 8,
            "patience": 10,
            "save_period": 1,
            "augment": False,
            "mosaic": 0.0,
            "mixup": 0.0,
            "copy_paste": 0.0
        },
        "dataset": {
            "name": "voc",
            "path": "/datasets/voc",
            "classes": ["aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"],
            "train_images": 0,
            "val_images": 4952,
            "test_images": 11599
        },
        "current_epoch": 0,
        "progress_percent": 0.0,
        "metrics": None,
        "best_metrics": None,
        "model_path": None,
        "weights_path": None,
        "logs_path": None,
        "created_at": "2024-01-17T09:45:00",
        "started_at": None,
        "completed_at": None,
        "error_message": None
    }
]

def restore_demo_jobs():
    """Restaurar jobs de demonstração"""
    try:
        # Garantir que o diretório existe
        JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar jobs de demonstração
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(demo_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {len(demo_jobs)} jobs de demonstração restaurados em {JOBS_FILE}")
        
        # Verificar se o arquivo foi criado corretamente
        if JOBS_FILE.exists():
            file_size = JOBS_FILE.stat().st_size
            print(f"📁 Arquivo criado: {JOBS_FILE} ({file_size} bytes)")
            
            # Ler e mostrar conteúdo para verificação
            with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                content = json.load(f)
            print(f"📊 Jobs no arquivo: {len(content)}")
            for job in content:
                print(f"   - {job['id']}: {job['name']} ({job['status']})")
        else:
            print("❌ Arquivo não foi criado")
            
    except Exception as e:
        print(f"❌ Erro ao restaurar jobs: {e}")

if __name__ == "__main__":
    restore_demo_jobs()