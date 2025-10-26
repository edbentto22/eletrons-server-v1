#!/usr/bin/env python3
"""
Script de Setup do Sistema de Treinamento YOLO
Configura o ambiente e inicializa o sistema
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse


def run_command(command, check=True, shell=False):
    """Executar comando do sistema"""
    print(f"Executando: {command}")
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=check, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {e}", file=sys.stderr)
        return False


def check_python_version():
    """Verificar versão do Python"""
    print("Verificando versão do Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def create_virtual_environment():
    """Criar ambiente virtual"""
    print("\nCriando ambiente virtual...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  Ambiente virtual já existe")
        return True
    
    if run_command("python -m venv venv"):
        print("✅ Ambiente virtual criado")
        return True
    else:
        print("❌ Erro ao criar ambiente virtual")
        return False


def activate_and_install_dependencies():
    """Ativar ambiente virtual e instalar dependências"""
    print("\nInstalando dependências...")
    
    # Determinar comando de ativação baseado no OS
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # Atualizar pip
    if not run_command(f"{python_path} -m pip install --upgrade pip"):
        print("❌ Erro ao atualizar pip")
        return False
    
    # Instalar dependências
    if not run_command(f"{pip_path} install -r requirements.txt"):
        print("❌ Erro ao instalar dependências")
        return False
    
    print("✅ Dependências instaladas")
    return True


def create_directories():
    """Criar estrutura de diretórios"""
    print("\nCriando estrutura de diretórios...")
    
    directories = [
        "data",
        "data/models",
        "data/datasets",
        "data/outputs",
        "data/logs",
        "data/temp",
        "interface-design/dist"  # Para o frontend
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 {directory}")
    
    print("✅ Diretórios criados")
    return True


def setup_environment_file():
    """Configurar arquivo de ambiente"""
    print("\nConfigurando arquivo de ambiente...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("⚠️  Arquivo .env já existe")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Arquivo .env criado a partir do .env.example")
        print("⚠️  Edite o arquivo .env com suas configurações específicas")
    else:
        # Criar .env básico
        basic_env = """# Configurações Básicas
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
        with open(env_file, 'w') as f:
            f.write(basic_env)
        print("✅ Arquivo .env básico criado")
    
    return True


def download_sample_models():
    """Baixar modelos de exemplo"""
    print("\nBaixando modelos YOLO de exemplo...")
    
    models_dir = Path("data/models")
    
    # Lista de modelos para baixar
    sample_models = [
        "yolov8n.pt",
        "yolov8s.pt"
    ]
    
    try:
        # Importar ultralytics para baixar modelos
        from ultralytics import YOLO
        
        for model_name in sample_models:
            model_path = models_dir / model_name
            if not model_path.exists():
                print(f"📥 Baixando {model_name}...")
                model = YOLO(model_name)  # Isso baixa o modelo automaticamente
                # Mover para o diretório correto
                downloaded_path = Path.home() / ".ultralytics" / "models" / model_name
                if downloaded_path.exists():
                    shutil.copy(downloaded_path, model_path)
                    print(f"✅ {model_name} baixado")
            else:
                print(f"⚠️  {model_name} já existe")
        
        return True
        
    except ImportError:
        print("⚠️  Ultralytics não instalado ainda. Modelos serão baixados na primeira execução.")
        return True
    except Exception as e:
        print(f"⚠️  Erro ao baixar modelos: {e}")
        return True  # Não é crítico


def build_frontend():
    """Fazer build do frontend"""
    print("\nFazendo build do frontend...")
    
    frontend_dir = Path("interface-design")
    if not frontend_dir.exists():
        print("⚠️  Diretório do frontend não encontrado")
        return True
    
    # Verificar se node_modules existe
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Instalando dependências do frontend...")
        if not run_command("npm install", shell=True):
            print("❌ Erro ao instalar dependências do frontend")
            return False
    
    # Fazer build
    print("🔨 Fazendo build do frontend...")
    original_cwd = os.getcwd()
    try:
        os.chdir(frontend_dir)
        if run_command("npm run build", shell=True):
            print("✅ Build do frontend concluído")
            return True
        else:
            print("❌ Erro no build do frontend")
            return False
    finally:
        os.chdir(original_cwd)


