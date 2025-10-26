"""
Validadores para dados e configurações
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import validator
import logging

logger = logging.getLogger(__name__)


def validate_model_type(model_type: str) -> str:
    """Validar tipo de modelo YOLO"""
    valid_models = [
        # YOLOv8
        "yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x",
        # YOLOv9
        "yolov9c", "yolov9e",
        # YOLOv10
        "yolov10n", "yolov10s", "yolov10m", "yolov10b", "yolov10l", "yolov10x",
        # YOLOv11
        "yolov11n", "yolov11s", "yolov11m", "yolov11l", "yolov11x",
        # Segmentação
        "yolov8n-seg", "yolov8s-seg", "yolov8m-seg", "yolov8l-seg", "yolov8x-seg",
        # Classificação
        "yolov8n-cls", "yolov8s-cls", "yolov8m-cls", "yolov8l-cls", "yolov8x-cls",
        # Pose
        "yolov8n-pose", "yolov8s-pose", "yolov8m-pose", "yolov8l-pose", "yolov8x-pose"
    ]
    
    if model_type not in valid_models:
        raise ValueError(f"Modelo inválido. Use um dos: {', '.join(valid_models)}")
    
    return model_type


def validate_image_size(image_size: Union[int, List[int]]) -> Union[int, List[int]]:
    """Validar tamanho de imagem"""
    if isinstance(image_size, int):
        if image_size < 32 or image_size > 2048:
            raise ValueError("Tamanho de imagem deve estar entre 32 e 2048 pixels")
        
        # Deve ser múltiplo de 32 para YOLO
        if image_size % 32 != 0:
            raise ValueError("Tamanho de imagem deve ser múltiplo de 32")
        
        return image_size
    
    elif isinstance(image_size, list):
        if len(image_size) != 2:
            raise ValueError("Lista de tamanho deve ter exatamente 2 valores [altura, largura]")
        
        height, width = image_size
        
        if not (32 <= height <= 2048 and 32 <= width <= 2048):
            raise ValueError("Dimensões devem estar entre 32 e 2048 pixels")
        
        if height % 32 != 0 or width % 32 != 0:
            raise ValueError("Dimensões devem ser múltiplas de 32")
        
        return image_size
    
    else:
        raise ValueError("Tamanho de imagem deve ser int ou lista [altura, largura]")


def validate_batch_size(batch_size: int, available_memory_gb: Optional[float] = None) -> int:
    """Validar tamanho do batch"""
    if batch_size < 1:
        raise ValueError("Batch size deve ser pelo menos 1")
    
    if batch_size > 256:
        raise ValueError("Batch size muito grande (máximo 256)")
    
    # Verificar se é potência de 2 (recomendado para performance)
    if batch_size & (batch_size - 1) != 0:
        logger.warning(f"Batch size {batch_size} não é potência de 2. Recomendado: 1, 2, 4, 8, 16, 32, 64, 128")
    
    # Estimar uso de memória se informação disponível
    if available_memory_gb:
        # Estimativa grosseira: ~100MB por imagem no batch para YOLOv8
        estimated_memory_gb = (batch_size * 100) / 1024  # MB para GB
        
        if estimated_memory_gb > available_memory_gb * 0.8:  # 80% da memória disponível
            suggested_batch = max(1, int((available_memory_gb * 0.8 * 1024) / 100))
            logger.warning(
                f"Batch size {batch_size} pode exceder memória disponível. "
                f"Sugerido: {suggested_batch}"
            )
    
    return batch_size


def validate_epochs(epochs: int) -> int:
    """Validar número de épocas"""
    if epochs < 1:
        raise ValueError("Número de épocas deve ser pelo menos 1")
    
    if epochs > 1000:
        raise ValueError("Número de épocas muito alto (máximo 1000)")
    
    return epochs


def validate_learning_rate(learning_rate: float) -> float:
    """Validar taxa de aprendizado"""
    if learning_rate <= 0:
        raise ValueError("Taxa de aprendizado deve ser positiva")
    
    if learning_rate > 1.0:
        raise ValueError("Taxa de aprendizado muito alta (máximo 1.0)")
    
    # Avisos para valores não usuais
    if learning_rate > 0.1:
        logger.warning(f"Taxa de aprendizado {learning_rate} é alta. Valores típicos: 0.001-0.01")
    
    if learning_rate < 1e-6:
        logger.warning(f"Taxa de aprendizado {learning_rate} é muito baixa")
    
    return learning_rate


def validate_optimizer(optimizer: str) -> str:
    """Validar otimizador"""
    valid_optimizers = ["SGD", "Adam", "AdamW", "RMSprop", "LBFGS"]
    
    if optimizer not in valid_optimizers:
        raise ValueError(f"Otimizador inválido. Use um dos: {', '.join(valid_optimizers)}")
    
    return optimizer


def validate_dataset_path(dataset_path: Union[str, Path]) -> Path:
    """Validar caminho do dataset"""
    path = Path(dataset_path)
    
    if not path.exists():
        raise ValueError(f"Dataset não encontrado: {path}")
    
    if not path.is_dir():
        raise ValueError(f"Caminho deve ser um diretório: {path}")
    
    # Verificar estrutura básica YOLO
    required_dirs = ["images"]
    for dir_name in required_dirs:
        dir_path = path / dir_name
        if not dir_path.exists():
            raise ValueError(f"Diretório obrigatório não encontrado: {dir_name}")
    
    # Verificar se há pelo menos um split de treino
    train_dir = path / "images" / "train"
    if not train_dir.exists():
        raise ValueError("Diretório 'images/train' não encontrado")
    
    # Verificar se há imagens
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    has_images = False
    
    for ext in image_extensions:
        if list(train_dir.glob(f"*{ext}")) or list(train_dir.glob(f"*{ext.upper()}")):
            has_images = True
            break
    
    if not has_images:
        raise ValueError("Nenhuma imagem encontrada no diretório de treino")
    
    return path


def validate_model_path(model_path: Union[str, Path]) -> Path:
    """Validar caminho do modelo"""
    path = Path(model_path)
    
    if not path.exists():
        raise ValueError(f"Modelo não encontrado: {path}")
    
    if not path.is_file():
        raise ValueError(f"Caminho deve ser um arquivo: {path}")
    
    # Verificar extensão
    valid_extensions = ['.pt', '.pth', '.onnx', '.engine', '.tflite']
    if path.suffix.lower() not in valid_extensions:
        raise ValueError(f"Extensão inválida. Use: {', '.join(valid_extensions)}")
    
    return path


def validate_job_name(job_name: str) -> str:
    """Validar nome do job"""
    if not job_name or not job_name.strip():
        raise ValueError("Nome do job não pode estar vazio")
    
    job_name = job_name.strip()
    
    if len(job_name) > 100:
        raise ValueError("Nome do job muito longo (máximo 100 caracteres)")
    
    # Verificar caracteres válidos
    if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', job_name):
        raise ValueError("Nome do job contém caracteres inválidos. Use apenas letras, números, espaços, hífens, underscores e pontos")
    
    return job_name


def validate_device(device: str) -> str:
    """Validar dispositivo"""
    valid_devices = ["auto", "cpu", "cuda", "mps"]
    
    # Permitir especificação de GPU específica (ex: cuda:0, cuda:1)
    if device.startswith("cuda:"):
        try:
            gpu_id = int(device.split(":")[1])
            if gpu_id < 0:
                raise ValueError("ID da GPU deve ser não-negativo")
            return device
        except (IndexError, ValueError):
            raise ValueError("Formato inválido para dispositivo CUDA. Use 'cuda:N' onde N é o ID da GPU")
    
    if device not in valid_devices:
        raise ValueError(f"Dispositivo inválido. Use um dos: {', '.join(valid_devices)} ou 'cuda:N'")
    
    return device


def validate_augmentation_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validar parâmetros de data augmentation"""
    valid_params = {
        "hsv_h": (0.0, 1.0),      # Hue
        "hsv_s": (0.0, 1.0),      # Saturation
        "hsv_v": (0.0, 1.0),      # Value
        "degrees": (0.0, 180.0),   # Rotation
        "translate": (0.0, 1.0),   # Translation
        "scale": (0.0, 2.0),       # Scale
        "shear": (0.0, 45.0),      # Shear
        "perspective": (0.0, 0.001), # Perspective
        "flipud": (0.0, 1.0),      # Flip up-down
        "fliplr": (0.0, 1.0),      # Flip left-right
        "mosaic": (0.0, 1.0),      # Mosaic
        "mixup": (0.0, 1.0),       # MixUp
        "copy_paste": (0.0, 1.0),  # Copy-paste
    }
    
    validated_params = {}
    
    for param, value in params.items():
        if param not in valid_params:
            logger.warning(f"Parâmetro de augmentation desconhecido: {param}")
            continue
        
        min_val, max_val = valid_params[param]
        
        if not isinstance(value, (int, float)):
            raise ValueError(f"Parâmetro {param} deve ser numérico")
        
        if not (min_val <= value <= max_val):
            raise ValueError(f"Parâmetro {param} deve estar entre {min_val} e {max_val}")
        
        validated_params[param] = float(value)
    
    return validated_params


