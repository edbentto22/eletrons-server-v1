"""
Funções auxiliares e utilitários
"""

import os
import json
import yaml
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_job_id() -> str:
    """Gerar ID único para job"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
    return f"job_{timestamp}_{random_hash}"


def format_bytes(bytes_value: int) -> str:
    """Formatar bytes em formato legível"""
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Formatar duração em formato legível"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_eta(current_epoch: int, total_epochs: int, elapsed_time: float) -> Optional[float]:
    """Calcular tempo estimado para conclusão"""
    if current_epoch == 0:
        return None
    
    time_per_epoch = elapsed_time / current_epoch
    remaining_epochs = total_epochs - current_epoch
    return remaining_epochs * time_per_epoch


def safe_json_load(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Carregar JSON com tratamento de erro"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Erro ao carregar JSON {file_path}: {e}")
        return {}


def safe_json_save(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """Salvar JSON com tratamento de erro"""
    try:
        # Criar diretório se não existir
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar JSON {file_path}: {e}")
        return False


def safe_yaml_load(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Carregar YAML com tratamento de erro"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Erro ao carregar YAML {file_path}: {e}")
        return {}


def safe_yaml_save(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """Salvar YAML com tratamento de erro"""
    try:
        # Criar diretório se não existir
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar YAML {file_path}: {e}")
        return False


def ensure_directory(path: Union[str, Path]) -> Path:
    """Garantir que diretório existe"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(filename: str) -> str:
    """Limpar nome de arquivo removendo caracteres inválidos"""
    import re
    # Remover caracteres especiais
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remover espaços múltiplos
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Remover underscores múltiplos
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remover underscore no início/fim
    cleaned = cleaned.strip('_')
    return cleaned


def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """Calcular hash de arquivo"""
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Erro ao calcular hash de {file_path}: {e}")
        return ""


def is_image_file(file_path: Union[str, Path]) -> bool:
    """Verificar se arquivo é uma imagem"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}
    return Path(file_path).suffix.lower() in image_extensions


def is_video_file(file_path: Union[str, Path]) -> bool:
    """Verificar se arquivo é um vídeo"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    return Path(file_path).suffix.lower() in video_extensions


def get_image_files(directory: Union[str, Path]) -> List[Path]:
    """Obter lista de arquivos de imagem em diretório"""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    image_files = []
    for file_path in directory.rglob('*'):
        if file_path.is_file() and is_image_file(file_path):
            image_files.append(file_path)
    
    return sorted(image_files)


def validate_yolo_dataset(dataset_path: Union[str, Path]) -> Dict[str, Any]:
    """Validar estrutura de dataset YOLO"""
    dataset_path = Path(dataset_path)
    result = {
        "valid": False,
        "issues": [],
        "statistics": {}
    }
    
    try:
        # Verificar estrutura básica
        required_dirs = ["images", "labels"]
        for dir_name in required_dirs:
            dir_path = dataset_path / dir_name
            if not dir_path.exists():
                result["issues"].append(f"Diretório obrigatório não encontrado: {dir_name}")
        
        # Verificar splits
        splits = ["train"]  # train é obrigatório
        optional_splits = ["val", "test"]
        
        for split in splits + optional_splits:
            images_dir = dataset_path / "images" / split
            labels_dir = dataset_path / "labels" / split
            
            if images_dir.exists():
                image_files = get_image_files(images_dir)
                label_files = list(labels_dir.glob("*.txt")) if labels_dir.exists() else []
                
                result["statistics"][f"{split}_images"] = len(image_files)
                result["statistics"][f"{split}_labels"] = len(label_files)
                
                # Verificar correspondência
                if labels_dir.exists():
                    image_stems = {f.stem for f in image_files}
                    label_stems = {f.stem for f in label_files}
                    
                    missing_labels = image_stems - label_stems
                    missing_images = label_stems - image_stems
                    
                    if missing_labels:
                        result["issues"].append(f"{split}: {len(missing_labels)} imagens sem labels")
                    if missing_images:
                        result["issues"].append(f"{split}: {len(missing_images)} labels sem imagens")
        
        # Verificar data.yaml
        yaml_files = ["data.yaml", "dataset.yaml"]
        yaml_found = False
        
        for yaml_file in yaml_files:
            yaml_path = dataset_path / yaml_file
            if yaml_path.exists():
                yaml_found = True
                yaml_data = safe_yaml_load(yaml_path)
                
                if "names" not in yaml_data:
                    result["issues"].append(f"{yaml_file}: campo 'names' não encontrado")
                else:
                    names = yaml_data["names"]
                    if isinstance(names, dict):
                        result["statistics"]["num_classes"] = len(names)
                        result["statistics"]["class_names"] = list(names.values())
                    elif isinstance(names, list):
                        result["statistics"]["num_classes"] = len(names)
                        result["statistics"]["class_names"] = names
                break
        
        if not yaml_found:
            result["issues"].append("Arquivo data.yaml ou dataset.yaml não encontrado")
        
        # Dataset é válido se não há issues críticos
        critical_issues = [issue for issue in result["issues"] if "obrigatório" in issue or "data.yaml" in issue]
        result["valid"] = len(critical_issues) == 0
        
    except Exception as e:
        result["issues"].append(f"Erro na validação: {str(e)}")
    
    return result


