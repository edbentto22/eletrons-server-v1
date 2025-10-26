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
import os
import re

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
            model = self._setup_model(job.config.base_model, getattr(job.config, 'pretrained', True))
            
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
            try:
                model = YOLO(model_file)
            except Exception as e:
                # Fallback: se não conseguir carregar pesos .pt (ex.: sem internet), usar YAML
                if model_file.endswith('.pt'):
                    yaml_file = model_file.replace('.pt', '.yaml')
                    logger.warning(f"Falha ao carregar '{model_file}' ({e}). Tentando YAML '{yaml_file}' sem pesos pré-treinados.")
                    model = YOLO(yaml_file)
                else:
                    raise
            
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
                # Normalizar dataset para garantir índices de classes contínuos e caminhos absolutos
                with open(original_yaml, 'r') as f:
                    data = yaml.safe_load(f) or {}
                original_names = data.get('names', [])
                names_list: list[str] = []
                id_map_from_yaml: dict[int, int] = {}
                if isinstance(original_names, dict):
                    sorted_ids = sorted(original_names.keys())
                    names_list = [original_names[i] for i in sorted_ids]
                    for new_idx, orig_id in enumerate(sorted_ids):
                        id_map_from_yaml[int(orig_id)] = new_idx
                elif isinstance(original_names, list):
                    names_list = original_names
                else:
                    names_list = []

                norm_root = job_dir / "normalized_dataset"
                (norm_root / "images").mkdir(parents=True, exist_ok=True)
                (norm_root / "labels").mkdir(parents=True, exist_ok=True)

                class_mapping: dict[int, int] = dict(id_map_from_yaml)

                if not class_mapping:
                    used_ids: set[int] = set()
                    for split in ['train', 'val', 'test']:
                        labels_dir = dataset_path / 'labels' / split
                        if labels_dir.exists():
                            for lbl_file in labels_dir.glob('*.txt'):
                                with open(lbl_file, 'r') as lf:
                                    for line in lf:
                                        parts = line.strip().split()
                                        if parts:
                                            try:
                                                used_ids.add(int(parts[0]))
                                            except ValueError:
                                                continue
                    sorted_used = sorted(used_ids)
                    for new_idx, orig_id in enumerate(sorted_used):
                        class_mapping[orig_id] = new_idx
                    if names_list:
                        names_list = [names_list[i] for i in sorted_used if i < len(names_list)]
                    else:
                        names_list = [f"class_{i}" for i in sorted_used]

                def remap_label_file(src_path: Path, dst_path: Path):
                    lines_out = []
                    if not src_path.exists():
                        return False
                    with open(src_path, 'r') as lf:
                        for line in lf:
                            parts = line.strip().split()
                            if not parts:
                                continue
                            try:
                                orig_cls = int(parts[0])
                            except ValueError:
                                lines_out.append(line)
                                continue
                            if orig_cls in class_mapping:
                                parts[0] = str(class_mapping[orig_cls])
                            else:
                                logger.warning(f"Classe {orig_cls} não mapeada em {src_path}, descartando anotação.")
                                continue
                            lines_out.append(" ".join(parts) + "\n")
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(dst_path, 'w') as df:
                        df.writelines(lines_out)
                    return True

                splits = []
                for split in ['train', 'val', 'test']:
                    images_dir = dataset_path / 'images' / split
                    labels_dir = dataset_path / 'labels' / split
                    if images_dir.exists():
                        splits.append(split)
                        (norm_root / 'images' / split).mkdir(parents=True, exist_ok=True)
                        (norm_root / 'labels' / split).mkdir(parents=True, exist_ok=True)
                        for img_file in images_dir.glob('*'):
                            if img_file.is_file():
                                dst = norm_root / 'images' / split / img_file.name
                                try:
                                    if dst.exists():
                                        dst.unlink()
                                    os.symlink(img_file, dst)
                                except Exception:
                                    shutil.copy2(img_file, dst)
                        if labels_dir.exists():
                            for lbl_file in labels_dir.glob('*.txt'):
                                dst_lbl = norm_root / 'labels' / split / lbl_file.name
                                remap_label_file(lbl_file, dst_lbl)

                names_dict = {i: name for i, name in enumerate(names_list)} if names_list else {}
                job_yaml = job_dir / "dataset.yaml"
                config = {
                    'path': str(norm_root),
                    'train': str(norm_root / 'images' / 'train') if 'train' in splits else None,
                    'val': str(norm_root / 'images' / 'val') if 'val' in splits else None,
                }
                if 'test' in splits:
                    config['test'] = str(norm_root / 'images' / 'test')
                if names_dict:
                    config['names'] = names_dict
                config = {k: v for k, v in config.items() if v is not None}
                with open(job_yaml, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                return str(job_yaml)

                
            else:
                # Criar dataset normalizado com índices de classes contínuos
                norm_root = job_dir / "normalized_dataset"
                (norm_root / "images").mkdir(parents=True, exist_ok=True)
                (norm_root / "labels").mkdir(parents=True, exist_ok=True)
                
                # Construir mapeamento original_id -> novo_id com base na lista de classes detectadas
                class_mapping: dict[int, int] = {}
                mapping_possible = True
                for new_idx, name in enumerate(job.dataset.classes):
                    m = re.search(r"(\d+)$", str(name))
                    if not m:
                        mapping_possible = False
                        break
                    orig_id = int(m.group(1))
                    class_mapping[orig_id] = new_idx
                
                # Função para remapear um arquivo de label
                def remap_label_file(src_path: Path, dst_path: Path):
                    lines_out = []
                    if not src_path.exists():
                        return False
                    with open(src_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if not parts:
                                continue
                            try:
                                orig_cls = int(parts[0])
                            except ValueError:
                                # Mantém linha se não conseguir interpretar índice
                                lines_out.append(line)
                                continue
                            if mapping_possible and orig_cls in class_mapping:
                                parts[0] = str(class_mapping[orig_cls])
                            elif mapping_possible:
                                # Índice fora do conjunto conhecido; registrar e descartar a anotação
                                logger.warning(f"Label com classe inválida {orig_cls} em {src_path}, descartando anotação.")
                                continue
                            lines_out.append(" ".join(parts) + "\n")
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(dst_path, 'w') as f:
                        f.writelines(lines_out)
                    return True
                
                # Copiar imagens (symlinks) e remapear labels para cada split existente
                splits = []
                for split in ['train', 'val', 'test']:
                    images_dir = dataset_path / 'images' / split
                    labels_dir = dataset_path / 'labels' / split
                    if images_dir.exists():
                        splits.append(split)
                        # Preparar diretórios
                        (norm_root / 'images' / split).mkdir(parents=True, exist_ok=True)
                        (norm_root / 'labels' / split).mkdir(parents=True, exist_ok=True)
                        # Symlink imagens
                        for img_file in images_dir.glob('*'):
                            if img_file.is_file():
                                dst = norm_root / 'images' / split / img_file.name
                                try:
                                    if dst.exists():
                                        dst.unlink()
                                    os.symlink(img_file, dst)
                                except Exception:
                                    # fallback: copiar arquivo
                                    shutil.copy2(img_file, dst)
                        # Remapear labels
                        if labels_dir.exists():
                            for lbl_file in labels_dir.glob('*.txt'):
                                dst_lbl = norm_root / 'labels' / split / lbl_file.name
                                remap_label_file(lbl_file, dst_lbl)
                
                # Configuração do dataset.yaml para o dataset normalizado
                names_dict = {i: name for i, name in enumerate(job.dataset.classes)}
                config = {
                    'path': str(norm_root),
                    'train': str(norm_root / 'images' / 'train') if 'train' in splits else None,
                    'val': str(norm_root / 'images' / 'val') if 'val' in splits else None,
                    'names': names_dict
                }
                # Remover chaves None
                config = {k: v for k, v in config.items() if v is not None}
                # Adicionar test se existir
                if 'test' in splits:
                    config['test'] = str(norm_root / 'images' / 'test')
                    
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