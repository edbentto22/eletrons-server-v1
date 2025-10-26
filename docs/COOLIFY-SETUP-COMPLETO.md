# 🚀 Guia Completo de Deploy no Coolify - Sistema de Treinamento YOLO

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Ambiente](#preparação-do-ambiente)
3. [Configuração no Coolify](#configuração-no-coolify)
4. [Variáveis de Ambiente](#variáveis-de-ambiente)
5. [Volumes e Persistência](#volumes-e-persistência)
6. [Configuração de Rede](#configuração-de-rede)
7. [Monitoramento e Logs](#monitoramento-e-logs)
8. [Troubleshooting](#troubleshooting)
9. [Otimizações de Performance](#otimizações-de-performance)
10. [Backup e Recuperação](#backup-e-recuperação)

---

## 🔧 Pré-requisitos

### Servidor Coolify
- **Coolify v4+** instalado e funcionando
- **Docker** e **Docker Compose** configurados
- **Mínimo 8GB RAM** (16GB recomendado para GPU)
- **50GB+ de espaço em disco** para datasets e modelos
- **GPU NVIDIA** (opcional, mas recomendado para treinamento)

### Repositório
- Repositório Git com o código: `https://github.com/edbentto22/eletrons-server-v1.git`
- Branch: `main`
- Docker Compose file: `docker-compose.coolify.yml`

---

## 🛠️ Preparação do Ambiente

### 1. Estrutura de Diretórios no Servidor

```bash
# Criar diretórios no servidor Coolify
sudo mkdir -p /data/yolo-training/{data,logs,models,datasets,temp}
sudo chown -R 1000:1000 /data/yolo-training/
sudo chmod -R 755 /data/yolo-training/
```

### 2. Configuração de GPU (se disponível)

```bash
# Instalar NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## ⚙️ Configuração no Coolify

### 1. Criar Novo Projeto

1. **Acesse o painel do Coolify**
2. **New Project** → **Docker Compose**
3. **Repository**: `https://github.com/edbentto22/eletrons-server-v1.git`
4. **Branch**: `main`
5. **Docker Compose File**: `docker-compose.coolify.yml`

### 2. Configuração Básica

```yaml
# Configurações no painel Coolify
Name: YOLO Training System
Description: Sistema completo de treinamento YOLO com Ultralytics
Environment: production
```

---

## 🔐 Variáveis de Ambiente

### Configuração no Painel Coolify

#### **Servidor e Segurança**
```bash
# Servidor
HOST=0.0.0.0
PORT=8060
DEBUG=false
LOG_LEVEL=info

# Segurança (OBRIGATÓRIO)
API_SECRET=seu_token_super_secreto_aqui_min_32_chars_2025
CALLBACK_SECRET=callback_secret_super_seguro_2025
ALLOWED_ORIGINS=["https://seu-dominio.com","https://api.seu-dominio.com"]
```

#### **URLs e Endpoints**
```bash
# URLs (substitua pelos seus domínios)
BACKEND_URL=https://api.seu-dominio.com
FRONTEND_URL=https://seu-dominio.com
WEBSOCKET_URL=wss://api.seu-dominio.com
```

#### **YOLO e Ultralytics**
```bash
# Configurações padrão do YOLO
DEFAULT_MODEL=yolov8n.pt
DEFAULT_EPOCHS=100
DEFAULT_BATCH_SIZE=16
DEFAULT_IMAGE_SIZE=640
DEFAULT_LEARNING_RATE=0.01
DEFAULT_OPTIMIZER=AdamW
```

#### **Sistema e Performance**
```bash
# Limites do sistema
MAX_CONCURRENT_JOBS=3
SYSTEM_MONITOR_INTERVAL=5
JOB_UPDATE_INTERVAL=2
CLEANUP_INTERVAL=3600

# Recursos
MEMORY_LIMIT=4G
CPU_LIMIT=2.0
MEMORY_RESERVATION=2G
CPU_RESERVATION=1.0
```

#### **GPU (se disponível)**
```bash
# Configuração GPU
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6"
```

#### **Redis (opcional)**
```bash
# Cache Redis
REDIS_PASSWORD=yolo_redis_password_2025
REDIS_URL=redis://redis:6379
```

#### **Caminhos de Dados**
```bash
# Diretórios persistentes
DATA_PATH=/data/yolo-training/data
LOGS_PATH=/data/yolo-training/logs
MODELS_PATH=/data/yolo-training/models
```

---

## 💾 Volumes e Persistência

### Configuração de Volumes no Coolify

```yaml
# Volumes persistentes (configurar no painel)
Volumes:
  - Name: yolo_data
    Host Path: /data/yolo-training/data
    Container Path: /app/data
    
  - Name: yolo_logs
    Host Path: /data/yolo-training/logs
    Container Path: /app/logs
    
  - Name: yolo_models
    Host Path: /data/yolo-training/models
    Container Path: /app/models
```

### Estrutura de Diretórios

```
/data/yolo-training/
├── data/
│   ├── datasets/          # Datasets para treinamento
│   ├── checkpoints/       # Checkpoints dos modelos
│   ├── jobs/             # Dados dos jobs
│   └── temp/             # Arquivos temporários
├── logs/                 # Logs do sistema
│   ├── app.log
│   ├── training.log
│   └── system.log
└── models/               # Modelos treinados
    ├── yolov8n.pt
    ├── custom_models/
    └── exports/
```

---

## 🌐 Configuração de Rede

### Domínios e SSL

1. **Backend API**: `api.seu-dominio.com` → Porta 8060
2. **Frontend Web**: `seu-dominio.com` → Porta 3000
3. **Redis** (interno): `redis` → Porta 6379

### Configuração no Coolify

```yaml
# Configurar domínios no painel
Services:
  yolo-backend:
    Domain: api.seu-dominio.com
    Port: 8060
    SSL: Enabled (Let's Encrypt)
    
  yolo-frontend:
    Domain: seu-dominio.com
    Port: 3000
    SSL: Enabled (Let's Encrypt)
```

---

## 📊 Monitoramento e Logs

### Health Checks

```yaml
# Health checks configurados automaticamente
Backend:
  - Endpoint: /health
  - Interval: 30s
  - Timeout: 15s
  - Retries: 5

Frontend:
  - Endpoint: /health
  - Interval: 30s
  - Timeout: 10s
  - Retries: 3
```

### Logs

```bash
# Visualizar logs no Coolify
# Ou via comando no servidor:
docker logs yolo-training-backend -f
docker logs yolo-training-frontend -f
```

### Métricas

- **CPU e Memória**: Monitorados pelo Coolify
- **GPU**: Logs internos do sistema
- **Jobs**: Dashboard web em tempo real
- **API**: Métricas via FastAPI

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. **Falha na Autenticação**
```bash
# Verificar API_SECRET
curl -H "Authorization: Bearer SEU_API_SECRET" https://api.seu-dominio.com/health
```

#### 2. **Erro de Permissões**
```bash
# Corrigir permissões
sudo chown -R 1000:1000 /data/yolo-training/
sudo chmod -R 755 /data/yolo-training/
```

#### 3. **Falta de Memória**
```bash
# Verificar recursos
docker stats
# Ajustar MEMORY_LIMIT e CPU_LIMIT
```

#### 4. **GPU não detectada**
```bash
# Verificar GPU
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

#### 5. **Falha no Build**
```bash
# Limpar cache Docker
docker system prune -a
# Rebuild no Coolify
```

### Logs de Debug

```bash
# Ativar debug temporariamente
DEBUG=true
LOG_LEVEL=debug
```

---

## ⚡ Otimizações de Performance

### 1. **Configuração de GPU**

```bash
# Para múltiplas GPUs
CUDA_VISIBLE_DEVICES=0,1
MAX_CONCURRENT_JOBS=2
```

### 2. **Otimização de Memória**

```bash
# Ajustar batch size baseado na GPU
DEFAULT_BATCH_SIZE=32  # Para GPU com 8GB+
DEFAULT_BATCH_SIZE=16  # Para GPU com 4-8GB
DEFAULT_BATCH_SIZE=8   # Para GPU com <4GB
```

### 3. **Cache e Redis**

```bash
# Ativar Redis para cache
REDIS_PASSWORD=senha_forte_aqui
# Configurar TTL para cache
CACHE_TTL=3600
```

### 4. **Limpeza Automática**

```bash
# Limpeza de arquivos temporários
CLEANUP_INTERVAL=1800  # 30 minutos
AUTO_CLEANUP=true
```

---

## 💾 Backup e Recuperação

### 1. **Backup Automático**

```bash
#!/bin/bash
# Script de backup (executar via cron)
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/yolo-training"

# Backup dos dados
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /data/yolo-training/data/
tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" /data/yolo-training/models/

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 2. **Restauração**

```bash
# Parar serviços
docker-compose -f docker-compose.coolify.yml down

# Restaurar dados
tar -xzf backup_data.tar.gz -C /

# Reiniciar serviços
docker-compose -f docker-compose.coolify.yml up -d
```

---

## 🚀 Deploy Step-by-Step

### 1. **Preparação**

```bash
# 1. Clonar repositório (se necessário)
git clone https://github.com/edbentto22/eletrons-server-v1.git
cd eletrons-server-v1

# 2. Verificar arquivos
ls -la docker-compose.coolify.yml
ls -la Dockerfile
ls -la interface-design/Dockerfile
```

### 2. **Configuração no Coolify**

1. **New Project** → **Docker Compose**
2. **Repository**: Cole a URL do GitHub
3. **Branch**: `main`
4. **Docker Compose File**: `docker-compose.coolify.yml`
5. **Environment Variables**: Cole todas as variáveis acima
6. **Domains**: Configure seus domínios
7. **Deploy** 🚀

### 3. **Verificação**

```bash
# Verificar serviços
curl https://api.seu-dominio.com/health
curl https://seu-dominio.com/health

# Verificar logs
# (via painel Coolify ou SSH no servidor)
```

### 4. **Primeiro Uso**

1. Acesse: `https://seu-dominio.com`
2. Faça upload de um dataset
3. Crie um job de treinamento
4. Monitore o progresso

---

## 📞 Suporte e Contato

### Recursos Úteis

- **Documentação Coolify**: https://coolify.io/docs
- **Ultralytics Docs**: https://docs.ultralytics.com
- **FastAPI Docs**: https://fastapi.tiangolo.com

### Comandos Úteis

```bash
# Status dos containers
docker ps

# Logs em tempo real
docker logs -f yolo-training-backend

# Recursos do sistema
docker stats

# Limpeza
docker system prune -a

# Backup rápido
docker exec yolo-training-backend tar -czf /tmp/backup.tar.gz /app/data
```

---

## ✅ Checklist de Deploy

- [ ] Servidor Coolify configurado
- [ ] Repositório GitHub atualizado
- [ ] Variáveis de ambiente configuradas
- [ ] Domínios configurados com SSL
- [ ] Volumes persistentes criados
- [ ] Health checks funcionando
- [ ] Logs acessíveis
- [ ] Backup configurado
- [ ] Primeiro job de teste executado

---

**🎉 Parabéns! Seu Sistema de Treinamento YOLO está rodando no Coolify!**

Para suporte adicional, consulte os logs do sistema ou entre em contato com a equipe de desenvolvimento.