def create_yolo_yaml(
    dataset_path: Union[str, Path],
    class_names: List[str],
    train_path: str = "images/train",
    val_path: str = "images/val",
    test_path: Optional[str] = None
) -> bool:
    """Criar arquivo data.yaml para dataset YOLO"""
    try:
        dataset_path = Path(dataset_path)
        
        yaml_data = {
            "path": str(dataset_path.absolute()),
            "train": train_path,
            "val": val_path,
            "nc": len(class_names),
            "names": {i: name for i, name in enumerate(class_names)}
        }
        
        if test_path:
            yaml_data["test"] = test_path
        
        yaml_path = dataset_path / "data.yaml"
        return safe_yaml_save(yaml_data, yaml_path)
        
    except Exception as e:
        logger.error(f"Erro ao criar data.yaml: {e}")
        return False


def parse_yolo_annotation(annotation_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parsear arquivo de anotação YOLO"""
    annotations = []
    
    try:
        with open(annotation_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    annotation = {
                        "class_id": class_id,
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": width,
                        "height": height
                    }
                    
                    # Adicionar pontos de segmentação se existirem
                    if len(parts) > 5:
                        points = [float(p) for p in parts[5:]]
                        if len(points) % 2 == 0:  # Deve ser par (x, y)
                            annotation["segmentation"] = points
                    
                    annotations.append(annotation)
                    
    except Exception as e:
        logger.error(f"Erro ao parsear anotação {annotation_path}: {e}")
    
    return annotations


def calculate_dataset_statistics(dataset_path: Union[str, Path]) -> Dict[str, Any]:
    """Calcular estatísticas detalhadas do dataset"""
    dataset_path = Path(dataset_path)
    stats = {
        "total_images": 0,
        "total_annotations": 0,
        "splits": {},
        "classes": {},
        "annotation_stats": {
            "min_objects_per_image": float('inf'),
            "max_objects_per_image": 0,
            "avg_objects_per_image": 0
        }
    }
    
    try:
        # Carregar informações de classes
        yaml_data = {}
        for yaml_file in ["data.yaml", "dataset.yaml"]:
            yaml_path = dataset_path / yaml_file
            if yaml_path.exists():
                yaml_data = safe_yaml_load(yaml_path)
                break
        
        class_names = {}
        if "names" in yaml_data:
            names = yaml_data["names"]
            if isinstance(names, dict):
                class_names = names
            elif isinstance(names, list):
                class_names = {i: name for i, name in enumerate(names)}
        
        # Analisar cada split
        for split in ["train", "val", "test"]:
            images_dir = dataset_path / "images" / split
            labels_dir = dataset_path / "labels" / split
            
            if not images_dir.exists():
                continue
            
            image_files = get_image_files(images_dir)
            split_stats = {
                "images": len(image_files),
                "annotations": 0,
                "objects_per_class": {}
            }
            
            # Inicializar contadores de classes
            for class_id, class_name in class_names.items():
                split_stats["objects_per_class"][class_name] = 0
            
            # Analisar anotações
            objects_per_image = []
            
            for image_file in image_files:
                label_file = labels_dir / f"{image_file.stem}.txt"
                
                if label_file.exists():
                    annotations = parse_yolo_annotation(label_file)
                    objects_count = len(annotations)
                    objects_per_image.append(objects_count)
                    split_stats["annotations"] += objects_count
                    
                    # Contar objetos por classe
                    for ann in annotations:
                        class_id = ann["class_id"]
                        if class_id in class_names:
                            class_name = class_names[class_id]
                            split_stats["objects_per_class"][class_name] += 1
                else:
                    objects_per_image.append(0)
            
            # Calcular estatísticas de objetos por imagem
            if objects_per_image:
                split_stats["min_objects_per_image"] = min(objects_per_image)
                split_stats["max_objects_per_image"] = max(objects_per_image)
                split_stats["avg_objects_per_image"] = sum(objects_per_image) / len(objects_per_image)
                
                # Atualizar estatísticas globais
                stats["annotation_stats"]["min_objects_per_image"] = min(
                    stats["annotation_stats"]["min_objects_per_image"],
                    split_stats["min_objects_per_image"]
                )
                stats["annotation_stats"]["max_objects_per_image"] = max(
                    stats["annotation_stats"]["max_objects_per_image"],
                    split_stats["max_objects_per_image"]
                )
            
            stats["splits"][split] = split_stats
            stats["total_images"] += split_stats["images"]
            stats["total_annotations"] += split_stats["annotations"]
        
        # Calcular média global de objetos por imagem
        if stats["total_images"] > 0:
            stats["annotation_stats"]["avg_objects_per_image"] = stats["total_annotations"] / stats["total_images"]
        
        # Agregar estatísticas de classes
        for split_stats in stats["splits"].values():
            for class_name, count in split_stats["objects_per_class"].items():
                if class_name not in stats["classes"]:
                    stats["classes"][class_name] = 0
                stats["classes"][class_name] += count
        
        # Corrigir infinito se não há objetos
        if stats["annotation_stats"]["min_objects_per_image"] == float('inf'):
            stats["annotation_stats"]["min_objects_per_image"] = 0
            
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        stats["error"] = str(e)
    
    return stats


async def run_async_command(command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """Executar comando assíncrono"""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "returncode": process.returncode,
            "stdout": stdout.decode('utf-8', errors='ignore'),
            "stderr": stderr.decode('utf-8', errors='ignore'),
            "success": process.returncode == 0
        }
        
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configurar logging"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Formato de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Handler para arquivo se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_system_info() -> Dict[str, Any]:
    """Obter informações do sistema"""
    import platform
    import psutil
    
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_usage": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free
            }
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações do sistema: {e}")
        return {"error": str(e)}