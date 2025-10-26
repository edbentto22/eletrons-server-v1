# 🚀 Guia Completo de Setup - Coolify + Sistema YOLO Training

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Configuração Inicial](#configuração-inicial)
- [Deploy Passo a Passo](#deploy-passo-a-passo)
- [Configurações Avançadas](#configurações-avançadas)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)
- [Otimizações](#otimizações)
- [Backup e Recovery](#backup-e-recovery)
- [Checklist Final](#checklist-final)

---

## 🎯 Visão Geral

Este guia fornece instruções completas para deploy do **Sistema de Treinamento YOLO** no **Coolify**, incluindo configurações de produção, monitoramento e otimizações.

### 🏗️ Arquitetura do Sistema
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Redis       │
│   React + Vite  │◄──►│  FastAPI + YOLO │◄──►│     Cache       │
│   Port: 3000    │    │   Port: 8060    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Volumes       │
                    │ /data, /logs,   │
                    │ /models, /temp  │
                    └─────────────────┘
```

### 📁 Arquivos Principais
- `docker-compose.coolify.yml` - Configuração Docker otimizada
- `.env.coolify` - Template de variáveis de ambiente
- `VARIAVEIS-AMBIENTE.md` - Documentação completa das variáveis
- `coolify.yml` - Configurações específicas do Coolify

---

## 🔧 Pré-requisitos

### 🖥️ Servidor Coolify
- **OS**: Ubuntu 20.04+ / Debian 11+
- **RAM**: Mínimo 4GB (Recomendado 8GB+)
- **CPU**: 2+ cores (Recomendado 4+ cores)
- **Storage**: 50GB+ SSD
- **Docker**: 20.10+
- **Coolify**: v4.0+

### 🌐 Domínios (Opcional)
- Domínio principal: `seu-dominio.com`
- API: `api.seu-dominio.com`
- Certificados SSL automáticos via Let's Encrypt

### 🎮 GPU (Opcional)
- **NVIDIA GPU** com CUDA 11.8+
- **NVIDIA Container Toolkit** instalado
- **Drivers NVIDIA** atualizados

---

## 🚀 Configuração Inicial

### 1️⃣ Preparar Repositório
```bash
# Clone o projeto
git clone https://github.com/edbentto22/eletrons-server-v1.git
cd eletrons-server-v1

# Verificar arquivos necessários
ls -la docker-compose.coolify.yml
ls -la .env.coolify
ls -la VARIAVEIS-AMBIENTE.md
```

### 2️⃣ Configurar Variáveis de Ambiente
```bash
# Copiar template
cp .env.coolify .env.production

# Editar variáveis (OBRIGATÓRIO!)
nano .env.production
```

**⚠️ ALTERE OBRIGATORIAMENTE:**
```bash
API_SECRET=SEU_TOKEN_SUPER_SECRETO_MIN_32_CHARS_2025
CALLBACK_SECRET=SEU_CALLBACK_SECRET_SUPER_SEGURO_2025
BACKEND_URL=https://api.seu-dominio.com
FRONTEND_URL=https://seu-dominio.com
```

### 3️⃣ Validar Configuração
```bash
# Testar sintaxe Docker Compose
docker-compose -f docker-compose.coolify.yml config

# Verificar se não há erros
echo $?  # Deve retornar 0
```

---

## 🎯 Deploy Passo a Passo

### Etapa 1: Criar Projeto no Coolify

1. **Acessar Painel Coolify**
   - URL: `https://coolify.seu-servidor.com`
   - Login com suas credenciais

2. **Novo Projeto**
   - Clique em **"+ New"**
   - Selecione **"Project"**
   - Nome: `yolo-training-system`

3. **Conectar Repositório**
   - **Source**: GitHub/GitLab
   - **Repository**: `edbentto22/eletrons-server-v1`
   - **Branch**: `main`

### Etapa 2: Configurar Aplicação

1. **Tipo de Aplicação**
   - Selecione **"Docker Compose"**
   - **Compose File**: `docker-compose.coolify.yml`

2. **Configurações Básicas**
   ```
   Name: YOLO Training System
   Description: Sistema completo de treinamento YOLO com Ultralytics
   Environment: production
   ```

### Etapa 3: Variáveis de Ambiente

**No painel Coolify > Environment Variables:**

#### 🔐 Segurança (CRÍTICO)
```
API_SECRET=seu_token_super_secreto_min_32_chars
CALLBACK_SECRET=seu_callback_secret_super_seguro
```

#### 🌐 URLs e Domínios
```
BACKEND_URL=https://api.seu-dominio.com
FRONTEND_URL=https://seu-dominio.com
WEBSOCKET_URL=wss://api.seu-dominio.com
ALLOWED_ORIGINS=["https://seu-dominio.com","https://api.seu-dominio.com"]
```

#### ⚙️ Sistema
```
HOST=0.0.0.0
PORT=8060
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info
```

#### 🤖 YOLO
```
DEFAULT_MODEL=yolov8n.pt
DEFAULT_EPOCHS=100
DEFAULT_BATCH_SIZE=16
DEFAULT_IMAGE_SIZE=640
DEFAULT_LEARNING_RATE=0.01
DEFAULT_OPTIMIZER=AdamW
```

#### 🎛️ Performance
```
MAX_CONCURRENT_JOBS=3
MEMORY_LIMIT=4G
CPU_LIMIT=2.0
SYSTEM_MONITOR_INTERVAL=5
```

#### 🌐 Frontend (Vite)
```
VITE_API_URL=https://api.seu-dominio.com
VITE_API_SECRET=mesmo_valor_do_api_secret
VITE_API_TIMEOUT=10000
VITE_WEBSOCKET_URL=wss://api.seu-dominio.com
```

### Etapa 4: Configurar Domínios

1. **Backend API**
   - **Domain**: `api.seu-dominio.com`
   - **Port**: `8060`
   - **SSL**: Automático (Let's Encrypt)

2. **Frontend**
   - **Domain**: `seu-dominio.com`
   - **Port**: `3000`
   - **SSL**: Automático (Let's Encrypt)

### Etapa 5: Volumes Persistentes

**Configuração automática via docker-compose.coolify.yml:**
```yaml
volumes:
  yolo_data:     # Datasets e dados
  yolo_logs:     # Logs do sistema
  yolo_models:   # Modelos treinados
  yolo_temp:     # Arquivos temporários
  redis_data:    # Cache Redis
```

### Etapa 6: Deploy

1. **Iniciar Deploy**
   - Clique em **"Deploy"**
   - Aguarde o build dos containers

2. **Monitorar Logs**
   - Acompanhe os logs em tempo real
   - Verifique se não há erros

3. **Verificar Status**
   - Todos os serviços devem estar **"Running"**
   - Health checks devem estar **"Healthy"**

---

## 🔧 Configurações Avançadas

### 🎮 GPU NVIDIA (Se Disponível)

1. **Instalar NVIDIA Container Toolkit**
```bash
# No servidor Coolify
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. **Configurar no Coolify**
```bash
# Adicionar variáveis
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6"

# Ajustar batch size para GPU
DEFAULT_BATCH_SIZE=32
MEMORY_LIMIT=8G
```

### 🗄️ Redis Cache (Opcional)

**Já incluído no docker-compose.coolify.yml:**
```yaml
redis:
  image: redis:7-alpine
  environment:
    REDIS_PASSWORD: ${REDIS_PASSWORD:-}
  volumes:
    - redis_data:/data
```

**Configurar variáveis:**
```bash
REDIS_PASSWORD=sua_senha_redis_segura
REDIS_URL=redis://redis:6379
```

### 🔒 Configurações de Segurança

1. **Firewall**
```bash
# Apenas portas necessárias
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

2. **SSL/TLS**
   - Let's Encrypt automático via Coolify
   - Renovação automática
   - HTTPS obrigatório

3. **Secrets Management**
   - Marcar variáveis sensíveis como "Secret"
   - Rotacionar tokens periodicamente
   - Usar senhas fortes (32+ caracteres)

---

## 📊 Monitoramento

### 🔍 Health Checks

**Automáticos via docker-compose.coolify.yml:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8060/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 1m
```

### 📈 Métricas do Sistema

1. **CPU e Memória**
   - Monitoramento via Coolify dashboard
   - Alertas automáticos

2. **Logs Centralizados**
   - Logs estruturados em JSON
   - Rotação automática
   - Retenção configurável

3. **Performance YOLO**
   - Métricas de treinamento
   - FPS de inferência
   - Uso de GPU

### 🚨 Alertas

**Configurar no Coolify:**
- CPU > 80%
- Memória > 90%
- Disk > 85%
- Serviços down
- SSL expirando

---

## 🔧 Troubleshooting

### ❌ Problemas Comuns

#### 1. Container não inicia
```bash
# Verificar logs
docker logs container_name

# Verificar recursos
docker stats

# Verificar variáveis
env | grep API_SECRET
```

#### 2. Erro de permissão nos volumes
```bash
# Ajustar permissões
sudo chown -R 1000:1000 /var/lib/coolify/yolo-training/
sudo chmod -R 755 /var/lib/coolify/yolo-training/
```

#### 3. SSL não funciona
```bash
# Verificar DNS
nslookup api.seu-dominio.com

# Forçar renovação SSL
# Via painel Coolify > SSL > Renew
```

#### 4. API não responde
```bash
# Testar conectividade
curl -H "Authorization: Bearer $API_SECRET" https://api.seu-dominio.com/health

# Verificar logs do backend
docker logs yolo-backend
```

#### 5. Frontend não carrega
```bash
# Verificar build
docker logs yolo-frontend

# Testar diretamente
curl -I https://seu-dominio.com
```

### 🔧 Comandos de Debug

```bash
# Status dos containers
docker ps -a

# Logs em tempo real
docker logs -f container_name

# Entrar no container
docker exec -it container_name /bin/bash

# Verificar recursos
docker system df
docker system prune -f

# Testar conectividade interna
docker network ls
docker network inspect coolify
```

---

## ⚡ Otimizações

### 🚀 Performance

1. **Recursos por Cenário**

**Desenvolvimento:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

**Produção:**
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
    reservations:
      cpus: '2.0'
      memory: 4G
```

**GPU (High-end):**
```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 16G
    reservations:
      cpus: '4.0'
      memory: 8G
```

2. **Cache e CDN**
```bash
# Redis para cache
ENABLE_CACHE=true
CACHE_TTL=3600

# CDN para assets estáticos
VITE_CDN_URL=https://cdn.seu-dominio.com
```

3. **Compressão**
```nginx
# nginx.conf (já incluído)
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;
```

### 🔄 Auto-scaling

**Configurar no Coolify:**
```yaml
deploy:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 10s
    failure_action: rollback
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
```

---

## 💾 Backup e Recovery

### 📦 Backup Automático

1. **Script de Backup**
```bash
#!/bin/bash
# backup-yolo.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/yolo-training"
VOLUMES_DIR="/var/lib/coolify/yolo-training"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup dos volumes
tar -czf $BACKUP_DIR/yolo-data-$DATE.tar.gz -C $VOLUMES_DIR data/
tar -czf $BACKUP_DIR/yolo-models-$DATE.tar.gz -C $VOLUMES_DIR models/
tar -czf $BACKUP_DIR/yolo-logs-$DATE.tar.gz -C $VOLUMES_DIR logs/

# Backup do banco Redis
docker exec redis redis-cli BGSAVE
cp /var/lib/coolify/redis/dump.rdb $BACKUP_DIR/redis-$DATE.rdb

# Limpeza (manter últimos 7 dias)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

2. **Cron Job**
```bash
# Executar diariamente às 2h
0 2 * * * /scripts/backup-yolo.sh >> /var/log/backup-yolo.log 2>&1
```

### 🔄 Recovery

1. **Restaurar Dados**
```bash
# Parar serviços
docker-compose -f docker-compose.coolify.yml down

# Restaurar volumes
tar -xzf backup/yolo-data-20250126_020000.tar.gz -C /var/lib/coolify/yolo-training/
tar -xzf backup/yolo-models-20250126_020000.tar.gz -C /var/lib/coolify/yolo-training/

# Ajustar permissões
chown -R 1000:1000 /var/lib/coolify/yolo-training/

# Reiniciar serviços
docker-compose -f docker-compose.coolify.yml up -d
```

2. **Disaster Recovery**
```bash
# Backup completo do sistema
rsync -avz /var/lib/coolify/ backup-server:/backups/coolify/

# Restauração completa
rsync -avz backup-server:/backups/coolify/ /var/lib/coolify/
```

---

## ✅ Checklist Final

### 🔧 Pré-Deploy
- [ ] Servidor Coolify configurado e funcionando
- [ ] Repositório Git atualizado
- [ ] Variáveis de ambiente configuradas
- [ ] Domínios apontando para o servidor
- [ ] SSL configurado
- [ ] Recursos adequados (CPU/RAM)

### 🚀 Deploy
- [ ] Projeto criado no Coolify
- [ ] Repositório conectado
- [ ] Docker Compose configurado
- [ ] Variáveis de ambiente adicionadas
- [ ] Domínios configurados
- [ ] Volumes persistentes criados
- [ ] Deploy executado com sucesso

### ✅ Pós-Deploy
- [ ] Todos os serviços rodando
- [ ] Health checks passando
- [ ] API respondendo (https://api.seu-dominio.com/health)
- [ ] Frontend carregando (https://seu-dominio.com)
- [ ] WebSocket conectando
- [ ] Logs sem erros críticos
- [ ] SSL funcionando
- [ ] Backup configurado

### 🔍 Testes
- [ ] Criar job de treinamento
- [ ] Upload de dataset
- [ ] Iniciar treinamento
- [ ] Monitorar progresso
- [ ] Verificar métricas
- [ ] Testar inferência
- [ ] Validar resultados

### 📊 Monitoramento
- [ ] Métricas do sistema
- [ ] Alertas configurados
- [ ] Logs centralizados
- [ ] Performance monitorada
- [ ] Backup funcionando

---

## 🎉 Conclusão

Seu **Sistema de Treinamento YOLO** está agora configurado e rodando no **Coolify**! 

### 🔗 Links Úteis
- **Frontend**: https://seu-dominio.com
- **API**: https://api.seu-dominio.com
- **Health Check**: https://api.seu-dominio.com/health
- **Docs**: https://api.seu-dominio.com/docs
- **Coolify Panel**: https://coolify.seu-servidor.com

### 📚 Próximos Passos
1. **Treinar seu primeiro modelo** com o dataset de infraestrutura elétrica
2. **Configurar monitoramento avançado**
3. **Implementar CI/CD** para deploys automáticos
4. **Escalar horizontalmente** conforme necessário
5. **Otimizar performance** baseado no uso real

**🚀 Agora é só treinar seus modelos YOLO e revolucionar sua visão computacional!**