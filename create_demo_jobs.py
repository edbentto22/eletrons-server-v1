#!/usr/bin/env python3
"""
Script para criar jobs de demonstração para a interface do YOLO Training Server
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import uuid

def create_demo_jobs():
    """Criar jobs de demonstração"""
    
    jobs_file = Path("data/jobs.json")
    
    # Dados dos jobs de exemplo
    demo_jobs = [
        # Job ativo em treinamento
        {
            "id": "job_active_001",
            "name": "Treinamento YOLOv8n - Detecção de Objetos",
            "status": "running",
            "config": {
                "base_model": "yolov8n.pt",
                "epochs": 100,
                "batch_size": 16,
                "image_size": 640,
                "learning_rate": 0.01,
                "optimizer": "AdamW",
                "device": "cuda:0",
                "workers": 8,
                "patience": 50,
                "save_period": 10,
                "augment": True,
                "mosaic": 1.0,
                "mixup": 0.0,
                "copy_paste": 0.0
            },
            "dataset": {
                "name": "coco128",
                "path": "data/datasets/coco128",
                "classes": ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"],
                "train_images": 128,
                "val_images": 128,
                "test_images": None
            },
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "started_at": (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
            "completed_at": None,
            "current_epoch": 45,
            "progress_percent": 45.0,
            "metrics": {
                "train_loss": 0.85,
                "val_loss": 0.92,
                "mAP_50": 0.68,
                "mAP_50_95": 0.42,
                "precision": 0.76,
                "recall": 0.61,
                "epoch": 45,
                "total_epochs": 100
            },
            "best_metrics": {
                "train_loss": 0.82,
                "val_loss": 0.89,
                "mAP_50": 0.72,
                "mAP_50_95": 0.45,
                "precision": 0.78,
                "recall": 0.65,
                "epoch": 32
            },
            "model_path": "data/outputs/job_active_001/weights/best.pt",
            "weights_path": "data/outputs/job_active_001/weights/last.pt",
            "logs_path": "data/outputs/job_active_001/logs/",
            "error_message": None
        },
        
        # Job na fila
        {
            "id": "job_queued_001",
            "name": "Treinamento YOLOv8s - Detecção de Veículos",
            "status": "pending",
            "config": {
                "base_model": "yolov8s.pt",
                "epochs": 150,
                "batch_size": 8,
                "image_size": 1024,
                "learning_rate": 0.005,
                "optimizer": "AdamW",
                "device": "cuda:0",
                "workers": 8,
                "patience": 50,
                "save_period": 10,
                "augment": True,
                "mosaic": 0.5,
                "mixup": 0.0,
                "copy_paste": 0.0
            },
            "dataset": {
                "name": "vehicle_detection",
                "path": "data/datasets/vehicles",
                "classes": ["car", "truck", "bus", "motorcycle", "bicycle"],
                "train_images": 2500,
                "val_images": 500,
                "test_images": 200
            },
            "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "started_at": None,
            "completed_at": None,
            "current_epoch": 0,
            "progress_percent": 0.0,
            "metrics": None,
            "best_metrics": None,
            "model_path": None,
            "weights_path": None,
            "logs_path": None,
            "error_message": None
        },
        
        # Job concluído com sucesso
        {
            "id": "job_completed_001",
            "name": "Treinamento YOLOv8m - Detecção de Pessoas",
            "status": "completed",
            "config": {
                "base_model": "yolov8m.pt",
                "epochs": 200,
                "batch_size": 12,
                "image_size": 640,
                "learning_rate": 0.001,
                "optimizer": "AdamW",
                "device": "cuda:0",
                "workers": 8,
                "patience": 50,
                "save_period": 10,
                "augment": True,
                "mosaic": 1.0,
                "mixup": 0.0,
                "copy_paste": 0.0
            },
            "dataset": {
                "name": "person_detection",
                "path": "data/datasets/persons",
                "classes": ["person"],
                "train_images": 5000,
                "val_images": 1000,
                "test_images": 500
            },
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "started_at": (datetime.now() - timedelta(days=1, hours=-1)).isoformat(),
            "completed_at": (datetime.now() - timedelta(hours=12)).isoformat(),
            "current_epoch": 200,
            "progress_percent": 100.0,
            "metrics": {
                "train_loss": 0.45,
                "val_loss": 0.52,
                "mAP_50": 0.92,
                "mAP_50_95": 0.78,
                "precision": 0.94,
                "recall": 0.89,
                "epoch": 200,
                "total_epochs": 200
            },
            "best_metrics": {
                "train_loss": 0.42,
                "val_loss": 0.48,
                "mAP_50": 0.94,
                "mAP_50_95": 0.81,
                "precision": 0.96,
                "recall": 0.91,
                "epoch": 175
            },
            "model_path": "data/outputs/job_completed_001/weights/best.pt",
            "weights_path": "data/outputs/job_completed_001/weights/last.pt",
            "logs_path": "data/outputs/job_completed_001/logs/",
            "error_message": None
        }
    ]
    
    # Salvar jobs no arquivo
    with open(jobs_file, 'w', encoding='utf-8') as f:
        json.dump(demo_jobs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(demo_jobs)} jobs de demonstração criados com sucesso!")
    print("📊 Jobs criados:")
    for job in demo_jobs:
        print(f"  - {job['name']} ({job['status']})")

if __name__ == "__main__":
    create_demo_jobs()