def validate_export_format(export_format: str) -> str:
    """Validar formato de exportação"""
    valid_formats = [
        "onnx", "openvino", "engine", "coreml", "saved_model",
        "pb", "tflite", "edgetpu", "tfjs", "paddle"
    ]
    
    if export_format.lower() not in valid_formats:
        raise ValueError(f"Formato de exportação inválido. Use um dos: {', '.join(valid_formats)}")
    
    return export_format.lower()


def validate_confidence_threshold(confidence: float) -> float:
    """Validar threshold de confiança"""
    if not (0.0 <= confidence <= 1.0):
        raise ValueError("Threshold de confiança deve estar entre 0.0 e 1.0")
    
    return confidence


def validate_iou_threshold(iou: float) -> float:
    """Validar threshold de IoU"""
    if not (0.0 <= iou <= 1.0):
        raise ValueError("Threshold de IoU deve estar entre 0.0 e 1.0")
    
    return iou


def validate_class_names(class_names: List[str]) -> List[str]:
    """Validar nomes de classes"""
    if not class_names:
        raise ValueError("Lista de classes não pode estar vazia")
    
    if len(class_names) > 1000:
        raise ValueError("Muitas classes (máximo 1000)")
    
    # Verificar duplicatas
    if len(class_names) != len(set(class_names)):
        raise ValueError("Nomes de classes duplicados encontrados")
    
    # Validar cada nome
    validated_names = []
    for i, name in enumerate(class_names):
        if not isinstance(name, str):
            raise ValueError(f"Nome da classe {i} deve ser string")
        
        name = name.strip()
        if not name:
            raise ValueError(f"Nome da classe {i} não pode estar vazio")
        
        if len(name) > 50:
            raise ValueError(f"Nome da classe {i} muito longo (máximo 50 caracteres)")
        
        validated_names.append(name)
    
    return validated_names


