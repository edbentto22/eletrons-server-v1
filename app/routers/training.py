"""
Roteador de Treinamento
Baseado no PRD - Seção 4: Endpoints da API
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from app.models.training import TrainingJob, JobCreateRequest, ProgressUpdate
from app.services.sse_manager import SSEManager, create_sse_response
from app.core.config import settings
from app.core.security import verify_api_key
from app.core.globals import job_manager

router = APIRouter(prefix="/training", tags=["training"], dependencies=[Depends(verify_api_key)])

# Usar a instância global do JobManager já inicializada
sse_manager = SSEManager()


@router.post("/start", response_model=TrainingJob)
async def start_training(
    job_request: JobCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    Iniciar um novo treinamento
    
    - **job_request**: Configurações do treinamento
    """
    try:
        # Criar job
        job = await job_manager.create_job(job_request)
        
        # Iniciar treinamento em background
        background_tasks.add_task(job_manager.start_job, job.id)
        
        return job
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar treinamento: {str(e)}")


@router.post("/{job_id}/pause")
async def pause_training(job_id: str):
    """
    Pausar um treinamento em execução
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status not in ["running", "training"]:
            raise HTTPException(status_code=400, detail=f"Job {job_id} não está em execução")
            
        # Pausar job (não implementado no JobManager)
        # Placeholder para futura implementação
        raise HTTPException(status_code=501, detail="Pausa de treinamento ainda não implementada")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao pausar treinamento: {str(e)}")


@router.post("/{job_id}/resume")
async def resume_training(
    job_id: str,
    background_tasks: BackgroundTasks
):
    """
    Retomar um treinamento pausado
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status != "paused":
            raise HTTPException(status_code=400, detail=f"Job {job_id} não está pausado")
            
        # Retomar job (não implementado no JobManager)
        raise HTTPException(status_code=501, detail="Retomada de treinamento ainda não implementada")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao retomar treinamento: {str(e)}")


@router.post("/{job_id}/stop")
async def stop_training(job_id: str):
    """
    Parar um treinamento
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Job {job_id} já foi finalizado")
            
        # Cancelar job
        await job_manager.cancel_job(job_id)
        
        return {"message": f"Job {job_id} cancelado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao parar treinamento: {str(e)}")


@router.get("/{job_id}/progress", response_model=ProgressUpdate)
async def get_training_progress(job_id: str):
    """
    Obter progresso atual do treinamento
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        # Obter último progresso
        # Placeholder: usa último evento de métricas se disponível
        events = await job_manager.get_job_events(job_id)
        metrics_events = [e for e in events if e.event_type == "metrics"]
        if not metrics_events:
            raise HTTPException(status_code=404, detail="Nenhum progresso disponível")
        
        return metrics_events[-1]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter progresso: {str(e)}")