def create_sample_dataset():
    """Criar dataset de exemplo"""
    print("\nCriando dataset de exemplo...")
    
    datasets_dir = Path("data/datasets/sample")
    
    if datasets_dir.exists():
        print("⚠️  Dataset de exemplo já existe")
        return True
    
    # Criar estrutura básica
    for split in ["train", "val"]:
        (datasets_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (datasets_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
    
    # Criar data.yaml
    data_yaml = datasets_dir / "data.yaml"
    yaml_content = """path: ./data/datasets/sample
train: images/train
val: images/val

nc: 2
names:
  0: person
  1: car
"""
    
    with open(data_yaml, 'w') as f:
        f.write(yaml_content)
    
    # Criar arquivo README
    readme = datasets_dir / "README.md"
    readme_content = """# Dataset de Exemplo

Este é um dataset de exemplo para testar o sistema.

## Estrutura
- `images/train/` - Imagens de treino
- `images/val/` - Imagens de validação
- `labels/train/` - Labels de treino (formato YOLO)
- `labels/val/` - Labels de validação (formato YOLO)
- `data.yaml` - Configuração do dataset

## Classes
- 0: person
- 1: car

Para usar este dataset, adicione suas próprias imagens e labels nos diretórios correspondentes.
"""
    
    with open(readme, 'w') as f:
        f.write(readme_content)
    
    print("✅ Dataset de exemplo criado")
    return True


def run_tests():
    """Executar testes básicos"""
    print("\nExecutando testes básicos...")
    
    try:
        # Teste de importação
        print("🧪 Testando importações...")
        
        import fastapi
        import uvicorn
        import pydantic
        print("✅ FastAPI, Uvicorn e Pydantic OK")
        
        try:
            import torch
            print(f"✅ PyTorch {torch.__version__} OK")
            
            if torch.cuda.is_available():
                print(f"✅ CUDA disponível: {torch.cuda.device_count()} GPU(s)")
            else:
                print("⚠️  CUDA não disponível (usando CPU)")
                
        except ImportError:
            print("❌ PyTorch não instalado")
            return False
        
        try:
            import ultralytics
            print(f"✅ Ultralytics OK")
        except ImportError:
            print("❌ Ultralytics não instalado")
            return False
        
        # Teste de configuração
        print("🧪 Testando configurações...")
        try:
            from app.core.config import settings
            print("✅ Configurações carregadas")
        except Exception as e:
            print(f"❌ Erro nas configurações: {e}")
            return False
        
        print("✅ Todos os testes passaram")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Setup do Sistema de Treinamento YOLO")
    parser.add_argument("--skip-venv", action="store_true", help="Pular criação do ambiente virtual")
    parser.add_argument("--skip-frontend", action="store_true", help="Pular build do frontend")
    parser.add_argument("--skip-models", action="store_true", help="Pular download de modelos")
    parser.add_argument("--skip-tests", action="store_true", help="Pular testes")
    
    args = parser.parse_args()
    
    print("🚀 Iniciando setup do Sistema de Treinamento YOLO")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Criar ambiente virtual
    if not args.skip_venv:
        if not create_virtual_environment():
            sys.exit(1)
        
        if not activate_and_install_dependencies():
            sys.exit(1)
    
    # Criar diretórios
    if not create_directories():
        sys.exit(1)
    
    # Configurar ambiente
    if not setup_environment_file():
        sys.exit(1)
    
    # Build do frontend
    if not args.skip_frontend:
        if not build_frontend():
            print("⚠️  Continuando sem build do frontend")
    
    # Baixar modelos
    if not args.skip_models:
        download_sample_models()
    
    # Criar dataset de exemplo
    create_sample_dataset()
    
    # Executar testes
    if not args.skip_tests:
        if not run_tests():
            print("⚠️  Alguns testes falharam, mas o setup pode continuar")
    
    print("\n" + "=" * 50)
    print("✅ Setup concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Edite o arquivo .env com suas configurações")
    print("2. Execute: python main.py")
    print("3. Acesse: http://localhost:8000")
    print("\n📚 Documentação da API: http://localhost:8000/docs")
    print("🎯 Interface Web: http://localhost:8000")


if __name__ == "__main__":
    main()