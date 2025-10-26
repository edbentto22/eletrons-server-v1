# Dockerfile para Sistema de Treinamento YOLO
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash yolo
USER yolo
WORKDIR /home/yolo/app

# Copiar requirements primeiro (para cache do Docker)
COPY --chown=yolo:yolo requirements.txt .

# Instalar dependências Python
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY --chown=yolo:yolo . .

# Criar estrutura de diretórios
RUN mkdir -p data/{models,datasets,outputs,logs,temp}

# Expor porta (padrão)
EXPOSE 8000

# Healthcheck para orquestradores (Coolify, Docker, etc.)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Comando padrão (respeita PORT do ambiente)
CMD ["sh", "-c", "python run_server.py --host 0.0.0.0 --port ${PORT:-8000}"]