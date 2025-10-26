#!/usr/bin/env python3
"""
Script para inicializar o servidor do Sistema de Treinamento YOLO
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path


def check_environment():
    """Verificar se o ambiente está configurado"""
    print("🔍 Verificando ambiente...")
    
    # Verificar se estamos no ambiente virtual
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Ambiente virtual ativo")
    else:
        print("⚠️  Ambiente virtual não detectado")
        print("💡 Execute: source venv/bin/activate (Linux/Mac) ou venv\\Scripts\\activate (Windows)")
    
    # Verificar estrutura de diretórios
    required_dirs = [
        "app",
        "data",
        "data/models",
        "data/datasets",
        "data/outputs",
        "data/logs"
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"❌ Diretórios faltando: {', '.join(missing_dirs)}")
        print("💡 Execute: python setup.py")
        return False
    
    print("✅ Estrutura de diretórios OK")
    
    # Verificar arquivo .env
    if not Path(".env").exists():
        print("⚠️  Arquivo .env não encontrado")
        print("💡 Execute: python setup.py ou copie .env.example para .env")
    else:
        print("✅ Arquivo .env encontrado")
    
    # Verificar dependências críticas
    try:
        import fastapi
        import uvicorn
        import ultralytics
        import torch
        print("✅ Dependências críticas instaladas")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False
    
    return True


def check_gpu():
    """Verificar disponibilidade de GPU"""
    print("\n🎮 Verificando GPU...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"✅ CUDA disponível: {gpu_count} GPU(s)")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
        
        elif torch.backends.mps.is_available():
            print("✅ MPS (Apple Silicon) disponível")
        
        else:
            print("⚠️  GPU não disponível - usando CPU")
            print("💡 Para melhor performance, considere usar uma GPU NVIDIA com CUDA")
    
    except ImportError:
        print("❌ PyTorch não instalado")


def start_server(host="0.0.0.0", port=8000, reload=False, workers=1, log_level="info"):
    """Iniciar o servidor FastAPI"""
    print(f"\n🚀 Iniciando servidor em {host}:{port}")
    print(f"📊 Workers: {workers}")
    print(f"🔄 Reload: {reload}")
    print(f"📝 Log Level: {log_level}")
    
    # Configurar variáveis de ambiente se necessário
    os.environ.setdefault("HOST", host)
    os.environ.setdefault("PORT", str(port))
    
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # Reload não funciona com múltiplos workers
            log_level=log_level,
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Servidor do Sistema de Treinamento YOLO")
    
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor (padrão: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Ativar reload automático (desenvolvimento)")
    parser.add_argument("--workers", type=int, default=1, help="Número de workers (padrão: 1)")
    parser.add_argument("--log-level", default="info", choices=["critical", "error", "warning", "info", "debug"], help="Nível de log")
    parser.add_argument("--skip-checks", action="store_true", help="Pular verificações de ambiente")
    parser.add_argument("--dev", action="store_true", help="Modo desenvolvimento (reload + debug)")
    
    args = parser.parse_args()
    
    # Modo desenvolvimento
    if args.dev:
        args.reload = True
        args.log_level = "debug"
        args.workers = 1
    
    print("🎯 Sistema de Treinamento YOLO")
    print("=" * 40)
    
    # Verificar ambiente
    if not args.skip_checks:
        if not check_environment():
            print("\n❌ Ambiente não está configurado corretamente")
            print("💡 Execute: python setup.py")
            sys.exit(1)
        
        check_gpu()
    
    # Iniciar servidor
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()