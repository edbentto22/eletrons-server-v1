#!/usr/bin/env python3
"""
Script de teste para verificar se o servidor está funcionando
"""
import sys
import time
import requests
from requests.exceptions import RequestException

def test_health():
    """Testa o endpoint de health"""
    url = "http://localhost:8000/health"
    max_attempts = 5
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Tentativa {attempt}/{max_attempts}: Testando {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS: Status {response.status_code}")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ FAIL: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except RequestException as e:
            print(f"❌ CONNECTION ERROR: {e}")
            
        if attempt < max_attempts:
            print("Aguardando 5 segundos...")
            time.sleep(5)
    
    print("❌ FINAL FAIL: Todas as tentativas falharam")
    return False

if __name__ == "__main__":
    success = test_health()
    sys.exit(0 if success else 1)