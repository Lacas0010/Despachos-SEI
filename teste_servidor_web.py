"""
Teste Automatizado do Servidor FastAPI e Rotas da WebUI
"""

import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_static_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Gerador SEI" in response.text
    print("  [OK] Rota raiz / entrega index.html com sucesso")

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "moldes" in data
    assert "RESUMÃO" in data["moldes"]
    print("  [OK] Endpoint /api/status operacional")

def test_historico_endpoints():
    response = client.get("/api/historico")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("  [OK] Endpoint /api/historico operacional")

def test_converter_sei_html():
    payload = {"texto": "**Governo do Distrito Federal**\n\n1. Trata-se de demanda de Ouvidoria.\n\n• Interessado: Cidadão\n\nAtenciosamente,"}
    response = client.post("/api/converter-sei-html", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("sucesso") is True
    assert "<strong>" in data.get("html", "")
    print("  [OK] Endpoint /api/converter-sei-html operacional")

def test_export_docx_pdf_csv():
    # Teste DOCX
    resp_docx = client.post("/api/exportar/docx", json={"texto": "Despacho teste\n1. Trata-se de teste.\nAtenciosamente,"})
    assert resp_docx.status_code == 200
    assert len(resp_docx.content) > 100
    
    # Teste PDF
    resp_pdf = client.post("/api/exportar/pdf", json={"texto": "Despacho teste\n1. Trata-se de teste.\nAtenciosamente,"})
    assert resp_pdf.status_code == 200
    assert len(resp_pdf.content) > 100

    # Teste CSV
    resp_csv = client.post("/api/exportar/csv", json={"resultados": [{"arquivo": "proc.pdf", "prioridade": "Alta"}]})
    assert resp_csv.status_code == 200
    assert len(resp_csv.content) > 10
    print("  [OK] Endpoints de exportação DOCX, PDF e CSV operacionais")

def test_upload_pasta_multipla():
    files = [
        ("files", ("pasta_teste/doc1.txt", b"Documento 1 do processo SEI", "text/plain")),
        ("files", ("pasta_teste/doc2.txt", b"Documento 2 com parecer tecnico", "text/plain")),
    ]
    resp = client.post("/api/upload-pasta-multipla", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("sucesso") is True
    assert "Documento 1" in data.get("texto_processo", "")
    assert "Documento 2" in data.get("texto_processo", "")
    print("  [OK] Endpoint /api/upload-pasta-multipla (upload de pastas completas) operacional")

def test_static_assets():
    resp_css = client.get("/styles.css")
    assert resp_css.status_code == 200
    assert len(resp_css.content) > 100

    resp_js = client.get("/app.js")
    assert resp_js.status_code == 200
    assert "API_BASE" in resp_js.text
    print("  [OK] Assets estáticos (/styles.css, /app.js) servidos com sucesso")

def test_upload_processo_arquivo():
    file_payload = ("processo_teste.txt", b"Texto de teste do processo 00112-00001234/2024-55 contendo despacho e relatorio.", "text/plain")
    resp = client.post("/api/upload-processo", files={"file": file_payload})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("sucesso") is True
    assert "processo_teste.txt" in data.get("nome_processo", "")
    assert "00112-00001234/2024-55" in data.get("texto_processo", "")
    print("  [OK] Endpoint /api/upload-processo (upload de arquivo unico) operacional")

if __name__ == "__main__":
    print("Testando Servidor Backend FastAPI do Gerador SEI...")
    print()
    
    test_static_index()
    test_static_assets()
    test_status_endpoint()
    test_historico_endpoints()
    test_converter_sei_html()
    test_export_docx_pdf_csv()
    test_upload_processo_arquivo()
    test_upload_pasta_multipla()
    
    print()
    print("Todos os endpoints do servidor FastAPI foram validados com sucesso!")
