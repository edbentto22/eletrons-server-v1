"""
Serviço de Treinamento YOLO com Ultralytics
Baseado no PRD - Seção 8: Integração com Ultralytics YOLO
"""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime

import torch
from ultralytics import YOLO
import yaml

from app.models.training import TrainingJob, TrainingMetrics, ModelType
from app.core.config import settings

logger = logging.getLogger("yolo_trainer")


class YOLOTrainer:
    """Serviço de treinamento YOLO"""
    
    def __init__(self):
        self.device = self._get_device()
        logger.info(f"🔧 YOLO Trainer inicializado - Device: {self.device}")
        
    def _get_device(self) -> str:
        """Detectar melhor device disponível"""
        if torch.cuda.is_available():
            device = "cuda"
            gpu_count = torch.cuda.device_count()
            logger.info(f"🚀 CUDA disponível - {gpu_count} GPU(s) detectada(s)")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
            logger.info("🍎 MPS (Apple Silicon) disponível")
        else:
            device = "cpu"
            logger.warning("⚠️ Usando CPU - Performance limitada")
            
        return device
        
    async def train(self, job: TrainingJob, progress_callback: Callable[[TrainingMetrics], None]) -> Dict[str, Any]:
        """Executar treinamento YOLO"""
        try:
            logger.info(f"🏋️ Iniciando treinamento YOLO para job {job.id}")
            
            # Preparar diretórios
            job_dir = settings.OUTPUTS_DIR / job.id
            job_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar modelo
            model = self._setup_model(job.config.model_type, job.config.pretrained)
            
            # Preparar dataset
            dataset_config = await self._prepare_dataset(job, job_dir)
            
            # Configurar argumentos de treinamento
            train_args = self._prepare_training_args(job, dataset_config, job_dir)
            
            # Callback personalizado para capturar métricas
            class TrainingCallback:
                def __init__(self, job_id: str, callback_func: Callable):
                    self.job_id = job_id
                    self.callback_func = callback_func
                    self.start_time = datetime.now()
                    
                def on_train_epoch_end(self, trainer):
                    """Callback chamado ao final de cada época"""
                    try:
                        epoch = trainer.epoch + 1
                        epochs = trainer.epochs
                        
                        # Extrair métricas do trainer
                        metrics_dict = {}
                        if hasattr(trainer, 'metrics') and trainer.metrics:
                            metrics_dict = trainer.metrics
                        elif hasattr(trainer, 'validator') and trainer.validator and hasattr(trainer.validator, 'metrics'):
                            metrics_dict = trainer.validator.metrics
                            
                        # Criar objeto de métricas
                        metrics = TrainingMetrics(
                            epoch=epoch,
                            total_epochs=epochs,
                            train_loss=metrics_dict.get('train/box_loss', 0.0),
                            val_loss=metrics_dict.get('val/box_loss', 0.0),
                            precision=metrics_dict.get('metrics/precision(B)', 0.0),
                            recall=metrics_dict.get('metrics/recall(B)', 0.0),
                            map50=metrics_dict.get('metrics/mAP50(B)', 0.0),
                            map50_95=metrics_dict.get('metrics/mAP50-95(B)', 0.0),
                            learning_rate=trainer.optimizer.param_groups[0]['lr'] if trainer.optimizer else 0.0,
                            elapsed_time=(datetime.now() - self.start_time).total_seconds()
                        )
                        
                        # Chamar callback assíncrono
                        asyncio.create_task(self.callback_func(metrics))
                        
                        logger.info(f"📊 Época {epoch}/{epochs} - mAP50: {metrics.map50:.3f}, Loss: {metrics.train_loss:.3f}")
                        
                    except Exception as e:
                        logger.error(f"Erro no callback de treinamento: {e}")
                        
            # Adicionar callback
            callback = TrainingCallback(job.id, progress_callback)
            model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
            
            # Executar treinamento
            logger.info(f"🚀 Iniciando treinamento com {train_args['epochs']} épocas")
            results = model.train(**train_args)
            
            # Processar resultados
            return await self._process_results(job, results, job_dir)
            
        except Exception as e:
            logger.error(f"💥 Erro no treinamento do job {job.id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _setup_model(self, model_type: ModelType, pretrained: bool = True) -> YOLO:
        """Configurar modelo YOLO"""
        try:
            # Mapear tipos de modelo para arquivos
            model_files = {
                ModelType.YOLOV8N: "yolov8n.pt" if pretrained else "yolov8n.yaml",
                ModelType.YOLOV8S: "yolov8s.pt" if pretrained else "yolov8s.yaml", 
                ModelType.YOLOV8M: "yolov8m.pt" if pretrained else "yolov8m.yaml",
                ModelType.YOLOV8L: "yolov8l.pt" if pretrained else "yolov8l.yaml",
                ModelType.YOLOV8X: "yolov8x.pt" if pretrained else "yolov8x.yaml",
                ModelType.YOLOV9C: "yolov9c.pt" if pretrained else "yolov9c.yaml",
                ModelType.YOLOV9E: "yolov9e.pt" if pretrained else "yolov9e.yaml",
                ModelType.YOLOV10N: "yolov10n.pt" if pretrained else "yolov10n.yaml",
                ModelType.YOLOV10S: "yolov10s.pt" if pretrained else "yolov10s.yaml",
                ModelType.YOLOV10M: "yolov10m.pt" if pretrained else "yolov10m.yaml",
                ModelType.YOLOV10L: "yolov10l.pt" if pretrained else "yolov10l.yaml",
                ModelType.YOLOV10X: "yolov10x.pt" if pretrained else "yolov10x.yaml"
            }
            
            model_file = model_files.get(model_type, "yolov8n.pt")
            
            logger.info(f"📦 Carregando modelo: {model_file}")
            model = YOLO(model_file)
            
            return model
            
        except Exception as e:
            logger.error(f"Erro ao configurar modelo {model_type}: {e}")
            raise
            
    async def _prepare_dataset(self, job: TrainingJob, job_dir: Path) -> str:
        """Preparar configuração do dataset"""
        try:
            dataset_path = Path(job.dataset.path)
            
            # Verificar se já existe data.yaml
            original_yaml = dataset_path / "data.yaml"
            if original_yaml.exists():
                # Copiar para diretório do job
                job_yaml = job_dir / "dataset.yaml"
                shutil.copy2(original_yaml, job_yaml)
                
                # Atualizar caminhos para absolutos
                with open(job_yaml, 'r') as f:
                    data = yaml.safe_load(f)
                    
                # Atualizar caminhos
                for split in ['train', 'val', 'test']:
                    if split in data:
                        split_path = dataset_path / data[split]
                        if not split_path.is_absolute():
                            data[split] = str(dataset_path / data[split])
                        else:
                            data[split] = str(split_path)
                            
                # Salvar configuração atualizada
                with open(job_yaml, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
                    
                return str(job_yaml)
                
            else:
                # Criar configuração do dataset
                config = {
                    'path': str(dataset_path),
                    'train': str(dataset_path / 'images' / 'train'),
                    'val': str(dataset_path / 'images' / 'val'),
                    'names': {i: name for i, name in enumerate(job.dataset.classes)}
                }
                
                # Adicionar test se existir
                test_path = dataset_path / 'images' / 'test'
                if test_path.exists():
                    config['test'] = str(test_path)
                    
                # Salvar configuração
                job_yaml = job_dir / "dataset.yaml"
                with open(job_yaml, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                    
                return str(job_yaml)
                
        except Exception as e:
            logger.error(f"Erro ao preparar dataset: {e}")
            raise
            
    def _prepare_training_args(self, job: TrainingJob, dataset_config: str, job_dir: Path) -> Dict[str, Any]:
        """Preparar argumentos de treinamento"""
        config = job.config
        
        args = {
            'data': dataset_config,
            'epochs': config.epochs,
            'batch': config.batch_size,
            'imgsz': config.image_size,
            'device': self.device,
            'project': str(job_dir.parent),
            'name': job.id,
            'exist_ok': True,
            'save': True,
            'save_period': max(1, config.epochs // 10),  # Salvar a cada 10% das épocas
            'cache': False,  # Desabilitar cache para economizar memória
            'workers': min(8, config.batch_size),
            'patience': config.patience,
            'verbose': True
        }
        
        # Configurações de otimização
        if config.optimizer:
            args['optimizer'] = config.optimizer
            
        if config.learning_rate:
            args['lr0'] = config.learning_rate
            
        # Configurações de augmentação
        if hasattr(config, 'augmentation') and config.augmentation:
            args.update({
                'hsv_h': 0.015,
                'hsv_s': 0.7,
                'hsv_v': 0.4,
                'degrees': 0.0,
                'translate': 0.1,
                'scale': 0.5,
                'shear': 0.0,
                'perspective': 0.0,
                'flipud': 0.0,
                'fliplr': 0.5,
                'mosaic': 1.0,
                'mixup': 0.0
            })
            
        # Configurações específicas do device
        if self.device == "cuda":
            args['amp'] = True  # Automatic Mixed Precision
            
        return args
        
    async def _process_results(self, job: TrainingJob, results, job_dir: Path) -> Dict[str, Any]:
        """Processar resultados do treinamento"""
        try:
            # Caminhos dos arquivos gerados
            runs_dir = job_dir.parent / job.id
            weights_dir = runs_dir / "weights"
            
            best_weights = weights_dir / "best.pt"
            last_weights = weights_dir / "last.pt"
            
            # Verificar se os pesos foram gerados
            if not best_weights.exists():
                raise FileNotFoundError("Arquivo best.pt não foi gerado")
                
            # Extrair métricas finais
            best_metrics = None
            if hasattr(results, 'results_dict'):
                metrics_dict = results.results_dict
                best_metrics = {
                    'map50': metrics_dict.get('metrics/mAP50(B)', 0.0),
                    'map50_95': metrics_dict.get('metrics/mAP50-95(B)', 0.0),
                    'precision': metrics_dict.get('metrics/precision(B)', 0.0),
                    'recall': metrics_dict.get('metrics/recall(B)', 0.0),
                    'final_loss': metrics_dict.get('train/box_loss', 0.0)
                }
                
            # Copiar arquivos importantes para local permanente
            models_dir = settings.MODELS_DIR / job.id
            models_dir.mkdir(parents=True, exist_ok=True)
            
            final_model_path = models_dir / "best.pt"
            shutil.copy2(best_weights, final_model_path)
            
            # Copiar logs se existirem
            logs_path = None
            results_csv = runs_dir / "results.csv"
            if results_csv.exists():
                logs_path = models_dir / "results.csv"
                shutil.copy2(results_csv, logs_path)
                
            logger.info(f"✅ Treinamento concluído - Modelo salvo em: {final_model_path}")
            
            return {
                "success": True,
                "model_path": str(final_model_path),
                "weights_path": str(final_model_path),
                "logs_path": str(logs_path) if logs_path else None,
                "best_metrics": best_metrics,
                "runs_dir": str(runs_dir)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resultados: {e}")
            return {
                "success": False,
                "error": f"Erro ao processar resultados: {str(e)}"
            }
            
    async def validate_model(self, model_path: str, dataset_config: str) -> Dict[str, Any]:
        """Validar modelo treinado"""
        try:
            model = YOLO(model_path)
            results = model.val(data=dataset_config, device=self.device)
            
            return {
                "success": True,
                "metrics": {
                    "map50": results.box.map50,
                    "map50_95": results.box.map,
                    "precision": results.box.mp,
                    "recall": results.box.mr
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na validação: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def predict(self, model_path: str, source: str, **kwargs) -> Dict[str, Any]:
        """Executar inferência com modelo treinado"""
        try:
            model = YOLO(model_path)
            results = model.predict(source=source, device=self.device, **kwargs)
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Erro na inferência: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def get_model_info(self, model_path: str) -> Dict[str, Any]:
        """Obter informações do modelo"""
        try:
            model = YOLO(model_path)
            
            return {
                "success": True,
                "info": {
                    "model_type": str(model.model),
                    "task": model.task,
                    "device": str(model.device),
                    "names": model.names if hasattr(model, 'names') else None
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter info do modelo: {e}")
            return {
                "success": False,
                "error": str(e)
            }