def validate_training_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validar configuração completa de treinamento"""
    validated_config = {}
    
    # Validações obrigatórias
    required_fields = ["model_type", "epochs", "batch_size", "image_size"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Campo obrigatório ausente: {field}")
    
    # Aplicar validações específicas
    validated_config["model_type"] = validate_model_type(config["model_type"])
    validated_config["epochs"] = validate_epochs(config["epochs"])
    validated_config["batch_size"] = validate_batch_size(config["batch_size"])
    validated_config["image_size"] = validate_image_size(config["image_size"])
    
    # Validações opcionais
    if "learning_rate" in config:
        validated_config["learning_rate"] = validate_learning_rate(config["learning_rate"])
    
    if "optimizer" in config:
        validated_config["optimizer"] = validate_optimizer(config["optimizer"])
    
    if "device" in config:
        validated_config["device"] = validate_device(config["device"])
    
    if "augmentation_params" in config:
        validated_config["augmentation_params"] = validate_augmentation_params(config["augmentation_params"])
    
    # Copiar outros campos sem validação específica
    other_fields = [
        "patience", "save_period", "workers", "project", "name",
        "exist_ok", "pretrained", "verbose", "seed", "deterministic",
        "single_cls", "rect", "cos_lr", "close_mosaic", "resume",
        "amp", "fraction", "profile", "freeze", "multi_scale",
        "overlap_mask", "mask_ratio", "dropout", "val"
    ]
    
    for field in other_fields:
        if field in config:
            validated_config[field] = config[field]
    
    return validated_config


def validate_system_resources(resources: Dict[str, Any]) -> bool:
    """Validar se recursos do sistema são suficientes"""
    warnings = []
    
    # Verificar memória RAM
    if "memory" in resources:
        memory_gb = resources["memory"].get("available", 0) / (1024**3)
        if memory_gb < 4:
            warnings.append("Memória RAM insuficiente (mínimo recomendado: 4GB)")
    
    # Verificar espaço em disco
    if "disk" in resources:
        disk_gb = resources["disk"].get("free", 0) / (1024**3)
        if disk_gb < 10:
            warnings.append("Espaço em disco insuficiente (mínimo recomendado: 10GB)")
    
    # Verificar GPU
    if "gpu" in resources and resources["gpu"]:
        gpu_info = resources["gpu"][0]  # Primeira GPU
        gpu_memory_gb = gpu_info.get("memory_total", 0) / (1024**3)
        
        if gpu_memory_gb < 2:
            warnings.append("Memória GPU insuficiente (mínimo recomendado: 2GB)")
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    # Retorna True se não há warnings críticos
    critical_warnings = [w for w in warnings if "insuficiente" in w]
    return len(critical_warnings) == 0


class ConfigValidator:
    """Classe para validação de configurações complexas"""
    
    @staticmethod
    def validate_job_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar configuração completa do job"""
        try:
            # Validar configuração de treinamento
            if "training_config" in config:
                config["training_config"] = validate_training_config(config["training_config"])
            
            # Validar nome do job
            if "name" in config:
                config["name"] = validate_job_name(config["name"])
            
            # Validar dataset
            if "dataset_path" in config:
                config["dataset_path"] = str(validate_dataset_path(config["dataset_path"]))
            
            # Validar modelo base se especificado
            if "base_model_path" in config and config["base_model_path"]:
                config["base_model_path"] = str(validate_model_path(config["base_model_path"]))
            
            return config
            
        except Exception as e:
            logger.error(f"Erro na validação da configuração: {e}")
            raise
    
    @staticmethod
    def validate_inference_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar configuração de inferência"""
        validated_config = {}
        
        # Validar modelo
        if "model_path" in config:
            validated_config["model_path"] = str(validate_model_path(config["model_path"]))
        
        # Validar thresholds
        if "confidence" in config:
            validated_config["confidence"] = validate_confidence_threshold(config["confidence"])
        
        if "iou" in config:
            validated_config["iou"] = validate_iou_threshold(config["iou"])
        
        # Validar dispositivo
        if "device" in config:
            validated_config["device"] = validate_device(config["device"])
        
        # Validar tamanho de imagem
        if "image_size" in config:
            validated_config["image_size"] = validate_image_size(config["image_size"])
        
        # Copiar outros campos
        other_fields = ["max_det", "classes", "agnostic_nms", "retina_masks", "embed"]
        for field in other_fields:
            if field in config:
                validated_config[field] = config[field]
        
        return validated_config