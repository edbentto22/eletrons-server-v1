# Coolify + Docker Compose - Configuração Completa

## 🎯 Problema Resolvido
O erro "port is already allocated" foi corrigido alterando `ports:` para `expose:` no docker-compose.yml.

## ✅ Mudanças Feitas no docker-compose.yml

### ❌ ANTES (causava erro):
```yaml
services:
  yolo-training-system:
    ports:
      - "8000:8000"  # ← Mapeava porta do HOST
```

### ✅ DEPOIS (correto para Coolify):
```yaml
services:
  yolo-training-system:
    expose:
      - "8000"  # ← Apenas expõe porta INTERNA
```

## 🔧 Configuração no Coolify

### 1. Tipo de Deployment
- Escolha: **"Docker Compose"** (não "Application from Git")
- Repository: `https://github.com/edbentto22/eletrons-server-v1.git`
- Branch: `main`

### 2. Configurações de Rede no Coolify

#### Ports & Domains:
```
┌─────────────────────────────────────────┐
│ 🌐 Ports & Domains                     │
├─────────────────────────────────────────┤
│ Service: yolo-training-system           │
│ Internal Port: 8000                     │
│ Domain: yolo.seudominio.com             │
│ HTTPS: ✅ Enabled                       │
└─────────────────────────────────────────┘
```

### 3. Environment Variables
Configure no Coolify (não no .env):

```bash
# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Segurança
API_SECRET=seu_token_super_secreto_aqui_min_32_chars
ALLOWED_ORIGINS=["https://yolo.seudominio.com"]

# Diretórios (opcionais)
DATA_DIR=/home/yolo/app/data
LOGS_DIR=/home/yolo/app/logs
```

### 4. Volumes Persistentes
Configure no Coolify:

```
Source (Host)              → Destination (Container)
/data/coolify/.../data     → /home/yolo/app/data
/data/coolify/.../logs     → /home/yolo/app/logs
```

### 5. Health Check
O Coolify detecta automaticamente do docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 🚀 Deploy Steps

### 1. Commit & Push
```bash
git add docker-compose.yml
git commit -m "fix: change ports to expose for Coolify compatibility"
git push origin main
```

### 2. No Coolify:
1. **Create New Resource** → **Docker Compose**
2. **Repository**: `https://github.com/edbentto22/eletrons-server-v1.git`
3. **Branch**: `main`
4. **Compose File**: `docker-compose.yml` (padrão)
5. **Environment Variables**: Adicionar as variáveis acima
6. **Domains**: Configurar seu domínio
7. **Deploy** 🚀

## 🧪 Testes Pós-Deploy

```bash
# Health check
curl -s -o /dev/null -w "%{http_code}\n" https://yolo.seudominio.com/health
# Esperado: 200

# Endpoint protegido sem token
curl -s -o /dev/null -w "%{http_code}\n" https://yolo.seudominio.com/api/v1/system/status
# Esperado: 403

# Endpoint protegido com token
curl -H "Authorization: Bearer SEU_API_SECRET" \
     -s -o /dev/null -w "%{http_code}\n" \
     https://yolo.seudominio.com/api/v1/system/status
# Esperado: 200
```

## 🔍 Troubleshooting

### Se ainda der erro de porta:
1. Verifique se usou `expose:` (não `ports:`)
2. Confirme que não há `HOST_PORT:CONTAINER_PORT` no compose
3. Reinicie o deployment no Coolify

### Se não conseguir acessar:
1. Verifique se o domínio está configurado
2. Confirme se HTTPS está habilitado
3. Teste o health check interno: `docker exec CONTAINER curl localhost:8000/health`

### Logs:
```bash
# No Coolify, vá para "Logs" da aplicação
# Ou via CLI:
docker logs yolo-training-system
```

## 📝 Próximos Passos

1. ✅ docker-compose.yml corrigido
2. 🔄 Fazer commit e push
3. 🚀 Deploy no Coolify
4. 🌐 Configurar domínio
5. 🧪 Testar endpoints
6. 🔒 Validar segurança (HTTPS + Bearer token)

## 🎯 Resumo da Correção

**O que mudou**: `ports: - "8000:8000"` → `expose: - "8000"`

**Por que funciona**: 
- `expose` apenas documenta que o container usa a porta 8000 internamente
- Coolify/Traefik roteia o domínio para essa porta interna
- Não há conflito com a porta 8000 do host do Coolify