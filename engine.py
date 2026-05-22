"""
Engine module for Gerador SEI
Contains business logic for text generation, validation, and data processing
"""

import datetime
import json
import os
import re
import zipfile
import logging
import threading
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

# Desativa telemetria do ChromaDB globalmente para evitar crash da thread PostHog no Windows
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Adiciona a pasta "dlls" local ao caminho de busca do Windows (para rodar sem permissão de admin)
if os.name == 'nt':
    dll_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dlls")
    if os.path.exists(dll_dir):
        try:
            os.add_dll_directory(dll_dir)
        except AttributeError:
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from sei_templates import (
    PREFIXO_DOCUMENTO, RESUMO_CRONOGRAMA,
    MODELO_HVEP, MODELO_CASTRACAO, MODELO_CONDICOES_HVEP, MODELO_CRONOGRAMA_CASTRACAO,
    MODELO_OUVIDORIA_SUBAN
)

logger = logging.getLogger(__name__)

# Banco de Vetores nativo em Python para substituir o ChromaDB.
# Resolve definitivamente crashes (Segfaults) das bibliotecas em Rust/C++ no Windows.
class TinyVectorDB:
    def __init__(self, filepath="vetores_ia.json"):
        self.filepath = filepath
        self.data = {}
        self.lock = threading.Lock()
        self.load()
        
    def load(self):
        with self.lock:
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        self.data = json.load(f)
                except Exception:
                    self.data = {}
                
    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception as e:
            logger.error(f"Erro ao salvar TinyVectorDB: {e}")
            
    def upsert(self, doc_id, text, embedding):
        if not embedding:
            return
        with self.lock:
            self.data[doc_id] = {"text": text, "embedding": embedding}
            self.save()
            
    def query(self, query_embedding, n_results=2):
        if not query_embedding:
            return []
        with self.lock:
            if not self.data:
                return []
            query_vec = np.array(query_embedding)
            norm_query = np.linalg.norm(query_vec)
            results = []
            for doc_id, doc in self.data.items():
                emb = np.array(doc["embedding"])
                norm_emb = np.linalg.norm(emb)
                sim = 0 if (norm_query == 0 or norm_emb == 0) else np.dot(query_vec, emb) / (norm_query * norm_emb)
                results.append((sim, doc["text"]))
            results.sort(key=lambda x: x[0], reverse=True)
            return [text for sim, text in results[:n_results]]
            
    def count(self):
        with self.lock:
            return len(self.data)