@router.get("/{job_id}/metrics")
async def get_training_metrics(job_id: str):
    """
    Obter métricas detalhadas do treinamento
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        # Obter métricas a partir do job
        metrics = job.metrics
        
        return {
            "job_id": job_id,
            "metrics": metrics,
            "status": job.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")


@router.get("/{job_id}/logs")
async def get_training_logs(
    job_id: str,
    lines: int = 100,
    level: Optional[str] = None
):
    """
    Obter logs do treinamento
    
    - **job_id**: ID do job de treinamento
    - **lines**: Número de linhas a retornar (padrão: 100)
    - **level**: Filtrar por nível de log (DEBUG, INFO, WARNING, ERROR)
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        # Placeholder de logs (integração futura com arquivos de log)
        logs = [
            f"[INFO] Job {job_id} - Epoch {job.current_epoch} - loss={job.metrics.train_loss if job.metrics else 'N/A'}"
        ]
        
        return {
            "job_id": job_id,
            "logs": logs,
            "total_lines": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter logs: {str(e)}")


@router.get("/{job_id}/stream")
async def stream_training_progress(job_id: str):
    """
    Stream de progresso do treinamento via SSE
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        return await create_sse_response("training", job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no stream: {str(e)}")


@router.get("/{job_id}/results")
async def get_training_results(job_id: str):
    """
    Obter resultados finais do treinamento
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job {job_id} ainda não foi concluído")
            
        # Obter resultados (placeholders)
        results = {
            "best_metrics": job.best_metrics,
            "model_path": job.model_path,
            "weights_path": job.weights_path
        }
        
        return {
            "job_id": job_id,
            "results": results,
            "model_path": job.model_path,
            "metrics": job.metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resultados: {str(e)}")


@router.post("/{job_id}/validate")
async def validate_trained_model(job_id: str):
    """
    Validar modelo treinado
    
    - **job_id**: ID do job de treinamento
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job {job_id} não foi concluído")
            
        if not job.model_path:
            raise HTTPException(status_code=400, detail=f"Modelo não encontrado para job {job_id}")
            
        # Validar modelo (integração com YOLOTrainer futura)
        validation_results = {"status": "ok", "message": "Validação placeholder"}
        
        return {
            "job_id": job_id,
            "validation": validation_results,
            "model_path": job.model_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")


@router.get("/{job_id}/export")
async def export_trained_model(
    job_id: str,
    format: str = "onnx",
    optimize: bool = True
):
    """
    Exportar modelo treinado para outros formatos
    
    - **job_id**: ID do job de treinamento
    - **format**: Formato de exportação (onnx, tensorrt, coreml, etc.)
    - **optimize**: Aplicar otimizações durante exportação
    """
    try:
        job = await job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
            
        if job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job {job_id} não foi concluído")
            
        if not job.model_path:
            raise HTTPException(status_code=400, detail=f"Modelo não encontrado para job {job_id}")
            
        # Exportar modelo (placeholder)
        export_result = {"path": job.model_path, "size": 0, "time": 0}
        
        return {
            "job_id": job_id,
            "original_model": job.model_path,
            "exported_model": export_result["path"],
            "format": format,
            "size_bytes": export_result["size"],
            "export_time": export_result["time"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exportação: {str(e)}")


@router.get("/active")
async def get_active_trainings():
    """
    Listar treinamentos ativos (em execução ou pausados)
    """
    try:
        # Jobs em execução
        active_jobs = [j for j in job_manager.jobs.values() if j.status == "running"]
        
        return {
            "active_jobs": active_jobs,
            "count": len(active_jobs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar treinamentos ativos: {str(e)}")


@router.get("/queue")
async def get_training_queue():
    """
    Obter fila de treinamentos
    """
    try:
        # Placeholder de fila
        queue_info = {"jobs": [], "total": 0, "estimated_wait": 0}
        
        return {
            "queue": queue_info["jobs"],
            "total_queued": queue_info["total"],
            "estimated_wait_time": queue_info["estimated_wait"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter fila: {str(e)}")


@router.post("/queue/clear")
async def clear_training_queue():
    """
    Limpar fila de treinamentos (cancelar jobs pendentes)
    """
    try:
        # Placeholder
        cleared_count = 0
        
        return {
            "message": f"{cleared_count} jobs removidos da fila",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar fila: {str(e)}")


@router.get("/statistics")
async def get_training_statistics():
    """
    Obter estatísticas gerais de treinamento
    """
    try:
        # Placeholder: usar stats do JobManager
        stats = await job_manager.get_stats()
        
        return {
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.post("/cleanup")
async def cleanup_training_data(
    older_than_days: int = 30,
    keep_successful: bool = True,
    dry_run: bool = False
):
    """
    Limpar dados antigos de treinamento
    
    - **older_than_days**: Remover dados mais antigos que X dias
    - **keep_successful**: Manter dados de treinamentos bem-sucedidos
    - **dry_run**: Apenas simular limpeza sem remover arquivos
    """
    try:
        # Placeholder: nenhuma ação real
        cleanup_result = {"removed": 0, "kept": 0}
        
        return {
            "cleanup_result": cleanup_result,
            "dry_run": dry_run,
            "message": "Limpeza concluída" if not dry_run else "Simulação de limpeza concluída"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na limpeza: {str(e)}")


@router.get("/templates")
async def get_training_templates():
    """
    Obter templates de configuração de treinamento
    """
    try:
        templates = {
            "object_detection": {
                "name": "Detecção de Objetos",
                "description": "Template para detecção de objetos genéricos",
                "config": {
                    "model_type": "yolov8n",
                    "epochs": 100,
                    "batch_size": 16,
                    "image_size": 640,
                    "optimizer": "AdamW",
                    "learning_rate": 0.001,
                    "augmentation": True
                }
            },
            "small_objects": {
                "name": "Objetos Pequenos",
                "description": "Otimizado para detecção de objetos pequenos",
                "config": {
                    "model_type": "yolov8s",
                    "epochs": 150,
                    "batch_size": 8,
                    "image_size": 1024,
                    "optimizer": "AdamW",
                    "learning_rate": 0.0005,
                    "augmentation": True,
                    "mosaic": 0.5
                }
            },
            "fast_inference": {
                "name": "Inferência Rápida",
                "description": "Modelo otimizado para velocidade",
                "config": {
                    "model_type": "yolov8n",
                    "epochs": 50,
                    "batch_size": 32,
                    "image_size": 416,
                    "optimizer": "SGD",
                    "learning_rate": 0.01,
                    "augmentation": False
                }
            },
            "high_accuracy": {
                "name": "Alta Precisão",
                "description": "Modelo otimizado para precisão máxima",
                "config": {
                    "model_type": "yolov8x",
                    "epochs": 300,
                    "batch_size": 4,
                    "image_size": 1280,
                    "optimizer": "AdamW",
                    "learning_rate": 0.0001,
                    "augmentation": True,
                    "mixup": 0.1,
                    "copy_paste": 0.1
                }
            }
        }
        
        return {
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter templates: {str(e)}")


@router.post("/benchmark")
async def run_training_benchmark(
    model_types: list = ["yolov8n", "yolov8s", "yolov8m"],
    dataset_id: str = "coco128",
    epochs: int = 10
):
    """
    Executar benchmark de diferentes modelos
    
    - **model_types**: Lista de modelos para testar
    - **dataset_id**: Dataset para benchmark
    - **epochs**: Número de épocas para cada teste
    """
    try:
        # Placeholder de benchmark
        benchmark_result = {"id": "benchmark_001"}
        
        return {
            "benchmark_id": benchmark_result["id"],
            "models_tested": model_types,
            "dataset": dataset_id,
            "epochs": epochs,
            "status": "started",
            "message": "Benchmark iniciado"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no benchmark: {str(e)}")