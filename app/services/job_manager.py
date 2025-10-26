"""
Gerenciador de Jobs de Treinamento
Baseado no PRD - Seção 7: Gerenciamento de Jobs
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from app.models.training import (
    TrainingJob, JobStatus, JobCreateRequest, TrainingConfig, 
    DatasetInfo, TrainingMetrics, ProgressUpdate
)
from app.core.config import settings
from app.services.yolo_trainer import YOLOTrainer

logger = logging.getLogger("jobs")


class JobManager:
    """Gerenciador de jobs de treinamento"""
    
    def __init__(self):
        self.jobs: Dict[str, TrainingJob] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_events: Dict[str, List[ProgressUpdate]] = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_JOBS)
        self.yolo_trainer = YOLOTrainer()
        
        # Arquivo de persistência
        self.jobs_file = settings.DATA_DIR / "jobs.json"
        
    async def initialize(self):
        """Inicializar gerenciador"""
        await self.load_jobs()
        logger.info(f"📋 Gerenciador de jobs inicializado - {len(self.jobs)} jobs carregados")
        
    async def cleanup(self):
        """Limpeza ao finalizar"""
        # Cancelar jobs ativos
        for job_id, task in self.active_jobs.items():
            if not task.done():
                task.cancel()
                logger.info(f"🛑 Job {job_id} cancelado durante cleanup")
                
        # Salvar estado
        await self.save_jobs()
        
        # Fechar executor
        self.executor.shutdown(wait=True)
        logger.info("🧹 Cleanup do gerenciador de jobs concluído")
        
    async def load_jobs(self):
        """Carregar jobs do arquivo"""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    jobs_data = json.load(f)
                    
                for job_data in jobs_data:
                    job = TrainingJob(**job_data)
                    self.jobs[job.id] = job
                    
                    # Resetar jobs que estavam rodando
                    if job.status == JobStatus.RUNNING:
                        job.status = JobStatus.FAILED
                        job.error_message = "Sistema reiniciado durante execução"
                        
                logger.info(f"📂 {len(self.jobs)} jobs carregados do arquivo")
                
        except Exception as e:
            logger.error(f"Erro ao carregar jobs: {e}")
            
    async def save_jobs(self):
        """Salvar jobs no arquivo"""
        try:
            jobs_data = []
            for job in self.jobs.values():
                # Converter para dict, tratando datetime
                job_dict = job.dict()
                
                # Converter datetime para string ISO
                for field in ['created_at', 'started_at', 'completed_at']:
                    if job_dict.get(field):
                        job_dict[field] = job_dict[field].isoformat()
                        
                jobs_data.append(job_dict)
                
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar jobs: {e}")
            
    def generate_job_id(self) -> str:
        """Gerar ID único para job"""
        return f"job_{uuid.uuid4().hex[:8]}"
        
    async def create_job(self, request: JobCreateRequest) -> TrainingJob:
        """Criar novo job de treinamento"""
        try:
            # Validar dataset
            dataset_path = Path(request.dataset_path)
            if not dataset_path.exists():
                raise ValueError(f"Dataset não encontrado: {request.dataset_path}")
                
            # Obter informações do dataset
            dataset_info = await self._analyze_dataset(dataset_path)
            
            # Criar job
            job = TrainingJob(
                id=self.generate_job_id(),
                name=request.name,
                status=JobStatus.PENDING,
                config=request.config,
                dataset=dataset_info,
                created_at=datetime.now()
            )
            
            # Adicionar à lista
            self.jobs[job.id] = job
            
            # Salvar
            await self.save_jobs()
            
            logger.info(f"✅ Job criado: {job.id} - {job.name}")
            
            return job
            
        except Exception as e:
            logger.error(f"Erro ao criar job: {e}")
            raise
            
    async def start_job(self, job_id: str) -> bool:
        """Iniciar job de treinamento"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError(f"Job não encontrado: {job_id}")
                
            if job.status != JobStatus.PENDING:
                raise ValueError(f"Job {job_id} não está pendente (status: {job.status})")
                
            # Verificar limite de jobs simultâneos
            active_count = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
            if active_count >= settings.MAX_CONCURRENT_JOBS:
                raise ValueError(f"Limite de jobs simultâneos atingido ({settings.MAX_CONCURRENT_JOBS})")
                
            # Atualizar status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            # Criar task assíncrona
            task = asyncio.create_task(self._run_training(job))
            self.active_jobs[job_id] = task
            
            await self.save_jobs()
            
            logger.info(f"🚀 Job iniciado: {job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar job {job_id}: {e}")
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.FAILED
                self.jobs[job_id].error_message = str(e)
            return False
            
    async def cancel_job(self, job_id: str) -> bool:
        """Cancelar job"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError(f"Job não encontrado: {job_id}")
                
            # Cancelar task se estiver rodando
            if job_id in self.active_jobs:
                task = self.active_jobs[job_id]
                if not task.done():
                    task.cancel()
                    
                del self.active_jobs[job_id]
                
            # Atualizar status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            await self.save_jobs()
            
            logger.info(f"🛑 Job cancelado: {job_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao cancelar job {job_id}: {e}")
            return False
            
    async def get_job(self, job_id: str) -> Optional[TrainingJob]:
        """Obter job por ID"""
        return self.jobs.get(job_id)
        
    async def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[TrainingJob]:
        """Listar jobs"""
        jobs = list(self.jobs.values())
        
        # Filtrar por status se especificado
        if status:
            jobs = [job for job in jobs if job.status == status]
            
        # Ordenar por data de criação (mais recentes primeiro)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limitar resultados
        return jobs[:limit]
        
    async def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas dos jobs"""
        total = len(self.jobs)
        pending = len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])
        running = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        completed = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        cancelled = len([j for j in self.jobs.values() if j.status == JobStatus.CANCELLED])
        
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "active": running
        }
        
    async def get_job_events(self, job_id: str) -> List[ProgressUpdate]:
        """Obter eventos de um job"""
        return self.job_events.get(job_id, [])
        
    async def add_job_event(self, job_id: str, event_type: str, data: Dict[str, Any]):
        """Adicionar evento a um job"""
        if job_id not in self.job_events:
            self.job_events[job_id] = []
            
        event = ProgressUpdate(
            job_id=job_id,
            event_type=event_type,
            data=data,
            timestamp=datetime.now()
        )
        
        self.job_events[job_id].append(event)
        
        # Manter apenas os últimos 1000 eventos por job
        if len(self.job_events[job_id]) > 1000:
            self.job_events[job_id] = self.job_events[job_id][-1000:]
            
    async def _analyze_dataset(self, dataset_path: Path) -> DatasetInfo:
        """Analisar dataset e extrair informações"""
        try:
            # Procurar arquivo data.yaml (formato YOLO)
            yaml_file = dataset_path / "data.yaml"
            if not yaml_file.exists():
                yaml_file = dataset_path / "dataset.yaml"
                
            if yaml_file.exists():
                import yaml
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                classes = data.get('names', [])
                if isinstance(classes, dict):
                    classes = list(classes.values())
                    
            else:
                # Tentar inferir classes dos diretórios
                classes = []
                labels_dir = dataset_path / "labels" / "train"
                if labels_dir.exists():
                    # Analisar arquivos de label para encontrar classes
                    class_ids = set()
                    for label_file in labels_dir.glob("*.txt"):
                        try:
                            with open(label_file, 'r') as f:
                                for line in f:
                                    parts = line.strip().split()
                                    if parts:
                                        class_ids.add(int(parts[0]))
                        except:
                            continue
                    classes = [f"class_{i}" for i in sorted(class_ids)]
                    
            # Contar imagens
            train_images = 0
            val_images = 0
            test_images = 0
            
            for split, var in [("train", "train_images"), ("val", "val_images"), ("test", "test_images")]:
                images_dir = dataset_path / "images" / split
                if images_dir.exists():
                    count = len(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + 
                              list(images_dir.glob("*.jpeg")))
                    if split == "train":
                        train_images = count
                    elif split == "val":
                        val_images = count
                    elif split == "test":
                        test_images = count
                        
            return DatasetInfo(
                name=dataset_path.name,
                path=str(dataset_path),
                classes=classes,
                train_images=train_images,
                val_images=val_images,
                test_images=test_images if test_images > 0 else None
            )
            
        except Exception as e:
            logger.error(f"Erro ao analisar dataset {dataset_path}: {e}")
            return DatasetInfo(
                name=dataset_path.name,
                path=str(dataset_path),
                classes=["unknown"],
                train_images=0,
                val_images=0
            )
            
    async def _run_training(self, job: TrainingJob):
        """Executar treinamento em thread separada"""
        try:
            logger.info(f"🏃 Iniciando treinamento do job {job.id}")
            
            # Callback para atualizações de progresso
            async def progress_callback(metrics: TrainingMetrics):
                job.metrics = metrics
                job.current_epoch = metrics.epoch
                job.progress_percent = (metrics.epoch / metrics.total_epochs) * 100
                
                await self.add_job_event(job.id, "metrics", metrics.dict())
                await self.save_jobs()
                
            # Executar treinamento
            result = await self.yolo_trainer.train(job, progress_callback)
            
            if result["success"]:
                job.status = JobStatus.COMPLETED
                job.model_path = result.get("model_path")
                job.weights_path = result.get("weights_path")
                job.logs_path = result.get("logs_path")
                job.best_metrics = result.get("best_metrics")
                
                await self.add_job_event(job.id, "completed", {
                    "model_path": job.model_path,
                    "best_metrics": job.best_metrics
                })
                
                logger.info(f"✅ Job {job.id} concluído com sucesso")
                
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.get("error", "Erro desconhecido")
                
                await self.add_job_event(job.id, "error", {
                    "error": job.error_message
                })
                
                logger.error(f"❌ Job {job.id} falhou: {job.error_message}")
                
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            logger.info(f"🛑 Job {job.id} foi cancelado")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            
            await self.add_job_event(job.id, "error", {
                "error": str(e)
            })
            
            logger.error(f"💥 Erro no job {job.id}: {e}")
            
        finally:
            job.completed_at = datetime.now()
            
            # Remover da lista de jobs ativos
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
                
            await self.save_jobs()