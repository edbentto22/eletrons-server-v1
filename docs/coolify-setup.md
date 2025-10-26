# Guia de Configuração no Coolify

Este guia prepara o servidor para ser configurado e implantado no Coolify com healthcheck estável, suporte a variável PORT, CORS e persistência de dados.

## 1) Pré-requisitos do projeto
- Dockerfile atualizado para respeitar a variável de ambiente `PORT` e incluir `HEALTHCHECK` interno.
- Endpoint `/health` disponível e leve (implementado em `main.py`).
- Variáveis de ambiente suportadas por `app/core/config.py`.

Status atual:
- `Dockerfile`: usa `CMD "python run_server.py --host 0.0.0.0 --port ${PORT:-8000}"` e `HEALTHCHECK` em `http://localhost:${PORT:-8000}/health`.
- `/health`: retorna `status`, `timestamp`, `gpu_available`, `memory_usage`, `cpu_usage`, `jobs` e `version`.

## 2) Variáveis de ambiente (obrigatórias e recomendadas)
Defina estas variáveis em Coolify (aba Environment):
- `API_SECRET`: token de autenticação para os routers protegidos.
- `CALLBACK_SECRET`: token para validação de callbacks.
- `ALLOWED_ORIGINS`: lista CSV de origens permitidas para CORS (ex.: `http://localhost:3000,https://seu-dominio.com`).
- `DEFAULT_MODEL`: nome do modelo YOLO padrão (ex.: `yolov8n.pt`).
- `HOST`: normalmente `0.0.0.0` em containers.
- `PORT`: porta que o Coolify irá expor internamente (padrão 8000). O container respeita esta variável.
- (Opcional) `DEBUG`: `true/false` para recarregar em desenvolvimento.

## 3) Persistência de dados (Volumes)
Crie volumes no Coolify e faça os binds:
- `data/models` → `/app/data/models`
- `data/datasets` → `/app/data/datasets`
- `data/outputs` → `/app/data/outputs`
- `data/logs` → `/app/data/logs`
- (Opcional) `data/temp` → `/app/data/temp`

Isso garante que treinamento, datasets e artefatos persistam entre implantações.

## 4) Criar Aplicação no Coolify
Opção A: Deploy via repositório Git
- Conecte seu repositório com Dockerfile.
- Build: use o Dockerfile da raiz.
- Porta: configure `PORT=8000` (ou outra porta disponível). O Dockerfile já respeita `PORT`.
- Healthcheck:
  - Caminho: `/health`
  - Timeout: 10–15s
  - Intervalo: 30s
  - Inicialização: 40s
- Variáveis: adicione `API_SECRET`, `CALLBACK_SECRET`, `ALLOWED_ORIGINS`, `DEFAULT_MODEL`, etc.
- Volumes: mapeie conforme seção 3.

Opção B: Deploy via imagem de container (Docker Hub/GHCR)
- Publique a imagem e aponte no Coolify.
- Configure `PORT`, healthcheck e variáveis como acima.

## 5) Rede, CORS e Segurança
- CORS: `ALLOWED_ORIGINS` deve incluir o domínio da interface (ex.: frontend no Coolify ou externo).
- TLS: gerenciado via Coolify/Traefik. Certifique-se de apontar o domínio correto.
- Headers SSE: para streaming estável, orquestradores/proxies não devem realizar buffering nos endpoints de SSE. Caso note buffering, desabilite na camada de proxy.

## 6) Recursos e Workers
- Uvicorn: o `run_server.py` inicia com parâmetros seguros. Para SSE (Server-Sent Events), é recomendado manter 1 worker para evitar divisão de conexões, a menos que o SSEManager suporte estado distribuído.
- GPU: se o nó do Coolify tiver GPU e runtime NVIDIA, o health mostrará `gpu_available=true`. Caso contrário, será `false`.

## 7) Testes de Saúde e Autenticação
Após o deploy:
- Health:
  ```bash
  curl -sSf http://SEU_HOST:PORT/health | jq
  ```
- Sem token (deve falhar com 401 nos routers protegidos):
  ```bash
  curl -i http://SEU_HOST:PORT/api/system
  ```
- Com token:
  ```bash
  curl -sSf http://SEU_HOST:PORT/api/system -H "Authorization: Bearer $API_SECRET" | jq
  ```
- SSE (verifique headers e conexão contínua):
  ```bash
  curl -N http://SEU_HOST:PORT/api/system/stream -H "Authorization: Bearer $API_SECRET"
  ```

## 8) Logs e Observabilidade
- Acompanhe logs no Coolify (stdout/stderr).
- Healthcheck no Coolify deve ficar verde; se ficar `unhealthy`, verifique `/health`, variáveis, porta e CORS.

## 9) Dicas de Troubleshooting
- 404 no `/health`: certifique-se de usar o serviço correto e que o container iniciou.
- 401 nos routers: revise `API_SECRET` e header `Authorization: Bearer ...`.
- CORS: ajuste `ALLOWED_ORIGINS` para incluir o domínio do frontend.
- SSE interrompido: verifique buffering no proxy e mantenha 1 worker.
- Porta incorreta: ajuste `PORT` no Coolify; o container respeita `${PORT:-8000}`.

## 10) Rollout e Atualizações
- Habilite auto-deploy no Coolify para novos commits (se usar Git).
- Versões: mantenha tag de imagem semântica (se usar registry) e configure deploy por tag.

Pronto! O servidor está preparado para ser configurado no Coolify com healthcheck funcional, variáveis de ambiente e persistência. Caso queira, posso acompanhar o deploy pelo Coolify e validar os testes de autenticação e SSE após a publicação.