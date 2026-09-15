"""
Inicializador Automático do Gerador SEI Web
Inicia o servidor backend FastAPI e abre o navegador padrão automaticamente.
"""

import sys
import os
import time
import webbrowser
import threading
import uvicorn

def abrir_navegador(url="http://127.0.0.1:8000"):
    """Espera o servidor subir e abre a página no navegador padrão."""
    time.sleep(1.2)
    print(f"\n[INFO] Abrindo Gerador SEI no navegador: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[AVISO] Não foi possível abrir o navegador automaticamente: {e}")

if __name__ == "__main__":
    porta = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{porta}"
    
    print("=" * 60)
    print(" ⚡ GERADOR SEI - SUÍTE DE ANÁLISE E REDAÇÃO OFICIAL")
    print(f" Servidor Backend iniciado em: {url}")
    print(" Pressione Ctrl+C no terminal para encerrar.")
    print("=" * 60)
    
    # Inicia a thread que abrirá o navegador
    t = threading.Thread(target=abrir_navegador, args=(url,), daemon=True)
    t.start()
    
    # Inicia o Uvicorn
    uvicorn.run("server:app", host=host, port=porta, log_level="info", reload=False)
