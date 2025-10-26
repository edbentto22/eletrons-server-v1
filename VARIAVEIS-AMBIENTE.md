# 🔧 Variáveis de Ambiente - Sistema YOLO Training

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Variáveis Obrigatórias](#variáveis-obrigatórias)
- [Variáveis de Configuração](#variáveis-de-configuração)
- [Variáveis Opcionais](#variáveis-opcionais)
- [Configuração no Coolify](#configuração-no-coolify)
- [Exemplos Práticos](#exemplos-práticos)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este documento detalha todas as variáveis de ambiente necessárias para configurar o Sistema de Treinamento YOLO no Coolify. As variáveis estão organizadas por categoria e importância.

### 📁 Arquivos de Referência
- `.env.coolify` - Template com todas as variáveis
- `docker-compose.coolify.yml` - Configuração Docker
- `COOLIFY-SETUP-COMPLETO.md` - Guia completo de setup

---

## 🚨 Variáveis Obrigatórias

### 🔐 Segurança (CRÍTICO)
```bash
# ALTERE OBRIGATORIAMENTE!
API_SECRET=ALTERE_ESTE_TOKEN_SUPER_SECRETO_MIN_32_CHARS_2025
CALLBACK_SECRET=ALTERE_ESTE_CALLBACK_SECRET_SUPER_SEGURO_2025
```

**⚠️ IMPORTANTE:**
- Tokens devem ter no mínimo 32 caracteres
- Use geradores de senha seguros
- Nunca use os valores padrão em produção

### 🌐 URLs e Domínios
```bash
BACKEND_URL=https://api.seu-dominio.com
FRONTEND_URL=https://seu-dominio.com
WEBSOCKET_URL=wss://api.seu-dominio.com
ALLOWED_ORIGINS=["https://seu-dominio.com","https://api.seu-dominio.com"]
```

**Configuração:**
- Substitua `seu-dominio.com` pelo seu domínio real
- Use HTTPS em produção
- WebSocket deve usar WSS (seguro)

### 🖥️ Servidor
```bash
HOST=0.0.0.0
PORT=8060
NODE_ENV=production
DEBUG=false
```

---

## ⚙️ Variáveis de Configuração

### 🤖 YOLO e Ultralytics
```bash
# Modelo padrão
DEFAULT_MODEL=yolov8n.pt

# Parâmetros de treinamento
DEFAULT_EPOCHS=100
DEFAULT_BATCH_SIZE=16
DEFAULT_IMAGE_SIZE=640
DEFAULT_LEARNING_RATE=0.01
DEFAULT_OPTIMIZER=AdamW
```

**Opções de Modelos:**
- `yolov8n.pt` - Nano (mais rápido)
- `yolov8s.pt` - Small
- `yolov8m.pt` - Medium
- `yolov8l.pt` - Large
- `yolov8x.pt` - Extra Large (mais preciso)

### 🎛️ Performance do Sistema
```bash
# Controle de jobs
MAX_CONCURRENT_JOBS=3
SYSTEM_MONITOR_INTERVAL=5
JOB_UPDATE_INTERVAL=2
CLEANUP_INTERVAL=3600
AUTO_CLEANUP=true

# Recursos
MEMORY_LIMIT=4G
CPU_LIMIT=2.0
MEMORY_RESERVATION=2G
CPU_RESERVATION=1.0
```

### 📁 Caminhos de Dados
```bash
DATA_PATH=/data/yolo-training/data
LOGS_PATH=/data/yolo-training/logs
MODELS_PATH=/data/yolo-training/models
```

---

## 🔧 Variáveis Opcionais

### 🎮 GPU NVIDIA (Se Disponível)
```bash
# Descomente se tiver GPU
# CUDA_VISIBLE_DEVICES=0
# TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6"
```

### 🗄️ Redis (Cache)
```bash
# Para melhor performance
# REDIS_PASSWORD=ALTERE_ESTA_SENHA_REDIS_2025
# REDIS_URL=redis://redis:6379
```

### 📊 Monitoramento
```bash
ENABLE_METRICS=true
METRICS_INTERVAL=30
LOG_RETENTION_DAYS=30
ENABLE_SYSTEM_MONITOR=true
```

### 💾 Backup
```bash
BACKUP_ENABLED=true
BACKUP_INTERVAL=86400
BACKUP_RETENTION_DAYS=7
MAINTENANCE_WINDOW=02:00-04:00
```

### 🌐 Frontend (Vite)
```bash
VITE_API_URL=https://api.seu-dominio.com
VITE_API_SECRET=MESMO_TOKEN_DO_API_SECRET_ACIMA
VITE_API_TIMEOUT=10000
VITE_WEBSOCKET_URL=wss://api.seu-dominio.com
```

---

## 🚀 Configuração no Coolify

### Passo 1: Acessar Variáveis
1. Entre no painel Coolify
2. Selecione seu projeto
3. Vá em **"Environment Variables"**

### Passo 2: Adicionar Variáveis
```bash
# Método 1: Uma por vez
Nome: API_SECRET
Valor: seu_token_super_secreto_aqui

# Método 2: Bulk (em massa)
API_SECRET=seu_token_super_secreto_aqui
BACKEND_URL=https://api.seu-dominio.com
FRONTEND_URL=https://seu-dominio.com
```

### Passo 3: Configurações Especiais

#### 🔒 Secrets (Sensíveis)
Marque como **"Secret"** estas variáveis:
- `API_SECRET`
- `CALLBACK_SECRET`
- `REDIS_PASSWORD`

#### 🔄 Build Time vs Runtime
- **Build Time**: `VITE_*` (frontend)
- **Runtime**: Todas as outras

---

## 💡 Exemplos Práticos

### Configuração Básica (Mínima)
```bash
# Segurança
API_SECRET=minha_chave_super_secreta_123456789012
CALLBACK_SECRET=callback_secreto_987654321098

# URLs
BACKEND_URL=https://api.meusite.com
FRONTEND_URL=https://meusite.com
WEBSOCKET_URL=wss://api.meusite.com

# Sistema
HOST=0.0.0.0
PORT=8060
NODE_ENV=production
DEBUG=false
```

### Configuração Avançada (Com GPU)
```bash
# Básica + GPU
CUDA_VISIBLE_DEVICES=0
DEFAULT_BATCH_SIZE=32
MEMORY_LIMIT=8G
CPU_LIMIT=4.0
MAX_CONCURRENT_JOBS=2
```

### Configuração de Desenvolvimento
```bash
# Para testes
DEBUG=true
LOG_LEVEL=debug
NODE_ENV=development
ENABLE_CORS=true
```

---

## 🔍 Troubleshooting

### ❌ Problemas Comuns

#### 1. Erro de Autenticação
```
Erro: 401 Unauthorized
```
**Solução:**
- Verifique se `API_SECRET` está correto
- Confirme se `VITE_API_SECRET` = `API_SECRET`

#### 2. CORS Error
```
Erro: CORS policy blocked
```
**Solução:**
```bash
ALLOWED_ORIGINS=["https://seu-dominio.com"]
ENABLE_CORS=true  # Apenas desenvolvimento
```

#### 3. WebSocket Falha
```
Erro: WebSocket connection failed
```
**Solução:**
- Use `wss://` (não `ws://`)
- Verifique `WEBSOCKET_URL`
- Confirme proxy/load balancer

#### 4. Out of Memory
```
Erro: CUDA out of memory
```
**Solução:**
```bash
DEFAULT_BATCH_SIZE=8  # Reduzir
MEMORY_LIMIT=6G       # Aumentar
```

### 🔧 Comandos de Debug

#### Verificar Variáveis no Container
```bash
# No Coolify terminal
env | grep API_SECRET
env | grep BACKEND_URL
```

#### Testar Conectividade
```bash
# Teste API
curl -H "Authorization: Bearer $API_SECRET" $BACKEND_URL/health

# Teste WebSocket
wscat -c $WEBSOCKET_URL
```

---

## 📚 Referências Rápidas

### 🎯 Valores Recomendados por Cenário

#### 💻 Desenvolvimento Local
```bash
MEMORY_LIMIT=2G
CPU_LIMIT=1.0
DEFAULT_BATCH_SIZE=8
MAX_CONCURRENT_JOBS=1
DEBUG=true
```

#### 🏢 Produção Pequena
```bash
MEMORY_LIMIT=4G
CPU_LIMIT=2.0
DEFAULT_BATCH_SIZE=16
MAX_CONCURRENT_JOBS=2
DEBUG=false
```

#### 🚀 Produção Grande (Com GPU)
```bash
MEMORY_LIMIT=8G
CPU_LIMIT=4.0
DEFAULT_BATCH_SIZE=32
MAX_CONCURRENT_JOBS=3
CUDA_VISIBLE_DEVICES=0
```

### 🔗 Links Úteis
- [Coolify Docs](https://coolify.io/docs)
- [Ultralytics Docs](https://docs.ultralytics.com)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## ✅ Checklist Final

- [ ] `API_SECRET` alterado (mín. 32 chars)
- [ ] `CALLBACK_SECRET` alterado
- [ ] URLs configuradas com seu domínio
- [ ] `ALLOWED_ORIGINS` atualizado
- [ ] Recursos (CPU/Memory) ajustados
- [ ] GPU configurada (se disponível)
- [ ] Variáveis marcadas como "Secret"
- [ ] Deploy testado
- [ ] Logs verificados
- [ ] API funcionando
- [ ] WebSocket conectando
- [ ] Interface carregando

---

**🎉 Pronto! Seu sistema YOLO está configurado e pronto para treinar modelos de visão computacional!**