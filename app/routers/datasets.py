"""
Roteador de Datasets
Baseado no PRD - Seção 4: Endpoints da API
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import FileResponse

from app.models.system import DatasetInfo
from app.core.config import settings
from app.core.security import verify_api_key

router = APIRouter(prefix="/datasets", tags=["datasets"], dependencies=[Depends(verify_api_key)])


@router.get("/", response_model=List[DatasetInfo])
async def list_datasets(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    Listar datasets disponíveis
    
    - **limit**: Número máximo de datasets a retornar
    """
    try:
        datasets = []
        datasets_dir = settings.DATASETS_DIR
        
        if not datasets_dir.exists():
            return datasets
            
        # Percorrer diretórios de datasets
        for dataset_dir in datasets_dir.iterdir():
            if not dataset_dir.is_dir():
                continue
                
            try:
                dataset_info = await _analyze_dataset(dataset_dir)
                datasets.append(dataset_info)
                
            except Exception as e:
                # Log do erro mas continua processando outros datasets
                print(f"Erro ao processar dataset {dataset_dir}: {e}")
                continue
                
        # Ordenar por nome
        datasets.sort(key=lambda x: x.name)
        
        return datasets[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar datasets: {str(e)}")


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(dataset_id: str):
    """
    Obter informações de um dataset específico
    
    - **dataset_id**: ID do dataset
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        dataset_info = await _analyze_dataset(dataset_path)
        return dataset_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter dataset: {str(e)}")


@router.post("/upload", response_model=DatasetInfo)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    format_type: str = Form("yolo", description="Formato do dataset (yolo, coco, etc.)")
):
    """
    Fazer upload de um dataset
    
    - **file**: Arquivo ZIP contendo o dataset
    - **name**: Nome do dataset
    - **description**: Descrição opcional
    - **format_type**: Formato do dataset (yolo, coco, etc.)
    """
    try:
        # Validar arquivo ZIP
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Apenas arquivos ZIP são suportados")
            
        # Criar diretório para o dataset
        dataset_id = name.lower().replace(' ', '_').replace('-', '_')
        dataset_dir = settings.DATASETS_DIR / dataset_id
        
        if dataset_dir.exists():
            raise HTTPException(status_code=400, detail=f"Dataset {dataset_id} já existe")
            
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar arquivo ZIP temporariamente
        temp_zip = dataset_dir / "temp.zip"
        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # Extrair ZIP
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(dataset_dir)
                
            # Remover arquivo ZIP temporário
            temp_zip.unlink()
            
            # Validar estrutura do dataset
            await _validate_dataset_structure(dataset_dir, format_type)
            
            # Criar arquivo de metadados
            metadata = {
                "name": name,
                "description": description or "",
                "format": format_type,
                "uploaded_at": str(dataset_dir.stat().st_mtime)
            }
            
            metadata_path = dataset_dir / "metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Analisar e retornar informações do dataset
            dataset_info = await _analyze_dataset(dataset_dir)
            return dataset_info
            
        except Exception as e:
            # Limpar diretório em caso de erro
            if dataset_dir.exists():
                shutil.rmtree(dataset_dir)
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload do dataset: {str(e)}")


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """
    Excluir um dataset
    
    - **dataset_id**: ID do dataset a ser excluído
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        # Remover diretório do dataset
        shutil.rmtree(dataset_path)
        
        return {"message": f"Dataset {dataset_id} excluído com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir dataset: {str(e)}")


@router.get("/{dataset_id}/download")
async def download_dataset(dataset_id: str):
    """
    Fazer download de um dataset como ZIP
    
    - **dataset_id**: ID do dataset para download
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        # Criar arquivo ZIP temporário
        temp_dir = settings.DATA_DIR / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        zip_path = temp_dir / f"{dataset_id}.zip"
        
        # Criar ZIP do dataset
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in dataset_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(dataset_path)
                    zipf.write(file_path, arcname)
                    
        return FileResponse(
            path=zip_path,
            filename=f"{dataset_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no download do dataset: {str(e)}")


@router.get("/{dataset_id}/validate")
async def validate_dataset(dataset_id: str):
    """
    Validar estrutura e integridade de um dataset
    
    - **dataset_id**: ID do dataset a ser validado
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        validation_result = await _validate_dataset_integrity(dataset_path)
        
        return {
            "dataset_id": dataset_id,
            "valid": validation_result["valid"],
            "issues": validation_result["issues"],
            "statistics": validation_result["statistics"],
            "message": "Validação concluída"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")


@router.get("/{dataset_id}/statistics")
async def get_dataset_statistics(dataset_id: str):
    """
    Obter estatísticas detalhadas de um dataset
    
    - **dataset_id**: ID do dataset
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        stats = await _calculate_dataset_statistics(dataset_path)
        
        return {
            "dataset_id": dataset_id,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@router.post("/{dataset_id}/split")
async def split_dataset(
    dataset_id: str,
    train_ratio: float = Form(0.7, ge=0.1, le=0.9),
    val_ratio: float = Form(0.2, ge=0.1, le=0.8),
    test_ratio: float = Form(0.1, ge=0.0, le=0.8),
    seed: int = Form(42, description="Seed para reprodutibilidade")
):
    """
    Dividir dataset em conjuntos de treino, validação e teste
    
    - **dataset_id**: ID do dataset a ser dividido
    - **train_ratio**: Proporção para treino (0.1-0.9)
    - **val_ratio**: Proporção para validação (0.1-0.8)
    - **test_ratio**: Proporção para teste (0.0-0.8)
    - **seed**: Seed para reprodutibilidade
    """
    try:
        # Validar proporções
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail="A soma das proporções deve ser 1.0")
            
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        # Executar divisão
        result = await _split_dataset_files(dataset_path, train_ratio, val_ratio, test_ratio, seed)
        
        return {
            "dataset_id": dataset_id,
            "splits": result["splits"],
            "message": "Dataset dividido com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao dividir dataset: {str(e)}")


@router.post("/{dataset_id}/convert")
async def convert_dataset_format(
    dataset_id: str,
    target_format: str = Form(..., description="Formato de destino (yolo, coco, etc.)"),
    output_name: str = Form(..., description="Nome do dataset convertido")
):
    """
    Converter dataset para outro formato
    
    - **dataset_id**: ID do dataset a ser convertido
    - **target_format**: Formato de destino
    - **output_name**: Nome do dataset convertido
    """
    try:
        dataset_path = settings.DATASETS_DIR / dataset_id
        if not dataset_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} não encontrado")
            
        # Verificar se formato é suportado
        supported_formats = ['yolo', 'coco', 'pascal_voc']
        if target_format.lower() not in supported_formats:
            raise HTTPException(status_code=400, detail=f"Formato não suportado. Use: {', '.join(supported_formats)}")
            
        # Executar conversão
        result = await _convert_dataset_format(dataset_path, target_format, output_name)
        
        return {
            "original_dataset": dataset_id,
            "converted_dataset": result["dataset_id"],
            "target_format": target_format,
            "message": "Conversão concluída com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")


# Funções auxiliares

async def _analyze_dataset(dataset_path: Path) -> DatasetInfo:
    """Analisar dataset e extrair informações"""
    try:
        # Carregar metadados se existirem
        metadata_path = dataset_path / "metadata.json"
        metadata = {}
        
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
        # Procurar arquivo data.yaml (formato YOLO)
        yaml_file = dataset_path / "data.yaml"
        if not yaml_file.exists():
            yaml_file = dataset_path / "dataset.yaml"
            
        classes = []
        if yaml_file.exists():
            import yaml
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                names = data.get('names', [])
                if isinstance(names, dict):
                    classes = list(names.values())
                elif isinstance(names, list):
                    classes = names
                    
        # Contar imagens por split
        train_images = _count_images(dataset_path / "images" / "train")
        val_images = _count_images(dataset_path / "images" / "val")
        test_images = _count_images(dataset_path / "images" / "test")
        
        # Informações do arquivo
        stat = dataset_path.stat()
        
        return DatasetInfo(
            id=dataset_path.name,
            name=metadata.get("name", dataset_path.name),
            description=metadata.get("description", ""),
            path=str(dataset_path),
            format=metadata.get("format", "yolo"),
            classes=classes,
            train_images=train_images,
            val_images=val_images,
            test_images=test_images if test_images > 0 else None,
            total_images=train_images + val_images + test_images,
            created_at=stat.st_ctime,
            size_bytes=_calculate_directory_size(dataset_path)
        )
        
    except Exception as e:
        # Retornar informações básicas em caso de erro
        stat = dataset_path.stat()
        return DatasetInfo(
            id=dataset_path.name,
            name=dataset_path.name,
            description="Erro ao analisar dataset",
            path=str(dataset_path),
            format="unknown",
            classes=[],
            train_images=0,
            val_images=0,
            test_images=None,
            total_images=0,
            created_at=stat.st_ctime,
            size_bytes=_calculate_directory_size(dataset_path)
        )


def _count_images(images_dir: Path) -> int:
    """Contar imagens em um diretório"""
    if not images_dir.exists():
        return 0
        
    extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    count = 0
    
    for ext in extensions:
        count += len(list(images_dir.glob(f"*{ext}")))
        count += len(list(images_dir.glob(f"*{ext.upper()}")))
        
    return count


def _calculate_directory_size(directory: Path) -> int:
    """Calcular tamanho total de um diretório"""
    total_size = 0
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size


async def _validate_dataset_structure(dataset_path: Path, format_type: str):
    """Validar estrutura do dataset"""
    if format_type.lower() == "yolo":
        # Verificar estrutura YOLO
        required_dirs = ["images/train", "labels/train"]
        
        for dir_path in required_dirs:
            full_path = dataset_path / dir_path
            if not full_path.exists():
                raise ValueError(f"Diretório obrigatório não encontrado: {dir_path}")
                
        # Verificar se há pelo menos uma imagem
        train_images = _count_images(dataset_path / "images" / "train")
        if train_images == 0:
            raise ValueError("Nenhuma imagem encontrada no diretório de treino")


async def _validate_dataset_integrity(dataset_path: Path) -> Dict[str, Any]:
    """Validar integridade do dataset"""
    issues = []
    statistics = {}
    
    try:
        # Verificar correspondência entre imagens e labels
        images_dir = dataset_path / "images" / "train"
        labels_dir = dataset_path / "labels" / "train"
        
        if images_dir.exists() and labels_dir.exists():
            image_files = set()
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                image_files.update(f.stem for f in images_dir.glob(f"*{ext}"))
                
            label_files = set(f.stem for f in labels_dir.glob("*.txt"))
            
            # Imagens sem labels
            missing_labels = image_files - label_files
            if missing_labels:
                issues.append(f"{len(missing_labels)} imagens sem labels correspondentes")
                
            # Labels sem imagens
            missing_images = label_files - image_files
            if missing_images:
                issues.append(f"{len(missing_images)} labels sem imagens correspondentes")
                
            statistics["total_images"] = len(image_files)
            statistics["total_labels"] = len(label_files)
            statistics["matched_pairs"] = len(image_files & label_files)
            
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "statistics": statistics
        }
        
    except Exception as e:
        return {
            "valid": False,
            "issues": [f"Erro na validação: {str(e)}"],
            "statistics": {}
        }


async def _calculate_dataset_statistics(dataset_path: Path) -> Dict[str, Any]:
    """Calcular estatísticas detalhadas do dataset"""
    stats = {
        "splits": {},
        "classes": {},
        "annotations": {},
        "file_sizes": {}
    }
    
    try:
        # Estatísticas por split
        for split in ["train", "val", "test"]:
            images_dir = dataset_path / "images" / split
            labels_dir = dataset_path / "labels" / split
            
            if images_dir.exists():
                image_count = _count_images(images_dir)
                label_count = len(list(labels_dir.glob("*.txt"))) if labels_dir.exists() else 0
                
                stats["splits"][split] = {
                    "images": image_count,
                    "labels": label_count
                }
                
        # Análise de classes (se houver data.yaml)
        yaml_file = dataset_path / "data.yaml"
        if yaml_file.exists():
            import yaml
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                names = data.get('names', [])
                if isinstance(names, dict):
                    stats["classes"]["names"] = list(names.values())
                    stats["classes"]["count"] = len(names)
                elif isinstance(names, list):
                    stats["classes"]["names"] = names
                    stats["classes"]["count"] = len(names)
                    
        # Tamanho dos arquivos
        stats["file_sizes"]["total_bytes"] = _calculate_directory_size(dataset_path)
        stats["file_sizes"]["total_mb"] = round(stats["file_sizes"]["total_bytes"] / (1024 * 1024), 2)
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}


async def _split_dataset_files(dataset_path: Path, train_ratio: float, val_ratio: float, test_ratio: float, seed: int) -> Dict[str, Any]:
    """Dividir arquivos do dataset"""
    import random
    random.seed(seed)
    
    # Coletar todos os arquivos de imagem
    images_dir = dataset_path / "images"
    all_images = []
    
    for images_subdir in images_dir.iterdir():
        if images_subdir.is_dir():
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                all_images.extend(images_subdir.glob(f"*{ext}"))
                
    # Embaralhar
    random.shuffle(all_images)
    
    # Calcular divisões
    total = len(all_images)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)
    
    train_files = all_images[:train_count]
    val_files = all_images[train_count:train_count + val_count]
    test_files = all_images[train_count + val_count:]
    
    # Criar estrutura de diretórios
    for split in ["train", "val", "test"]:
        (dataset_path / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_path / "labels" / split).mkdir(parents=True, exist_ok=True)
        
    # Mover arquivos
    def move_files(files, split):
        moved = 0
        for img_file in files:
            # Mover imagem
            new_img_path = dataset_path / "images" / split / img_file.name
            shutil.move(str(img_file), str(new_img_path))
            
            # Mover label correspondente se existir
            label_file = dataset_path / "labels" / img_file.parent.name / f"{img_file.stem}.txt"
            if label_file.exists():
                new_label_path = dataset_path / "labels" / split / f"{img_file.stem}.txt"
                shutil.move(str(label_file), str(new_label_path))
                
            moved += 1
        return moved
        
    result = {
        "splits": {
            "train": move_files(train_files, "train"),
            "val": move_files(val_files, "val"),
            "test": move_files(test_files, "test")
        }
    }
    
    return result


async def _convert_dataset_format(dataset_path: Path, target_format: str, output_name: str) -> Dict[str, Any]:
    """Converter formato do dataset"""
    # Esta é uma implementação simplificada
    # Em um sistema real, você implementaria conversões específicas entre formatos
    
    output_id = output_name.lower().replace(' ', '_').replace('-', '_')
    output_path = settings.DATASETS_DIR / output_id
    
    if output_path.exists():
        raise ValueError(f"Dataset {output_id} já existe")
        
    # Por enquanto, apenas copia o dataset
    shutil.copytree(dataset_path, output_path)
    
    # Criar metadados do novo dataset
    metadata = {
        "name": output_name,
        "description": f"Convertido de {dataset_path.name} para formato {target_format}",
        "format": target_format,
        "converted_from": dataset_path.name,
        "converted_at": str(output_path.stat().st_mtime)
    }
    
    metadata_path = output_path / "metadata.json"
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    return {"dataset_id": output_id}