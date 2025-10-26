# Dockerfile para Sistema de Treinamento YOLO
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgtk-3-0 libgl1 \
    curl wget git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt /tmp/requirements.txt

# Instalar dependências Python em nível de sistema (root)
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Criar usuário não-root e diretório de trabalho
RUN useradd --create-home --shell /bin/bash yolo
USER yolo
WORKDIR /home/yolo/app

# Copiar código da aplicação
COPY --chown=yolo:yolo . .

# Criar estrutura de diretórios
RUN mkdir -p data/{models,datasets,outputs,logs,temp}

# Expor porta (padrão)
EXPOSE 8060

# Healthcheck removido - será controlado pelo docker-compose.yml

# Comando padrão (respeita PORT do ambiente)
CMD ["sh", "-c", "python run_server.py --host 0.0.0.0 --port ${PORT:-8060}"]
