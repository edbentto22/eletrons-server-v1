# PRD - Sistema de Treinamento Ultralytics YOLO com FastAPI

## 1. VISÃO GERAL DO SISTEMA

### 1.1 Objetivo
Criar um servidor de treinamento standalone usando FastAPI + Ultralytics que:
- Receba requisições de treinamento do aplicativo principal via webhook
- Execute treinamento YOLO de forma assíncrona
- Forneça interface visual (UI) para monitorar progresso em tempo real
- Envie callbacks de progresso e conclusão de volta ao aplicativo
- Seja escalável e robusto para produção

### 1.2 Stack Tecnológica
- **Backend**: FastAPI (Python 3.11+)
- **ML Framework**: Ultralytics YOLO (versão 8.3.0+)
- **Deep Learning**: PyTorch 2.2.0+
- **UI Frontend**: HTML/CSS/JavaScript com SSE (Server-Sent Events)
- **Task Queue**: Worker dedicado (Celery/RQ/Arq) ou subprocesso; FastAPI apenas enfileira jobs
- **Storage**: Sistema de arquivos local + suporte para URLs assinadas
- **Deploy**: Docker + Gunicorn/Uvicorn

---

## 2. ARQUITETURA DO SISTEMA

### 2.1 Componentes Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                      APLICATIVO PRINCIPAL                        │
│  (React + Supabase Edge Functions)                              │
│                                                                  │
│  ┌──────────────────┐         ┌─────────────────────┐          │
│  │ useTrainingJobs  │────────▶│ train-yolo-model    │          │
│  │ (Frontend Hook)  │         │ (Edge Function)     │          │
│  └──────────────────┘         └──────────┬──────────┘          │
│                                           │                      │
└───────────────────────────────────────────┼──────────────────────┘
                                            │
                                            │ HTTP POST
                                            │ (Training Request)
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              SERVIDOR DE TREINAMENTO (FastAPI)                   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    API ENDPOINTS                        │    │
│  │  • POST   /api/v1/train         (Iniciar treinamento)  │    │
│  │  • GET    /api/v1/jobs/{id}     (Status do job)        │    │
│  │  • DELETE /api/v1/jobs/{id}     (Cancelar job)         │    │
│  │  • GET    /api/v1/jobs          (Listar todos jobs)    │    │
│  │  • GET    /health               (Health check)         │    │
│  │  • GET    /metrics              (Métricas Prometheus)  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                 WEB UI (Dashboard)                      │    │
│  │  • GET  /                       (Dashboard principal)  │    │
│  │  • GET  /jobs/{id}              (Detalhes do job)      │    │
│  │  • GET  /stream/progress/{id}   (SSE - Real-time)      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              TRAINING ENGINE                            │    │
│  │  • Job Queue Manager                                    │    │
│  │  • Dataset Downloader & Validator                      │    │
│  │  • YOLO Training Executor                               │    │
│  │  • Progress Tracker                                     │    │
│  │  • Callback Dispatcher                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ HTTP POST (Callbacks)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SUPABASE EDGE FUNCTIONS                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  webhook-ingest                                       │      │
│  │  • Recebe callbacks de progresso                     │      │
│  │  • Atualiza training_jobs table                      │      │
│  │  • Dispara notificações real-time                    │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. FLUXO DE DADOS DETALHADO

### 3.1 Fluxo de Início de Treinamento

```
1. Frontend (useTrainingJobs.createJob)
   │
   ├─▶ Cria registro na tabela training_jobs
   │   Status: "pending"
   │   Dados: dataset_id, model_name, hyperparameters
   │
   └─▶ Invoca Edge Function: train-yolo-model
       │
       └─▶ Edge Function:
           ├─▶ Busca job details da tabela
           ├─▶ Busca dataset da tabela datasets
           ├─▶ Gera signed URL do dataset (Supabase Storage)
           ├─▶ Atualiza job para status "training"
           │
           └─▶ Envia HTTP POST para Servidor FastAPI
               Endpoint: POST /api/v1/train
               
               Payload:
               {
                 "job_id": "uuid",
                 "callback_url": "https://[project].supabase.co/functions/v1/webhook-ingest",
                 "callback_secret": "secret_token",
                 "model_config": {
                   "name": "poste-detector-v1",
                   "base_model": "yolov8n.pt",
                   "epochs": 100,
                   "batch_size": 16,
                   "image_size": 640,
                   "learning_rate": 0.01
                 },
                 "dataset": {
                   "url": "https://[storage-url]/datasets/dataset.zip",
                   "format": "yolo"
                 }
               }
```

### 3.2 Fluxo de Treinamento no Servidor FastAPI

