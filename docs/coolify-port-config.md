# Configuração de Portas no Coolify - Guia Visual

## 🎯 Problema
O erro "port is already allocated" acontece porque o Coolify já usa a porta 8000 do HOST. Precisamos configurar apenas a porta INTERNA do container.

## 📍 Onde Configurar no Coolify

### 1. Acesse sua Aplicação
- Vá para o **Dashboard do Coolify**
- Clique na sua aplicação (YOLO Training System)
- Vá para a aba **"Configuration"** ou **"Settings"**

### 2. Seção "Ports & Domains"
Procure pela seção **"Ports & Domains"** ou **"Network"**:

```
┌─────────────────────────────────────────┐
│ 🌐 Ports & Domains                     │
├─────────────────────────────────────────┤
│                                         │
│ ❌ Host Port: [8000] ← REMOVER ISSO     │
│                                         │
│ ✅ Container Port: [8000] ← MANTER      │
│                                         │
│ 🔗 Domain: [seu-dominio.com]           │
│                                         │
└─────────────────────────────────────────┘
```

### 3. Configurações Corretas

#### ❌ ERRADO (causa o erro):
```
Host Port: 8000
Container Port: 8000
```

#### ✅ CORRETO:
```
Host Port: [VAZIO/REMOVIDO]
Container Port: 8000
Domain: yolo.seudominio.com
```

### 4. Passos Detalhados

1. **Remover Host Port**:
   - Encontre o campo "Host Port" ou "External Port"
   - **DELETE** o valor "8000"
   - Deixe VAZIO ou clique em "Remove"

2. **Manter Container Port**:
   - No campo "Container Port" ou "Internal Port"
   - Mantenha o valor **8000**

3. **Configurar Domínio**:
   - No campo "Domain" ou "Custom Domain"
   - Digite: `yolo.seudominio.com`
   - Habilite HTTPS/SSL

### 5. Outras Configurações Importantes

#### Environment Variables:
```
HOST=0.0.0.0
PORT=8000
API_SECRET=seu_token_secreto_aqui
ALLOWED_ORIGINS=["https://yolo.seudominio.com"]
```

#### Health Check:
```
Type: HTTP
Method: GET
Path: /health
Port: 8000  ← Porta INTERNA do container
Timeout: 10s
Interval: 30s
Retries: 3
Start Period: 40s
```

## 🔍 Como Identificar os Campos

### Interface Coolify v4:
- **"Ports"** → Remover mapeamento host
- **"Domains"** → Adicionar domínio
- **"Environment"** → Variáveis

### Interface Coolify v3:
- **"Network"** → Port Configuration
- **"Routing"** → Domain Setup

## 🧪 Teste Após Configuração

```bash
# Via domínio (recomendado)
curl -s -o /dev/null -w "%{http_code}\n" https://yolo.seudominio.com/health
# Deve retornar: 200

# Teste endpoint protegido
curl -H "Authorization: Bearer SEU_TOKEN" https://yolo.seudominio.com/api/v1/system/status
```

## 🚨 Pontos Importantes

1. **NÃO** mapeie porta do host (8000:8000)
2. **SIM** defina porta interna (8000)
3. **SEMPRE** use domínio + HTTPS
4. **Traefik** do Coolify faz o roteamento automaticamente

## 📞 Precisa de Ajuda?

Se não encontrar esses campos, me diga:
1. Qual versão do Coolify você está usando?
2. Você está em "Application from Git" ou "Docker Compose"?
3. Pode compartilhar uma screenshot da tela de configuração?