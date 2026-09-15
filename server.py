"""
Gerador SEI - Servidor Backend FastAPI
Modern REST & SSE Streaming API for SEI Process Analysis, AI Drafting, and History.
"""

import os
import io
import json
import time
import queue
import tempfile
import threading
import logging
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

from engine import SEIEngine
from sei_utils import convert_text_to_sei_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GeradorSEIServer")

app = FastAPI(
    title="Gerador SEI - API",
    description="Backend moderno para Análise de Processos, Triagem e Redação Oficial SEI com IA",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia o motor de inteligência e persistência
engine = SEIEngine("modelos_custom.json")

# Diretório do frontend estático
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
os.makedirs(WEB_DIR, exist_ok=True)


# --- Pydantic Models ---
class AnaliseRequest(BaseModel):
    texto_processo: str
    nome_processo: str = "Processo"
    molde: str = "AUTO"


class ChatRequest(BaseModel):
    mensagem: str
    texto_processo: Optional[str] = ""
    nome_processo: Optional[str] = "Processo"
    modo: Optional[str] = "Auto"  # Auto, Autos, Refinar, Geral
    texto_atual_documento: Optional[str] = ""


class RefinamentoRequest(BaseModel):
    texto_atual: str
    instrucoes: str
    texto_processo: Optional[str] = ""
    nome_processo: Optional[str] = "Processo"


class ExportTextRequest(BaseModel):
    texto: str
    nome_arquivo: Optional[str] = "documento"


class ExportCSVRequest(BaseModel):
    resultados: List[Dict[str, Any]]
    nome_arquivo: Optional[str] = "triagem_lote.csv"


class SelecionarModeloRequest(BaseModel):
    modelo: str


# --- Status & Healthcheck ---
@app.get("/api/status")
def get_status():
    """Verifica conexão com o Ollama, modelos disponíveis e estatísticas do RAG."""
    ollama_ok = False
    modelos_ollama = []
    try:
        import ollama
        resp = ollama.list()
        if hasattr(resp, "models"):
            modelos_ollama = [m.model for m in resp.models if "embed" not in m.model]
        elif isinstance(resp, dict) and "models" in resp:
            modelos_ollama = [m.get("name", "") for m in resp["models"] if "embed" not in m.get("name", "")]
        ollama_ok = True
    except Exception as e:
        logger.warning(f"Ollama offline ou indisponível: {e}")

    rag_count = engine._vector_db.count()
    moldes_disponiveis = [
        "AUTO", "RESUMÃO", "LINHA DO TEMPO", "AUDITORIA", "EXTRAÇÃO",
        "OUVIDORIA MINUTA", "OUVIDORIA SUBAN", "OUVIDORIA ELOGIO", "DILACAO", "GENERICO"
    ]

    return {
        "status": "online",
        "ollama_conectado": ollama_ok,
        "modelos_ollama": modelos_ollama,
        "modelo_ativo": getattr(engine, "model_name", "llama3.2"),
        "rag_documentos": rag_count,
        "moldes": moldes_disponiveis
    }


@app.get("/api/modelos")
def get_modelos():
    """Lista todos os modelos de IA instalados no Ollama e o modelo ativo."""
    modelos = []
    try:
        import ollama
        resp = ollama.list()
        if hasattr(resp, "models"):
            modelos = [m.model for m in resp.models if "embed" not in m.model]
        elif isinstance(resp, dict) and "models" in resp:
            modelos = [m.get("name", "") for m in resp["models"] if "embed" not in m.get("name", "")]
    except Exception as e:
        logger.warning(f"Erro ao listar modelos: {e}")

    return {
        "modelos": modelos,
        "modelo_ativo": getattr(engine, "model_name", "llama3.2")
    }


@app.post("/api/selecionar-modelo")
def selecionar_modelo(req: SelecionarModeloRequest):
    """Altera o modelo de IA ativo e persiste no config.json."""
    novo_modelo = req.modelo.strip()
    if not novo_modelo:
        raise HTTPException(status_code=400, detail="Nome do modelo não pode ser vazio.")

    # Remove tag :latest se presente para consistência
    clean_model = novo_modelo.split(":")[0] if ":" in novo_modelo else novo_modelo
    engine.model_name = clean_model

    try:
        cfg = {}
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
        cfg["modelo_ia"] = clean_model
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar config.json: {e}")

    logger.info(f"Modelo de IA alterado para: {clean_model}")
    return {"sucesso": True, "modelo_ativo": clean_model}


# --- Upload e Seleção de Processos (Pasta / Dossiê / Arquivo) ---
@app.post("/api/selecionar-pasta-local")
def selecionar_pasta_local():
    """Abre o diálogo nativo do Windows para selecionar uma pasta de processo usando subprocesso isolado."""
    import subprocess
    import sys
    
    script = (
        "import sys, tkinter as tk, tkinter.filedialog as fd; "
        "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True); "
        "res = fd.askdirectory(title='Selecione a pasta do processo SEI'); "
        "r.destroy(); "
        "sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None; "
        "print(res or '')"
    )
    try:
        raw_out = subprocess.check_output([sys.executable, "-c", script])
        folder_selected = raw_out.decode("utf-8", errors="replace").strip()
    except Exception as e:
        logger.error(f"Erro ao abrir diálogo de pasta: {e}")
        return {"sucesso": False, "erro": str(e)}

    if not folder_selected:
        return {"sucesso": False, "cancelado": True}

    texto_extraido, nome_proc = engine.extrair_texto_de_alvo(folder_selected)
    if not texto_extraido or len(texto_extraido.strip()) == 0:
        raise HTTPException(status_code=400, detail="Nenhum texto extraível foi encontrado na pasta selecionada (arquivos vazios ou imagens sem OCR).")

    return {
        "sucesso": True,
        "caminho_pasta": folder_selected,
        "nome_processo": nome_proc or os.path.basename(folder_selected),
        "tamanho_caracteres": len(texto_extraido),
        "texto_processo": texto_extraido,
        "resumo_inicial": texto_extraido[:600] + "..." if len(texto_extraido) > 600 else texto_extraido
    }


@app.post("/api/selecionar-arquivo-local")
def selecionar_arquivo_local():
    """Abre o diálogo nativo do Windows para selecionar um arquivo (.zip, .pdf, .docx) usando subprocesso isolado."""
    import subprocess
    import sys
    
    script = (
        "import sys, tkinter as tk, tkinter.filedialog as fd; "
        "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True); "
        "types = [('Arquivos de Processo', '*.zip;*.pdf;*.docx;*.txt;*.html;*.htm'), ('Todos os Arquivos', '*.*')]; "
        "res = fd.askopenfilename(title='Selecione o arquivo do processo', filetypes=types); "
        "r.destroy(); "
        "sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None; "
        "print(res or '')"
    )
    try:
        raw_out = subprocess.check_output([sys.executable, "-c", script])
        file_selected = raw_out.decode("utf-8", errors="replace").strip()
    except Exception as e:
        logger.error(f"Erro ao abrir diálogo de arquivo: {e}")
        return {"sucesso": False, "erro": str(e)}

    if not file_selected:
        return {"sucesso": False, "cancelado": True}

    texto_extraido, nome_proc = engine.extrair_texto_de_alvo(file_selected)
    if not texto_extraido or len(texto_extraido.strip()) == 0:
        raise HTTPException(status_code=400, detail="Nenhum texto extraível foi encontrado no arquivo selecionado (se for PDF, verifique se possui camada de texto).")

    return {
        "sucesso": True,
        "caminho_arquivo": file_selected,
        "nome_processo": nome_proc or os.path.basename(file_selected),
        "tamanho_caracteres": len(texto_extraido),
        "texto_processo": texto_extraido,
        "resumo_inicial": texto_extraido[:600] + "..." if len(texto_extraido) > 600 else texto_extraido
    }


@app.post("/api/upload-processo")
async def upload_processo(file: UploadFile = File(...)):
    """Recebe um arquivo (.zip, .pdf, .docx, .html, .txt) e extrai o texto integral dos autos."""
    filename = file.filename or "processo.pdf"
    suffix = os.path.splitext(filename)[1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)
        
    try:
        texto_extraido, nome_proc = engine.extrair_texto_de_alvo(tmp_path)
        if not texto_extraido or len(texto_extraido.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Não foi possível extrair texto do arquivo enviado. Se for um PDF digitalizado/escaneado (imagem), certifique-se de que ele possui camada de texto (OCR)."
            )
            
        display_name = filename if filename else (nome_proc or "Processo")
        return {
            "sucesso": True,
            "nome_processo": display_name,
            "tamanho_caracteres": len(texto_extraido),
            "texto_processo": texto_extraido,
            "resumo_inicial": texto_extraido[:600] + "..." if len(texto_extraido) > 600 else texto_extraido
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao extrair arquivo {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.post("/api/upload-pasta-multipla")
async def upload_pasta_multipla(files: List[UploadFile] = File(...)):
    """Recebe múltiplos arquivos enviados via pasta (webkitdirectory ou drag-and-drop de pasta)."""
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")
        
    with tempfile.TemporaryDirectory() as tmpdir:
        salvos = 0
        for f in files:
            safe_rel_path = (f.filename or "doc.txt").replace("\\", "/").lstrip("/")
            if not safe_rel_path:
                safe_rel_path = f"doc_{salvos}.bin"
            full_target = os.path.join(tmpdir, safe_rel_path)
            os.makedirs(os.path.dirname(full_target), exist_ok=True)
            with open(full_target, "wb") as out_f:
                out_f.write(await f.read())
            salvos += 1
                
        texto_extraido, nome_proc = engine.extrair_texto_de_alvo(tmpdir)
        if not texto_extraido or len(texto_extraido.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail=f"{salvos} arquivo(s) recebido(s), mas nenhum texto extraível foi encontrado. Verifique se os documentos (.pdf, .docx, .html, .txt) possuem texto digital."
            )
            
        pasta_raiz = files[0].filename.split("/")[0] if "/" in (files[0].filename or "") else (nome_proc or "Pasta do Processo")
        
        return {
            "sucesso": True,
            "nome_processo": pasta_raiz,
            "tamanho_caracteres": len(texto_extraido),
            "texto_processo": texto_extraido,
            "resumo_inicial": texto_extraido[:600] + "..." if len(texto_extraido) > 600 else texto_extraido
        }


# --- Gerenciamento de Cancelamento de IA ---
active_cancellations = set()
cancel_lock = threading.Lock()


def register_cancellation_event() -> threading.Event:
    ev = threading.Event()
    with cancel_lock:
        active_cancellations.add(ev)
    return ev


def unregister_cancellation_event(ev: threading.Event):
    with cancel_lock:
        active_cancellations.discard(ev)


@app.post("/api/cancelar-ia")
def cancelar_ia():
    """Cancela imediatamente todos os processos ativos de IA em andamento."""
    logger.info("Solicitação de cancelamento de IA recebida via API.")
    with cancel_lock:
        total = len(active_cancellations)
        for ev in list(active_cancellations):
            ev.set()
    return {"sucesso": True, "mensagem": f"Comando de cancelamento enviado ({total} processo(s) afetado(s))."}


# --- Streaming SSE: Análise do Processo com Molde ---
@app.post("/api/analisar-stream")
def analisar_processo_stream(req: AnaliseRequest):
    """Executa a análise do processo com o molde solicitado e transmite via SSE."""
    def event_generator():
        token_queue = queue.Queue()
        done_event = threading.Event()
        cancel_event = register_cancellation_event()
        resultado_final = {}

        def stream_cb(full_text):
            if cancel_event.is_set():
                return False
            token_queue.put({"type": "stream", "full_text": full_text})
            return True

        def worker():
            try:
                res = engine.analisar_processo_direto(
                    texto_processo=req.texto_processo,
                    nome_processo=req.nome_processo,
                    molde_ia=req.molde,
                    stream_callback=stream_cb,
                    cancel_event=cancel_event
                )
                resultado_final.update(res)
            except Exception as e:
                resultado_final.update({"sucesso": False, "erro": str(e)})
            finally:
                done_event.set()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        try:
            while not done_event.is_set() or not token_queue.empty():
                if cancel_event.is_set():
                    break
                try:
                    item = token_queue.get(timeout=0.08)
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    continue

            # Processamento final e salvamento no histórico
            if cancel_event.is_set() or resultado_final.get("cancelado"):
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "cancelado": True,
                    "erro": "Geração cancelada pelo usuário."
                }
            elif resultado_final.get("sucesso"):
                tipo_doc = resultado_final.get("tipo_documento", req.molde)
                texto_gerado = resultado_final.get("texto_gerado", "")
                raciocinio = resultado_final.get("raciocinio", "")
                subject = f"[{tipo_doc}] {resultado_final.get('resumo', req.nome_processo)}"
                hist_id = engine.save_to_history(
                    doc_type=tipo_doc,
                    subject=subject,
                    full_text=texto_gerado,
                    process_context=req.texto_processo,
                    raciocinio=raciocinio
                )
                done_payload = {
                    "type": "done",
                    "sucesso": True,
                    "history_id": hist_id,
                    "tipo_documento": tipo_doc,
                    "subject": subject,
                    "texto_gerado": texto_gerado,
                    "raciocinio": raciocinio
                }
            else:
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "erro": resultado_final.get("erro", "Falha na análise do processo.")
                }

            yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
        finally:
            unregister_cancellation_event(cancel_event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Streaming SSE: Chat & Dúvidas dos Autos / RAG ---
@app.post("/api/chat-stream")
def chat_stream(req: ChatRequest):
    """Responde dúvidas sobre o processo ou pesquisa geral RAG transmitindo via SSE."""
    def event_generator():
        token_queue = queue.Queue()
        done_event = threading.Event()
        cancel_event = register_cancellation_event()
        resultado_final = {}

        def stream_cb(full_text):
            if cancel_event.is_set():
                return False
            token_queue.put({"type": "stream", "full_text": full_text})
            return True

        modo = req.modo or "Auto"
        msg = req.mensagem

        def worker():
            try:
                if modo == "Autos" or (modo == "Auto" and req.texto_processo and ("qual" in msg.lower() or "quem" in msg.lower() or "quando" in msg.lower() or "onde" in msg.lower() or "quanto" in msg.lower() or "?" in msg)):
                    res = engine.responder_pergunta_sobre_processo(msg, req.texto_processo, stream_callback=stream_cb, cancel_event=cancel_event)
                    res["doc_type"] = "Consulta aos Autos"
                elif modo == "Refinar" and req.texto_atual_documento:
                    res = engine.refinar_texto_com_ia(req.texto_atual_documento, msg, stream_callback=stream_cb, cancel_event=cancel_event)
                    res["doc_type"] = "Refinamento"
                    res["is_refinement"] = True
                else:
                    res = engine.responder_pergunta_geral_com_ia(msg, stream_callback=stream_cb, cancel_event=cancel_event)
                    res["doc_type"] = "Pesquisa RAG"
                resultado_final.update(res)
            except Exception as e:
                resultado_final.update({"sucesso": False, "erro": str(e)})
            finally:
                done_event.set()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        try:
            while not done_event.is_set() or not token_queue.empty():
                if cancel_event.is_set():
                    break
                try:
                    item = token_queue.get(timeout=0.08)
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    continue

            if cancel_event.is_set() or resultado_final.get("cancelado"):
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "cancelado": True,
                    "erro": "Processamento cancelado pelo usuário."
                }
            elif resultado_final.get("sucesso"):
                tipo_doc = resultado_final.get("doc_type", "Chat")
                texto_gerado = resultado_final.get("texto_gerado", "")
                raciocinio = resultado_final.get("raciocinio", "")
                hist_id = engine.save_to_history(
                    doc_type=tipo_doc,
                    subject=f"[{tipo_doc}] via Chat: {msg[:25]}",
                    full_text=texto_gerado,
                    process_context=req.texto_processo or "",
                    raciocinio=raciocinio
                )
                done_payload = {
                    "type": "done",
                    "sucesso": True,
                    "history_id": hist_id,
                    "doc_type": tipo_doc,
                    "is_refinement": resultado_final.get("is_refinement", False),
                    "texto_gerado": texto_gerado,
                    "raciocinio": raciocinio
                }
            else:
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "erro": resultado_final.get("erro", "Erro no processamento da mensagem.")
                }

            yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
        finally:
            unregister_cancellation_event(cancel_event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Streaming SSE: Refinamento de Documento ---
@app.post("/api/refinar-stream")
def refinar_stream(req: RefinamentoRequest):
    """Refina o texto do documento de acordo com as instruções fornecidas."""
    def event_generator():
        token_queue = queue.Queue()
        done_event = threading.Event()
        cancel_event = register_cancellation_event()
        resultado_final = {}

        def stream_cb(full_text):
            if cancel_event.is_set():
                return False
            token_queue.put({"type": "stream", "full_text": full_text})
            return True

        def worker():
            try:
                res = engine.refinar_texto_com_ia(req.texto_atual, req.instrucoes, stream_callback=stream_cb, cancel_event=cancel_event)
                resultado_final.update(res)
            except Exception as e:
                resultado_final.update({"sucesso": False, "erro": str(e)})
            finally:
                done_event.set()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        try:
            while not done_event.is_set() or not token_queue.empty():
                if cancel_event.is_set():
                    break
                try:
                    item = token_queue.get(timeout=0.08)
                    yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    continue

            if cancel_event.is_set() or resultado_final.get("cancelado"):
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "cancelado": True,
                    "erro": "Refinamento cancelado pelo usuário."
                }
            elif resultado_final.get("sucesso"):
                texto_gerado = resultado_final.get("texto_gerado", "")
                raciocinio = resultado_final.get("raciocinio", "")
                hist_id = engine.save_to_history(
                    doc_type="Refinamento",
                    subject=f"[Refinamento] {req.instrucoes[:25]}",
                    full_text=texto_gerado,
                    process_context=req.texto_processo or "",
                    raciocinio=raciocinio
                )
                done_payload = {
                    "type": "done",
                    "sucesso": True,
                    "history_id": hist_id,
                    "texto_gerado": texto_gerado,
                    "raciocinio": raciocinio
                }
            else:
                done_payload = {
                    "type": "done",
                    "sucesso": False,
                    "erro": resultado_final.get("erro", "Erro ao refinar documento.")
                }

            yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
        finally:
            unregister_cancellation_event(cancel_event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Histórico CRUD ---
@app.get("/api/historico")
def get_historico(busca: str = Query(default="")):
    """Retorna itens do histórico com suporte a busca rápida."""
    if busca:
        return engine.search_history(busca)
    return engine.get_history()


@app.get("/api/historico/{entry_id}")
def get_historico_item(entry_id: int):
    """Recupera um item específico do histórico incluindo o contexto original dos autos."""
    entries = engine.history_db.get_all_entries(limit=300)
    for item in entries:
        if item.get("id") == entry_id:
            return item
    raise HTTPException(status_code=404, detail="Item do histórico não encontrado.")


@app.delete("/api/historico/{entry_id}")
def delete_historico_item(entry_id: int):
    """Remove um item do histórico."""
    ok = engine.delete_history_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item não encontrado ou já excluído.")
    return {"sucesso": True, "id": entry_id}


# --- Triagem em Lote ---
@app.post("/api/triagem-lote")
async def triagem_lote(file: UploadFile = File(...)):
    """Recebe um arquivo compactado (.zip) com múltiplos processos e executa triagem automatizada."""
    cancel_event = register_cancellation_event()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, file.filename or "lote.zip")
            with open(zip_path, "wb") as f:
                f.write(await file.read())
                
            resultados, erro = engine.processar_lote_processos(tmpdir, cancel_event=cancel_event)
            if erro and not cancel_event.is_set():
                raise HTTPException(status_code=500, detail=erro)
                
            return {
                "sucesso": True,
                "cancelado": cancel_event.is_set(),
                "total_processados": len(resultados),
                "resultados": resultados
            }
    finally:
        unregister_cancellation_event(cancel_event)