# Classe SEIEngine: define comportamento e estrutura desta parte do aplicativo.
class SEIEngine:
    """Business logic engine for SEI document generation."""

    # Função interna __init__(modelos_file: str = "modelos_custom.json"): executa lógica relacionada a init.
    def __init__(self, modelos_file: str = "modelos_custom.json"):
        self.modelos_file = modelos_file
        self._vector_db = TinyVectorDB()
        self.modelos: Dict[str, Any] = {
            "HVeP - Atendimento/HVeP": MODELO_HVEP,
            "Castração de Cães e Gatos": MODELO_CASTRACAO,
            "Condições de exames e cirurgia HVeP": MODELO_CONDICOES_HVEP,
            "Demanda de Ouvidoria - Ausência de Cronograma Castração": MODELO_CRONOGRAMA_CASTRACAO,
            "Ouvidoria à Suban": MODELO_OUVIDORIA_SUBAN
        }
        self._load_custom_modelos()

    def _load_custom_modelos(self) -> None:
        """Load custom models from file."""
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults if file is corrupted

    def _save_custom_modelos(self) -> None:
        """Save custom models to file."""
        defaults = {
            "HVeP - Atendimento/HVeP",
            "Castração de Cães e Gatos",
            "Condições de exames e cirurgia HVeP",
            "Demanda de Ouvidoria - Ausência de Cronograma Castração",
            "Ouvidoria à Suban"
        }
        custom = {k: v for k, v in self.modelos.items() if k not in defaults}
        try:
            with open(self.modelos_file, "w", encoding="utf-8") as f:
                json.dump(custom, f, ensure_ascii=False, indent=4)
        except IOError:
            pass

    def validate_sei(self, sei: str) -> bool:
        """Validate SEI field input; accept user-provided expression (no auto-format)."""
        return bool(str(sei).strip())

    def validate_form_data(self, data: Any) -> List[str]:
        """Validate form data and return list of errors."""
        # suporte a lista ou dicionário (compatibilidade com código legado)
        if isinstance(data, list):
            data = {
                "oficio": data[0] if len(data) > 0 else "",
                "sei_oficio": data[1] if len(data) > 1 else "",
                "sei_manifestacao": data[2] if len(data) > 2 else "",
                "protocolo": data[3] if len(data) > 3 else "",
                "resumo": data[4] if len(data) > 4 else "",
                "prazo": data[5] if len(data) > 5 else ""
            }

        errors = []

        if not data.get("oficio", "").strip():
            errors.append("Ofício obrigatório")

        sei_oficio = data.get("sei_oficio", "").strip()
        if not self.validate_sei(sei_oficio):
            errors.append("SEI Ofício inválido")

        sei_manifestacao = data.get("sei_manifestacao", "").strip()
        if not self.validate_sei(sei_manifestacao):
            errors.append("SEI Manifestação inválido")

        protocolo = data.get("protocolo", "").strip()
        if not protocolo.startswith("OUV-"):
            errors.append("Protocolo OUV inválido")

        if not data.get("resumo", "").strip():
            errors.append("Resumo obrigatório")

        try:
            prazo_date = datetime.datetime.strptime(data.get("prazo", ""), "%d/%m/%Y").date()
            if prazo_date < datetime.date.today():
                errors.append("Prazo não pode ser no passado")
        except ValueError:
            errors.append("Data de prazo inválida")

        return errors

    def format_prazo(self, prazo: str) -> str:
        """Formata prazo no padrão: 3 de abril de 2026."""
        if not prazo:
            return ""

        # aceita entrada dd/mm/yyyy ou '3 de abril de 2026'
        try:
            # formato esperado dd/mm/yyyy
            data = datetime.datetime.strptime(prazo.strip(), "%d/%m/%Y").date()
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                     "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            return f"{data.day} de {meses[data.month - 1]} de {data.year}"
        except ValueError:
            # Se já estiver no formato extenso, retorna como está
            return prazo.strip()

    def _verificar_ollama(self) -> Tuple[bool, str]:
        """Verifica rapidamente se o Ollama está rodando para evitar travamentos ou crashes."""
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    return True, ""
        except Exception:
            pass
        return False, "O serviço do Ollama não está rodando. Por favor, abra o aplicativo Ollama no seu computador."

    def _get_embedding_ollama(self, text: str) -> List[float]:
        """Gera embeddings localmente chamando a API nativa do Ollama."""
        import urllib.request
        import json
        req = urllib.request.Request(
            "http://localhost:11434/api/embeddings",
            data=json.dumps({"model": "llama3.2", "prompt": text}).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Connection': 'close'}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('embedding', [])

    def generate_despacho(self, data: Dict[str, str]) -> str:
        """Generate SEI dispatch text using named tag placeholders."""
        modelo = self.modelos.get(data.get("modelo", "HVeP - Atendimento/HVeP"), MODELO_HVEP)

        hoje = datetime.date.today()
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        data_atual = f"{hoje.day:02d} de {meses[hoje.month - 1]} de {hoje.year}"

        context = {
            "NUM_OFICIO": data.get("oficio", ""),
            "SEI_OFICIO": data.get("sei_oficio", ""),
            "SEI_MANIFESTACAO": data.get("sei_manifestacao", ""),
            "PROTOCOLO": data.get("protocolo", ""),
            "RESUMO": data.get("resumo", ""),
            "PRAZO": self.format_prazo(data.get("prazo", "")),
            "DATA": data_atual
        }

        if isinstance(modelo, str):
            try:
                corpo = modelo.format(**context)
            except Exception:
                corpo = modelo
        elif callable(modelo):
            corpo = modelo(
                context["NUM_OFICIO"],
                context["SEI_OFICIO"],
                context["SEI_MANIFESTACAO"],
                context["PROTOCOLO"],
                context["RESUMO"],
                context["PRAZO"]
            )
        else:
            corpo = ""

        corpo = corpo.strip()
        if "À Subsecretaria de Bem-estar Animal" not in corpo:
            return PREFIXO_DOCUMENTO + corpo
        return corpo

    def export_to_pdf(self, text: str, filepath: str) -> Tuple[bool, str]:
        """Export text to PDF, retornando status e mensagem de erro quando aplicável."""
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            for line in text.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
                else:
                    story.append(Spacer(1, 12))

            doc.build(story)
            return True, ""
        except Exception as err:
            return False, str(err)

    def add_custom_modelo(self, nome: str, template: str) -> bool:
        """Add custom model string template with tag placeholders."""
        if nome and template and nome not in self.modelos:
            self.modelos[nome] = template
            self._save_custom_modelos()
            return True
        return False

    def update_modelo(self, nome: str, template: str) -> bool:
        """Update existing model with tag-based template."""
        if nome in self.modelos and template:
            self.modelos[nome] = template
            self._save_custom_modelos()
            return True
        return False

    def delete_modelo(self, nome: str) -> bool:
        """Delete custom model."""
        defaults = {
            "HVeP - Atendimento/HVeP",
            "Castração de Cães e Gatos",
            "Condições de exames e cirurgia HVeP",
            "Demanda de Ouvidoria - Ausência de Cronograma Castração",
            "Ouvidoria à Suban"
        }

        if nome in self.modelos and nome not in defaults:
            del self.modelos[nome]
            self._save_custom_modelos()
            return True
        return False

    def get_modelos_list(self) -> List[str]:
        """Get list of available models."""
        return list(self.modelos.keys())

    def calcular_data_prazo(self, dias: int) -> str:
        """Calcula prazo a partir de hoje (dias) e retorna no formato dd/mm/YYYY."""
        hoje = datetime.date.today()
        data_prazo = hoje + datetime.timedelta(days=dias)
        return data_prazo.strftime("%d/%m/%Y")

    def _extrair_texto_arquivo(self, filepath: str) -> str:
        """Extrai texto de um arquivo individual."""
        ext = filepath.lower()
        texto = ""
        try:
            if ext.endswith('.pdf'):
                try:
                    import fitz
                    with fitz.open(filepath) as doc:
                        for page in doc:
                            text = page.get_text()
                            if text:
                                texto += text + "\n"
                except ImportError:
                    pass
            elif ext.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    texto = f.read()
            elif ext.endswith(('.html', '.htm')):
                try:
                    from bs4 import BeautifulSoup
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        texto = soup.get_text(separator='\n', strip=True)
                except ImportError:
                    import html
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_text = f.read()
                        texto = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', raw_text, flags=re.IGNORECASE | re.DOTALL)
                        texto = re.sub(r'<[^>]+>', ' ', texto)
                        texto = html.unescape(texto)
                        texto = re.sub(r'\s+', ' ', texto).strip()
            elif ext.endswith('.docx'):
                try:
                    import docx
                    document = docx.Document(filepath)
                    texto = "\n".join([para.text for para in document.paragraphs])
                except ImportError:
                    pass
        except Exception as e:
            logger.warning(f"Erro ao extrair texto de {filepath}: {e}")
            
        texto = re.sub(r'Documento assinado eletronicamente por.*?\.', '', texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'A autenticidade do documento pode ser conferida.*?código CRC.*?\.', '', texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'"Brasília - Patrimônio Cultural da Humanidade".*?(?=\n\n|$)', '', texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'Doc\. SEI/GDF.*?\n', '', texto, flags=re.IGNORECASE)

        return texto.strip()

    def _get_regras_redacao(self) -> str:
        """Lê regras de redação do config.json ou retorna as regras padrão."""
        regras_padrao = (
            "1. Não pode hífen no assunto.\n"
            "2. A grafia correta é \"Sepan\" e não \"SEPAN\".\n"
            "3. Não utilize negrito no nome da pessoa no endereçamento.\n"
            "4. Siglas com até 3 letras devem ser totalmente em maiúsculas. Siglas com 4 letras ou mais devem ter apenas a primeira letra maiúscula e as demais minúsculas (ex: Suban, Sepan).\n"
            "5. Datas devem ser SEMPRE escritas por extenso e o local deve ser sempre 'Brasília' (ex: Brasília, 14 de maio de 2026, e nunca 'Brasil, 14/05/2026').\n"
            "6. A abreviação de número para processos deve ser com \"n\" minúsculo (ex: processo nº).\n"
            "7. Todo documento oficial do GDF deve ter seus parágrafos numerados em ordem crescente (ex: 1. Trata-se de..., 2. Sobre o tema..., 3. Encaminho...).\n"
            "8. É OBRIGATÓRIO incluir a linha 'Assunto:' no topo do documento logo após o cabeçalho e a data.\n"
            "9. Se o processo for de Ouvidoria, adicione logo abaixo do despacho a palavra 'MINUTA' centralizada, seguida da sugestão de resposta formal direcionada ao Ouvidor (Senhor Ouvidor...).\n"
            "10. É ESTRITAMENTE PROIBIDO gerar rodapés de assinatura eletrônica, linhas em branco para assinar (_______) ou blocos de autenticidade. O documento deve terminar imediatamente no parágrafo de encaminhamento ou na palavra 'Atenciosamente'.\n"
            "11. No caso de circulares (memorando ou ofício), siga sempre a ordem alfabética das unidades/pastas.\n"
            "12. Ao se basear em exemplos anteriores (ex: da Secex), faça as adequações necessárias na minuta (evite cópia integral sem revisão), lembrando sempre que quem assinará o documento será o Secretário."
        )
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("regras_redacao", regras_padrao)
        except Exception:
            pass
        return regras_padrao

    def processar_pasta_com_ia(self, folderpath: str, historico: list = None, stream_callback=None, molde_ia: str = "AUTO") -> Dict[str, Any]:
        """
        Processa todos os documentos de uma pasta de processo SEI,
        busca exemplos no banco de vetores e gera resposta com Ollama (Local).
        """
        # Verifica se o Ollama está online antes de começar
        ollama_ok, erro_ollama = self._verificar_ollama()
        if not ollama_ok:
            return {"sucesso": False, "erro": erro_ollama}

        meses = ['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        hoje = datetime.datetime.now()
        data_atual = f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

        extracted_text = ""
        try:
            try:
                import ollama
            except ImportError as e:
                return {"sucesso": False, "erro": f"Erro de dependência ({str(e)}). Execute 'pip install ollama' no terminal."}
            
            # 1. Extração de texto de arquivos dentro da pasta
            for root, dirs, files in os.walk(folderpath):
                files.sort(key=lambda x: int(re.search(r'\[(\d+)\]', x).group(1)) if re.search(r'\[(\d+)\]', x) else 999999)
                for file in files:
                    if file.lower().endswith(('.pdf', '.txt', '.html', '.htm', '.docx')):
                        filepath = os.path.join(root, file)
                        extracted_text += self._extrair_texto_arquivo(filepath) + "\n\n"
            
            if not extracted_text.strip():
                return {"sucesso": False, "erro": "Nenhum texto extraível foi encontrado nos arquivos da pasta (Podem ser arquivos sem OCR ou faltam bibliotecas)."}

            # Limitar o texto para não estourar o contexto da IA (Foco no final do processo)
            extracted_text = extracted_text[-8000:] if len(extracted_text) > 8000 else extracted_text
            
            # 1.5 Classificação do Processo (Routing)
            if molde_ia == "AUTO":
                prompt_class = f"Analise o texto a seguir e identifique o tipo de processo. Responda APENAS com UMA destas palavras: OUVIDORIA MINUTA, OUVIDORIA SUBAN, DILACAO ou GENERICO.\n\nTexto: {extracted_text[:2000]}"
                try:
                    res_class = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt_class}], options={'temperature': 0.1})
                    tipo_raw = res_class.get('message', {}).get('content', '').upper()
                    if 'OUVIDORIA MINUTA' in tipo_raw: tipo_detectado = "OUVIDORIA MINUTA"
                    elif 'OUVIDORIA SUBAN' in tipo_raw: tipo_detectado = "OUVIDORIA SUBAN"
                    elif 'OUVIDORIA' in tipo_raw: tipo_detectado = "OUVIDORIA MINUTA"
                    elif 'DILACAO' in tipo_raw or 'DILAÇÃO' in tipo_raw: tipo_detectado = "DILACAO"
                    else: tipo_detectado = "GENERICO"
                except Exception as e:
                    logger.error(f"Erro na classificação: {e}")
                    tipo_detectado = "GENERICO"
                    
                if stream_callback:
                    stream_callback(f"[Classificação Ollama: {tipo_detectado}]\nGerando documento...\n\n")
            else:
                tipo_detectado = molde_ia
                if stream_callback:
                    stream_callback(f"[Molde Selecionado: {tipo_detectado}]\nGerando documento...\n\n")

            # 2. Busca de Exemplos Passados (RAG com ChromaDB)
            contexto_historico = ""
            try:
                if self._vector_db.count() > 0:
                    emb = self._get_embedding_ollama(extracted_text[:1000])
                    docs_recuperados = self._vector_db.query(emb, n_results=2)
                    if docs_recuperados:
                        contexto_historico = "\n\nExemplos de despachos anteriores similares:\n" + "\n---\n".join(docs_recuperados)
            except Exception as e:
                logger.error(f"Aviso Banco de Vetores (RAG falhou): {e}", exc_info=True)
            
            # 3. Prompt para o Ollama (IA Local)
            regras_redacao = self._get_regras_redacao()
            
            molde_ouvidoria = f"Governo do Distrito Federal\nSecretaria Extraordinária de Proteção Animal do Distrito Federal\nGabinete\nAssessoria Especial\n\nDespacho - SEPAN/GAB/ASSESP\n\nBrasília, {data_atual}.\n\nAo Gabinete,\n\nAssunto: Demanda de Ouvidoria. (INSERIR AQUI O ASSUNTO RESUMIDO).\n\n1. Trata-se da reclamação registrada na Ouvidoria sob Ofício nº (INSERIR NUMERO), referente à Manifestação (INSERIR PROTOCOLO), na qual o cidadão (INSERIR RESUMO DA DEMANDA).\n\n2. Sobre o tema, esclarece-se que (INSERIR A RESPOSTA TÉCNICA E A JUSTIFICATIVA DE FORMA FLUIDA, COM SUAS PRÓPRIAS PALAVRAS).\n\n3. Encaminham-se os autos para conhecimento e adoção de providências.\n\nAtenciosamente,"

            MOLDES_RIGIDOS = {
                "OUVIDORIA MINUTA": molde_ouvidoria,
                "OUVIDORIA SUBAN": molde_ouvidoria,
                "OUVIDORIA": molde_ouvidoria,
                "DILACAO": f"Governo do Distrito Federal\nSecretaria Extraordinária de Proteção Animal do Distrito Federal\n\nBrasília, {data_atual}.\n\nAssunto: Dilação de Prazo.\n\n1. Trata-se do processo nº (INSERIR NUMERO), referente a (INSERIR TEMA).\n\n2. Solicita-se a dilação de prazo por mais 05 (cinco) dias devido à (INSERIR JUSTIFICATIVA DE COMPLEXIDADE DA DEMANDA).\n\n3. Encaminham-se os autos para as devidas providências.\n\nAtenciosamente,",
                "GENERICO": f"Governo do Distrito Federal\nSecretaria Extraordinária de Proteção Animal do Distrito Federal\nGabinete\n\nBrasília, {data_atual}.\n\nAssunto: (INSERIR AQUI O ASSUNTO RESUMIDO).\n\n1. Trata-se de (INSERIR EXPLICACAO DA DEMANDA).\n\n2. Sobre o tema, esclarece-se que (INSERIR A RESPOSTA TECNICA DE FORMA FLUIDA).\n\n3. Encaminham-se os autos para as devidas providências.\n\nAtenciosamente,"
            }
            molde_escolhido = MOLDES_RIGIDOS.get(tipo_detectado, MOLDES_RIGIDOS["GENERICO"])
            
            system_prompt = f"""Você é um ASSESSOR DE GABINETE EXTREMAMENTE RIGOROSO e AUTORAL da SEPAN-DF. Sua função é redigir a MINUTA COMPLETA de um documento oficial.
Você atua como um FILTRO. Você NUNCA repete o que os outros setores escreveram. Você lê, compreende, sintetiza e escreve a sua própria versão dos fatos.

MOLDE OBRIGATÓRIO (SIGA ESTA ESTRUTURA RIGOROSAMENTE, INCLUINDO O "Atenciosamente,"):
{molde_escolhido}

SUA TAREFA (CRÍTICA E INEGOCIÁVEL):
1. Leia o texto e PREENCHA as áreas indicadas por parênteses no molde com os dados REAIS do processo.
2. PARÁFRASE RADICAL (ANTI-CÓPIA): É ESTRITAMENTE PROIBIDO fazer "copia e cola" do texto do processo. Se você encontrar frases muito longas no original, você DEVE resumi-las com suas próprias palavras. Altere os verbos, os substantivos e a estrutura das frases.
   - Exemplo de Paráfrase: Ao invés de "o paciente possuía histórico clínico prévio", escreva "nota-se que o animal já apresentava registros de atendimento anteriores".
3. ESTRUTURA NUMERADA OBRIGATÓRIA: O corpo do texto DEVE ser estritamente em parágrafos numerados (1., 2., 3.). A estrutura do molde é engessada, sua liberdade criativa é apenas na reescrita dos fatos.
4. ATENÇÃO AO REMETENTE: Você está redigindo pela Assessoria Especial (ASSESP). Nunca copie o tom de voz, jargões ou as conclusões de outros departamentos (como a SECEX, SUBAN, OSC, etc.). O texto deve parecer escrito inteiramente por você.
5. REGRA DE IMPESSOALIDADE (CRÍTICA): É terminantemente PROIBIDO utilizar a primeira pessoa do plural (como "esclarecemos", "informamos"). A minuta deve ser redigida de forma impessoal (terceira pessoa + 'se'). Ex: "esclarece-se que", "nota-se que", "informa-se que", "encaminha-se".
6. FINALIZAÇÃO: A geração de texto DEVE acabar IMEDIATAMENTE após a palavra "Atenciosamente,". NUNCA adicione blocos de assinatura, nomes (ex: [SEU NOME]), cargos ou "Assinado por" ao final.

REGRAS DE FORMATAÇÃO:
{regras_redacao}"""

            user_prompt = f"""Aqui está o documento original com os fatos do processo:

--- INÍCIO DO DOCUMENTO ORIGINAL ---
{extracted_text}
--- FIM DO DOCUMENTO ORIGINAL ---

Agora, com base EXCLUSIVAMENTE nos fatos acima, gere a MINUTA COMPLETA preenchendo o MOLDE fornecido nas instruções do sistema.
Lembre-se:
1. Resuma e reescreva a justificativa com suas próprias palavras (PARÁFRASE RADICAL).
2. É expressamente PROIBIDO copiar as frases do texto original.
3. Mantenha os parágrafos sempre numerados (1., 2., 3.) conforme exigido no molde.
4. NUNCA use a primeira pessoa (ex: "Encaminhamos"). Use SEMPRE a forma impessoal (ex: "Encaminham-se").
5. Gere APENAS o documento final. Comece com "Governo do Distrito Federal" e termine na palavra "Atenciosamente,". Não adicione nenhuma assinatura."""

            try:
                resposta = ollama.chat(model='llama3.2', messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ], options={'temperature': 0.4, 'top_p': 0.85, 'stop': ['Assinado,', 'Assinatura', '[SEU NOME]', '[Nome]', 'Secretário Executivo']}, stream=True)
            except Exception as e:
                logger.error(f"Erro de comunicação com Ollama: {e}", exc_info=True)
                return {"sucesso": False, "erro": f"Erro de comunicação com o modelo no Ollama: {str(e)}. Verifique se o modelo 'llama3.2' está instalado."}
            
            conteudo_ia = ""
            for chunk in resposta:
                if 'message' in chunk and 'content' in chunk['message']:
                    conteudo_ia += chunk['message']['content']
                    if stream_callback:
                        stream_callback(conteudo_ia)
            
            # Mantém o texto gerado (incluindo raciocínio) como texto livre
            conteudo_ia_limpo = conteudo_ia.strip()
            
            # --- GUILHOTINA DE PÓS-PROCESSAMENTO ---
            # 1. Remove títulos indesejados no topo gerados pela IA
            conteudo_ia_limpo = re.sub(r'^(?:\*\*MINUTA COMPLETA\*\*|MINUTA COMPLETA|Aqui está a minuta:.*|MOLDE:.*)\s*\n+', '', conteudo_ia_limpo, flags=re.IGNORECASE).strip()

            # 2. Corta absolutamente tudo que vier depois da assinatura
            match_assinatura = re.search(r'(Atenciosamente,?)', conteudo_ia_limpo, re.IGNORECASE)
            if match_assinatura:
                conteudo_ia_limpo = conteudo_ia_limpo[:match_assinatura.end()]
            # ---------------------------------------

            # Inferir o tipo de documento pelo texto gerado
            tipo_doc = "Despacho" if "Despacho" in conteudo_ia_limpo[:200] else "Ofício"

            return {
                "sucesso": True,
                "tipo_documento": tipo_doc,
                "resumo": "Minuta gerada via IA",
                "texto_gerado": conteudo_ia_limpo
            }
        except Exception as e:
            logger.error(f"Erro geral em processar_zip_com_ia: {e}", exc_info=True)
            return {"sucesso": False, "erro": str(e)}

    def refinar_texto_com_ia(self, texto_atual: str, instrucao: str, stream_callback=None) -> Dict[str, Any]:
        """Usa o Ollama para refinar um texto existente baseado nas instruções do usuário."""
        ollama_ok, erro_ollama = self._verificar_ollama()
        if not ollama_ok:
            return {"sucesso": False, "erro": erro_ollama}

        try:
            import ollama
            
            regras_redacao = self._get_regras_redacao()
            system_prompt = f"""Você é um assistente administrativo especialista na redação de despachos do Governo.
Seu objetivo é alterar um documento oficial existente conforme as instruções do usuário.
ATENÇÃO: NÃO RESUMA. Mantenha a formalidade, a extensão, a estrutura e os parágrafos do documento original, aplicando estritamente a mudança solicitada.

REGRAS:
{regras_redacao}

Retorne APENAS o texto modificado pronto para uso."""

            prompt_user = f"Texto Atual:\n{texto_atual}\n\nInstrução do que deve ser alterado:\n{instrucao}\n\nReescreva o texto aplicando as alterações solicitadas."

            resposta = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt_user}
            ], stream=True)
            
            conteudo_ia = ""
            for chunk in resposta:
                if 'message' in chunk and 'content' in chunk['message']:
                    conteudo_ia += chunk['message']['content']
                    if stream_callback:
                        stream_callback(conteudo_ia)
                        
            conteudo_ia_limpo = conteudo_ia.strip()
            return {"sucesso": True, "texto_gerado": conteudo_ia_limpo}
        except Exception as e:
            logger.error(f"Erro ao refinar texto com o Ollama: {e}", exc_info=True)
            return {"sucesso": False, "erro": str(e)}

    def responder_pergunta_geral_com_ia(self, pergunta: str, stream_callback=None) -> Dict[str, Any]:
        """Usa o Ollama para responder uma pergunta geral usando o RAG."""
        ollama_ok, erro_ollama = self._verificar_ollama()
        if not ollama_ok:
            return {"sucesso": False, "erro": erro_ollama}

        try:
            import ollama
            
            contexto_historico = ""
            try:
                if self._vector_db.count() > 0:
                    emb = self._get_embedding_ollama(pergunta)
                    docs_recuperados = self._vector_db.query(emb, n_results=3)
                    if docs_recuperados:
                        contexto_historico = "\n\n---\n\n".join(docs_recuperados)
            except Exception as e:
                logger.error(f"Aviso Banco de Vetores (RAG falhou na pergunta): {e}", exc_info=True)

            system_prompt = """Você é o Assistente de Inteligência Artificial do SEI. Sua única função aqui é responder perguntas no chat de forma coloquial, como um colega de trabalho conversando no WhatsApp ou Teams.

=== REGRAS DE SOBREVIVÊNCIA (OBRIGATÓRIO) ===
1. Você é um CHATBOT, não um despachante. Fale de forma natural, usando parágrafos normais e curtos.
2. É EXPRESSAMENTE PROIBIDO iniciar sua resposta com "Assunto:".
3. É EXPRESSAMENTE PROIBIDO criar listas numeradas burocráticas (ex: "1. Trata-se...", "2. Sobre o tema...").
4. É EXPRESSAMENTE PROIBIDO usar palavras como "Encaminho", "Despacho", "À consideração".
5. Se a mensagem do usuário for só um "oi", "bom dia" ou "tudo bem?", ignore qualquer contexto de processos e seja apenas educado.
"""

            if contexto_historico:
                system_prompt += f"""
=== BASE DE CONHECIMENTO (APENAS PARA CONSULTA) ===
{contexto_historico}

INSTRUÇÃO: Use a Base de Conhecimento acima para descobrir a resposta da pergunta. Mas ATENÇÃO: Nunca copie a forma como esses textos estão escritos. Leia, entenda e explique para o usuário com suas próprias palavras, num tom de conversa normal.
"""

            user_prompt = f"Mensagem do Usuário: {pergunta}\n\n[Lembrete de Sistema: Responda obrigatoriamente como se estivesse em um chat de WhatsApp. Sem ofícios, sem 'Assunto:', sem numeração de parágrafos. Apenas texto normal.]"

            resposta = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ], stream=True)
            
            conteudo_ia = ""
            for chunk in resposta:
                if 'message' in chunk and 'content' in chunk['message']:
                    conteudo_ia += chunk['message']['content']
                    if stream_callback:
                        stream_callback(conteudo_ia)
                        
            conteudo_ia_limpo = conteudo_ia.strip()
            return {"sucesso": True, "texto_gerado": conteudo_ia_limpo}
        except Exception as e:
            logger.error(f"Erro ao responder pergunta com o Ollama: {e}", exc_info=True)
            return {"sucesso": False, "erro": str(e)}

    def salvar_no_banco_ia(self, texto_despacho: str) -> None:
        """Salva um despacho gerado no banco de vetores (ChromaDB) para servir de exemplo."""
        ollama_ok, _ = self._verificar_ollama()
        if not ollama_ok:
            return
            
        try:
            import hashlib
            emb = self._get_embedding_ollama(texto_despacho)
            doc_id = hashlib.md5(texto_despacho.encode('utf-8')).hexdigest()
            self._vector_db.upsert(doc_id, texto_despacho, emb)
        except Exception as e:
            logger.error(f"Erro em salvar_no_banco_ia: {e}", exc_info=True)

    def alimentar_banco_ia_por_pastas(self, parent_folder: str, progress_callback=None) -> Tuple[int, str]:
        """Lê uma pasta contendo processos (subpastas) e salva o contexto de cada processo como um exemplo único."""
        ollama_ok, erro_ollama = self._verificar_ollama()
        if not ollama_ok:
            return 0, erro_ollama
            
        sucesso_count = 0
        try:
            try:
                import hashlib
            except ImportError as e:
                return 0, f"Erro de biblioteca ({str(e)})."
            
            erros_detalhados = []
            
            # Cada subpasta representa um processo independente
            subfolders = [f.path for f in os.scandir(parent_folder) if f.is_dir()]
            if not subfolders:
                # Caso o usuário selecione a pasta de um único processo diretamente
                subfolders = [parent_folder]
                
            total_folders = len(subfolders)
            for idx, folder in enumerate(subfolders):
                if progress_callback:
                    progress_callback(idx + 1, total_folders, os.path.basename(folder))
                
                try:
                    texto_processo = ""
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if file.lower().endswith(('.pdf', '.txt', '.html', '.htm', '.docx')):
                                filepath = os.path.join(root, file)
                                texto_processo += self._extrair_texto_arquivo(filepath) + "\n\n"
                    
                    texto_processo = texto_processo.strip()
                    if texto_processo:
                        # Limita texto para evitar OOM e timeout no modelo local de Embeddings
                        texto_processo = texto_processo[:8000]
                        doc_id = hashlib.md5(texto_processo.encode('utf-8')).hexdigest()
                        emb = self._get_embedding_ollama(texto_processo)
                        self._vector_db.upsert(doc_id, texto_processo, emb)
                        sucesso_count += 1
                    else:
                        erros_detalhados.append(f"[{os.path.basename(folder)}] Vazio ou sem texto (PDF escaneado sem OCR?)")
                except Exception as e:
                    logger.error(f"Erro ao processar pasta {folder}: {e}", exc_info=True)
                    erros_detalhados.append(f"[{os.path.basename(folder)}] Erro: {str(e)}")
                    continue
            
            msg_erro = (" | ".join(erros_detalhados[:4]) + ("..." if len(erros_detalhados) > 4 else "")) if erros_detalhados else ""
            return sucesso_count, msg_erro
        except Exception as e:
            logger.error(f"Erro geral em alimentar_banco_ia_por_pastas: {e}", exc_info=True)
            return sucesso_count, str(e)
