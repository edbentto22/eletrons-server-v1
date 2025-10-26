#!/usr/bin/env python3
"""
Script de teste para verificar se o servidor está funcionando
Usa httpx (já presente em requirements.txt)
- Primeiro verifica liveness (/live) para evitar falso negativo no arranque
- Depois, se necessário, verifica /health com algumas tentativas
"""
import sys
import time
import httpx
from httpx import RequestError

LIVENESS_URLS = [
    "http://localhost:8060/live",
    "http://127.0.0.1:8060/live",
]

HEALTH_URLS = [
    "http://localhost:8060/health",
    "http://127.0.0.1:8060/health",
]


def ping_liveness() -> bool:
    """Tenta endpoints de liveness rápidos"""
    for url in LIVENESS_URLS:
        try:
            res = httpx.get(url, timeout=3)
            if res.status_code == 200:
                print(f"✅ Liveness OK: {url}")
                return True
        except Exception as e:
            print(f"⚠️  Liveness falhou em {url}: {e}")
    return False


def check_health(max_attempts: int = 5) -> bool:
    """Verifica /health com retries"""
    for attempt in range(1, max_attempts + 1):
        for url in HEALTH_URLS:
            try:
                print(f"Tentativa {attempt}/{max_attempts}: Testando {url}")
                with httpx.Client(timeout=10) as client:
                    response = client.get(url)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS: Status {response.status_code}")
                    try:
                        print(f"Response: {response.json()}")
                    except Exception:
                        print(f"Response: {response.text}")
                    return True
                else:
                    print(f"❌ FAIL: Status {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except RequestError as e:
                print(f"❌ CONNECTION ERROR: {e}")
        
        if attempt < max_attempts:
            print("Aguardando 5 segundos...")
            time.sleep(5)
    
    print("❌ FINAL FAIL: Todas as tentativas falharam")
    return False


def main():
    # Liveness primeiro para não degradar no arranque
    if ping_liveness():
        sys.exit(0)
    # Se liveness falhar, tentar health completo
    ok = check_health()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()