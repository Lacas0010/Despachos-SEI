"""
Gerador SEI - Main Application
Modern interface for SEI document generation, process analysis, and markdown rendering
"""

import datetime
import re
import tkinter as tk
from tkinter import filedialog, simpledialog
import json
import os
import logging
import threading
from typing import Dict, List, Optional, Any
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor

from sei_templates import RESUMO_CRONOGRAMA
from sei_utils import (
    copy_html_to_clipboard, convert_text_to_sei_html,
    setup_markdown_tags, insert_markdown_text, render_markdown_inplace
)
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
    """Aplicação principal unificada com suporte a Markdown e Q&A no Chat."""
    def __init__(self):
        super().__init__()
        self.title("Gerador SEI - Suíte de Análise e Redação Oficial")
        self.geometry("1480x880")
        self.minsize(1200, 720)
        
        self.engine = SEIEngine("modelos_custom.json")
        self.theme_manager = ThemeManager(self._carregar_config())
        configure_appearance(self.theme_manager.is_dark)
        
        self.historico: List[Dict[str, Any]] = []
        self.selected_history_item: Optional[Dict[str, Any]] = None
        self.processo_ativo_texto: str = ""
        self.processo_ativo_nome: str = ""
        self.lote_resultados: List[Dict[str, Any]] = []
        self.current_cancel_event: Optional[threading.Event] = None
        
        self._chat_stream_start_index: Optional[str] = None
        
        import queue
        self.task_queue = queue.Queue()
        self._process_queue()
        
        self.ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AI_Worker")
        
        self._build_ui()
        self._load_history()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main Layout (2 Columns)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        body.grid_rowconfigure(0, weight=1)
        
        # Coluna 0: Sidebar (Tabview)
        body.grid_columnconfigure(0, weight=0, minsize=380)
        # Coluna 1: Main Area
        body.grid_columnconfigure(1, weight=1, minsize=650)
        
        # Criando o Tabview para a Sidebar
        self.sidebar_tabs = ctk.CTkTabview(body, width=380, corner_radius=15, fg_color=get_color_tuple("surface"))
        self.sidebar_tabs.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.sidebar_tabs.add("Assistente")
        self.sidebar_tabs.add("Lote")
        self.sidebar_tabs.add("Histórico")
        
        self.sidebar_tabs.tab("Assistente").grid_columnconfigure(0, weight=1)
        self.sidebar_tabs.tab("Assistente").grid_rowconfigure(0, weight=1)
        
        self.sidebar_tabs.tab("Lote").grid_columnconfigure(0, weight=1)
        self.sidebar_tabs.tab("Lote").grid_rowconfigure(0, weight=1)

        self.sidebar_tabs.tab("Histórico").grid_columnconfigure(0, weight=1)
        self.sidebar_tabs.tab("Histórico").grid_rowconfigure(0, weight=1)
        
        self._build_chat_panel(self.sidebar_tabs.tab("Assistente"), 0)
        self._build_lote_panel(self.sidebar_tabs.tab("Lote"), 0)
        self._build_historico(self.sidebar_tabs.tab("Histórico"), 0)
        self._build_output(body, 1)

    def _get_emoji_icon(self, emoji_char: str, size: tuple = (20, 20)) -> Optional[ctk.CTkImage]:
        """Gera um ícone colorido em tempo real lendo a fonte COLR/CPAL do Windows."""
        try:
            img = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            font_size = int(min(size) * 0.75)
            try:
                font = ImageFont.truetype("seguiemj.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            draw.text((size[0]/2, size[1]/2), emoji_char, font=font, anchor="mm", embedded_color=True)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            logger.error(f"Erro ao gerar emoji {emoji_char}: {e}")
            return None

    def _build_chat_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="nsew")
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # 1. Seletor de Molde
        molde_frame = ctk.CTkFrame(frame, fg_color="transparent")
        molde_frame.grid(row=0, column=0, sticky="ew", pady=(5, 10))
        ctk.CTkLabel(molde_frame, text="Molde:", font=get_font(13, "bold"), text_color=get_color_tuple("text_secondary")).pack(side="left", padx=(0, 10))
        
        self.ia_molde_var = tk.StringVar(value="AUTO")
        self.ia_molde_combo = ctk.CTkComboBox(
            molde_frame, 
            variable=self.ia_molde_var, 
            values=[
                "AUTO", "RESUMÃO", "LINHA DO TEMPO", "AUDITORIA", "EXTRAÇÃO", 
                "OUVIDORIA MINUTA", "OUVIDORIA SUBAN", "OUVIDORIA ELOGIO", "DILACAO", "GENERICO"
            ], 
            state="readonly", 
            height=36, 
            corner_radius=8, 
            font=get_font(13)
        )
        self.ia_molde_combo.pack(side="left", fill="x", expand=True)
        
        # 2. Botões de Abertura de Processo (Pasta ou Arquivo ZIP/PDF)
        btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        btn_box.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        btn_box.grid_columnconfigure(0, weight=1)
        btn_box.grid_columnconfigure(1, weight=1)
        
        icon_folder = self._get_emoji_icon("📁", (18, 18))
        ctk.CTkButton(
            btn_box, 
            text=" Pasta", 
            image=icon_folder,
            compound="left",
            command=self._on_analisar_pasta, 
            height=40, 
            corner_radius=8,
            font=get_font(13, "bold"),
            fg_color=get_color_tuple("primary"),
            hover_color=get_color_tuple("hover_primary")
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        icon_zip = self._get_emoji_icon("📦", (18, 18))
        ctk.CTkButton(
            btn_box, 
            text=" ZIP / PDF", 
            image=icon_zip,
            compound="left",
            command=self._on_analisar_arquivo, 
            height=40, 
            corner_radius=8,
            font=get_font(13, "bold"),
            fg_color=get_color_tuple("surface"),
            border_width=1,
            border_color=get_color_tuple("border"),
            text_color=get_color_tuple("text_primary")
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        # 3. Badge de Processo Ativo
        self.badge_processo_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.badge_processo_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.badge_processo_frame.grid_columnconfigure(0, weight=1)
        
        self.badge_label = ctk.CTkLabel(
            self.badge_processo_frame,
            text="Nenhum processo carregado",
            font=get_font(11),
            text_color=get_color_tuple("text_secondary"),
            anchor="w"
        )
        self.badge_label.grid(row=0, column=0, sticky="ew")
        
        # 4. Histórico do Chat
        self.chat_history = ctk.CTkTextbox(
            frame, 
            font=get_font(13), 
            wrap="word", 
            state="disabled", 
            fg_color="transparent", 
            border_width=1, 
            border_color=get_color_tuple("border"), 
            corner_radius=10
        )
        self.chat_history.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        setup_markdown_tags(self.chat_history, is_dark=self.theme_manager.is_dark, base_size=13)
        
        # 5. Modo do Chat (Segmented Button)
        self.chat_mode_var = tk.StringVar(value="Auto")
        self.chat_mode_segmented = ctk.CTkSegmentedButton(
            frame,
            values=["Auto", "Autos", "Refinar", "Geral"],
            variable=self.chat_mode_var,
            height=28,
            font=get_font(11, "bold")
        )
        self.chat_mode_segmented.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        
        # 6. Input do Chat
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.grid(row=5, column=0, sticky="ew", pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="Dúvidas dos autos ou instruções...", height=42, corner_radius=8, font=get_font(13), border_width=1)
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.chat_input.bind("<Return>", lambda e: self._on_enviar_chat())
        
        icon_send = self._get_emoji_icon("📤", (18, 18))
        ctk.CTkButton(
            input_frame, 
            text="", 
            image=icon_send, 
            width=42, 
            height=42, 
            corner_radius=8, 
            command=self._on_enviar_chat, 
            fg_color=get_color_tuple("primary"), 
            hover_color=get_color_tuple("hover_primary")
        ).grid(row=0, column=1)

    def _build_lote_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="nsew")
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(5, 10))
        
        icon_batch = self._get_emoji_icon("📊", (20, 20))
        ctk.CTkButton(
            header,
            text=" Iniciar Triagem em Pasta",
            image=icon_batch,
            compound="left",
            command=self._on_iniciar_lote,
            height=40,
            corner_radius=8,
            font=get_font(13, "bold"),
            fg_color=get_color_tuple("primary"),
            hover_color=get_color_tuple("hover_primary")
        ).pack(fill="x")
        
        self.lote_status_lbl = ctk.CTkLabel(
            frame, 
            text="Selecione uma pasta com múltiplos processos (.zip/pastas)",
            font=get_font(11), 
            text_color=get_color_tuple("text_secondary")
        )
        self.lote_status_lbl.grid(row=1, column=0, sticky="w", pady=(0, 8))
        
        self.lote_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.lote_scroll.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        
        icon_csv = self._get_emoji_icon("📥", (18, 18))
        self.btn_export_csv = ctk.CTkButton(
            footer,
            text=" Exportar Planilha (CSV)",
            image=icon_csv,
            compound="left",
            command=self._on_exportar_lote_csv,
            height=38,
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        )
        self.btn_export_csv.pack(fill="x")

    def _build_output(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=15)
        frame.grid(row=0, column=col, sticky="nsew", padx=(10, 0))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(15, 10))
        
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        icon_logo = self._get_emoji_icon("⚡", (26, 26))
        if icon_logo:
            ctk.CTkLabel(title_frame, text="", image=icon_logo).pack(side="left")
        ctk.CTkLabel(title_frame, text=" Gerador SEI", font=get_font(22, "bold"), text_color=get_color_tuple("text_primary")).pack(side="left", padx=(8,0))
        
        self.theme_btn = ctk.CTkButton(
            header, 
            text="Light" if self.theme_manager.is_dark else "Dark", 
            width=75, 
            height=32, 
            corner_radius=16, 
            command=self._toggle_theme, 
            fg_color=get_color_tuple("primary"), 
            text_color=get_color_tuple("text_primary"), 
            font=get_font(12, "bold")
        )
        self.theme_btn.pack(side="right")
        
        self.text_saida = ctk.CTkTextbox(frame, font=get_font(15, family="Segoe UI"), wrap="word", fg_color="transparent", corner_radius=0)
        self.text_saida.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 10))
        self.text_saida.insert("1.0", "O documento gerado ou análise do processo aparecerá aqui...")
        setup_markdown_tags(self.text_saida, is_dark=self.theme_manager.is_dark, base_size=15)
        
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=25, pady=(0, 15))
        
        self.status_label = ctk.CTkLabel(footer, text="Pronto.", font=get_font(13, "bold"), text_color=get_color_tuple("success"))
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(footer, mode="indeterminate", width=180, height=8, corner_radius=4)
        self.progress_bar.set(0)
        
        self.btn_cancelar_processo = ctk.CTkButton(
            footer,
            text="✖ Cancelar",
            command=self._on_cancelar_processo,
            height=28,
            width=85,
            corner_radius=6,
            font=get_font(11, "bold"),
            fg_color=get_color_tuple("error"),
            hover_color="#c92a2a"
        )
        
        # Botões de Exportação
        icon_clear = self._get_emoji_icon("🧹", (18, 18))
        ctk.CTkButton(
            footer, 
            text=" Limpar", 
            image=icon_clear,
            compound="left",
            command=self._on_copiar_limpar, 
            height=38,
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        ).pack(side="right")
        
        icon_copy_sei = self._get_emoji_icon("✨", (18, 18))
        self.btn_copiar_sei = ctk.CTkButton(
            footer, 
            text=" Copiar p/ SEI", 
            image=icon_copy_sei,
            compound="left",
            command=self._on_copiar_sei, 
            height=38,
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color=get_color_tuple("primary"),
            hover_color=get_color_tuple("hover_primary")
        )
        self.btn_copiar_sei.pack(side="right", padx=(8, 8))
        
        icon_copy_plain = self._get_emoji_icon("📋", (18, 18))
        self.btn_copiar_plain = ctk.CTkButton(
            footer, 
            text=" Texto", 
            image=icon_copy_plain,
            compound="left",
            command=self._on_copiar_plain, 
            height=38,
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        )
        self.btn_copiar_plain.pack(side="right", padx=(0, 4))
        
        icon_docx = self._get_emoji_icon("📝", (18, 18))
        ctk.CTkButton(
            footer, 
            text=" Word", 
            image=icon_docx,
            compound="left",
            command=self._on_docx, 
            height=38, 
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color="transparent", 
            border_width=1,
            text_color=get_color_tuple("text_primary")
        ).pack(side="right", padx=4)

        icon_pdf = self._get_emoji_icon("📄", (18, 18))
        ctk.CTkButton(
            footer, 
            text=" PDF", 
            image=icon_pdf,
            compound="left",
            command=self._on_pdf, 
            height=38, 
            corner_radius=8,
            font=get_font(12, "bold"),
            fg_color="transparent", 
            border_width=1,
            text_color=get_color_tuple("text_primary")
        ).pack(side="right", padx=4)

    def _build_historico(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=col, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_rowconfigure(4, weight=2)
        
        # 1. Search Bar
        search_frame = ctk.CTkFrame(frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", pady=(5, 6))
        search_frame.grid_columnconfigure(0, weight=1)
        self.history_search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="🔍 Buscar no histórico por assunto ou texto...", 
            height=36, 
            corner_radius=8, 
            font=get_font(12)
        )
        self.history_search_entry.grid(row=0, column=0, sticky="ew")
        self.history_search_entry.bind("<KeyRelease>", self._on_history_search)
        
        # 2. History List Label
        lbl_list = ctk.CTkLabel(frame, text="Itens Salvos (clique p/ rever ou duplo-clique p/ carregar):", font=get_font(11, "bold"), text_color=get_color_tuple("text_secondary"), anchor="w")
        lbl_list.grid(row=1, column=0, sticky="w", pady=(0, 2))

        # 3. History Scrollable Cards List
        self.historico_scroll = ctk.CTkScrollableFrame(frame, height=170, fg_color="transparent")
        self.historico_scroll.grid(row=2, column=0, sticky="nsew", pady=(0, 6))
        
        # 4. Selected Item Header / Info Badge
        self.hist_item_info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.hist_item_info_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        self.hist_item_info_frame.grid_columnconfigure(0, weight=1)
        
        self.hist_item_info_lbl = ctk.CTkLabel(
            self.hist_item_info_frame,
            text="Nenhum item selecionado",
            font=get_font(11, "bold"),
            text_color=get_color_tuple("text_secondary"),
            anchor="w"
        )
        self.hist_item_info_lbl.grid(row=0, column=0, sticky="w")
        
        # 5. Preview Textbox
        self.history_text_display = ctk.CTkTextbox(
            frame, 
            font=get_font(12), 
            wrap="word", 
            state="disabled", 
            fg_color="transparent", 
            border_width=1, 
            border_color=get_color_tuple("border"), 
            corner_radius=8
        )
        self.history_text_display.grid(row=4, column=0, sticky="nsew", pady=(0, 6))
        setup_markdown_tags(self.history_text_display, is_dark=self.theme_manager.is_dark, base_size=12)
        
        # 6. Action Toolbar for Selected Item
        actions_frame = ctk.CTkFrame(frame, fg_color="transparent")
        actions_frame.grid(row=5, column=0, sticky="ew", pady=(0, 4))
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        
        icon_load = self._get_emoji_icon("🚀", (16, 16))
        self.btn_load_history = ctk.CTkButton(
            actions_frame,
            text=" Carregar p/ Edição",
            image=icon_load,
            compound="left",
            command=self._on_carregar_historico_ativo,
            height=34,
            corner_radius=6,
            font=get_font(11, "bold"),
            fg_color=get_color_tuple("primary"),
            hover_color=get_color_tuple("hover_primary")
        )
        self.btn_load_history.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=2)
        
        icon_chat = self._get_emoji_icon("💬", (16, 16))
        self.btn_chat_history = ctk.CTkButton(
            actions_frame,
            text=" Perguntar no Chat",
            image=icon_chat,
            compound="left",
            command=self._on_perguntar_historico,
            height=34,
            corner_radius=6,
            font=get_font(11, "bold"),
            fg_color=get_color_tuple("surface"),
            border_width=1,
            border_color=get_color_tuple("border"),
            text_color=get_color_tuple("text_primary")
        )
        self.btn_chat_history.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=2)
        
        # Row 2 of actions: Copiar p/ SEI | Copiar Texto | Word | PDF | Excluir
        sub_actions = ctk.CTkFrame(frame, fg_color="transparent")
        sub_actions.grid(row=6, column=0, sticky="ew", pady=(0, 6))
        
        icon_sei = self._get_emoji_icon("✨", (15, 15))
        self.btn_hist_copy_sei = ctk.CTkButton(
            sub_actions,
            text=" SEI",
            image=icon_sei,
            compound="left",
            command=self._on_copiar_sei_historico,
            height=30,
            corner_radius=6,
            font=get_font(11, "bold"),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        )
        self.btn_hist_copy_sei.pack(side="left", padx=(0, 3))
        
        icon_copy = self._get_emoji_icon("📋", (15, 15))
        self.btn_hist_copy_plain = ctk.CTkButton(
            sub_actions,
            text=" Texto",
            image=icon_copy,
            compound="left",
            command=self._on_copiar_plain_historico,
            height=30,
            corner_radius=6,
            font=get_font(11),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        )
        self.btn_hist_copy_plain.pack(side="left", padx=(0, 3))
        
        icon_docx = self._get_emoji_icon("📝", (15, 15))
        ctk.CTkButton(
            sub_actions,
            text=" Word",
            image=icon_docx,
            compound="left",
            command=self._on_docx_historico,
            height=30,
            corner_radius=6,
            font=get_font(11),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        ).pack(side="left", padx=(0, 3))

        icon_pdf = self._get_emoji_icon("📄", (15, 15))
        ctk.CTkButton(
            sub_actions,
            text=" PDF",
            image=icon_pdf,
            compound="left",
            command=self._on_pdf_historico,
            height=30,
            corner_radius=6,
            font=get_font(11),
            fg_color="transparent",
            border_width=1,
            text_color=get_color_tuple("text_primary")
        ).pack(side="left", padx=(0, 3))
        
        icon_del = self._get_emoji_icon("🗑️", (15, 15))
        ctk.CTkButton(
            sub_actions,
            text="",
            image=icon_del,
            command=self._on_delete_history_item,
            width=32,
            height=30,
            corner_radius=6,
            fg_color="transparent",
            border_width=1,
            border_color=get_color_tuple("error"),
            hover_color=get_color_tuple("error")
        ).pack(side="right")
        
        # 7. Bottom Global Footer
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=7, column=0, sticky="ew", pady=(2, 0))
        
        icon_brain = self._get_emoji_icon("🧠", (16, 16))
        ctk.CTkButton(
            footer, 
            text=" Alimentar IA (RAG com Pasta)", 
            image=icon_brain,
            compound="left",
            command=self._on_alimentar_ia, 
            height=34,
            corner_radius=6,
            font=get_font(11, "bold"),
            fg_color="transparent", 
            border_width=1,
            text_color=get_color_tuple("text_secondary")
        ).pack(fill="x")

    def _show_progress(self, mode="indeterminate"):
        self.current_cancel_event = threading.Event()
        self.progress_bar.configure(mode=mode)
        self.progress_bar.pack(side="left", padx=(15, 6))
        self.btn_cancelar_processo.pack(side="left", padx=4)
        if mode == "indeterminate":
            self.progress_bar.start()

    def _hide_progress(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.btn_cancelar_processo.pack_forget()
        self.current_cancel_event = None

    def _on_cancelar_processo(self):
        if self.current_cancel_event:
            self.current_cancel_event.set()
            self.status_label.configure(text="Cancelando processo...", text_color=get_color_tuple("warning"))

    def _add_to_chat(self, role: str, text: str):
        """Adiciona uma mensagem ao chat com formatação markdown rica e cores por papel."""
        self.chat_history.configure(state="normal")
        
        tag_role = "role_user" if role == "Você" else ("role_system" if role == "Sistema" else "role_ollama")
        self.chat_history.insert(tk.END, f"{role}:\n", (tag_role,))
        
        insert_markdown_text(self.chat_history, text, is_dark=self.theme_manager.is_dark, base_size=13)
        self.chat_history.insert(tk.END, "\n\n")
        
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)

    def _init_chat_stream(self, role: str = "Ollama"):
        """Prepara o chat para receber streaming em tempo real da resposta da IA."""
        self.chat_history.configure(state="normal")
        tag_role = "role_ollama"
        self.chat_history.insert(tk.END, f"{role}:\n", (tag_role,))
        self._chat_stream_start_index = self.chat_history.index(tk.END + "-1c")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)

    def _on_chat_stream_update(self, full_text: str):
        """Atualiza a mensagem em tempo real no Chat conforme o Ollama responde."""
        def update():
            output_text = full_text.strip()
            if output_text and self._chat_stream_start_index:
                final_text = output_text
                if "<think>" in output_text:
                    if "</think>" in output_text:
                        parts = output_text.split("</think>", 1)
                        final_text = parts[1].strip()
                    else:
                        final_text = "Pensando..."
                
                if final_text:
                    self.chat_history.configure(state="normal")
                    self.chat_history.delete(self._chat_stream_start_index, tk.END)
                    self.chat_history.insert(self._chat_stream_start_index, final_text)
                    self.chat_history.configure(state="disabled")
                    self.chat_history.see(tk.END)
        self.schedule_task(update)

    def _on_doc_stream_update(self, full_text: str):
        """Atualiza a área principal de Documento (Resumão / Minuta) em tempo real."""
        def update():
            output_text = full_text.strip()
            if output_text:
                final_text = output_text
                if "<think>" in output_text:
                    if "</think>" in output_text:
                        parts = output_text.split("</think>", 1)
                        final_text = parts[1].strip()
                    else:
                        final_text = ""
                if final_text:
                    self.text_saida.delete("1.0", tk.END)
                    self.text_saida.insert("1.0", final_text)
                    self.text_saida.see(tk.END)
        self.schedule_task(update)

    def _load_history(self):
        self.historico = self.engine.get_history()
        self._refresh_historico()

    def _on_enviar_chat(self):
        msg = self.chat_input.get().strip()
        if not msg: return
        
        self.chat_input.delete(0, tk.END)
        self._add_to_chat("Você", msg)
        
        modo = self.chat_mode_var.get()
        texto_atual = self.text_saida.get("1.0", tk.END).strip()
        
        self.status_label.configure(text="Ollama pensando...", text_color=get_color_tuple("warning"))
        self._show_progress()
        
        if modo == "Autos" or (modo == "Auto" and self.processo_ativo_texto and ("qual" in msg.lower() or "quem" in msg.lower() or "quando" in msg.lower() or "onde" in msg.lower() or "quanto" in msg.lower() or "?" in msg)):
            # Pergunta direta sobre os autos carregados (Responde no CHAT, mantém o documento no meio intacto!)
            self._init_chat_stream("Ollama")
            self.ai_executor.submit(self._process_qa_processo, msg, self.processo_ativo_texto)
        elif modo == "Refinar" or (modo == "Auto" and texto_atual and texto_atual != "O documento gerado ou análise do processo aparecerá aqui..." and ("altere" in msg.lower() or "mude" in msg.lower() or "reescreva" in msg.lower() or "adicione" in msg.lower() or "retire" in msg.lower())):
            # Refinamento do documento (Atualiza a área central de documento)
            self.ai_executor.submit(self._process_chat, msg, texto_atual)
        else:
            # Pergunta geral contra o banco de vetores RAG (Responde no CHAT, mantém o documento no meio intacto!)
            self._init_chat_stream("Ollama")
            self.ai_executor.submit(self._process_general_query, msg)

    def _process_qa_processo(self, msg: str, texto_processo: str):
        res = self.engine.responder_pergunta_sobre_processo(msg, texto_processo, stream_callback=self._on_chat_stream_update, cancel_event=self.current_cancel_event)
        self.schedule_task(lambda: self._apply_chat_qa_result(res, label_tipo="Consulta aos Autos"))

    def _process_general_query(self, msg: str):
        res = self.engine.responder_pergunta_geral_com_ia(msg, stream_callback=self._on_chat_stream_update, cancel_event=self.current_cancel_event)
        self.schedule_task(lambda: self._apply_chat_qa_result(res, label_tipo="Pesquisa RAG"))

    def _apply_chat_qa_result(self, res: Dict[str, Any], label_tipo: str = "Chat"):
        self._hide_progress()
        if res.get("cancelado"):
            self.status_label.configure(text=f"{label_tipo} cancelado!", text_color=get_color_tuple("warning"))
            if self._chat_stream_start_index:
                self.chat_history.configure(state="normal")
                self.chat_history.delete(self._chat_stream_start_index, tk.END)
                self.chat_history.insert(tk.END, "*(Operação cancelada pelo usuário)*\n\n")
                self.chat_history.configure(state="disabled")
                self.chat_history.see(tk.END)
                self._chat_stream_start_index = None
            return

        if res.get("sucesso"):
            novo_texto = res.get("texto_gerado", "")
            
            # Formata a resposta final no Chat com Markdown nativo
            if self._chat_stream_start_index:
                self.chat_history.configure(state="normal")
                self.chat_history.delete(self._chat_stream_start_index, tk.END)
                insert_markdown_text(self.chat_history, novo_texto, is_dark=self.theme_manager.is_dark, base_size=13)
                self.chat_history.insert(tk.END, "\n\n")
                self.chat_history.configure(state="disabled")
                self.chat_history.see(tk.END)
                self._chat_stream_start_index = None
                
            self.status_label.configure(text=f"{label_tipo} concluído!", text_color=get_color_tuple("success"))
            self.engine.save_to_history(
                doc_type=label_tipo, 
                subject=f"[{label_tipo}] via Chat", 
                full_text=novo_texto,
                process_context=self.processo_ativo_texto
            )
            self._load_history()
        else:
            self._show_message("Erro Ollama", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha no chat", text_color=get_color_tuple("error"))

    def _process_chat(self, msg: str, texto_atual: str):
        res = self.engine.refinar_texto_com_ia(texto_atual, msg, stream_callback=self._on_doc_stream_update, cancel_event=self.current_cancel_event)
        self.schedule_task(lambda: self._apply_refine_result(res))

    def _apply_refine_result(self, res: Dict[str, Any]):
        self._hide_progress()
        if res.get("cancelado"):
            self.status_label.configure(text="Refinamento cancelado!", text_color=get_color_tuple("warning"))
            self._add_to_chat("Sistema", "Refinamento cancelado pelo usuário.")
            return

        if res.get("sucesso"):
            novo_texto = res.get("texto_gerado", "")
            if novo_texto:
                self.text_saida.delete("1.0", tk.END)
                insert_markdown_text(self.text_saida, novo_texto, is_dark=self.theme_manager.is_dark, base_size=15)
            
            self._add_to_chat("Ollama", "Documento refinado e atualizado na área central conforme suas instruções.")
            self.status_label.configure(text="Texto refinado!", text_color=get_color_tuple("success"))
            
            self.engine.save_to_history(
                doc_type="Refinamento", 
                subject="[Refinamento] via Chat", 
                full_text=novo_texto,
                process_context=self.processo_ativo_texto
            )
            self._load_history()
        else:
            self._show_message("Erro Ollama", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha no refinamento", text_color=get_color_tuple("error"))

    def _on_analisar_pasta(self):
        path = filedialog.askdirectory(title="Selecione a pasta do processo SEI")
        if not path: return
        self._iniciar_analise_alvo(path)

    def _on_analisar_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo do processo (.zip, .pdf, .docx)",
            filetypes=[
                ("Arquivos de Processo", "*.zip;*.pdf;*.docx;*.txt;*.html;*.htm"),
                ("Arquivo Compactado SEI (.zip)", "*.zip"),
                ("Documento PDF (.pdf)", "*.pdf"),
                ("Todos os Arquivos", "*.*")
            ]
        )
        if not path: return
        self._iniciar_analise_alvo(path)

    def _iniciar_analise_alvo(self, path: str):
        molde_selecionado = getattr(self, "ia_molde_var", tk.StringVar(value="AUTO")).get()
        self.status_label.configure(text="Analisando processo...", text_color=get_color_tuple("warning"))
        self._show_progress()
        self.ai_executor.submit(self._process_ia, path, molde_selecionado)

    def _process_ia(self, path: str, molde_selecionado: str = "AUTO"):
        res = self.engine.processar_pasta_com_ia(path, stream_callback=self._on_doc_stream_update, molde_ia=molde_selecionado, cancel_event=self.current_cancel_event)
        self.schedule_task(lambda: self._apply_ia_result(res))
        
    def _apply_ia_result(self, res: Dict[str, Any]):
        self._hide_progress()
        if res.get("cancelado"):
            self.status_label.configure(text="Análise cancelada pelo usuário!", text_color=get_color_tuple("warning"))
            return

        if res.get("sucesso"):
            tipo_doc = res.get("tipo_documento", "Documento")
            texto_gerado = res.get("texto_gerado", "")
            self.processo_ativo_texto = res.get("texto_processo", "")
            self.processo_ativo_nome = res.get("nome_processo", "Processo")
            
            # Atualiza Badge de Processo Ativo
            self.badge_label.configure(
                text=f"📌 Ativo: {self.processo_ativo_nome[:32]}",
                text_color=get_color_tuple("primary")
            )
            
            if texto_gerado:
                self.text_saida.delete("1.0", tk.END)
                insert_markdown_text(self.text_saida, texto_gerado, is_dark=self.theme_manager.is_dark, base_size=15)
                self._add_to_chat("Sistema", f"[{tipo_doc}] gerado com sucesso para {self.processo_ativo_nome}.")
            self.status_label.configure(text="Análise concluída!", text_color=get_color_tuple("success"))
            
            subject = f"[{tipo_doc}] {res.get('resumo', self.processo_ativo_nome)}"
            self.engine.save_to_history(
                doc_type=tipo_doc, 
                subject=subject, 
                full_text=texto_gerado,
                process_context=self.processo_ativo_texto
            )
            self._load_history()
        else:
            self._show_message("Erro na Análise", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha Ollama", text_color=get_color_tuple("error"))

    def _on_iniciar_lote(self):
        path = filedialog.askdirectory(title="Selecione a pasta com múltiplos processos")
        if not path: return
        self.lote_status_lbl.configure(text=f"Processando pasta: {os.path.basename(path)}...")
        self.status_label.configure(text="Executando Triagem em Lote...", text_color=get_color_tuple("warning"))
        self._show_progress("determinate")
        self.progress_bar.set(0)
        self.ai_executor.submit(self._process_lote, path)

    def _process_lote(self, path: str):
        def cb(cur, tot, f):
            self.schedule_task(lambda: self.status_label.configure(text=f"Triando {cur}/{tot}: {f[:25]}"))
            self.schedule_task(lambda: self.progress_bar.set(cur / tot if tot > 0 else 0))
        resultados, erro = self.engine.processar_lote_processos(path, cb, cancel_event=self.current_cancel_event)
        self.schedule_task(lambda: self._apply_lote_result(resultados, erro))

    def _apply_lote_result(self, resultados: List[Dict[str, Any]], erro: str):
        self._hide_progress()
        if erro and "cancelad" in erro.lower():
            self.status_label.configure(text="Triagem cancelada pelo usuário!", text_color=get_color_tuple("warning"))
            self.lote_status_lbl.configure(text="Triagem cancelada.")
            return

        if erro:
            self._show_message("Erro no Lote", erro, "error")
            self.status_label.configure(text="Erro na triagem", text_color=get_color_tuple("error"))
            return
            
        self.lote_resultados = resultados
        self.lote_status_lbl.configure(text=f"Triagem concluída: {len(resultados)} processos analisados.")
        self.status_label.configure(text="Triagem concluída!", text_color=get_color_tuple("success"))
        
        for w in self.lote_scroll.winfo_children():
            w.destroy()
            
        for item in resultados:
            card = ctk.CTkFrame(self.lote_scroll, corner_radius=8, border_width=1, fg_color="transparent")
            card.pack(fill="x", pady=4, padx=2)
            
            header_row = ctk.CTkFrame(card, fg_color="transparent")
            header_row.pack(fill="x", padx=8, pady=(5, 2))
            
            prio = item.get("prioridade", "Normal")
            prio_color = get_color_tuple("error") if prio == "Urgente" else (get_color_tuple("warning") if prio == "Alta" else get_color_tuple("secondary"))
            
            lbl_proc = ctk.CTkLabel(header_row, text=f"{item.get('arquivo', 'Processo')}", font=get_font(12, "bold"), anchor="w")
            lbl_proc.pack(side="left")
            
            lbl_prio = ctk.CTkLabel(header_row, text=f"[{prio}]", font=get_font(11, "bold"), text_color=prio_color)
            lbl_prio.pack(side="right")
            
            detalhe = f"Interessado: {item.get('interessado', '-')}\nAssunto: {item.get('assunto', '-')}\nPrazo: {item.get('prazo', '-')}\nEncaminhamento: {item.get('encaminhamento', '-')}"
            lbl_detalhes = ctk.CTkLabel(card, text=detalhe, font=get_font(11), justify="left", anchor="w", text_color=get_color_tuple("text_secondary"))
            lbl_detalhes.pack(fill="x", padx=8, pady=(0, 5))

    def _on_exportar_lote_csv(self):
        if not self.lote_resultados:
            self._show_message("Aviso", "Execute primeiro a triagem em lote para gerar os dados.", "info")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Planilha CSV", "*.csv")])
        if path:
            suc, err = self.engine.exportar_lote_csv(self.lote_resultados, path)
            if suc:
                self._show_message("Sucesso", "Planilha exportada com sucesso!", "success")
            else:
                self._show_message("Erro", f"Falha ao exportar CSV: {err}", "error")

    def _on_copiar_sei(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto or "aparecerá aqui..." in texto:
            return
        
        html_formatado = convert_text_to_sei_html(texto)
        copiou_rico = copy_html_to_clipboard(html_formatado, texto)
        if not copiou_rico:
            self.clipboard_clear()
            self.clipboard_append(texto)
            
        cor_original = self.btn_copiar_sei.cget("fg_color")
        texto_original = self.btn_copiar_sei.cget("text")
        icon_check = self._get_emoji_icon("✔️", (18, 18))
        
        self.btn_copiar_sei.configure(
            fg_color=get_color_tuple("success"),
            text=" Copiado p/ SEI!",
            image=icon_check
        )
        self.after(1500, lambda: self.btn_copiar_sei.configure(fg_color=cor_original, text=texto_original, image=self._get_emoji_icon("✨", (18, 18))))

    def _on_copiar_plain(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto or "aparecerá aqui..." in texto: return
        self.clipboard_clear()
        self.clipboard_append(texto)
        
        cor_original = self.btn_copiar_plain.cget("fg_color")
        texto_original = self.btn_copiar_plain.cget("text")
        icon_check = self._get_emoji_icon("✔️", (18, 18))
        self.btn_copiar_plain.configure(fg_color=get_color_tuple("success"), text=" Copiado!", image=icon_check)
        self.after(1500, lambda: self.btn_copiar_plain.configure(fg_color=cor_original, text=texto_original, image=self._get_emoji_icon("📋", (18, 18))))

    def _on_docx(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto or "aparecerá aqui..." in texto: return
        path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Documento Word (.docx)", "*.docx")])
        if path:
            suc, err = self.engine.export_to_docx(texto, path)
            if suc: self._show_message("Sucesso", "Documento Word (.docx) salvo com sucesso!", "success")
            else: self._show_message("Erro", err, "error")

    def _on_pdf(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if not texto or "aparecerá aqui..." in texto: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Documento PDF (.pdf)", "*.pdf")])
        if path:
            suc, err = self.engine.export_to_pdf(texto, path)
            if suc: self._show_message("Sucesso", "PDF salvo com sucesso!", "success")
            else: self._show_message("Erro", err, "error")

    def _on_copiar_limpar(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if texto and texto != "O documento gerado ou análise do processo aparecerá aqui...":
            self.clipboard_clear()
            self.clipboard_append(texto)
        self.text_saida.delete("1.0", tk.END)
        self.processo_ativo_texto = ""
        self.processo_ativo_nome = ""
        self.badge_label.configure(text="Nenhum processo carregado", text_color=get_color_tuple("text_secondary"))
        self.status_label.configure(text="Copiado e limpo!", text_color=get_color_tuple("success"))
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state="disabled")

    def _refresh_historico(self, items_to_display: Optional[List[Dict]] = None):
        for widget in self.historico_scroll.winfo_children():
            widget.destroy()
            
        items = items_to_display if items_to_display is not None else self.historico
        
        if not items:
            lbl_vazio = ctk.CTkLabel(
                self.historico_scroll, 
                text="Nenhum item salvo no histórico.", 
                font=get_font(11), 
                text_color=get_color_tuple("text_secondary")
            )
            lbl_vazio.pack(pady=15)
            return
            
        for item in items[:50]:
            is_selected = self.selected_history_item and self.selected_history_item.get("id") == item.get("id")
            card_border = get_color_tuple("primary") if is_selected else get_color_tuple("border")
            card_bg = get_color_tuple("surface") if is_selected else "transparent"
            
            card = ctk.CTkFrame(
                self.historico_scroll, 
                corner_radius=8, 
                border_width=1, 
                border_color=card_border,
                fg_color=card_bg, 
                cursor="hand2"
            )
            card.pack(fill="x", pady=3, padx=2)
            card.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))
            card.bind("<Double-Button-1>", lambda e, i=item: self._on_carregar_historico_ativo(i))

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(4, 2))
            top_row.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))
            top_row.bind("<Double-Button-1>", lambda e, i=item: self._on_carregar_historico_ativo(i))

            doc_type = item.get("doc_type", "Documento")
            icon_str = "⚡" if "Resum" in doc_type else ("⏳" if "Tempo" in doc_type else ("⚖️" if "Audit" in doc_type else ("💬" if "Chat" in doc_type or "Consulta" in doc_type else "📋")))
            
            has_ctx = bool(item.get("process_context"))
            badge_text = f"{icon_str} [{doc_type[:12]}]" + (" 📁" if has_ctx else "")
            
            lbl_type = ctk.CTkLabel(
                top_row, 
                text=badge_text, 
                font=get_font(11, "bold"), 
                text_color=get_color_tuple("primary")
            )
            lbl_type.pack(side="left")
            lbl_type.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))
            lbl_type.bind("<Double-Button-1>", lambda e, i=item: self._on_carregar_historico_ativo(i))

            try:
                dt_obj = datetime.datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S')
                date_str = dt_obj.strftime("%d/%m %H:%M")
            except (ValueError, KeyError):
                date_str = ""

            lbl_date = ctk.CTkLabel(top_row, text=date_str, font=get_font(10), text_color=get_color_tuple("text_secondary"))
            lbl_date.pack(side="right")
            lbl_date.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))
            lbl_date.bind("<Double-Button-1>", lambda e, i=item: self._on_carregar_historico_ativo(i))

            subject = item.get("subject", "Documento Gerado")
            lbl_subject = ctk.CTkLabel(card, text=subject, font=get_font(11), anchor="w", justify="left")
            lbl_subject.pack(fill="x", padx=8, pady=(0, 4))
            lbl_subject.bind("<Button-1>", lambda e, i=item: self._on_history_card_click(i))
            lbl_subject.bind("<Double-Button-1>", lambda e, i=item: self._on_carregar_historico_ativo(i))

    def _on_history_search(self, event=None):
        search_term = self.history_search_entry.get().strip()
        filtered_items = self.engine.search_history(search_term)
        self._refresh_historico(filtered_items)

    def _on_history_card_click(self, item: Dict[str, Any]):
        self.selected_history_item = item
        
        has_ctx = bool(item.get("process_context"))
        ctx_tag = " • 📁 Autos Salvos" if has_ctx else ""
        doc_type = item.get("doc_type", "Documento")
        subj = item.get("subject", "Item")
        self.hist_item_info_lbl.configure(
            text=f"📌 [{doc_type}] {subj[:28]}{ctx_tag}",
            text_color=get_color_tuple("text_primary")
        )
        
        self.history_text_display.configure(state="normal")
        self.history_text_display.delete("1.0", tk.END)
        insert_markdown_text(
            self.history_text_display, 
            item.get("full_text", "Texto não encontrado."), 
            is_dark=self.theme_manager.is_dark, 
            base_size=12
        )
        self.history_text_display.configure(state="disabled")
        self._refresh_historico()

    def _on_carregar_historico_ativo(self, item: Optional[Dict[str, Any]] = None):
        target = item or self.selected_history_item
        if not target:
            self._show_message("Aviso", "Selecione um item no histórico primeiro.", "info")
            return
            
        self.selected_history_item = target
        self.processo_ativo_texto = target.get("process_context") or target.get("full_text", "")
        self.processo_ativo_nome = target.get("subject", "Processo do Histórico")
        
        # Atualiza badge de processo ativo
        self.badge_label.configure(
            text=f"📌 Ativo (Histórico): {self.processo_ativo_nome[:30]}",
            text_color=get_color_tuple("primary")
        )
        
        # Carrega texto na área principal
        texto = target.get("full_text", "")
        self.text_saida.delete("1.0", tk.END)
        insert_markdown_text(self.text_saida, texto, is_dark=self.theme_manager.is_dark, base_size=15)
        
        self.status_label.configure(text="Processo do histórico carregado como ativo!", text_color=get_color_tuple("success"))
        self._add_to_chat("Sistema", f"Contexto de '{self.processo_ativo_nome}' carregado do histórico. Você pode fazer perguntas nos Autos ou refinar o documento sem precisar reprocessar!")
        self.sidebar_tabs.set("Assistente")

    def _on_perguntar_historico(self, item: Optional[Dict[str, Any]] = None):
        self._on_carregar_historico_ativo(item)
        self.chat_mode_var.set("Autos")
        self.chat_input.focus()

    def _on_copiar_sei_historico(self):
        target = self.selected_history_item
        texto = target.get("full_text", "") if target else self.history_text_display.get("1.0", tk.END).strip()
        if not texto: 
            self._show_message("Aviso", "Selecione um item no histórico para copiar.", "info")
            return
        
        html_formatado = convert_text_to_sei_html(texto)
        copiou_rico = copy_html_to_clipboard(html_formatado, texto)
        if not copiou_rico:
            self.clipboard_clear()
            self.clipboard_append(texto)
            
        cor_original = self.btn_hist_copy_sei.cget("fg_color")
        texto_original = self.btn_hist_copy_sei.cget("text")
        icon_check = self._get_emoji_icon("✔️", (15, 15))
        self.btn_hist_copy_sei.configure(fg_color=get_color_tuple("success"), text=" Copiado!", image=icon_check)
        self.after(1500, lambda: self.btn_hist_copy_sei.configure(fg_color=cor_original, text=texto_original, image=self._get_emoji_icon("✨", (15, 15))))

    def _on_copiar_plain_historico(self):
        target = self.selected_history_item
        texto = target.get("full_text", "") if target else self.history_text_display.get("1.0", tk.END).strip()
        if not texto: 
            self._show_message("Aviso", "Selecione um item no histórico para copiar.", "info")
            return
        self.clipboard_clear()
        self.clipboard_append(texto)
        
        cor_original = self.btn_hist_copy_plain.cget("fg_color")
        texto_original = self.btn_hist_copy_plain.cget("text")
        icon_check = self._get_emoji_icon("✔️", (15, 15))
        self.btn_hist_copy_plain.configure(fg_color=get_color_tuple("success"), text=" Copiado!", image=icon_check)
        self.after(1500, lambda: self.btn_hist_copy_plain.configure(fg_color=cor_original, text=texto_original, image=self._get_emoji_icon("📋", (15, 15))))

    def _on_docx_historico(self):
        target = self.selected_history_item
        texto = target.get("full_text", "") if target else self.history_text_display.get("1.0", tk.END).strip()
        if not texto: 
            self._show_message("Aviso", "Selecione um item no histórico para exportar.", "info")
            return
        path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Documento Word (.docx)", "*.docx")])
        if path:
            suc, err = self.engine.export_to_docx(texto, path)
            if suc: self._show_message("Sucesso", "Documento Word (.docx) exportado do histórico!", "success")
            else: self._show_message("Erro", err, "error")

    def _on_pdf_historico(self):
        target = self.selected_history_item
        texto = target.get("full_text", "") if target else self.history_text_display.get("1.0", tk.END).strip()
        if not texto: 
            self._show_message("Aviso", "Selecione um item no histórico para exportar.", "info")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Documento PDF (.pdf)", "*.pdf")])
        if path:
            suc, err = self.engine.export_to_pdf(texto, path)
            if suc: self._show_message("Sucesso", "PDF exportado do histórico!", "success")
            else: self._show_message("Erro", err, "error")

    def _on_delete_history_item(self):
        if not self.selected_history_item:
            self._show_message("Aviso", "Selecione um item no histórico para excluir.", "info")
            return
            
        item_id = self.selected_history_item.get("id")
        if item_id:
            self.engine.delete_history_entry(item_id)
            self.selected_history_item = None
            self.hist_item_info_lbl.configure(text="Item excluído do histórico", text_color=get_color_tuple("text_secondary"))
            self.history_text_display.configure(state="normal")
            self.history_text_display.delete("1.0", tk.END)
            self.history_text_display.configure(state="disabled")
            self._load_history()
            self.status_label.configure(text="Item removido do histórico.", text_color=get_color_tuple("success"))

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

    def _toggle_theme(self):
        self.theme_manager.toggle_theme()
        self.theme_btn.configure(text="Light" if self.theme_manager.is_dark else "Dark")
        setup_markdown_tags(self.text_saida, is_dark=self.theme_manager.is_dark, base_size=15)
        setup_markdown_tags(self.chat_history, is_dark=self.theme_manager.is_dark, base_size=13)
        setup_markdown_tags(self.history_text_display, is_dark=self.theme_manager.is_dark, base_size=13)
        self._salvar_config()

    def _show_message(self, title, msg, type="info"):
        # pyrefly: ignore [missing-import]
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
