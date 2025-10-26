# Deploy no Coolify — Guia Completo e Checklists

Este documento consolida todos os passos e detalhes para implantar o Sistema de Treinamento YOLO no Coolify, incluindo pré-requisitos, variáveis de ambiente, volumes, healthcheck, CORS/SSE, publicação de imagem e validação pós-deploy.

---

## 1) Pré-requisitos do projeto
- Dockerfile atualizado com:
  - `CMD` respeitando `PORT` via `${PORT:-8000}`
  - `HEALTHCHECK` interno em `http://localhost:${PORT:-8000}/health`
  - `curl` instalado (para healthcheck)
- Endpoint `/health` implementado em `main.py`
- Configurações de CORS em `app/core/config.py` via `ALLOWED_ORIGINS`
- Servidor iniciado por `run_server.py` com host/port configuráveis

### Portas e documentação
- Porta padrão exposta: 8000
- Documentação da API: `/api/docs` e `/api/redoc`
- Frontend (se build existir): `/`

---

## 2) Variáveis de ambiente
Defina-as na aba "Environment" do Coolify:
- `API_SECRET`: token para autenticação das rotas protegidas
- `CALLBACK_SECRET`: token para callbacks
- `ALLOWED_ORIGINS`: CSV de origens permitidas (ex.: `http://localhost:3000,https://seu-dominio.com`)
- `DEFAULT_MODEL`: modelo YOLO padrão (ex.: `yolov8n.pt`)
- `HOST`: `0.0.0.0`
- `PORT`: `8000` (ou outra porta desejada)
- (Opcional) `DEBUG`: `true/false`

Observação: O container respeita `PORT` e o healthcheck interno usa a mesma porta.

---

## 3) Volumes (persistência)
No Coolify, mapeie os volumes:
- `/app/data/models` — modelos e pesos
- `/app/data/datasets` — datasets
- `/app/data/outputs` — resultados de treino/validação
- `/app/data/logs` — logs
- (Opcional) `/app/data/temp`

Isso garante persistência entre versões.

---

## 4) Publicação da imagem (opcional)
Se optar por deploy via registry:

### Docker Hub
```bash
# Build
docker build -t seu-usuario/sistema-yolo:latest .

# Login
docker login

# Push
docker push seu-usuario/sistema-yolo:latest
```

### GitHub Container Registry (GHCR)
```bash
# Build
docker build -t ghcr.io/seu-org/sistema-yolo:latest .

# Login (token/pat com scope de packages)
echo "$GHCR_TOKEN" | docker login ghcr.io -u seu-usuario --password-stdin

# Push
docker push ghcr.io/seu-org/sistema-yolo:latest
```

No Coolify, selecione a imagem publicada e configure variáveis/volumes conforme seções anteriores.

---

## 5) Criar aplicação no Coolify
### Opção A: Usando repositório Git
- Conecte o repositório com o Dockerfile
- Configure `PORT` na aba de Environment
- Mapeie volumes (ver seção 3)
- Healthcheck:
  - Caminho: `/health`
  - Intervalo: `30s`
  - Timeout: `10–15s`
  - Start period: `40s`
- Configure `API_SECRET`, `CALLBACK_SECRET`, `ALLOWED_ORIGINS` e demais variáveis
- Realize o deploy

### Opção B: Usando imagem do registry
- Selecione a imagem (`seu-usuario/sistema-yolo:latest` ou `ghcr.io/seu-org/sistema-yolo:latest`)
- Configure `PORT`, variáveis e volumes como acima
- Defina o Healthcheck
- Realize o deploy

---

## 6) CORS, SSE e segurança
- `ALLOWED_ORIGINS` deve incluir o domínio do frontend (Coolify ou externo)
- TLS: normalmente gerenciado por Coolify/Traefik
- SSE (Server-Sent Events):
  - Use 1 worker por padrão para conexões estáveis
  - Evite buffering em proxies nos endpoints de SSE (`/api/system/stream`, `/api/jobs/{id}/stream`)

---

## 7) Checklists
### Checklist de Pré-deploy
- [ ] Dockerfile com `PORT` e `HEALTHCHECK`
- [ ] `/health` funcional localmente
- [ ] Variáveis definidas (API_SECRET, CALLBACK_SECRET, ALLOWED_ORIGINS, DEFAULT_MODEL, HOST, PORT)
- [ ] Volumes planejados
- [ ] CORS correto para seu domínio

### Checklist de Deploy no Coolify
- [ ] App criada (Git ou imagem)
- [ ] PORT definida no ambiente
- [ ] Healthcheck configurado em `/health`
- [ ] Volumes mapeados
- [ ] Variáveis aplicadas
- [ ] TLS/host configurado (se aplicável)

### Checklist Pós-deploy (validação)
- [ ] Health: `curl -sSf http://SEU_HOST:PORT/health | jq`
- [ ] Sem token: `curl -i http://SEU_HOST:PORT/api/system` (deve retornar 401)
- [ ] Com token: `curl -sSf http://SEU_HOST:PORT/api/system -H "Authorization: Bearer $API_SECRET" | jq`
- [ ] SSE: `curl -N http://SEU_HOST:PORT/api/system/stream -H "Authorization: Bearer $API_SECRET"`

---

## 8) Troubleshooting
- 404 no `/health`: verifique se o container está rodando e a porta/host corretos
- 401 nas rotas protegidas: revise `API_SECRET` e o header `Authorization: Bearer ...`
- CORS bloqueando o frontend: ajuste `ALLOWED_ORIGINS` para incluir o domínio correto
- SSE interrompido: verifique buffering do proxy e workers
- Porta incorreta: ajuste `PORT` no Coolify; o container usa `${PORT:-8000}`
- Dependências (Torch/Ultralytics): verifique logs e recursos do host (GPU opcional)

---

## 9) Manutenção e atualizações
- Auto-deploy: habilite para novos commits (se usar Git)
- Versionamento de imagem: use tags semânticas e atualize o Coolify por tag
- Logs: acompanhe stdout/stderr no Coolify e os arquivos em `/app/data/logs`
- Backup: faça snapshots dos volumes, especialmente datasets e models

---

## 10) Referências internas
- `main.py`: define `/health`, routers, CORS e documentação da API
- `run_server.py`: inicialização do Uvicorn e verificações de ambiente
- `app/core/config.py`: parsing de variáveis (`HOST`, `PORT`, `ALLOWED_ORIGINS`, tokens)
- `docker-compose.yml`: exemplo local com healthcheck e mapeamento de porta

---

Pronto! Com este guia e os checklists, seu deploy no Coolify deve ocorrer de forma previsível e segura. Em caso de dúvidas ou ajustes específicos de rede/domínio, atualize `ALLOWED_ORIGINS` e revise os endpoints de SSE e healthcheck.