```
1. FastAPI recebe POST /api/v1/train
   │
   ├─▶ Valida payload
   ├─▶ Cria registro interno do job
   ├─▶ Retorna resposta imediata: 202 Accepted
   │   Response: { "job_id": "uuid", "status": "queued" }
   │
   └─▶ Enfileirar no Job Queue e um worker dedicado inicia:
       │
       ├─▶ FASE 1: Download do Dataset
       │   ├─▶ Download do ZIP da URL assinada
       │   ├─▶ Extração para /workdir/datasets/{job_id}/
       │   ├─▶ Validação do formato YOLO (data.yaml, images/, labels/)
       │   └─▶ Callback: training_progress (progress: 5%, status: "downloading")
       │
       ├─▶ FASE 2: Preparação do Modelo
       │   ├─▶ Download do base model (yolov8n.pt)
       │   ├─▶ Configuração dos hyperparameters
       │   ├─▶ Validação do data.yaml
       │   └─▶ Callback: training_progress (progress: 10%, status: "preparing")
       │
       ├─▶ FASE 3: Treinamento
       │   │
       │   └─▶ Loop de Épocas (1 a N):
       │       │
       │       ├─▶ Epoch Start
       │       │   └─▶ Callback: training_progress
       │       │       {
       │       │         "progress": (epoch/total) * 100,
       │       │         "current_epoch": epoch,
       │       │         "status": "training",
       │       │         "metrics": {
       │       │           "box_loss": 0.0234,
       │       │           "cls_loss": 0.0156,
       │       │           "dfl_loss": 0.0089,
       │       │           "precision": 0.876,
       │       │           "recall": 0.834,
       │       │           "mAP50": 0.891,
       │       │           "mAP50-95": 0.723
       │       │         },
       │       │         "eta_seconds": 3420
       │       │       }
       │       │
       │       └─▶ Epoch End
       │
       ├─▶ FASE 4: Validação Final
       │   ├─▶ Execução do validation set
       │   ├─▶ Geração de métricas finais
       │   └─▶ Callback: training_progress (progress: 95%, status: "validating")
       │
       └─▶ FASE 5: Conclusão
           ├─▶ Salvamento do modelo treinado: /workdir/models/{job_id}/best.pt
           ├─▶ Geração de artefatos (confusion matrix, PR curve, etc)
           ├─▶ Upload opcional para storage
           │
           └─▶ Callback: training_completed
               {
                 "job_id": "uuid",
                 "status": "completed",
                 "model_url": "https://[storage]/models/best.pt",
                 "metrics": {
                   "final_mAP50": 0.923,
                   "final_mAP50-95": 0.789,
                   "training_time_seconds": 3600,
                   "total_epochs": 100
                 },
                 "artifacts": {
                   "confusion_matrix": "url",
                   "pr_curve": "url",
                   "results_csv": "url"
                 }
               }
```

### 3.3 Fluxo de Callbacks para o Aplicativo

```
Servidor FastAPI
   │
   ├─▶ Envia HTTP POST para callback_url
   │   Headers:
   │     - Content-Type: application/json
   │     - X-Callback-Secret: [callback_secret]
   │     - X-Job-ID: [job_id]
   │
   │   Body: (ver seção 4.3)
   │
   └─▶ Edge Function: webhook-ingest
       │
       ├─▶ Valida secret
       ├─▶ Valida job_id
       │
       └─▶ Atualiza tabela training_jobs:
           ├─▶ progress
           ├─▶ current_epoch
           ├─▶ loss
           ├─▶ metrics (JSONB)
           ├─▶ status
           ├─▶ completed_at (se completed)
           └─▶ error_message (se failed)
```

---

## 4. ESPECIFICAÇÃO DE DADOS

### 4.1 Payload de Treinamento (App → Servidor)

**Endpoint**: `POST /api/v1/train`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "callback_url": "https://pdbqkhutwgtmgaudujwl.supabase.co/functions/v1/webhook-ingest",
  "callback_secret": "sk_live_abc123xyz789",
  
  "model_config": {
    "name": "poste-detector-v1",
    "base_model": "yolov8n.pt",
    "epochs": 100,
    "batch_size": 16,
    "image_size": 640,
    "learning_rate": 0.01,
    "optimizer": "AdamW",
    "augmentation": {
      "hsv_h": 0.015,
      "hsv_s": 0.7,
      "hsv_v": 0.4,
      "degrees": 10.0,
      "translate": 0.1,
      "scale": 0.5,
      "shear": 0.0,
      "perspective": 0.0,
      "flipud": 0.0,
      "fliplr": 0.5,
      "mosaic": 1.0,
      "mixup": 0.0
    }
  },
  
  "dataset": {
    "url": "https://pdbqkhutwgtmgaudujwl.supabase.co/storage/v1/object/sign/datasets/abc.zip?token=xyz",
    "format": "yolo",
    "expected_structure": {
      "data.yaml": true,
      "images/train": true,
      "images/val": true,
      "labels/train": true,
      "labels/val": true
    }
  },
  
  "resources": {
    "device": "cuda:0",
    "workers": 8,
    "max_memory_gb": 16
  }
}
```

**Response**: `202 Accepted`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Training job queued successfully",
  "estimated_start_time": "2025-01-20T10:30:00Z"
}
```

