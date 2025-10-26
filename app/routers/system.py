"""
Roteador de Sistema e Recursos
Baseado no PRD - Seção 4: Endpoints da API
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.models.system import SystemResources, SystemStatus, ModelInfo, DatasetInfo
from app.services.system_monitor import SystemMonitor
from app.services.sse_manager import create_sse_response
from app.core.config import settings
from app.core.security import verify_api_key

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(verify_api_key)])

# Instância do monitor de sistema
system_monitor = SystemMonitor()


@router.get("/resources", response_model=SystemResources)
async def get_system_resources():
    """
    Obter recursos do sistema em tempo real
    
    Retorna informações sobre CPU, GPU, memória e disco
    """
    try:
        resources = await system_monitor.get_resources()
        return resources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter recursos do sistema: {str(e)}")


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """
    Obter status geral do sistema
    
    Retorna status consolidado e alertas do sistema
    """
    try:
        status = await system_monitor.get_system_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status do sistema: {str(e)}")


@router.get("/gpu")
async def get_gpu_info():
    """
    Obter informações detalhadas das GPUs
    
    Retorna lista com informações de todas as GPUs disponíveis
    """
    try:
        gpu_info = await system_monitor.get_gpu_info()
        return {"gpus": gpu_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações da GPU: {str(e)}")


@router.get("/cpu")
async def get_cpu_info():
    """
    Obter informações detalhadas da CPU
    
    Retorna informações sobre processador e uso
    """
    try:
        cpu_info = await system_monitor.get_cpu_info()
        return cpu_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações da CPU: {str(e)}")


@router.get("/memory")
async def get_memory_info():
    """
    Obter informações detalhadas da memória
    
    Retorna informações sobre RAM e swap
    """
    try:
        memory_info = await system_monitor.get_memory_info()
        return memory_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações da memória: {str(e)}")


@router.get("/disk")
async def get_disk_info():
    """
    Obter informações detalhadas do disco
    
    Retorna informações sobre espaço em disco
    """
    try:
        disk_info = await system_monitor.get_disk_info()
        return disk_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações do disco: {str(e)}")


@router.get("/stream")
async def stream_system_resources():
    """
    Stream de recursos do sistema em tempo real (SSE)
    
    Monitora recursos do sistema continuamente
    """
    try:
        return await create_sse_response("system")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar stream do sistema: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Verificação de saúde do sistema
    
    Endpoint simples para verificar se o sistema está respondendo
    """
    try:
        resources = await system_monitor.get_resources()
        
        # Verificações básicas de saúde
        health_status = "healthy"
        issues = []
        
        # Verificar uso de CPU
        if resources.cpu.usage_percent > 90:
            health_status = "warning"
            issues.append("CPU usage high")
            
        # Verificar uso de memória
        if resources.memory.usage_percent > 90:
            health_status = "warning"
            issues.append("Memory usage high")
            
        # Verificar espaço em disco
        if resources.disk and any(d.usage_percent > 90 for d in resources.disk):
            health_status = "critical"
            issues.append("Disk space critical")
            
        return {
            "status": health_status,
            "timestamp": resources.timestamp,
            "issues": issues,
            "uptime": resources.cpu.uptime if hasattr(resources.cpu, "uptime") else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/config")
async def get_system_config():
    """
    Obter configurações do sistema
    
    Retorna configurações relevantes do sistema
    """
    try:
        config = {
            "data_dir": str(settings.DATA_DIR),
            "models_dir": str(settings.MODELS_DIR),
            "datasets_dir": str(settings.DATASETS_DIR),
            "outputs_dir": str(settings.OUTPUTS_DIR),
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
            "default_model": settings.DEFAULT_MODEL,
            "default_epochs": settings.DEFAULT_EPOCHS,
            "default_batch_size": settings.DEFAULT_BATCH_SIZE,
            "default_image_size": settings.DEFAULT_IMAGE_SIZE,
            "monitoring_interval": settings.SYSTEM_MONITOR_INTERVAL
        }
        
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter configurações: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO"
):
    """
    Obter logs do sistema
    
    - **lines**: Número de linhas a retornar (padrão: 100)
    - **level**: Nível mínimo de log (DEBUG, INFO, WARNING, ERROR)
    """
    try:
        import os
        from pathlib import Path
        
        log_file = settings.LOGS_DIR / "app.log"
        
        if not log_file.exists():
            return {"logs": [], "message": "Arquivo de log não encontrado"}
            
        # Ler últimas linhas do arquivo
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # Filtrar por nível se especificado
        if level != "DEBUG":
            level_priority = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            min_priority = level_priority.get(level.upper(), 1)
            
            filtered_lines = []
            for line in all_lines:
                for log_level, priority in level_priority.items():
                    if log_level in line and priority >= min_priority:
                        filtered_lines.append(line)
                        break
                        
            all_lines = filtered_lines
            
        # Retornar últimas N linhas
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {str(e)}")


@router.post("/cleanup")
async def cleanup_system():
    """
    Executar limpeza do sistema
    
    Remove arquivos temporários e otimiza espaço
    """
    try:
        import shutil
        import tempfile
        
        cleaned_items = []
        total_freed = 0
        
        # Limpar diretório temporário do sistema
        temp_dir = Path(tempfile.gettempdir())
        for item in temp_dir.glob("yolo_*"):
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                shutil.rmtree(item, ignore_errors=True)
                cleaned_items.append(f"Temp dir: {item.name}")
                total_freed += size
                
        # Limpar logs antigos (manter apenas últimos 7 dias)
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=7)
        
        logs_dir = settings.LOGS_DIR
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned_items.append(f"Old log: {log_file.name}")
                    total_freed += size
                    
        return {
            "message": "Limpeza concluída",
            "items_cleaned": cleaned_items,
            "space_freed_bytes": total_freed,
            "space_freed_mb": round(total_freed / (1024 * 1024), 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza do sistema: {str(e)}")


@router.get("/performance")
async def get_performance_metrics():
    """
    Obter métricas de performance do sistema
    
    Retorna métricas detalhadas para monitoramento
    """
    try:
        import psutil
        import time
        
        # Coletar métricas em dois momentos para calcular deltas
        cpu_percent_1 = psutil.cpu_percent(interval=None)
        time.sleep(0.1)
        cpu_percent_2 = psutil.cpu_percent(interval=None)
        
        # Informações de rede
        net_io = psutil.net_io_counters()
        
        # Informações de processos
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 1.0:  # Apenas processos com uso significativo
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Ordenar por uso de CPU
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return {
            "cpu": {
                "usage_percent": cpu_percent_2,
                "cores": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "top_processes": processes[:10],
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas de performance: {str(e)}")