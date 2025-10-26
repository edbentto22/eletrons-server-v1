"""
Roteador de Modelos
Baseado no PRD - Seção 4: Endpoints da API
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import FileResponse

from app.models.system import ModelInfo
from app.services.yolo_trainer import YOLOTrainer
from app.core.config import settings
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from app.core.security import verify_api_key

router = APIRouter(prefix="/models", tags=["models"], dependencies=[Depends(verify_api_key)])

# Instância do trainer YOLO
yolo_trainer = YOLOTrainer()


@router.get("/", response_model=List[ModelInfo])
async def list_models(
    model_type: Optional[str] = Query(None, description="Filtrar por tipo de modelo"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    Listar modelos disponíveis
    
    - **model_type**: Filtrar por tipo específico (opcional)
    - **limit**: Número máximo de modelos a retornar
    """
    try:
        models = []
        models_dir = settings.MODELS_DIR
        
        if not models_dir.exists():
            return models
            
        # Percorrer diretórios de modelos
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue
                
            # Procurar arquivos de modelo
            model_files = list(model_dir.glob("*.pt")) + list(model_dir.glob("*.onnx"))
            
            for model_file in model_files:
                try:
                    # Obter informações do modelo
                    model_info = await _get_model_info(model_file)
                    
                    # Filtrar por tipo se especificado
                    if model_type and model_info.model_type != model_type:
                        continue
                        
                    models.append(model_info)
                    
                except Exception as e:
                    # Log do erro mas continua processando outros modelos
                    print(f"Erro ao processar modelo {model_file}: {e}")
                    continue
                    
        # Ordenar por data de modificação (mais recentes primeiro)
        models.sort(key=lambda x: x.created_at, reverse=True)
        
        return models[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """
    Obter informações de um modelo específico
    
    - **model_id**: ID do modelo
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        model_info = await _get_model_info(model_path)
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter modelo: {str(e)}")


@router.post("/upload", response_model=ModelInfo)
async def upload_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    model_type: Optional[str] = Form(None)
):
    """
    Fazer upload de um modelo
    
    - **file**: Arquivo do modelo (.pt ou .onnx)
    - **name**: Nome do modelo
    - **description**: Descrição opcional
    - **model_type**: Tipo do modelo (opcional)
    """
    try:
        # Validar extensão do arquivo
        if not file.filename.endswith(('.pt', '.onnx')):
            raise HTTPException(status_code=400, detail="Apenas arquivos .pt e .onnx são suportados")
            
        # Criar diretório para o modelo
        model_id = name.lower().replace(' ', '_').replace('-', '_')
        model_dir = settings.MODELS_DIR / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar arquivo
        file_extension = Path(file.filename).suffix
        model_path = model_dir / f"model{file_extension}"
        
        with open(model_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Criar arquivo de metadados
        metadata = {
            "name": name,
            "description": description or "",
            "model_type": model_type or "custom",
            "uploaded_at": str(Path(model_path).stat().st_mtime)
        }
        
        metadata_path = model_dir / "metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Retornar informações do modelo
        model_info = await _get_model_info(model_path)
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload do modelo: {str(e)}")


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """
    Excluir um modelo
    
    - **model_id**: ID do modelo a ser excluído
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        # Remover diretório do modelo
        model_dir = model_path.parent
        shutil.rmtree(model_dir)
        
        return {"message": f"Modelo {model_id} excluído com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir modelo: {str(e)}")


@router.get("/{model_id}/download")
async def download_model(model_id: str):
    """
    Fazer download de um modelo
    
    - **model_id**: ID do modelo para download
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        return FileResponse(
            path=model_path,
            filename=f"{model_id}{model_path.suffix}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no download do modelo: {str(e)}")


@router.post("/{model_id}/validate")
async def validate_model(
    model_id: str,
    dataset_path: str = Form(..., description="Caminho para o dataset de validação")
):
    """
    Validar um modelo com um dataset
    
    - **model_id**: ID do modelo a ser validado
    - **dataset_path**: Caminho para o dataset de validação
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        # Verificar se dataset existe
        if not Path(dataset_path).exists():
            raise HTTPException(status_code=400, detail=f"Dataset não encontrado: {dataset_path}")
            
        # Executar validação
        result = await yolo_trainer.validate_model(str(model_path), dataset_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"Erro na validação: {result['error']}")
            
        return {
            "model_id": model_id,
            "dataset_path": dataset_path,
            "metrics": result["metrics"],
            "message": "Validação concluída com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na validação: {str(e)}")


@router.post("/{model_id}/predict")
async def predict_with_model(
    model_id: str,
    file: UploadFile = File(...),
    confidence: float = Form(0.5, ge=0.0, le=1.0),
    iou_threshold: float = Form(0.45, ge=0.0, le=1.0)
):
    """
    Executar inferência com um modelo
    
    - **model_id**: ID do modelo para inferência
    - **file**: Imagem para inferência
    - **confidence**: Threshold de confiança (0.0-1.0)
    - **iou_threshold**: Threshold de IoU para NMS (0.0-1.0)
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        # Validar tipo de arquivo
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Apenas arquivos de imagem são suportados")
            
        # Salvar imagem temporariamente
        temp_dir = settings.DATA_DIR / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"predict_{file.filename}"
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # Executar inferência
            result = await yolo_trainer.predict(
                str(model_path),
                str(temp_file),
                conf=confidence,
                iou=iou_threshold,
                save=False
            )
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=f"Erro na inferência: {result['error']}")
                
            # Processar resultados
            predictions = []
            for r in result["results"]:
                if hasattr(r, 'boxes') and r.boxes is not None:
                    for box in r.boxes:
                        predictions.append({
                            "class_id": int(box.cls.item()),
                            "class_name": r.names[int(box.cls.item())] if hasattr(r, 'names') else f"class_{int(box.cls.item())}",
                            "confidence": float(box.conf.item()),
                            "bbox": box.xyxy.tolist()[0]  # [x1, y1, x2, y2]
                        })
                        
            return {
                "model_id": model_id,
                "filename": file.filename,
                "predictions": predictions,
                "total_detections": len(predictions)
            }
            
        finally:
            # Limpar arquivo temporário
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na inferência: {str(e)}")


@router.get("/{model_id}/export/{format}")
async def export_model(
    model_id: str,
    format: str,
    optimize: bool = Query(False, description="Otimizar modelo exportado"),
    half: bool = Query(False, description="Usar precisão half (FP16)")
):
    """
    Exportar modelo para diferentes formatos
    
    - **model_id**: ID do modelo a ser exportado
    - **format**: Formato de destino (onnx, torchscript, tflite, etc.)
    - **optimize**: Otimizar modelo exportado
    - **half**: Usar precisão half (FP16)
    """
    try:
        model_path = _find_model_path(model_id)
        if not model_path:
            raise HTTPException(status_code=404, detail=f"Modelo {model_id} não encontrado")
            
        # Formatos suportados
        supported_formats = ['onnx', 'torchscript', 'tflite', 'edgetpu', 'tfjs', 'paddle']
        if format.lower() not in supported_formats:
            raise HTTPException(status_code=400, detail=f"Formato não suportado. Use: {', '.join(supported_formats)}")
            
        # Carregar modelo e exportar
        from ultralytics import YOLO
        model = YOLO(str(model_path))
        
        export_path = model.export(
            format=format.lower(),
            optimize=optimize,
            half=half
        )
        
        return {
            "model_id": model_id,
            "original_format": model_path.suffix,
            "exported_format": format.lower(),
            "exported_path": str(export_path),
            "message": f"Modelo exportado para {format.upper()} com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exportação: {str(e)}")


# Funções auxiliares

def _find_model_path(model_id: str) -> Optional[Path]:
    """Encontrar caminho do modelo pelo ID"""
    models_dir = settings.MODELS_DIR
    
    # Procurar diretório do modelo
    model_dir = models_dir / model_id
    if not model_dir.exists():
        return None
        
    # Procurar arquivo do modelo
    for ext in ['.pt', '.onnx']:
        model_file = model_dir / f"model{ext}"
        if model_file.exists():
            return model_file
            
    # Procurar qualquer arquivo .pt ou .onnx
    for pattern in ['*.pt', '*.onnx']:
        files = list(model_dir.glob(pattern))
        if files:
            return files[0]
            
    return None


async def _get_model_info(model_path: Path) -> ModelInfo:
    """Obter informações de um modelo"""
    try:
        # Informações básicas do arquivo
        stat = model_path.stat()
        
        # Tentar carregar metadados
        metadata_path = model_path.parent / "metadata.json"
        metadata = {}
        
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
        # Tentar obter informações do modelo YOLO
        model_info_dict = {}
        try:
            model_info_result = yolo_trainer.get_model_info(str(model_path))
            if model_info_result["success"]:
                model_info_dict = model_info_result["info"]
        except:
            pass
            
        return ModelInfo(
            id=model_path.parent.name,
            name=metadata.get("name", model_path.parent.name),
            description=metadata.get("description", ""),
            model_type=metadata.get("model_type", model_info_dict.get("model_type", "unknown")),
            file_path=str(model_path),
            file_size=stat.st_size,
            created_at=stat.st_ctime,
            task=model_info_dict.get("task", "detect"),
            classes=model_info_dict.get("names", []) if model_info_dict.get("names") else []
        )
        
    except Exception as e:
        # Retornar informações básicas em caso de erro
        stat = model_path.stat()
        return ModelInfo(
            id=model_path.parent.name,
            name=model_path.parent.name,
            description="Erro ao carregar metadados",
            model_type="unknown",
            file_path=str(model_path),
            file_size=stat.st_size,
            created_at=stat.st_ctime,
            task="detect",
            classes=[]
        )