# --- Exportações DOCX / PDF / CSV / HTML SEI ---
@app.post("/api/exportar/docx")
def exportar_docx(req: ExportTextRequest):
    """Gera e faz download de documento DOCX."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp_path = tmp.name
        
    suc, err = engine.export_to_docx(req.texto, tmp_path)
    if not suc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar DOCX: {err}")
        
    safe_name = "".join(c for c in req.nome_arquivo if c.isalnum() or c in (' ', '_', '-')).strip() or "documento"
    return FileResponse(
        tmp_path,
        filename=f"{safe_name}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.post("/api/exportar/pdf")
def exportar_pdf(req: ExportTextRequest):
    """Gera e faz download de documento PDF oficial."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
        
    suc, err = engine.export_to_pdf(req.texto, tmp_path)
    if not suc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {err}")
        
    safe_name = "".join(c for c in req.nome_arquivo if c.isalnum() or c in (' ', '_', '-')).strip() or "documento"
    return FileResponse(
        tmp_path,
        filename=f"{safe_name}.pdf",
        media_type="application/pdf"
    )


@app.post("/api/exportar/csv")
def exportar_csv(req: ExportCSVRequest):
    """Gera e faz download da planilha de triagem em lote."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp_path = tmp.name
        
    suc, err = engine.exportar_lote_csv(req.resultados, tmp_path)
    if not suc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar CSV: {err}")
        
    return FileResponse(
        tmp_path,
        filename=req.nome_arquivo or "triagem_lote.csv",
        media_type="text/csv"
    )


@app.post("/api/converter-sei-html")
def converter_sei_html_endpoint(req: ExportTextRequest):
    """Converte texto puro ou markdown para HTML formatado nas normas oficiais do SEI-GDF."""
    html_out = convert_text_to_sei_html(req.texto)
    return {"sucesso": True, "html": html_out}


# --- Servir Frontend SPA ---
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    """Entrega a aplicação SPA e arquivos estáticos (styles.css, app.js, etc)."""
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    if full_path:
        clean_path = full_path.lstrip("/")
        # Remove prefixo static/ se fornecido
        if clean_path.startswith("static/"):
            clean_path = clean_path[7:]
        target = os.path.join(WEB_DIR, clean_path)
        if os.path.isfile(target):
            media_type = None
            if target.endswith(".js"): media_type = "application/javascript"
            elif target.endswith(".css"): media_type = "text/css"
            elif target.endswith(".html"): media_type = "text/html"
            return FileResponse(target, headers=headers, media_type=media_type)
            
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, headers=headers, media_type="text/html")
    return JSONResponse({"status": "Servidor backend operacional. Interface web em construção."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