### 4.2 Callbacks de Progresso (Servidor → App)

**Endpoint**: `POST {callback_url}`

**Headers**:
```
Content-Type: application/json
X-Callback-Secret: sk_live_abc123xyz789
X-Job-ID: 550e8400-e29b-41d4-a716-446655440000
X-Callback-Type: training_progress | training_completed | training_failed
```

#### 4.2.1 Callback: training_progress

Enviado a cada época ou a cada 5% de progresso (o que ocorrer primeiro).

```json
{
  "type": "training_progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-20T10:35:42Z",
  
  "progress": {
    "percentage": 45.0,
    "current_epoch": 45,
    "total_epochs": 100,
    "phase": "training",
    "eta_seconds": 1980
  },
  
  "metrics": {
    "current": {
      "box_loss": 0.02347,
      "cls_loss": 0.01562,
      "dfl_loss": 0.00891,
      "precision": 0.8765,
      "recall": 0.8342,
      "mAP50": 0.8914,
      "mAP50-95": 0.7234
    },
    "best": {
      "mAP50": 0.8954,
      "mAP50-95": 0.7289,
      "epoch": 42
    }
  },
  
  "resources": {
    "gpu_utilization": 87.5,
    "memory_used_gb": 12.3,
    "temperature_c": 72
  }
}
```

#### 4.2.2 Callback: training_completed

Enviado quando o treinamento termina com sucesso.

```json
{
  "type": "training_completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-20T11:45:30Z",
  
  "status": "completed",
  "duration_seconds": 3600,
  
  "model": {
    "name": "poste-detector-v1",
    "download_url": "https://training-server.com/models/550e8400.pt",
    "size_mb": 45.2,
    "format": "pytorch",
    "expires_at": "2025-01-27T11:45:30Z"
  },
  
  "final_metrics": {
    "mAP50": 0.9234,
    "mAP50-95": 0.7891,
    "precision": 0.8876,
    "recall": 0.8523,
    "box_loss": 0.0187,
    "cls_loss": 0.0123,
    "dfl_loss": 0.0076,
    "best_epoch": 87,
    "total_epochs": 100
  },
  
  "artifacts": {
    "confusion_matrix": "https://training-server.com/artifacts/550e8400/confusion_matrix.png",
    "pr_curve": "https://training-server.com/artifacts/550e8400/pr_curve.png",
    "f1_curve": "https://training-server.com/artifacts/550e8400/f1_curve.png",
    "results_csv": "https://training-server.com/artifacts/550e8400/results.csv",
    "training_logs": "https://training-server.com/artifacts/550e8400/logs.txt"
  },
  
  "dataset_info": {
    "total_images": 1500,
    "train_images": 1200,
    "val_images": 300,
    "classes": ["poste", "transformador", "cabo"],
    "class_distribution": {
      "poste": 856,
      "transformador": 234,
      "cabo": 1122
    }
  }
}
```

#### 4.2.3 Callback: training_failed

Enviado quando o treinamento falha.

```json
{
  "type": "training_failed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-20T10:42:15Z",
  
  "status": "failed",
  "error": {
    "code": "DATASET_INVALID",
    "message": "Missing data.yaml file in dataset",
    "details": "The dataset archive does not contain a valid data.yaml configuration file. Please ensure your dataset follows the YOLO format.",
    "phase": "dataset_validation",
    "epoch": null
  },
  
  "partial_metrics": null
}
```

**Error Codes**:
- `DATASET_DOWNLOAD_FAILED`: Falha ao baixar dataset
- `DATASET_INVALID`: Dataset não está no formato correto
- `DATASET_CORRUPTED`: Arquivo ZIP corrompido
- `MODEL_DOWNLOAD_FAILED`: Falha ao baixar base model
- `INSUFFICIENT_MEMORY`: Memória insuficiente
- `TRAINING_DIVERGED`: Loss divergiu (NaN/Inf)
- `CANCELLED`: Treinamento cancelado pelo usuário
- `UNKNOWN_ERROR`: Erro inesperado

### 4.3 Formato da Tabela `training_jobs` (Supabase)

```sql
CREATE TABLE training_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users NOT NULL,
  dataset_id UUID REFERENCES datasets NOT NULL,
  
  -- Model Configuration
  model_name TEXT NOT NULL,
  base_model TEXT NOT NULL,
  epochs INTEGER NOT NULL,
  batch_size INTEGER NOT NULL,
  image_size INTEGER NOT NULL,
  learning_rate FLOAT NOT NULL,
  
  -- Status & Progress
  status TEXT NOT NULL CHECK (status IN ('pending', 'queued', 'training', 'completed', 'failed', 'cancelled')),
  progress FLOAT DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 100),
  current_epoch INTEGER,
  
  -- Metrics (stored as JSONB)
  loss FLOAT,
  metrics JSONB,
  
  -- Results
  model_url TEXT,
  error_message TEXT,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
);

-- Indexes
CREATE INDEX idx_training_jobs_user_id ON training_jobs(user_id);
CREATE INDEX idx_training_jobs_status ON training_jobs(status);
CREATE INDEX idx_training_jobs_created_at ON training_jobs(created_at DESC);

-- Enable RLS
ALTER TABLE training_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own jobs"
  ON training_jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own jobs"
  ON training_jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Real-time
ALTER TABLE training_jobs REPLICA IDENTITY FULL;
ALTER PUBLICATION supabase_realtime ADD TABLE training_jobs;
```

