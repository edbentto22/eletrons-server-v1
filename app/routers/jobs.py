from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from app.models.training import TrainingJob, JobCreateRequest
from app.services.job_manager import JobManager
from app.services.sse_manager import SSEManager, create_sse_response
from app.core.security import verify_api_key

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(verify_api_key)])

job_manager = JobManager()
sse_manager = SSEManager()


@router.get("/", response_model=list[TrainingJob])
async def list_jobs(status: Optional[str] = None):
    try:
        jobs = await job_manager.list_jobs(status=status)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar jobs: {str(e)}")


@router.post("/", response_model=TrainingJob)
async def create_job(job_request: JobCreateRequest):
    try:
        job = await job_manager.create_job(job_request)
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar job: {str(e)}")


@router.get("/{job_id}", response_model=TrainingJob)
async def get_job(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job


@router.post("/{job_id}/start")
async def start_job(job_id: str):
    try:
        await job_manager.start_job(job_id)
        return {"message": "Job iniciado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar job: {str(e)}")


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    try:
        await job_manager.cancel_job(job_id)
        return {"message": "Job cancelado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar job: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    try:
        # Placeholder de delete (não implementado)
        return {"message": f"Job {job_id} removido"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover job: {str(e)}")


@router.get("/{job_id}/stream")
async def stream_job_events(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return await create_sse_response("jobs", job_id)


@router.get("/stream/all")
async def stream_all_jobs_events():
    return await create_sse_response("jobs", "all")


@router.get("/stats")
async def get_job_stats():
    try:
        stats = await job_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")