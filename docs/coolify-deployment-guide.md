# Guia de Deploy no Coolify - YOLO Training System

Este guia fornece instruções completas para fazer o deploy do YOLO Training System no Coolify.

## Pré-requisitos

1. **Servidor Coolify configurado e funcionando**
2. **Acesso ao painel administrativo do Coolify**
3. **Repositório Git com o código do projeto**
4. **Domínios configurados (opcional, mas recomendado)**

## Estrutura do Projeto

O projeto está configurado com os seguintes arquivos para deployment:

```
├── Dockerfile                    # Container do backend FastAPI
├── docker-compose.yml           # Configuração local
├── coolify.yml                  # Configuração específica do Coolify
├── .coolify                     # Configurações do Coolify
├── interface-design/
│   ├── Dockerfile              # Container do frontend React
│   └── nginx.conf              # Configuração do Nginx
└── docs/
    └── coolify-deployment-guide.md
```

## Passo a Passo do Deployment

### 1. Preparação do Repositório

Certifique-se de que todos os arquivos estão commitados no seu repositório Git:

```bash
git add .
git commit -m "Preparação para deploy no Coolify"
git push origin main
```

### 2. Configuração no Coolify

#### 2.1 Criar Novo Projeto

1. Acesse o painel do Coolify
2. Clique em "New Project"
3. Escolha "Docker Compose" como tipo de aplicação
4. Conecte seu repositório Git

#### 2.2 Configurar Variáveis de Ambiente

No painel do Coolify, configure as seguintes variáveis:

**Backend (Obrigatórias):**
```env
API_SECRET=v63ilgo6j41o7xn75c
CALLBACK_SECRET=changeme_callback_secret
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info
```

**Frontend:**
```env
VITE_API_BASE_URL=https://seu-backend-domain.com
VITE_API_TIMEOUT=10000
```

**Domínios (se aplicável):**
```env
FRONTEND_URL=https://seu-frontend-domain.com
BACKEND_URL=https://seu-backend-domain.com
```

#### 2.3 Configurar Domínios

1. No painel do Coolify, vá para "Domains"
2. Adicione os domínios para backend e frontend:
   - Backend: `api.seu-dominio.com` (porta 8000)
   - Frontend: `app.seu-dominio.com` (porta 3000)

#### 2.4 Configurar Volumes Persistentes

Configure os volumes para persistir dados:

```yaml
volumes:
  yolo_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/coolify/yolo-training/data
  yolo_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/coolify/yolo-training/logs
```

### 3. Deploy da Aplicação

#### 3.1 Deploy Automático

1. No painel do Coolify, clique em "Deploy"
2. Aguarde o processo de build e deploy
3. Monitore os logs para verificar se não há erros

#### 3.2 Verificação do Deploy

Após o deploy, verifique:

1. **Health Check do Backend:**
   ```bash
   curl https://seu-backend-domain.com/health
   ```

2. **Acesso ao Frontend:**
   - Abra `https://seu-frontend-domain.com`
   - Verifique se a interface carrega corretamente

3. **Conectividade Backend-Frontend:**
   - Teste se o frontend consegue se comunicar com o backend
   - Verifique os logs do navegador para erros de CORS

### 4. Configurações Avançadas

#### 4.1 SSL/TLS

O Coolify gerencia automaticamente os certificados SSL via Let's Encrypt. Certifique-se de que:

1. Os domínios estão apontando para o servidor
2. As portas 80 e 443 estão abertas
3. O Coolify tem permissões para gerar certificados

#### 4.2 Backup e Monitoramento

Configure backups automáticos dos volumes:

```bash
# Backup dos dados
tar -czf yolo-backup-$(date +%Y%m%d).tar.gz /var/lib/coolify/yolo-training/data

# Backup dos logs
tar -czf yolo-logs-backup-$(date +%Y%m%d).tar.gz /var/lib/coolify/yolo-training/logs
```

#### 4.3 Scaling (Opcional)

Para alta disponibilidade, configure múltiplas instâncias:

```yaml
services:
  yolo-training-system:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 5. Troubleshooting

#### 5.1 Problemas Comuns

**1. Erro de Conexão Frontend-Backend:**
```bash
# Verifique as variáveis de ambiente
docker exec -it <container_id> env | grep VITE_API_BASE_URL

# Teste conectividade
curl -H "Authorization: Bearer v63ilgo6j41o7xn75c" https://seu-backend-domain.com/health
```

**2. Problemas de CORS:**
```bash
# Verifique ALLOWED_ORIGINS no backend
docker logs <backend_container_id> | grep CORS
```

**3. Volumes não Persistindo:**
```bash
# Verifique se os volumes estão montados
docker inspect <container_id> | grep Mounts -A 10
```

#### 5.2 Logs e Debugging

```bash
# Logs do backend
docker logs -f <backend_container_id>

# Logs do frontend
docker logs -f <frontend_container_id>

# Logs do Coolify
tail -f /var/log/coolify/coolify.log
```

### 6. Manutenção

#### 6.1 Atualizações

Para atualizar a aplicação:

1. Faça push das mudanças para o repositório
2. No Coolify, clique em "Redeploy"
3. Monitore o processo de atualização

#### 6.2 Backup Regular

Configure um cron job para backups automáticos:

```bash
# Adicione ao crontab
0 2 * * * /usr/local/bin/backup-yolo-training.sh
```

### 7. Configurações de Produção

#### 7.1 Segurança

1. **Altere as chaves secretas:**
   ```env
   API_SECRET=sua_chave_super_secreta_aqui
   CALLBACK_SECRET=sua_callback_secret_aqui
   ```

2. **Configure HTTPS obrigatório**
3. **Limite acesso por IP (se necessário)**

#### 7.2 Performance

1. **Configure limites de recursos:**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
       reservations:
         memory: 1G
         cpus: '0.5'
   ```

2. **Configure cache do Nginx**
3. **Otimize o banco de dados (se aplicável)**

## Conclusão

Seguindo este guia, você terá o YOLO Training System funcionando perfeitamente no Coolify com:

- ✅ Backend FastAPI funcionando
- ✅ Frontend React/Vite funcionando
- ✅ Comunicação entre frontend e backend
- ✅ Volumes persistentes configurados
- ✅ SSL/TLS automático
- ✅ Health checks configurados
- ✅ Logs centralizados

Para suporte adicional, consulte a documentação oficial do Coolify ou abra uma issue no repositório do projeto.