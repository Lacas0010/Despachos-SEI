"""
Gerador SEI - Main Application
Modern interface for SEI document generation
"""

import datetime
import re
import tkinter as tk
from tkinter import filedialog, simpledialog
import json
import os
import logging
from typing import Dict, List, Optional, Any
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

from sei_templates import RESUMO_CRONOGRAMA
from theme_config import (
    get_color_tuple, configure_appearance, get_font, ThemeObserver, ThemeManager
)
from ui_animations import UIAnimations
from engine import SEIEngine

logging.basicConfig(
    filename='app_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Tooltip:
    """Tooltips para widgets."""
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None) -> None:
        if self.tooltip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0",
                        relief="solid", borderwidth=1, font=("Arial", 10))
        label.pack()

    def hide_tooltip(self, event=None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class GeradorSEIApp(ctk.CTk):
    """Aplicação principal unificada (Single-Page Layout)."""
    def __init__(self):
        super().__init__()
        self.title("Gerador de Despacho SEI")
        self.geometry("1450x850")
        self.minsize(1200, 700)
        
        self.engine = SEIEngine("modelos_custom.json")
        self.theme_manager = ThemeManager(self._carregar_config())
        configure_appearance(self.theme_manager.is_dark)
        
        self.historico: List[Dict[str, Any]] = []
        
        import queue
        self.task_queue = queue.Queue()
        self._process_queue()
        
        from concurrent.futures import ThreadPoolExecutor
        self.ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AI_Worker")
        
        self._build_ui()
        self._load_history()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=get_color_tuple("surface"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        
        ctk.CTkLabel(header, text="Gerador de Despacho SEI (Ollama)", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20)
        
        self.theme_btn = ctk.CTkButton(header, text="Light" if self.theme_manager.is_dark else "Dark", width=40, command=self._toggle_theme, fg_color="transparent", border_width=1)
        self.theme_btn.pack(side="right", padx=20, pady=15)
        
        # Main Layout
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=0, minsize=350)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0, minsize=380)
        
        self._build_chat_panel(body, 0)
        self._build_output(body, 1)
        self._build_historico(body, 2)

    def _get_emoji_icon(self, emoji_char: str, size: tuple = (20, 20)) -> Optional[ctk.CTkImage]:
        """Gera um ícone colorido em tempo real lendo a fonte COLR/CPAL do Windows."""
        try:
            # Cria uma imagem vazia com fundo 100% transparente
            img = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            font_size = int(min(size) * 0.75)
            try:
                # Carrega a fonte nativa de Emojis do Windows
                font = ImageFont.truetype("seguiemj.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                
            # O parâmetro embedded_color=True ativa a renderização do padrão COLR/CPAL
            draw.text((size[0]/2, size[1]/2), emoji_char, font=font, anchor="mm", embedded_color=True)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            logger.error(f"Erro ao gerar emoji dinâmico {emoji_char}: {e}")
            return None

    def _build_chat_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=12)
        frame.grid(row=0, column=col, sticky="nsew", padx=(0, 10))
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        icon_robot = self._get_emoji_icon("🤖", (24, 24))
        ctk.CTkLabel(
            frame, 
            text=" Assistente" if icon_robot else "🤖 Assistente", 
            image=icon_robot,
            compound="left",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(10, 10), padx=10)
        
        molde_frame = ctk.CTkFrame(frame, fg_color="transparent")
        molde_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkLabel(molde_frame, text="Molde do Documento:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.ia_molde_var = tk.StringVar(value="AUTO")
        self.ia_molde_combo = ctk.CTkComboBox(molde_frame, variable=self.ia_molde_var, values=["AUTO", "EXTRAÇÃO", "OUVIDORIA MINUTA", "OUVIDORIA SUBAN", "OUVIDORIA ELOGIO", "DILACAO", "GENERICO"], state="readonly", height=28)
        self.ia_molde_combo.pack(side="left", fill="x", expand=True)
        
        icon_folder = self._get_emoji_icon("📁", (20, 20))
        ctk.CTkButton(
            frame, 
            text=" Analisar Processo (Pasta)" if icon_folder else "📁 Analisar Processo (Pasta)", 
            image=icon_folder,
            compound="left",
            command=self._on_analisar_pasta, 
            height=40, 
            font=ctk.CTkFont(weight="bold")
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.chat_history = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=13), wrap="word", state="disabled")
        self.chat_history.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="O que alterar?", height=35)
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.chat_input.bind("<Return>", lambda e: self._on_enviar_chat())
        
        ctk.CTkButton(input_frame, text="Enviar", width=60, height=35, command=self._on_enviar_chat).grid(row=0, column=1)

    def _build_output(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=12)
        frame.grid(row=0, column=col, sticky="nsew", padx=10)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        icon_result = self._get_emoji_icon("📝", (24, 24))
        ctk.CTkLabel(
            header, 
            text=" Resultado" if icon_result else "📝 Resultado", 
            image=icon_result,
            compound="left",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        self.text_saida = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=14, family="Consolas"), wrap="word")
        self.text_saida.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.text_saida.insert("1.0", "O documento a do aparecerá aqui...")
        
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.status_label = ctk.CTkLabel(footer, text="Pronto.", text_color=get_color_tuple("success"))
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(footer, mode="indeterminate", width=200)
        self.progress_bar.set(0)
        
        icon_copy = self._get_emoji_icon("📋", (20, 20))
        ctk.CTkButton(
            footer, 
            text=" Copiar e Limpar" if icon_copy else "📋 Copiar e Limpar", 
            image=icon_copy,
            compound="left",
            command=self._on_copiar_limpar, 
            height=35
        ).pack(side="right")
        
        icon_copy_minuta = self._get_emoji_icon("📋", (20, 20))
        self.btn_copiar_minuta = ctk.CTkButton(
            footer, 
            text=" Copiar Minuta" if icon_copy_minuta else "📋 Copiar Minuta", 
            image=icon_copy_minuta,
            compound="left",
            command=self._on_copiar_minuta, 
            height=35
        )
        self.btn_copiar_minuta.pack(side="right", padx=(10, 10))
        
        icon_pdf = self._get_emoji_icon("📄", (20, 20))
        ctk.CTkButton(
            footer, 
            text=" PDF" if icon_pdf else "📄 PDF", 
            image=icon_pdf,
            compound="left",
            command=self._on_pdf, 
            height=35, 
            fg_color="transparent", 
            border_width=1
        ).pack(side="right", padx=10)

    def _build_historico(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=12)
        frame.grid(row=0, column=col, sticky="nsew", padx=(10, 0))
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)  # Caixa da lista de histórico
        frame.grid_rowconfigure(3, weight=2)  # Caixa de visualização do texto

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        icon_history = self._get_emoji_icon("📚", (24, 24))
        ctk.CTkLabel(
            header, 
            text=" Histórico" if icon_history else "📚 Histórico", 
            image=icon_history,
            compound="left",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)
        self.history_search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Buscar no histórico...")
        self.history_search_entry.grid(row=0, column=0, sticky="ew")
        self.history_search_entry.bind("<KeyRelease>", self._on_history_search)

        self.historico_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=160)
        self.historico_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.history_text_display = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=13, family="Consolas"), wrap="word", state="disabled")
        self.history_text_display.grid(row=3, column=0, sticky="nsew", padx=15, pady=(0, 10))

        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            footer, 
            text="Alimentar Ollama", 
            command=self._on_alimentar_ia, 
            width=120, 
            height=35, 
            fg_color="transparent", 
            border_width=1
        ).pack(side="left")

        icon_copy_hist = self._get_emoji_icon("📋", (20, 20))
        self.btn_copy_history = ctk.CTkButton(
            footer,
            text=" Copiar Histórico" if icon_copy_hist else "📋 Copiar Histórico",
            image=icon_copy_hist,
            compound="left",
            command=self._on_copy_history_text,
            height=35
        )
        self.btn_copy_history.pack(side="right")

    def _show_progress(self, mode="indeterminate"):
        self.progress_bar.configure(mode=mode)
        self.progress_bar.pack(side="left", padx=15)
        if mode == "indeterminate":
            self.progress_bar.start()

    def _hide_progress(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def destacar_tags_minuta(self, text_widget: ctk.CTkTextbox):
        """Aplica realce de sintaxe em padrões específicos no texto gerado."""
        # Configura as tags visualmente
        text_widget.tag_config("keyword", foreground="#2563EB")
        text_widget.tag_config("sei_num", foreground="#EA580C", background="#FEF08A")
        text_widget.tag_config("date_expr", foreground="#059669", underline=True)

        # Remove as tags antigas para evitar sobreposição de formatação
        for tag in ["keyword", "sei_num", "date_expr"]:
            text_widget.tag_remove(tag, "1.0", tk.END)

        conteudo = text_widget.get("1.0", tk.END)

        # Mapeamento de padrões usando Regex
        padroes = {
            "keyword": r'\b(MINUTA|Despacho|Ao Gabinete)\b',
            "sei_num": r'\b\d{6,}\b',
            "date_expr": r'\b\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4}\b'
        }

        for tag, padrao in padroes.items():
            flags = re.IGNORECASE if tag == "keyword" else 0
            for match in re.finditer(padrao, conteudo, flags):
                text_widget.tag_add(tag, f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def _add_to_chat(self, role, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, f"{role}: {text}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)

    def _load_history(self):
        """Carrega o histórico do banco de dados e atualiza a UI."""
        self.historico = self.engine.get_history()
        self._refresh_historico()

    def _on_stream_update(self, full_text):
        def update():
            output_text = full_text.strip()
            if output_text:
                self.text_saida.delete("1.0", tk.END)
                self.text_saida.insert("1.0", output_text)
                self.text_saida.see(tk.END)
                self.destacar_tags_minuta(self.text_saida)
        self.schedule_task(update)

    def _on_enviar_chat(self):
        msg = self.chat_input.get().strip()
        if not msg: return
        
        self.chat_input.delete(0, tk.END)
        self._add_to_chat("Você", msg)
        
        texto_atual = self.text_saida.get("1.0", tk.END).strip()
        # Se a caixa de texto estiver vazia ou com o placeholder, é uma pergunta geral
        if not texto_atual or texto_atual == "O documento gerado aparecerá aqui...":
            self.status_label.configure(text="Ollama pensando...", text_color=get_color_tuple("warning"))
            self._show_progress()
            self.ai_executor.submit(self._process_general_query, msg)
        else:
            # Caso contrário, é um refinamento do texto existente
            self.status_label.configure(text="Ollama pensando...", text_color=get_color_tuple("warning"))
            self._show_progress()
            self.ai_executor.submit(self._process_chat, msg, texto_atual)

    def _process_general_query(self, msg: str):
        """Processa uma pergunta geral do usuário contra o banco de vetores."""
        res = self.engine.responder_pergunta_geral_com_ia(msg, stream_callback=self._on_stream_update)
        self.schedule_task(lambda: self._apply_chat_result(res, is_general_query=True))

    def _process_chat(self, msg, texto_atual):
        res = self.engine.refinar_texto_com_ia(texto_atual, msg, stream_callback=self._on_stream_update)
        self.schedule_task(lambda: self._apply_chat_result(res, is_general_query=False))
        
    def _apply_chat_result(self, res: Dict[str, Any], is_general_query: bool = False):
        self._hide_progress()
        if res.get("sucesso"):
            novo_texto = res.get("texto_gerado", "")
            if novo_texto:
                self.text_saida.delete("1.0", tk.END)
                self.text_saida.insert("1.0", novo_texto)
                self.destacar_tags_minuta(self.text_saida)
            
            if is_general_query:
                self._add_to_chat("Ollama", "Resposta enviada para a área de Resultado.")
                self.status_label.configure(text="Resposta concluída!", text_color=get_color_tuple("success"))
                subject = "Pesquisa na base de dados"
                doc_type = "Pesquisa"
            else:
                self._add_to_chat("Ollama", "Texto atualizado conforme sua solicitação!")
                self.status_label.configure(text="Texto refinado!", text_color=get_color_tuple("success"))
                subject = "Texto refinado via chat"
                doc_type = "Refinamento"

            self.engine.save_to_history(doc_type=doc_type, subject=subject, full_text=novo_texto)
            self._load_history()
        else:
            self._show_message("Erro Ollama", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha no chat", text_color=get_color_tuple("error"))

    def _refresh_historico(self, items_to_display: Optional[List[Dict]] = None):
        for widget in self.historico_scroll.winfo_children():
            widget.destroy()
            
        items = items_to_display if items_to_display is not None else self.historico
        
        for item in items[:50]:
            card = ctk.CTkFrame(self.historico_scroll, corner_radius=8, border_width=1, fg_color="transparent", cursor="hand2")
            card.pack(fill="x", pady=4, padx=4)
            card.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))

            subject = item.get("subject", "Documento Gerado")
            if len(subject) > 35: subject = subject[:32] + "..."
            
            lbl_subject = ctk.CTkLabel(card, text=subject, font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            lbl_subject.pack(fill="x", padx=10, pady=(5,0))
            lbl_subject.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))

            try:
                dt_obj = datetime.datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                date_str = dt_obj.strftime("%d/%m/%y %H:%M")
            except (ValueError, KeyError):
                date_str = "Data inválida"

            lbl_date = ctk.CTkLabel(card, text=date_str, font=ctk.CTkFont(size=10), text_color=get_color_tuple("text_secondary"), anchor="w")
            lbl_date.pack(fill="x", padx=10, pady=(0,5))
            lbl_date.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))

    def _on_history_search(self, event=None):
        search_term = self.history_search_entry.get().strip()
        filtered_items = self.engine.search_history(search_term)
        self._refresh_historico(filtered_items)

    def _on_history_card_click(self, item: Dict[str, Any]):
        self.history_text_display.configure(state="normal")
        self.history_text_display.delete("1.0", tk.END)
        self.history_text_display.insert("1.0", item.get("full_text", "Texto não encontrado."))
        self.history_text_display.configure(state="disabled")

    def _on_copy_history_text(self):
        texto = self.history_text_display.get("1.0", tk.END).strip()
        if not texto: return
        self.clipboard_clear()
        self.clipboard_append(texto)

        cor_original = self.btn_copy_history.cget("fg_color")
        texto_original = self.btn_copy_history.cget("text")
        icon_original = self.btn_copy_history.cget("image")
        
        icon_check = self._get_emoji_icon("✔️", (20, 20))
        self.btn_copy_history.configure(fg_color=get_color_tuple("success"), text=" Copiado!" if icon_check else "✔️ Copiado!", image=icon_check)
        self.after(1500, lambda: self.btn_copy_history.configure(fg_color=cor_original, text=texto_original, image=icon_original))

    def _on_analisar_pasta(self):
        path = filedialog.askdirectory(title="Selecione a pasta do processo")
        if not path: return
        molde_selecionado = getattr(self, "ia_molde_var", tk.StringVar(value="AUTO")).get()
        self.status_label.configure(text="Analisando Ollama...", text_color=get_color_tuple("warning"))
        self._show_progress()
        self.ai_executor.submit(self._process_ia, path, molde_selecionado)

    def _process_ia(self, path, molde_selecionado="AUTO"):
        res = self.engine.processar_pasta_com_ia(path, stream_callback=self._on_stream_update, molde_ia=molde_selecionado)
        self.schedule_task(lambda: self._apply_ia_result(res))
        
    def _apply_ia_result(self, res):
        self._hide_progress()
        if res.get("sucesso"):
            tipo_doc = res.get("tipo_documento", "Documento")
            texto_gerado = res.get("texto_gerado", "")
            if texto_gerado:
                self.text_saida.delete("1.0", tk.END)
                self.text_saida.insert("1.0", texto_gerado)
                self.destacar_tags_minuta(self.text_saida)
                self._add_to_chat("Sistema", f"[{tipo_doc}] gerado com sucesso a partir da análise do processo.")
            self.status_label.configure(text="Análise concluída!", text_color=get_color_tuple("success"))
            
            subject = f"[{tipo_doc}] {res.get('resumo', 'Arquivo analisado pelo Ollama')}"
            self.engine.save_to_history(doc_type=tipo_doc, subject=subject, full_text=texto_gerado)
            self._load_history()
        else:
            self._show_message("Erro Ollama", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha Ollama", text_color=get_color_tuple("error"))

    def _on_alimentar_ia(self):
        path = filedialog.askdirectory(title="Selecione a pasta principal com os processos")
        if not path: return
        self.status_label.configure(text="Alimentando Ollama...", text_color=get_color_tuple("warning"))
        self._show_progress("determinate")
        self.progress_bar.set(0)
        self.ai_executor.submit(self._process_alimentar_ia, path)

    def _process_alimentar_ia(self, path):
        def cb(cur, tot, f):
            self.schedule_task(lambda: self.status_label.configure(text=f"Lendo {cur}/{tot}: {f}"))
            self.schedule_task(lambda: self.progress_bar.set(cur / tot if tot > 0 else 0))
        suc, err = self.engine.alimentar_banco_ia_por_pastas(path, cb)
        self.schedule_task(lambda: self._show_message("Ollama Alimentado", f"Processos aprendidos: {suc}\nErros: {err}", "success" if suc > 0 else "error"))
        self.schedule_task(lambda: self.status_label.configure(text="Ollama Atualizada!", text_color=get_color_tuple("success")))
        self.schedule_task(lambda: self._hide_progress())

    def _on_copiar_minuta(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto or "aparecerá aqui..." in texto:
            return
            
        self.clipboard_clear()
        self.clipboard_append(texto)
        
        cor_original = self.btn_copiar_minuta.cget("fg_color")
        texto_original = self.btn_copiar_minuta.cget("text")
        icon_original = self.btn_copiar_minuta.cget("image")
        
        icon_check = self._get_emoji_icon("✔️", (20, 20))
        self.btn_copiar_minuta.configure(
            fg_color=get_color_tuple("success"), 
            text=" Copiado!" if icon_check else "✔️ Copiado!",
            image=icon_check
        )
        self.after(1500, lambda: self.btn_copiar_minuta.configure(fg_color=cor_original, text=texto_original, image=icon_original))

    def _on_copiar_limpar(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if texto and texto != "O despacho gerado aparecerá aqui...":
            self.clipboard_clear()
            self.clipboard_append(texto)
        self.text_saida.delete("1.0", tk.END)
        self.status_label.configure(text="Copiado e limpo!", text_color=get_color_tuple("success"))
        
        self.thinking_box.delete("1.0", tk.END)
        self.thinking_box.insert("1.0", "Raciocínio do Ollama (Deep Thinking) aparecerá aqui...")
        
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state="disabled")

    def _on_pdf(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path:
            suc, err = self.engine.export_to_pdf(texto, path)
            if suc: self._show_message("Sucesso", "PDF salvo!", "success")
            else: self._show_message("Erro", err, "error")

    def _toggle_theme(self):
        self.theme_manager.toggle_theme()
        self.theme_btn.configure(text="Light" if self.theme_manager.is_dark else "Dark")
        self._salvar_config()

    def _show_message(self, title, msg, type="info"):
        from CTkMessagebox import CTkMessagebox
        icon_name = "cancel" if type == "error" else ("check" if type == "success" else type)
        CTkMessagebox(title=title, message=msg, icon=icon_name)

    def _process_queue(self):
        import queue
        try:
            for _ in range(10):
                task = self.task_queue.get_nowait()
                task()
        except queue.Empty: pass
        self.after(100, self._process_queue)

    def schedule_task(self, task):
        self.task_queue.put(task)
        
    def _carregar_config(self):
        try:
            with open("config.json", "r") as f: return json.load(f).get("dark_mode", True)
        except: return True

    def _salvar_config(self):
        try:
            with open("config.json", "w") as f: json.dump({"dark_mode": self.theme_manager.is_dark}, f)
        except: pass

    def _on_closing(self, event=None):
        self.ai_executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()
        self.quit()


if __name__ == "__main__":
    try:
        app = GeradorSEIApp()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicação encerrada pelo usuário.")
