#!/usr/bin/env python3
"""
Script para criar um job de treinamento customizado
usando o dataset projeto-classe-excluded preparado
"""

import requests
import json
from datetime import datetime

# Configurações da API
API_BASE_URL = "http://localhost:8060"
API_SECRET = "v63ilgo6j41o7xn75c"

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {API_SECRET}",
    "Content-Type": "application/json"
}

def create_training_job():
    """Cria um novo job de treinamento para o dataset customizado"""
    
    # Configuração do job no formato correto (JobCreateRequest)
    job_config = {
        "name": "Treinamento Infraestrutura Elétrica - Projeto Classe Excluded",
        "dataset_path": "/Volumes/SSD NVME - Backup/TRAINING SYSTEM YOLO/datasets/projeto-classe-excluded/data.yaml",
        "config": {
            "base_model": "yolov8n.pt",
            "epochs": 100,
            "batch_size": 16,
            "image_size": 640,
            "learning_rate": 0.01,
            "optimizer": "AdamW",
            "device": "0",  # GPU 0 ou "cpu" se não tiver GPU
            "workers": 4,
            "patience": 20,
            "save_period": 10,
            "augment": True,
            "mosaic": 1.0,
            "mixup": 0.0,
            "copy_paste": 0.0
        }
    }
    
    print("🚀 Criando job de treinamento...")
    print(f"📊 Dataset: projeto-classe-excluded")
    print(f"📊 Caminho: {job_config['dataset_path']}")
    print(f"⚙️  Modelo base: {job_config['config']['base_model']}")
    print(f"⚙️  Épocas: {job_config['config']['epochs']}")
    print(f"⚙️  Batch size: {job_config['config']['batch_size']}")
    
    try:
        # Fazer requisição para criar o job
        response = requests.post(
            f"{API_BASE_URL}/training/start",
            headers=headers,
            json=job_config,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Job criado com sucesso!")
            print(f"📋 Job ID: {result.get('job_id', 'N/A')}")
            print(f"📋 Status: {result.get('status', 'N/A')}")
            return result
        else:
            print(f"❌ Erro ao criar job: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def list_jobs():
    """Lista todos os jobs existentes"""
    
    print("\n📋 Listando jobs existentes...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"📊 Total de jobs: {len(jobs)}")
            
            for i, job in enumerate(jobs, 1):
                print(f"\n{i}. {job.get('name', 'Sem nome')}")
                print(f"   ID: {job.get('id', 'N/A')}")
                print(f"   Status: {job.get('status', 'N/A')}")
                print(f"   Criado em: {job.get('created_at', 'N/A')}")
                
                if job.get('dataset'):
                    dataset = job['dataset']
                    print(f"   Dataset: {dataset.get('name', 'N/A')}")
                    
        else:
            print(f"❌ Erro ao listar jobs: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    """Função principal"""
    
    print("=" * 60)
    print("🎯 CRIAÇÃO DE JOB DE TREINAMENTO CUSTOMIZADO")
    print("=" * 60)
    
    # Listar jobs existentes primeiro
    list_jobs()
    
    # Criar novo job
    result = create_training_job()
    
    if result:
        print("\n" + "=" * 60)
        print("✅ JOB CRIADO COM SUCESSO!")
        print("=" * 60)
        print("🌐 Acesse o dashboard em: http://localhost:3002")
        print("📊 Para monitorar o progresso do treinamento")
        
        # Listar jobs novamente para mostrar o novo job
        list_jobs()
    else:
        print("\n" + "=" * 60)
        print("❌ FALHA AO CRIAR JOB")
        print("=" * 60)
        print("🔧 Verifique se o backend está rodando em http://localhost:8060")
        print("🔧 Verifique se o dataset está no caminho correto")

if __name__ == "__main__":
    main()