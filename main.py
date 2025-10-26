#!/usr/bin/env python3
"""
Sistema de Treinamento YOLO - Servidor Principal
Conforme especificado no PRD: Sistema completo para treinamento, validação e inferência
com interface web integrada e API REST.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Importações dos roteadores (serão criados)
from app.routers import jobs, models, datasets, system, training
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.services.system_monitor import SystemMonitor
from app.services.job_manager import JobManager
from app.services.sse_manager import SSEManager

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Gerenciadores globais (agora definidos em app/core/globals.py)
from app.core.globals import system_monitor, job_manager, sse_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando Sistema de Treinamento YOLO...")
    
    # Inicializar serviços
    await system_monitor.start()
    await job_manager.initialize()
    
    # Verificar dependências críticas
    try:
        import torch
        import ultralytics
        logger.info(f"✅ PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}")
        logger.info(f"✅ Ultralytics {ultralytics.__version__}")
    except ImportError as e:
        logger.error(f"❌ Dependência crítica não encontrada: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Finalizando Sistema de Treinamento YOLO...")
    await system_monitor.stop()
    await job_manager.cleanup()


# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Treinamento YOLO",
    description="API completa para treinamento, validação e inferência de modelos YOLO com Ultralytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Middleware de compressão
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Incluir roteadores da API
app.include_router(jobs.router)
app.include_router(system.router)
app.include_router(models.router)
app.include_router(datasets.router)
app.include_router(training.router)

# Servir arquivos estáticos do frontend (suporta dist/ ou build/)
FRONTEND_ROOT = Path(__file__).parent / "interface-design"
FRONTEND_DIST = None
for candidate in ["build", "dist"]:
    candidate_path = FRONTEND_ROOT / candidate
    index_exists = (candidate_path / "index.html").exists()
    assets_exists = (candidate_path / "assets").exists()
    if index_exists and assets_exists:
        FRONTEND_DIST = candidate_path
        break

if FRONTEND_DIST:
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    logger.info(f"✅ Servindo assets do frontend: {FRONTEND_DIST / 'assets'}")
else:
    logger.warning(f"⚠️  Diretório do frontend não encontrado com estrutura válida (index.html e assets). Execute 'npm run build' em interface-design.")


@app.get("/")
async def serve_frontend():
    """Servir a página principal do frontend"""
    if not FRONTEND_DIST:
        raise HTTPException(
            status_code=404,
            detail="Frontend não encontrado. Execute 'npm run build' na pasta interface-design"
        )
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        raise HTTPException(
            status_code=404, 
            detail="Frontend não encontrado. Execute 'npm run build' na pasta interface-design"
        )


@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde do sistema"""
    try:
        # Verificar recursos do sistema
        resources = await system_monitor.get_resources()
        
        # Verificar status dos jobs
        job_stats = await job_manager.get_stats()
        
        # GPU pode ser uma lista de GPUs; considerar disponível se houver pelo menos uma disponível
        gpu_available = any(g.available for g in resources.gpu) if resources.gpu else False
        
        return {
            "status": "healthy",
            "timestamp": system_monitor.get_timestamp(),
            "system": {
                "gpu_available": gpu_available,
                "memory_usage": resources.memory.usage_percent,
                "cpu_usage": resources.cpu.usage_percent
            },
            "jobs": job_stats,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Sistema indisponível")


@app.get("/api")
async def api_info():
    """Informações da API"""
    return {
        "name": "Sistema de Treinamento YOLO API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "endpoints": {
            "jobs": "/api/jobs",
            "models": "/api/models", 
            "datasets": "/api/datasets",
            "system": "/api/system",
            "training": "/api/training"
        }
    }


@app.get("/live")
async def live_check():
    """Endpoint de liveness simples para orquestradores"""
    return {"status": "ok"}

if __name__ == "__main__":
    # Configuração para desenvolvimento
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG
    )