---

## 5. INTERFACE DO SERVIDOR (WEB UI)

### 5.1 Dashboard Principal (`GET /`)

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  🎯 YOLO Training Server                    [Health: ●]     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ Active Jobs  │ Queued Jobs  │ Completed    │  Failed  │ │
│  │     2        │     3        │    127       │    8     │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
│                                                              │
│  🔥 Active Training Jobs                     [Refresh: 5s]  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Job: poste-detector-v1          [●] Training           │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░ 65% (Epoch 65/100)   │ │
│  │ mAP50: 0.891 | Loss: 0.023 | ETA: 22m                  │ │
│  │ [View Details]                                          │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ Job: cabo-detector-v2           [●] Training           │ │
│  │ ━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░ 18% (Epoch 18/100)   │ │
│  │ mAP50: 0.723 | Loss: 0.045 | ETA: 1h 15m              │ │
│  │ [View Details]                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⏳ Queued Jobs                                             │
│  • transformador-v3 (waiting for GPU)                       │
│  • multi-class-v1 (position: #2)                           │
│  • defect-detector (position: #3)                          │
│                                                              │
│  📈 System Resources                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ GPU: NVIDIA RTX 4090                                   │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 87%  (Temp: 72°C)    │ │
│  │ Memory: 12.3 / 24.0 GB (51%)                           │ │
│  │ CPU: 45% | RAM: 28.4 / 64.0 GB                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Tecnologias**:
- HTML5 + CSS3 (Tailwind ou Bootstrap)
- JavaScript Vanilla ou Alpine.js
- Chart.js para gráficos
- Server-Sent Events (SSE) para updates real-time

### 5.2 Página de Detalhes do Job (`GET /jobs/{job_id}`)

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                         │
├─────────────────────────────────────────────────────────────┤
│  Job: poste-detector-v1                                      │
│  ID: 550e8400-e29b-41d4-a716-446655440000                   │
│  Status: [●] Training                                        │
│                                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━░░░ 65% Complete             │
│                                                              │
│  📊 Training Progress                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Current Epoch: 65 / 100                                │ │
│  │ Elapsed Time: 38m 24s                                  │ │
│  │ Estimated Remaining: 22m 18s                           │ │
│  │ Start Time: 2025-01-20 10:30:15                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📈 Live Metrics                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │    mAP50 Progress                                       │ │
│  │  1.0 ┤                                          ╭──     │ │
│  │      │                                    ╭────╯        │ │
│  │  0.5 │                          ╭────────╯              │ │
│  │      │                ╭────────╯                        │ │
│  │  0.0 └────────────────┴────────────────────────▶       │ │
│  │       0    20    40    60    80   100  Epoch           │ │
│  │                                                         │ │
│  │  Current Metrics:                                       │ │
│  │  • mAP50: 0.891  • mAP50-95: 0.723                     │ │
│  │  • Precision: 0.876  • Recall: 0.834                   │ │
│  │  • Box Loss: 0.023  • Cls Loss: 0.016                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⚙️ Configuration                                           │
│  Base Model: yolov8n.pt                                     │
│  Image Size: 640px                                          │
│  Batch Size: 16                                             │
│  Learning Rate: 0.01                                        │
│  Optimizer: AdamW                                           │
│                                                              │
│  📦 Dataset Info                                            │
│  Total Images: 1500 (Train: 1200, Val: 300)                │
│  Classes: poste, transformador, cabo                        │
│                                                              │
│  🎬 Actions                                                 │
│  [Cancel Training]  [Download Logs]  [View in App]         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Endpoint SSE para Real-Time Updates

**Endpoint**: `GET /stream/progress/{job_id}`

**Response**: `text/event-stream`

```
event: progress
data: {"epoch": 65, "progress": 65.0, "mAP50": 0.891, "loss": 0.023, "eta_seconds": 1338}

event: progress
data: {"epoch": 66, "progress": 66.0, "mAP50": 0.894, "loss": 0.022, "eta_seconds": 1284}

event: completed
data: {"status": "completed", "final_mAP50": 0.923, "model_url": "https://..."}

event: heartbeat
data: {"timestamp": "2025-01-20T10:45:30Z"}
```

**Client-Side JavaScript**:
```javascript
const eventSource = new EventSource(`/stream/progress/${jobId}`);

eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.progress);
  updateMetrics(data);
  updateETA(data.eta_seconds);
});

eventSource.addEventListener('completed', (event) => {
  const data = JSON.parse(event.data);
  showCompletionNotification(data);
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  console.error('SSE error:', event);
  eventSource.close();
});
```

---

## 6. ESTRUTURA DO PROJETO (FastAPI Server)

```
training-server/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── training.py     # Training endpoints
│   │   │   │   ├── jobs.py         # Job management endpoints
│   │   │   │   ├── health.py       # Health check
│   │   │   │   └── metrics.py      # Prometheus metrics
│   │   │   └── router.py
│   │   └── deps.py                 # Dependencies
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings & environment
│   │   ├── security.py             # Auth & secrets validation
│   │   └── logging.py              # Logging configuration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── training.py             # Pydantic models for training
│   │   ├── callbacks.py            # Callback payload models
│   │   └── responses.py            # API response models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── training_service.py     # Core training logic
│   │   ├── dataset_service.py      # Dataset download/validation
│   │   ├── callback_service.py     # Callback dispatching
│   │   ├── storage_service.py      # Model storage/upload
│   │   └── monitoring_service.py   # Resource monitoring
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── executor.py             # YOLO training executor
│   │   ├── callbacks.py            # YOLO training callbacks
│   │   └── validators.py           # Dataset validators
│   │
│   ├── queue/
│   │   ├── __init__.py
│   │   ├── manager.py              # Job queue manager
│   │   └── worker.py               # Background worker
│   │
│   └── ui/
│       ├── __init__.py
│       ├── routes.py               # UI routes
│       ├── templates/
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   └── job_detail.html
│       └── static/
│           ├── css/
│           │   └── styles.css
│           ├── js/
│           │   ├── dashboard.js
│           │   └── job_detail.js
│           └── images/
│
├── workdir/                         # Working directory
│   ├── datasets/                    # Downloaded datasets
│   ├── models/                      # Trained models
│   └── runs/                        # Training runs (logs, artifacts)
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_training.py
│   └── test_callbacks.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── deploy.sh
```

---

## 7. ENDPOINTS DA API (Detalhado)

### 7.1 POST /api/v1/train

**Descrição**: Inicia um novo job de treinamento

**Request**:
```json
{
  "job_id": "uuid",
  "callback_url": "https://...",
  "callback_secret": "secret",
  "model_config": { ... },
  "dataset": { ... }
}
```

**Response**: `202 Accepted`
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Training job queued successfully",
  "estimated_start_time": "ISO8601"
}
```

**Errors**:
- `400`: Invalid payload
- `409`: Job ID already exists
- `503`: Service unavailable (queue full)

### 7.2 GET /api/v1/jobs/{job_id}

**Descrição**: Obtém status e detalhes de um job

**Response**: `200 OK`
```json
{
  "job_id": "uuid",
  "status": "training",
  "progress": 65.0,
  "current_epoch": 65,
  "total_epochs": 100,
  "metrics": { ... },
  "created_at": "ISO8601",
  "started_at": "ISO8601",
  "eta_seconds": 1338
}
```

**Errors**:
- `404`: Job not found

### 7.3 DELETE /api/v1/jobs/{job_id}

**Descrição**: Cancela um job em andamento

**Response**: `200 OK`
```json
{
  "job_id": "uuid",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Errors**:
- `404`: Job not found
- `409`: Job already completed/failed

### 7.4 GET /api/v1/jobs

**Descrição**: Lista todos os jobs

**Query Params**:
- `status`: Filtrar por status (opcional)
- `limit`: Limite de resultados (default: 50)
- `offset`: Offset para paginação (default: 0)

**Response**: `200 OK`
```json
{
  "total": 138,
  "jobs": [
    {
      "job_id": "uuid",
      "model_name": "poste-detector-v1",
      "status": "training",
      "progress": 65.0,
      "created_at": "ISO8601"
    }
  ]
}
```

### 7.5 GET /health

**Descrição**: Health check do servidor

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "ISO8601",
  "version": "1.0.0",
  "gpu_available": true,
  "active_jobs": 2,
  "queue_size": 3
}
```

### 7.6 GET /metrics

**Descrição**: Métricas Prometheus

**Response**: `200 OK` (text/plain)
```
# HELP training_jobs_total Total number of training jobs
# TYPE training_jobs_total counter
training_jobs_total{status="completed"} 127
training_jobs_total{status="failed"} 8
training_jobs_total{status="training"} 2

# HELP gpu_utilization_percent GPU utilization percentage
# TYPE gpu_utilization_percent gauge
gpu_utilization_percent{device="cuda:0"} 87.5
```

---

## 8. INTEGRAÇÃO COM O APLICATIVO EXISTENTE

### 8.1 Modificações Necessárias

#### 8.1.1 Edge Function: `train-yolo-model/index.ts`

**Mudanças**:
1. Trocar `TRAINING_WEBHOOK_URL` por `TRAINING_API_URL`
2. Adicionar `TRAINING_API_SECRET` como secret
3. Enviar payload no formato especificado (seção 4.1)
4. Remover lógica de simulação

```typescript
// Exemplo de código atualizado
const trainingApiUrl = Deno.env.get('TRAINING_API_URL');
const trainingApiSecret = Deno.env.get('TRAINING_API_SECRET');

if (!trainingApiUrl) {
  throw new Error('TRAINING_API_URL not configured');
}

const trainingPayload = {
  job_id: jobId,
  callback_url: `${supabaseUrl}/functions/v1/webhook-ingest`,
  callback_secret: callbackSecret,
  model_config: {
    name: jobData.model_name,
    base_model: jobData.base_model,
    epochs: jobData.epochs,
    batch_size: jobData.batch_size,
    image_size: jobData.image_size,
    learning_rate: jobData.learning_rate,
  },
  dataset: {
    url: datasetUrl,
    format: 'yolo',
  },
};

const response = await fetch(`${trainingApiUrl}/api/v1/train`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${trainingApiSecret}`,
  },
  body: JSON.stringify(trainingPayload),
});
```

#### 8.1.2 Edge Function: `webhook-ingest/index.ts`

**Mudanças**:
1. Validar header `X-Callback-Secret`
2. Processar callbacks de acordo com tipos (seção 4.2)
3. Atualizar `training_jobs` table com dados corretos

```typescript
const callbackType = req.headers.get('X-Callback-Type');
const callbackSecret = req.headers.get('X-Callback-Secret');
const jobId = req.headers.get('X-Job-ID');

// Validate secret
const expectedSecret = Deno.env.get('TRAINING_CALLBACK_SECRET');
if (callbackSecret !== expectedSecret) {
  return new Response('Unauthorized', { status: 401 });
}

const payload = await req.json();

switch (callbackType) {
  case 'training_progress':
    await supabase
      .from('training_jobs')
      .update({
        progress: payload.progress.percentage,
        current_epoch: payload.progress.current_epoch,
        metrics: payload.metrics,
        updated_at: new Date().toISOString(),
      })
      .eq('id', jobId);
    break;
    
  case 'training_completed':
    await supabase
      .from('training_jobs')
      .update({
        status: 'completed',
        progress: 100,
        metrics: payload.final_metrics,
        model_url: payload.model.download_url,
        completed_at: new Date().toISOString(),
      })
      .eq('id', jobId);
    break;
    
  case 'training_failed':
    await supabase
      .from('training_jobs')
      .update({
        status: 'failed',
        error_message: payload.error.message,
        updated_at: new Date().toISOString(),
      })
      .eq('id', jobId);
    break;
}
```

#### 8.1.3 Frontend: `src/pages/Training.tsx`

**Mudanças**:
1. Adicionar exibição de métricas em tempo real (mAP50, Loss, etc)
2. Adicionar botão para abrir UI do servidor de treinamento
3. Melhorar visualização de progresso com gráficos

```tsx
// Adicionar link para UI do servidor
<Button
  variant="outline"
  onClick={() => window.open(`${trainingServerUrl}/jobs/${job.id}`, '_blank')}
>
  <ExternalLink className="w-4 h-4 mr-2" />
  Ver no Servidor
</Button>

// Exibir métricas detalhadas
{job.metrics && (
  <div className="grid grid-cols-2 gap-4 mt-4">
    <div>
      <Label>mAP50</Label>
      <Progress value={job.metrics.current?.mAP50 * 100} />
      <span className="text-sm">{(job.metrics.current?.mAP50 * 100).toFixed(1)}%</span>
    </div>
    <div>
      <Label>Loss</Label>
      <span className="text-sm">{job.metrics.current?.box_loss?.toFixed(4)}</span>
    </div>
  </div>
)}
```

### 8.2 Variáveis de Ambiente

**Supabase (Edge Functions)**:
```env
TRAINING_API_URL=https://training.seu-dominio.com
TRAINING_API_SECRET=sk_live_abc123xyz789
TRAINING_CALLBACK_SECRET=callback_secret_xyz789
```

**React App (.env)**:
```env
VITE_TRAINING_SERVER_URL=https://training.seu-dominio.com
```

---

## 9. DEPLOY E PRODUÇÃO

### 9.1 Dockerfile

```dockerfile
# Base com CUDA e cuDNN compatível com PyTorch 2.2.0
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Instala dependências do sistema necessárias (OpenCV etc.)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requisitos e instala libs Python
COPY requirements.txt .
# Observação: a imagem já contém torch/torchvision com CUDA.
# Manter versões compatíveis no requirements.
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY app/ ./app/

# Diretórios de trabalho
RUN mkdir -p /app/workdir/datasets /app/workdir/models /app/workdir/runs

# Porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Executa com Uvicorn (um worker recomendado para acesso exclusivo à GPU)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 9.2 docker-compose.yml

```yaml
version: '3.8'

services:
  training-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - API_SECRET=${API_SECRET}
      - CALLBACK_SECRET=${CALLBACK_SECRET}
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    volumes:
      - ./workdir:/app/workdir
      - /dev/shm:/dev/shm  # Shared memory for PyTorch
    runtime: nvidia
    restart: unless-stopped
```

### 9.3 Opções de Deploy

#### 9.3.1 Railway
- **Prós**: Fácil deploy com GPU, CI/CD automático
- **Contras**: Custo mais alto para GPU
- **Setup**: Connect GitHub → Deploy → Adicionar variáveis de ambiente

#### 9.3.2 Modal
- **Prós**: GPU sob demanda, paga apenas pelo uso
- **Contras**: Requer adaptação do código
- **Setup**: Usar `@app.function(gpu="A100")` decorators

#### 9.3.3 RunPod
- **Prós**: GPUs baratas, bom para treinos longos
- **Contras**: Setup mais manual
- **Setup**: Template Docker → Deploy → Configure network

#### 9.3.4 Cloud VM (GCP/AWS/Azure)
- **Prós**: Controle total, customizável
- **Contras**: Gerenciamento de infraestrutura
- **Setup**: Provisionar VM com GPU → Docker → Nginx reverse proxy

---

## 10. MONITORAMENTO E LOGS

### 10.1 Logging Structure

```python
import logging

logger = logging.getLogger(__name__)

# Durante treinamento
logger.info(f"Job {job_id}: Starting epoch {epoch}/{total_epochs}")
logger.info(f"Job {job_id}: mAP50={map50:.3f}, Loss={loss:.4f}")
logger.warning(f"Job {job_id}: GPU temperature high: {temp}°C")
logger.error(f"Job {job_id}: Training failed: {error}")
```

### 10.2 Métricas Prometheus

**Métricas para coletar**:
- `training_jobs_total{status}`: Total de jobs por status
- `training_duration_seconds`: Tempo de treinamento
- `gpu_utilization_percent`: Uso da GPU
- `gpu_memory_used_bytes`: Memória GPU usada
- `gpu_temperature_celsius`: Temperatura da GPU
- `active_training_jobs`: Jobs ativos no momento
- `queue_size`: Tamanho da fila

### 10.3 Alertas

**Configurar alertas para**:
- GPU temperatura > 85°C
- Training job > 12 horas
- Loss = NaN ou Inf
- Memória GPU > 95%
- Fila > 10 jobs

---

## 11. TESTES

### 11.1 Testes de API

```python
def test_create_training_job():
    response = client.post("/api/v1/train", json={
        "job_id": "test-job-id",
        "callback_url": "https://example.com/callback",
        "callback_secret": "secret",
        "model_config": { ... },
        "dataset": { ... }
    })
    assert response.status_code == 202
    assert response.json()["status"] == "queued"

def test_get_job_status():
    response = client.get("/api/v1/jobs/test-job-id")
    assert response.status_code == 200
    assert "progress" in response.json()
```

### 11.2 Testes de Treinamento

```python
def test_dataset_validation():
    validator = DatasetValidator()
    result = validator.validate("/path/to/dataset")
    assert result.is_valid
    assert result.num_images > 0

def test_training_callback():
    callback_service = CallbackService()
    result = callback_service.send_progress(job_id, progress_data)
    assert result.success
```

---

## 12. CRONOGRAMA DE IMPLEMENTAÇÃO

### Fase 1: Setup Básico (1 semana)
- [ ] Estrutura do projeto FastAPI
- [ ] Endpoints básicos (/train, /jobs/{id}, /health)
- [ ] Download e validação de dataset
- [ ] Integração com Ultralytics YOLO

### Fase 2: Callbacks e Monitoramento (1 semana)
- [ ] Sistema de callbacks HTTP
- [ ] Tracking de progresso
- [ ] Métricas e logging
- [ ] Tratamento de erros

### Fase 3: UI Web (1 semana)
- [ ] Dashboard principal
- [ ] Página de detalhes do job
- [ ] SSE para real-time updates
- [ ] Gráficos de métricas

### Fase 4: Integração com App (1 semana)
- [ ] Atualizar edge functions
- [ ] Atualizar frontend React
- [ ] Testes end-to-end
- [ ] Documentação

### Fase 5: Deploy e Produção (1 semana)
- [ ] Dockerfile e docker-compose
- [ ] Deploy em ambiente de produção
- [ ] Configuração de monitoramento
- [ ] Testes de carga

**Total: 5 semanas**

---

## 13. SEGURANÇA

### 13.1 Autenticação e Autorização

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != os.getenv("API_SECRET"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials
```

### 13.2 Validação de Callbacks

```python
def verify_callback_secret(secret: str, job_id: str) -> bool:
    expected_secret = os.getenv("CALLBACK_SECRET")
    return secrets.compare_digest(secret, expected_secret)
```

### 13.3 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/train")
@limiter.limit("10/minute")
async def create_training_job(request: Request, ...):
    ...
```

---

## 14. TROUBLESHOOTING

### 14.1 Problemas Comuns

**Dataset download failed**:
- Verificar se URL está válida e não expirou
- Verificar conectividade de rede
- Verificar espaço em disco

**Training diverged (NaN loss)**:
- Reduzir learning rate
- Verificar qualidade do dataset
- Aumentar batch size

**GPU out of memory**:
- Reduzir batch size
- Reduzir image size
- Usar gradient checkpointing

**Callback failed**:
- Verificar se callback_url está acessível
- Verificar se callback_secret está correto
- Verificar logs do edge function

---

## 15. PRÓXIMOS PASSOS

1. **Revisar este PRD** com a equipe técnica
2. **Validar requisitos** com stakeholders
3. **Criar protótipo** da UI web
4. **Definir infraestrutura** de deploy
5. **Iniciar implementação** seguindo cronograma

---

## 16. CONTATOS E RECURSOS

**Documentação**:
- Ultralytics YOLO: https://docs.ultralytics.com/
- FastAPI: https://fastapi.tiangolo.com/
- PyTorch: https://pytorch.org/docs/

**Suporte**:
- Email: suporte@seu-dominio.com
- Slack: #training-server
- GitHub: https://github.com/seu-org/training-server

---

## APÊNDICE A: Exemplo de requirements.txt

```txt
# Web Framework
fastapi==0.108.0
uvicorn[standard]==0.25.0
gunicorn==21.2.0

# YOLO e Deep Learning
ultralytics==8.3.0
# torch/torchvision com CUDA já vêm na imagem base (pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime)
# Se precisar instalar via pip, use os pacotes com sufixo +cu121 a partir do índice oficial:
# torch==2.2.0+cu121 ; torchvision==0.17.0+cu121

# Utilities
requests==2.31.0
Pillow==10.2.0
opencv-python-headless==4.9.0.80
pyyaml==6.0.1
numpy>=1.24.0

# API & Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Monitoring
prometheus-client==0.19.0
nvidia-ml-py3==7.352.0
psutil==5.9.8

# Rate Limiting
slowapi==0.1.9

# Templating (for UI)
jinja2==3.1.2

# Async
httpx==0.26.0
aiofiles==23.2.1
```

---

## 17. Correções e Atualizações (v1.1)

### 17.1 GPU e Base de Container
- Dockerfile atualizado para imagem com CUDA/cuDNN (pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime).
- requirements.txt atualizado para coleta de métricas GPU (nvidia-ml-py3) e sistema (psutil).
- Observação: se optar por instalar torch via pip, use pacotes +cu121 e índice oficial da PyTorch.

### 17.2 Docker Compose com GPU
- Troca de `deploy.resources` (Swarm-only) por `runtime: nvidia` e variáveis `NVIDIA_*` para ambientes locais.
- Alternativa (Compose v2 com nvidia-container-toolkit):
```yaml
services:
  training-server:
    build: .
    device_requests:
      - capabilities: ["gpu"]
```

### 17.3 Arquitetura de Execução
- FastAPI não executa treinos diretamente em background task do request.
- Jobs são enfileirados e executados por um worker dedicado (processo separado), garantindo resiliência, cancelamento real e não bloqueio da API.

### 17.4 Cancelamento de Treino
- `DELETE /api/v1/jobs/{job_id}` deve:
  - Marcar o job como `cancelled`.
  - Disparar token/sinal de cancelamento para o executor (via shared state/IPC ou encerramento controlado de subprocesso).
  - Registrar logs e estado parcial, se disponível.

### 17.5 Índices SQL
- Correção da sintaxe de índices para Postgres usando `CREATE INDEX` pós `CREATE TABLE`.

### 17.6 Callbacks e Secrets
- O servidor deve assinar callbacks com o `callback_secret` fornecido no payload do job.
- A Edge Function valida contra seu `TRAINING_CALLBACK_SECRET` esperado.

### 17.7 CORS e SSE
- Habilitar CORS para o domínio do app principal.
- Implementar reconexão automática no cliente SSE:
```javascript
function connectSSE(jobId) {
  let retries = 0;
  const maxRetries = 10;
  const baseDelay = 1000;
  function open() {
    const es = new EventSource(`/stream/progress/${jobId}`, { withCredentials: false });
    es.addEventListener('progress', (e) => { /* update UI */ });
    es.addEventListener('completed', (e) => es.close());
    es.onerror = () => {
      es.close();
      if (retries < maxRetries) {
        const delay = Math.min(baseDelay * 2 ** retries, 30000);
        setTimeout(open, delay);
        retries++;
      }
    };
  }
  open();
}
```

### 17.8 Limites de Recursos
- `resources.max_memory_gb`: comportamento documentado como best-effort.
- Estratégias: reduzir batch/imgsz automaticamente; emitir alertas e cancelar se ultrapassar limite seguro.

---

**FIM DO PRD**
