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
from typing import Dict, List, Optional, Any
import customtkinter as ctk
from PIL import Image

from sei_templates import RESUMO_CRONOGRAMA
from theme_config import (
    get_color_tuple, configure_appearance, get_font, ThemeObserver, ThemeManager
)
from engine import SEIEngine


# Classe Tooltip: define comportamento e estrutura desta parte do aplicativo.
class Tooltip:
    """Tooltips para widgets."""

    # Função interna __init__(widget: tk.Widget, text: str): executa lógica relacionada a init.
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


# Classe ScreenBase: define comportamento e estrutura desta parte do aplicativo.
class ScreenBase(ctk.CTkFrame):
    """Classe base para todas as telas com suporte a tema."""

    # Função interna __init__(parent, theme_manager: ThemeManager, **kwargs): executa lógica relacionada a init.
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme_manager = theme_manager
        # Garantir responsividade em todas as telas derivadas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        try:
            self.theme_manager.attach(self)
        except AttributeError:
            pass

    def on_theme_change(self, is_dark: bool) -> None:
        """Override em subclasses se necessário atualizar cores."""
        pass
    
    # Função show(): executa lógica relacionada a show.
    def show(self):
        """Mostra a tela."""
        self.grid(row=0, column=0, sticky='nsew')
    
    # Função hide(): executa lógica relacionada a hide.
    def hide(self):
        """Esconde a tela."""
        self.grid_forget()


# Classe GenerarScreen: define comportamento e estrutura desta parte do aplicativo.
class GenerarScreen(ScreenBase):
    """Tela completa para geração de despachos."""

    def __init__(self, parent, theme_manager: ThemeManager, engine: SEIEngine,
                 on_show_message, icons: Optional[Dict[str, ctk.CTkImage]] = None, **kwargs):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        self.engine = engine
        self.on_show_message = on_show_message
        self.icons = icons or {}

        self.inputs: Dict[int, Any] = {}
        self.template_var = tk.StringVar(value="HVeP - Atendimento/HVeP")
        self.text_saida: Optional[ctk.CTkTextbox] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.model_select: Optional[ctk.CTkComboBox] = None
        self.input_map: Dict[str, ctk.CTkEntry] = {}

        self._build_ui()
    
    def _is_valid_sei(self, value: str) -> bool:
        if not value:
            return False
        # Exemplo de formato esperado: apenas dígitos ou número com barra
        return bool(re.match(r"^\d{4,12}$", value.strip()))

    def _is_valid_protocolo(self, value: str) -> bool:
        return bool(re.match(r"^OUV-\d+\/\d{4}$", value.strip()))

    def _apply_prazo_shortcut(self, dias: int, prazo_entry: ctk.CTkEntry) -> None:
        prazo_entry.delete(0, tk.END)
        prazo_entry.insert(0, self.engine.calcular_data_prazo(dias))
        self._validate_live()

    def _validate_field(self, entry: ctk.CTkEntry, field_name: str) -> None:
        valor = entry.get().strip()
        if field_name in ["SEI Ofício", "SEI Manifestação"]:
            if not valor:
                entry.configure(border_color=get_color_tuple("border"))
            elif self._is_valid_sei(valor):
                entry.configure(border_color=get_color_tuple("success"))
            else:
                entry.configure(border_color=get_color_tuple("error"))
        elif field_name == "Protocolo OUV":
            if not valor:
                entry.configure(border_color=get_color_tuple("border"))
            elif self._is_valid_protocolo(valor):
                entry.configure(border_color=get_color_tuple("success"))
            else:
                entry.configure(border_color=get_color_tuple("error"))
        else:
            entry.configure(border_color=get_color_tuple("border"))

    def _build_ui(self) -> None:
        """Constrói interface moderna com layout em grid."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Container principal com scroll e padding
        main_scroll = ctk.CTkScrollableFrame(self, fg_color=get_color_tuple("background"))
        main_scroll.grid(row=0, column=0, sticky='nsew')
        main_scroll.grid_rowconfigure(0, weight=1)
        main_scroll.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(main_scroll, fg_color=get_color_tuple("background"),
                                 corner_radius=12)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        main_frame.grid_rowconfigure(2, weight=1)  # Área de resultado expande
        main_frame.grid_columnconfigure(0, weight=1)

        # Título principal
        title = ctk.CTkLabel(main_frame, text="Gerar Despacho SEI",
                            font=get_font(24, "bold"),
                            text_color=get_color_tuple("text_primary"))
        title.grid(row=0, column=0, pady=(20, 30))

        # Formulário com grid layout
        self._create_form(main_frame)

        # Área de resultado
        self._create_output_area(main_frame)

        # Força responsividade extra: o conteúdo do frame principal cresce livremente
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=0)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

    # Função interna _create_form(parent): executa lógica relacionada a create form.
    def _create_form(self, parent):
        """Cria formulário com layout em grid e agrupamento lógico."""
        # Frame do formulário
        form_frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                 corner_radius=12)
        form_frame.grid(row=1, column=0, sticky='ew', padx=20, pady=(0, 30))
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        hoje = datetime.date.today()
        prazo_inicial = hoje.strftime("%d/%m/%Y")
        
        # Bloco 1: Dados do Documento
        doc_frame = ctk.CTkFrame(form_frame, fg_color=get_color_tuple("background"),
                                border_width=1, border_color=get_color_tuple("border"),
                                corner_radius=8)
        doc_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=20, pady=(20, 15))
        doc_frame.grid_columnconfigure(0, weight=1)
        doc_frame.grid_columnconfigure(1, weight=1)
        
        # Título do bloco
        doc_title = ctk.CTkLabel(doc_frame, text="📄 Dados do Documento",
                                font=get_font(14, "bold"),
                                text_color=get_color_tuple("text_primary"))
        doc_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=15, pady=(15, 10))
        
        # Campos do documento
        doc_fields = [
            ("Ofício", "778/2026", 1, 0),
            ("SEI Ofício", "198654234", 1, 1),
            ("SEI Manifestação", "220622554", 3, 0),
        ]
        
        for field in doc_fields:
            label_text, placeholder, row, col = field
            
            # Label
            label = ctk.CTkLabel(doc_frame, text=label_text, 
                                font=get_font(12, "bold"),
                                text_color=get_color_tuple("text_secondary"))
            label.grid(row=row, column=col, sticky="w", padx=15, pady=(10, 5))
            
            # Input com transições de foco
            entry = ctk.CTkEntry(doc_frame, placeholder_text=placeholder,
                                font=get_font(12), height=42,
                                border_width=1, corner_radius=10,
                                fg_color=get_color_tuple("background"),
                                border_color=get_color_tuple("border"))
            entry.grid(row=row+1, column=col, sticky="ew", padx=15, pady=(0, 15))
            
            # Bind focus transitions
            # Função on_focus_in(e, ent=entry): executa lógica relacionada a on focus in.
            def on_focus_in(e, ent=entry):
                ent.configure(border_color=self.theme_manager.get_focus_border_color())
            
            # Função on_focus_out(e, ent=entry, name=label_text): executa lógica relacionada a on focus out.
            def on_focus_out_field(e, ent=entry, name=label_text):
                self._validate_field(ent, name)
            
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out_field)
            entry.bind("<KeyRelease>", self._validate_live)
            
            self.inputs[len(self.inputs)] = entry
            Tooltip(entry, label_text)
        
        # Bloco 2: Dados da Manifestação
        manifest_frame = ctk.CTkFrame(form_frame, fg_color=get_color_tuple("background"),
                                     border_width=1, border_color=get_color_tuple("border"),
                                     corner_radius=8)
        manifest_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 15))
        manifest_frame.grid_columnconfigure(0, weight=1)
        manifest_frame.grid_columnconfigure(1, weight=1)
        
        # Título do bloco
        manifest_title = ctk.CTkLabel(manifest_frame, text="📋 Dados da Manifestação",
                                     font=get_font(14, "bold"),
                                     text_color=get_color_tuple("text_primary"))
        manifest_title.grid(row=0, column=0, columnspan=2, sticky='w', padx=15, pady=(15, 10))
        
        # Campos da manifestação
        manifest_fields = [
            ("Protocolo OUV", "OUV-078543/2026", 1, 0),
            ("Prazo", prazo_inicial, 1, 1),
            ("Resumo", "Falta de vagas de castração", 4, 0, 2),  # Span 2 colunas
        ]
        
        for field in manifest_fields:
            label_text, placeholder, row, col = field[:4]
            colspan = field[4] if len(field) > 4 else 1
            
            # Label
            label = ctk.CTkLabel(manifest_frame, text=label_text, 
                                font=get_font(12, "bold"),
                                text_color=get_color_tuple("text_secondary"))
            label.grid(row=row, column=col, sticky="w", padx=15, pady=(10, 5))
            
            # Input
            if label_text == "Prazo":
                # Frame para entrada + botão calendário
                date_frame = ctk.CTkFrame(manifest_frame, fg_color=get_color_tuple("transparent"), height=42)
                date_frame.grid(row=row+1, column=col, sticky="ew", padx=15, pady=(0, 5))
                date_frame.grid_propagate(False)
                
                entry = ctk.CTkEntry(date_frame, placeholder_text=placeholder,
                                    font=get_font(12), height=42,
                                    border_width=1, corner_radius=10,
                                    fg_color=get_color_tuple("background"))
                entry.pack(side="left", fill="x", expand=True)
                
                # Botão calendário
                calendar_btn = ctk.CTkButton(date_frame, text="📅", width=50, height=42,
                                           command=lambda e=entry: self._open_date_picker(e),
                                           fg_color=get_color_tuple("transparent"), border_width=1,
                                           border_color=get_color_tuple("border"), corner_radius=10)
                calendar_btn.pack(side="right", padx=(5, 0))
                
                # Set initial date
                hoje = datetime.date.today()
                entry.insert(0, hoje.strftime("%d/%m/%Y"))

                # Atalhos de prazo
                shortcut_frame = ctk.CTkFrame(manifest_frame, fg_color="transparent")
                shortcut_frame.grid(row=row+2, column=col, sticky="ew", padx=15, pady=(0, 10))
                for dias in [5, 15, 30]:
                    ctk.CTkButton(shortcut_frame, text=f"+{dias}d", width=60, height=28,
                                  font=get_font(10), command=lambda d=dias, e=entry: self._apply_prazo_shortcut(d, e)).pack(side="left", padx=4)
            else:
                entry = ctk.CTkEntry(manifest_frame, placeholder_text=placeholder,
                                    font=get_font(12), height=42,
                                    border_width=1, corner_radius=10,
                                    fg_color=get_color_tuple("background"),
                                    border_color=get_color_tuple("border"))
                entry.grid(row=row+1, column=col, columnspan=colspan, sticky="ew", 
                          padx=15, pady=(0, 15))
                if colspan == 1:
                    manifest_frame.grid_columnconfigure(col, weight=1)
            
            # Bind focus transitions para todos os campos
            # Função on_focus_in(e, ent=entry): executa lógica relacionada a on focus in.
            def on_focus_in(e, ent=entry):
                ent.configure(border_color=self.theme_manager.get_focus_border_color())
            
            # Função on_focus_out(e, ent=entry, name=label_text): executa lógica relacionada a on focus out.
            def on_focus_out_manifest(e, ent=entry, name=label_text):
                self._validate_field(ent, name)
            
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out_manifest)
            entry.bind("<KeyRelease>", lambda e, ent=entry, name=label_text: (self._validate_live(), self._validate_field(ent, name)))
            
            self.inputs[len(self.inputs)] = entry
            Tooltip(entry, label_text)

        # Modelo
        model_label = ctk.CTkLabel(form_frame, text="Modelo", 
                                  font=get_font(12, "bold"),
                                  text_color=get_color_tuple("text_secondary"))
        model_label.grid(row=4, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.model_select = ctk.CTkComboBox(form_frame, values=self.engine.get_modelos_list(),
                                           variable=self.template_var, state="readonly",
                                           height=42, font=get_font(12),
                                           border_width=1, corner_radius=10,
                                           fg_color=get_color_tuple("background"))
        self.model_select.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.model_select.bind("<<ComboboxSelected>>", self._on_template_selected)
        Tooltip(self.model_select, "Selecionar modelo")
        
        # Botões
        self._create_buttons(form_frame)
    
    # Função interna _create_buttons(parent): executa lógica relacionada a create buttons.
    def _create_buttons(self, parent):
        """Cria botões diferenciados com animações."""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20))
        
        # Botão Gerar (primário) com animação
        gerar_icon = self.icons.get("gerar")
        self.gerar_btn = ctk.CTkButton(buttons_frame, text="Gerar Despacho", 
                                     command=self._on_gerar_animated,
                                     height=45, font=get_font(12, "bold"),
                                     fg_color=self.theme_manager.get_color("primary"),
                                     hover_color=self.theme_manager.get_hover_color("primary"), 
                                     corner_radius=10, image=gerar_icon)
        self.gerar_btn.pack(side="left", padx=(0, 10), expand=True)
        
        # Botões secundários
        actions = [("💾 Salvar", self._on_salvar), ("📥 Carregar", self._on_carregar),
                  ("📄 PDF", self._on_pdf)]
        
        for text, cmd in actions:
            btn = ctk.CTkButton(buttons_frame, text=text, command=cmd, height=45,
                               font=get_font(11, "bold"),
                               fg_color="transparent", border_width=1,
                               border_color=get_color_tuple("border"),
                               corner_radius=8)
            btn.pack(side="left", padx=5)
            Tooltip(btn, text)
    
    # Função interna _create_output_area(parent): executa lógica relacionada a create output area.
    def _create_output_area(self, parent):
        """Cria área de resultado com fonte monoespaçada."""
        output_frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                   corner_radius=12)
        output_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=(0, 20))
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # Header com botão copiar
        header_frame = ctk.CTkFrame(output_frame, fg_color="transparent", height=50)
        header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        result_label = ctk.CTkLabel(header_frame, text="Resultado do Despacho", 
                                   font=get_font(16, "bold"),
                                   text_color=self.theme_manager.get_color("text_primary"))
        result_label.grid(row=0, column=0, sticky='w')
        
        copy_btn = ctk.CTkButton(header_frame, text="📋 Copiar", command=self._on_copiar,
                                height=35, width=100, font=get_font(11, "bold"),
                                fg_color=get_color_tuple("success"),
                                hover_color="#059669", corner_radius=8)
        copy_btn.grid(row=0, column=1, sticky='e')
        
        # Textbox com fonte mono
        self.text_saida = ctk.CTkTextbox(output_frame, wrap="word",
                                        font=get_font(13, family="Consolas"),
                                        corner_radius=10, border_width=1,
                                        fg_color=self.theme_manager.get_color("background"),
                                        text_color=self.theme_manager.get_color("text_primary"),
                                        height=300)
        self.text_saida.grid(row=1, column=0, sticky='nsew', padx=(20, 0), pady=(0, 20))

        # Scrollbar associada ao textarea do resultado
        output_scroll = ctk.CTkScrollbar(output_frame, orientation="vertical",
                                         command=self.text_saida.yview)
        output_scroll.grid(row=1, column=1, sticky='ns', padx=(0, 20), pady=(0, 20))
        self.text_saida.configure(yscrollcommand=output_scroll.set)
        # Manter em estado normal para poder rolar mesmo com visualização somente
        self.text_saida.configure(state="normal")

        # Botão Copiar e Limpar
        clear_copy_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        clear_copy_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=(0, 20))
        
        clear_copy_btn = ctk.CTkButton(clear_copy_frame, text="📋 Copiar e Limpar", 
                                      command=self._on_copiar_limpar,
                                      height=40, font=get_font(12, "bold"),
                                      fg_color=get_color_tuple("primary"),
                                      hover_color="#0056CC", corner_radius=8)
        clear_copy_btn.pack(fill="x")

        # Grid responsivo do output_frame
        output_frame.grid_rowconfigure(0, weight=0)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_rowconfigure(2, weight=0)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_columnconfigure(1, weight=0)

        # Placeholder
        self.text_saida.insert("1.0", "O despacho gerado aparecerá aqui após preencher os dados acima.")
        self.text_saida.configure(state="normal")

        # Status
        self.status_label = ctk.CTkLabel(output_frame, text="Pronto para gerar",
                                        text_color=get_color_tuple("text_secondary"),
                                        font=get_font(11))
        self.status_label.grid(row=2, column=0, sticky='w', padx=20, pady=(0, 20))
    
    # Função interna _open_date_picker(entry): executa lógica relacionada a open date picker.
    def _open_date_picker(self, entry):
        """Abre seletor de data customizado."""
        # Janela do date picker
        picker = ctk.CTkToplevel(self)
        picker.title("")
        picker.geometry("300x350")
        picker.resizable(False, False)
        picker.transient(self.winfo_toplevel())
        picker.grab_set()
        
        # Centralizar na tela
        picker.update_idletasks()
        x = (picker.winfo_screenwidth() // 2) - (300 // 2)
        y = (picker.winfo_screenheight() // 2) - (350 // 2)
        picker.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(picker, fg_color=get_color_tuple("surface"),
                                 corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header com navegação mês/ano
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        # Obter data atual do campo ou hoje
        try:
            current_date = datetime.datetime.strptime(entry.get(), "%d/%m/%Y").date()
        except:
            current_date = datetime.date.today()
        
        # Variáveis para mês/ano
        picker_year = tk.IntVar(value=current_date.year)
        picker_month = tk.IntVar(value=current_date.month)
        
        # Botões navegação
        prev_btn = ctk.CTkButton(header_frame, text="◀", width=40, height=40,
                                command=lambda: self._change_month(picker_year, picker_month, -1, days_frame, current_date, entry, picker, month_label),
                                fg_color="transparent", border_width=1, border_color=get_color_tuple("border"))
        prev_btn.pack(side="left")
        
        # Mês/Ano
        month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                      "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        
        month_label = ctk.CTkLabel(header_frame, 
                                  text=f"{month_names[picker_month.get()-1]} {picker_year.get()}",
                                  font=ctk.CTkFont(size=14, weight="bold"),
                                  text_color=get_color_tuple("text_primary"))
        month_label.pack(side="left", expand=True)
        
        next_btn = ctk.CTkButton(header_frame, text="▶", width=40, height=40,
                                command=lambda: self._change_month(picker_year, picker_month, 1, days_frame, current_date, entry, picker, month_label),
                                fg_color="transparent", border_width=1, border_color=get_color_tuple("border"))
        next_btn.pack(side="right")
        
        # Grid de dias
        days_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        days_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Dias da semana
        weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for i, day in enumerate(weekdays):
            ctk.CTkLabel(days_frame, text=day, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=get_color_tuple("text_secondary")).grid(
                            row=0, column=i, padx=2, pady=2)
        
        # Gerar grid de dias
        self._populate_days(days_frame, picker_year, picker_month, current_date, entry, picker, month_label)
        
        # Botão Hoje
        today_btn = ctk.CTkButton(main_frame, text="Hoje", height=35,
                                 command=lambda: self._select_today(entry, picker),
                                 fg_color=get_color_tuple("primary"),
                                 hover_color="#0056CC")
        today_btn.pack(fill="x", padx=15, pady=(0, 15))
    
    # Função interna _change_month(year_var, month_var, delta, days_frame, current_date, entry, picker, month_label): executa lógica relacionada a change month.
    def _change_month(self, year_var, month_var, delta, days_frame, current_date, entry, picker, month_label):
        """Muda mês e atualiza grid."""
        month_var.set(month_var.get() + delta)
        if month_var.get() < 1:
            month_var.set(12)
            year_var.set(year_var.get() - 1)
        elif month_var.get() > 12:
            month_var.set(1)
            year_var.set(year_var.get() + 1)

        # Limpar grid antigo
        for widget in days_frame.winfo_children():
            if widget.grid_info():
                widget.destroy()

        # Recriar headers dos dias
        weekdays = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for i, day in enumerate(weekdays):
            ctk.CTkLabel(days_frame, text=day, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=get_color_tuple("text_secondary")).grid(
                             row=0, column=i, padx=2, pady=2)

        # Atualizar label do mês diretamente
        month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                       "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        if month_label:
            month_label.configure(text=f"{month_names[month_var.get()-1]} {year_var.get()}")

        # Repopular dias
        self._populate_days(days_frame, year_var, month_var, current_date, entry, picker, month_label)
    
    # Função interna _populate_days(parent, year_var, month_var, current_date, entry, picker, month_label=None): executa lógica relacionada a populate days.
    def _populate_days(self, parent, year_var, month_var, current_date, entry, picker, month_label=None):
        """Popula grid de dias."""
        import calendar
        
        # Obter calendário do mês
        cal = calendar.monthcalendar(year_var.get(), month_var.get())
        
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day == 0:
                    continue
                
                # Verificar se é o dia selecionado
                selected_date = datetime.date(year_var.get(), month_var.get(), day)
                is_selected = (selected_date == current_date)
                
                # Botão do dia
                day_btn = ctk.CTkButton(parent, text=str(day), width=35, height=35,
                                       fg_color=get_color_tuple("primary") if is_selected else "transparent",
                                       text_color="white" if is_selected else get_color_tuple("text_primary"),
                                       border_width=1, border_color=get_color_tuple("border"),
                                       corner_radius=8,
                                       command=lambda d=day, y=year_var.get(), m=month_var.get(): self._select_date(d, y, m, entry, picker))
                
                day_btn.grid(row=week_idx+1, column=day_idx, padx=1, pady=1)
    
    # Função interna _select_date(day, year, month, entry, picker): executa lógica relacionada a select date.
    def _select_date(self, day, year, month, entry, picker):
        """Seleciona data."""
        selected_date = datetime.date(year, month, day)
        entry.delete(0, tk.END)
        entry.insert(0, selected_date.strftime("%d/%m/%Y"))
        picker.destroy()
        self._validate_live()
    
    # Função interna _select_today(entry, picker): executa lógica relacionada a select today.
    def _select_today(self, entry, picker):
        """Seleciona data de hoje."""
        today = datetime.date.today()
        entry.delete(0, tk.END)
        entry.insert(0, today.strftime("%d/%m/%Y"))
        picker.destroy()
        self._validate_live()
    
    # Função interna _on_theme_change(is_dark): executa lógica relacionada a on theme change.
    def _on_theme_change(self, is_dark):
        """Atualiza cores ao mudar tema."""
        self.configure(fg_color=get_color_tuple("background"))
        # As cores dos frames e inputs serão atualizadas automaticamente pelo ThemeManager
    
    # Função interna _validate_live(event=None): executa lógica relacionada a validate live.
    def _validate_live(self, event=None):
        """Validação ao vivo com feedback visual."""
        if self.status_label is None:
            return

        erros = self._validar_campos(silent=True)
        if erros:
            self.status_label.configure(
                text=f"{len(erros)} problema(s) encontrado(s)",
                text_color=get_color_tuple("error")
            )
        else:
            self.status_label.configure(
                text="Pronto para gerar",
                text_color=get_color_tuple("success")
            )
    
    # Função interna _validar_campos(silent=False): executa lógica relacionada a validar campos.
    def _validar_campos(self, silent=False):
        """Valida campos com engine."""
        values = [self.inputs[i].get().strip() for i in range(6)]
        data = {
            "oficio": values[0],
            "prazo": values[1],
            "sei_oficio": values[2],
            "sei_manifestacao": values[3],
            "protocolo": values[4],
            "resumo": values[5]
        }

        erros = self.engine.validate_form_data(data)

        if not silent and erros:
            self.on_show_message("Erro", "; ".join(erros), "error")

        return erros
    
    # Função interna _on_gerar_animated(): executa lógica relacionada a on gerar animated.
    def _on_gerar_animated(self):
        """Gera despacho com animações completas."""
        from ui_animations import UIAnimations
        
        # Animação do botão: shrink
        UIAnimations.button_press_animation(self.gerar_btn, duration=150)
        
        # Muda ícone para spinner/loading
        original_text = self.gerar_btn.cget("text")
        UIAnimations.icon_swap_animation(self.gerar_btn, original_text, "⏳ Gerando...", duration=1000)
        
        # Pequeno delay antes de executar a geração
        self.after(200, self._on_gerar)
    
    # Função interna _on_gerar(): executa lógica relacionada a on gerar.
    def _on_gerar(self):
        """Gera despacho e copia automaticamente com feedback visual."""
        if self._validar_campos():
            return
        
        if self.text_saida is None or self.status_label is None:
            return

        # Feedback visual: muda cor da borda do text_saida
        original_border_color = self.text_saida.cget("border_color")
        self.text_saida.configure(border_color=get_color_tuple("success"))
        
        # Animação do botão (check temporário) - simplificado
        self._show_generation_feedback()
        
        values = [self.inputs[i].get().strip() for i in range(6)]
        despacho_data = {
            "oficio": values[0],
            "prazo": values[1],
            "sei_oficio": values[2],
            "sei_manifestacao": values[3],
            "protocolo": values[4],
            "resumo": values[5],
            "modelo": self.template_var.get()
        }
        
        try:
            texto = self.engine.generate_despacho(despacho_data)
            
            # Fade-in do texto no resultado
            from ui_animations import UIAnimations
            UIAnimations.text_fade_in(self.text_saida, texto, duration=800)
            
            # Copia automaticamente para clipboard
            root = self.winfo_toplevel()
            if hasattr(root, "clipboard_clear") and hasattr(root, "clipboard_append"):
                root.clipboard_clear()
                root.clipboard_append(texto)

            # Atualiza status e histórico
            if self.status_label is not None:
                self.status_label.configure(text="Despacho gerado e copiado!",
                                           text_color=get_color_tuple("success"))

            # Armazena registro no histórico como card
            if hasattr(root, "historico"):
                historico_attr = getattr(root, "historico", None)
                if isinstance(historico_attr, list):
                    historico_attr.append({
                        "modelo": despacho_data["modelo"],
                        "sei": despacho_data["sei_manifestacao"],
                        "data_criacao": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "texto": texto,
                        "oficio": despacho_data["oficio"],
                        "protocolo": despacho_data["protocolo"],
                        "resumo": despacho_data["resumo"],
                        "prazo": despacho_data["prazo"]
                    })

            if hasattr(root, "screens"):
                screens_attr = getattr(root, "screens", None)
                if isinstance(screens_attr, dict) and "historico" in screens_attr:
                    screens_attr["historico"]._refresh()

            self.on_show_message("Sucesso", "Despacho gerado e copiado automaticamente!", "success")

            # Reset visual feedback after 2 seconds
            self.after(2000, lambda: self._reset_visual_feedback(original_border_color))
            
        except Exception as e:
            # Reset visual feedback on error
            self._reset_visual_feedback(original_border_color)
            self.on_show_message("Erro", f"Erro na geração: {str(e)}", "error")
    
    # Função interna _show_generation_feedback(): executa lógica relacionada a show generation feedback.
    def _show_generation_feedback(self):
        """Mostra feedback visual de geração."""
        if self.status_label is None:
            return
        self.status_label.configure(
            text="Gerando despacho...",
            text_color=get_color_tuple("primary")
        )
    
    # Função interna _reset_visual_feedback(border_color): executa lógica relacionada a reset visual feedback.
    def _reset_visual_feedback(self, border_color):
        """Reseta o feedback visual."""
        if self.text_saida is not None:
            self.text_saida.configure(border_color=border_color)
        self._validate_live()
    
    # Função interna _on_template_selected(event=None): executa lógica relacionada a on template selected.
    def _on_template_selected(self, event=None):
        """Atualiza resumo quando modelo muda."""
        modelo = self.template_var.get()
        if modelo == "Demanda de Ouvidoria - Ausência de Cronograma Castração":
            self.inputs[4].delete(0, tk.END)
            self.inputs[4].insert(0, RESUMO_CRONOGRAMA)
            self.inputs[4].configure(state="disabled")
        else:
            self.inputs[4].configure(state="normal")
    
    # Função interna _on_salvar(): executa lógica relacionada a on salvar.
    def _on_salvar(self):
        """Salva dados."""
        valores = {f"campo_{i}": self.inputs[i].get().strip() for i in range(6)}
        valores["modelo"] = self.template_var.get()
        try:
            with open("dados_ultimo.json", "w", encoding="utf-8") as f:
                json.dump(valores, f, ensure_ascii=False, indent=4)
            self.on_show_message("Sucesso", "Dados salvos!", "success")
        except Exception as e:
            self.on_show_message("Erro", f"Erro: {str(e)}", "error")
    
    # Função interna _on_carregar(): executa lógica relacionada a on carregar.
    def _on_carregar(self):
        """Carrega dados."""
        if not os.path.exists("dados_ultimo.json"):
            self.on_show_message("Aviso", "Nenhum dado encontrado", "warning")
            return
        try:
            with open("dados_ultimo.json", "r", encoding="utf-8") as f:
                valores = json.load(f)
            for i in range(6):
                self.inputs[i].delete(0, tk.END)
                self.inputs[i].insert(0, valores.get(f"campo_{i}", ""))
            self.template_var.set(valores.get("modelo", "HVeP - Atendimento/HVeP"))
            self._on_template_selected()
            self.on_show_message("Sucesso", "Dados carregados!", "success")
        except Exception as e:
            self.on_show_message("Erro", f"Erro: {str(e)}", "error")
    
    # Função interna _on_pdf(): executa lógica relacionada a on pdf.
    def _on_pdf(self):
        """Exporta PDF."""
        if self.text_saida is None:
            return
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto or texto == "Resultado aparecerá aqui...":
            self.on_show_message("Aviso", "Nada para exportar", "warning")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                                filetypes=[("PDF", "*.pdf")])
        if not file_path:
            return
        
        try:
            success, msg = self.engine.export_to_pdf(texto, file_path)
            if success:
                self.on_show_message("Sucesso", "PDF exportado!", "success")
            else:
                self.on_show_message("Erro", f"Erro ao exportar PDF: {msg}", "error")
        except Exception as e:
            self.on_show_message("Erro", f"Erro ao exportar PDF: {str(e)}", "error")
    
    # Função interna _on_copiar(): executa lógica relacionada a on copiar.
    def _on_copiar(self):
        """Copia para clipboard com feedback."""
        if self.text_saida is None:
            return

        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto or texto == "O despacho gerado aparecerá aqui após preencher os dados acima.":
            self.on_show_message("Aviso", "Nada para copiar", "warning")
            return

        root = self.winfo_toplevel()
        if hasattr(root, "clipboard_clear") and hasattr(root, "clipboard_append"):
            root.clipboard_clear()
            root.clipboard_append(texto)

        if self.status_label is not None:
            self.status_label.configure(
                text="Copiado para área de transferência!",
                text_color=get_color_tuple("success")
            )
        self.after(2000, lambda: self._validate_live())  # Reset status after 2s
    
    # Função interna _on_copiar_limpar(): executa lógica relacionada a on copiar limpar.
    def _on_copiar_limpar(self):
        """Copia para clipboard e limpa todos os campos."""
        if self.text_saida is None:
            return

        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto or texto == "O despacho gerado aparecerá aqui após preencher os dados acima.":
            self.on_show_message("Aviso", "Nada para copiar", "warning")
            return

        # Copia para clipboard
        root = self.winfo_toplevel()
        if hasattr(root, "clipboard_clear") and hasattr(root, "clipboard_append"):
            root.clipboard_clear()
            root.clipboard_append(texto)
        
        # Limpa todos os campos
        for entry in self.inputs.values():
            entry.delete(0, tk.END)
        
        # Reset modelo
        self.template_var.set("HVeP - Atendimento/HVeP")
        
        # Reset text_saida para placeholder
        if self.text_saida is not None:
            self.text_saida.configure(state="normal")
            self.text_saida.delete("1.0", ctk.END)
            self.text_saida.insert("1.0", "O despacho gerado aparecerá aqui após preencher os dados acima.")
        
        # Feedback
        if self.status_label is not None:
            self.status_label.configure(text="Copiado e campos limpos!",
                                       text_color=get_color_tuple("success"))
        self.on_show_message("Sucesso", "Texto copiado e campos limpos para o próximo despacho!", "success")
        self.after(3000, lambda: self._validate_live())  # Reset status after 3s


# Classe HistoricoScreen: define comportamento e estrutura desta parte do aplicativo.
class HistoricoScreen(ScreenBase):
    """Tela de histórico de despachos em cards modernos."""
    
    # Função interna __init__(parent, theme_manager, historico, **kwargs): executa lógica relacionada a init.
    def __init__(self, parent, theme_manager, historico, **kwargs):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        self.historico = historico
        self.cards_container = None
        
        self._build_ui()
    
    # Função interna _build_ui(): executa lógica relacionada a build ui.
    def _build_ui(self):
        """Constrói interface."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color=get_color_tuple("background"))
        container.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        container.grid_rowconfigure(0, weight=0)  # Header não expande
        container.grid_rowconfigure(1, weight=0)  # Label e busca não expande
        container.grid_rowconfigure(2, weight=0)  # Espaço de busca
        container.grid_rowconfigure(3, weight=1)  # Listbox expande
        container.grid_rowconfigure(4, weight=0)  # Botões não expandem
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(container, text="Histórico de Despachos",
                             font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=self.theme_manager.get_color("text_primary"))
        header.grid(row=0, column=0, sticky='w', pady=(0, 15))

        self.cards_container = ctk.CTkFrame(container, border_width=1,
                                               border_color=get_color_tuple("border"),
                                               corner_radius=6)
        self.cards_container.grid(row=2, column=0, sticky='nsew', pady=(0, 15))
        self.cards_container.grid_columnconfigure(0, weight=1)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky='ew', pady=10)
        
        ctk.CTkButton(btn_frame, text="🗑️ Limpar", command=self._on_limpar,
                     height=32, font=ctk.CTkFont(size=10, weight="bold"),
                     width=150).pack(side="left", padx=5)
        
        self._refresh()
    
    # Função interna _on_theme_change(is_dark): executa lógica relacionada a on theme change.
    def _on_theme_change(self, is_dark):
        """Atualiza cores."""
        self.configure(fg_color=get_color_tuple("background"))
        if self.cards_container:
            self.cards_container.configure(border_color=get_color_tuple("border"))
    
    # Função interna _refresh(): executa lógica relacionada a refresh.
    def _refresh(self):
        """Atualiza cards de histórico com efeitos hover."""
        if self.cards_container is None:
            return
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        for item in reversed(self.historico[-20:]):
            card = ctk.CTkFrame(self.cards_container, fg_color=get_color_tuple("surface"),
                                border_width=1, border_color=get_color_tuple("border"),
                                corner_radius=8)
            card.pack(fill="x", padx=5, pady=5)

            # Armazenar cores originais para hover
            original_bg = get_color_tuple("surface")
            hover_bg = self.theme_manager.get_hover_color("surface")
            original_border = get_color_tuple("border")
            hover_border = self.theme_manager.get_color("primary")

            # Bind hover effects
            # Função on_enter(c=card, ob=original_bg, hb=hover_bg, obr=original_border, hbr=hover_border): executa lógica relacionada a on enter.
            def on_enter(c=card, ob=original_bg, hb=hover_bg, obr=original_border, hbr=hover_border):
                from ui_animations import UIAnimations
                UIAnimations.card_hover_effect(c, True, ob, hb, obr, hbr, duration=150)

            # Função on_leave(c=card, ob=original_bg, hb=hover_bg, obr=original_border, hbr=hover_border): executa lógica relacionada a on leave.
            def on_leave(c=card, ob=original_bg, hb=hover_bg, obr=original_border, hbr=hover_border):
                from ui_animations import UIAnimations
                UIAnimations.card_hover_effect(c, False, hb, ob, hbr, obr, duration=150)

            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            titulo = ctk.CTkLabel(card, text=f"{item.get('modelo', 'Sem Modelo')}",
                                  font=get_font(12, "bold"),
                                  text_color=get_color_tuple("text_primary"))
            titulo.grid(row=0, column=0, sticky='w', padx=10, pady=(8, 2))

            sei_txt = ctk.CTkLabel(card, text=f"SEI: {item.get('sei', '-')}",
                                  font=get_font(10, "bold"),
                                  text_color=get_color_tuple("text_secondary"))
            sei_txt.grid(row=1, column=0, sticky='w', padx=10)

            data_txt = ctk.CTkLabel(card, text=f"Criado em: {item.get('data_criacao', '-')}",
                                    font=get_font(10),
                                    text_color=get_color_tuple("text_secondary"))
            data_txt.grid(row=1, column=1, sticky='e', padx=10)

            texto_preview = ctk.CTkLabel(card, text=item.get('texto', '')[:150].replace('\n', ' ')+('...' if len(item.get('texto', ''))>150 else ''),
                                         font=get_font(9),
                                         text_color=get_color_tuple("text_secondary"),
                                         wraplength=900, justify='left')
            texto_preview.grid(row=2, column=0, columnspan=2, sticky='w', padx=10, pady=(2, 8))

            btn_container = ctk.CTkFrame(card, fg_color="transparent")
            btn_container.grid(row=3, column=0, columnspan=2, sticky='e', padx=10, pady=(0, 8))

            ctk.CTkButton(btn_container, text="📋 Copiar Novamente",
                          command=lambda i=item: self._copy_to_clipboard(i.get('texto', '')),
                          width=140, height=28, font=get_font(9, "bold")).pack(side='right', padx=4)

            ctk.CTkButton(btn_container, text="🔄 Carregar Dados", 
                          command=lambda i=item: self._call_reutilizar(i),
                          width=130, height=28, font=get_font(9, "bold")).pack(side='right', padx=4)
            # O histórico já foi adicionado ao card acima; não há item_frame definido aqui.
    
    # Função interna _on_carregar(): executa lógica relacionada a on carregar.
    def _on_carregar(self):
        """Carrega item selecionado (deprecated - usar reutilizar)."""
        pass  # Agora usa _on_reutilizar
    
    # Função interna _on_reutilizar(idx): executa lógica relacionada a on reutilizar.
    def _on_reutilizar(self, idx):
        """Reutiliza dados do item selecionado."""
        texto = self.historico[-20 + idx]
        root = self.winfo_toplevel()
        method = getattr(root, "_reutilizar_dados", None)
        if callable(method):
            try:
                method(texto)
            except Exception:
                pass

    # Função interna _copy_to_clipboard(texto): executa lógica relacionada a copy to clipboard.
    def _copy_to_clipboard(self, texto):
        root = self.winfo_toplevel()
        if hasattr(root, "clipboard_clear") and hasattr(root, "clipboard_append"):
            root.clipboard_clear()
            root.clipboard_append(texto)

    # Função interna _call_reutilizar(item): executa lógica relacionada a call reutilizar.
    def _call_reutilizar(self, item):
        root = self.winfo_toplevel()
        if hasattr(root, "_reutilizar_dados"):
            method = getattr(root, "_reutilizar_dados")
            if callable(method):
                method(item)

    # Função interna _on_limpar(): executa lógica relacionada a on limpar.
    def _on_limpar(self):
        """Limpa histórico."""
        self.historico.clear()
        self._refresh()


# Classe MensagensScreen: define comportamento e estrutura desta parte do aplicativo.
class MensagensScreen(ScreenBase):
    """Tela de mensagens."""
    
    # Função interna __init__(parent, theme_manager, **kwargs): executa lógica relacionada a init.
    def __init__(self, parent, theme_manager, **kwargs):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        
        self._build_ui()
    
    # Função interna _build_ui(): executa lógica relacionada a build ui.
    def _build_ui(self):
        """Constrói interface."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkLabel(self, text="Mensagens",
                             font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=get_color_tuple("text_primary"))
        header.grid(row=0, column=0, sticky='w', padx=15, pady=(15, 10))
        
        self.message_frame = ctk.CTkScrollableFrame(self,
                                                   fg_color=get_color_tuple("background"),
                                                   border_width=1,
                                                   border_color=get_color_tuple("border"),
                                                   corner_radius=6)
        self.message_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=15)
    
    # Função interna _on_theme_change(is_dark): executa lógica relacionada a on theme change.
    def _on_theme_change(self, is_dark):
        """Atualiza cores."""
        self.configure(fg_color=get_color_tuple("background"))
        if self.message_frame:
            self.message_frame.configure(
                fg_color=get_color_tuple("background"),
                border_color=get_color_tuple("border")
            )
    
    # Função add_message(title, message, msg_type="info"): executa lógica relacionada a add message.
    def add_message(self, title, message, msg_type="info"):
        """Adiciona mensagem."""
        msg_frame = ctk.CTkFrame(
            self.message_frame,
            fg_color=self._get_message_color(msg_type),
            corner_radius=6,
            border_width=1,
            border_color=get_color_tuple("border")
        )
        msg_frame.pack(fill="x", padx=5, pady=3)
        
        title_label = ctk.CTkLabel(msg_frame, text=f"• {title}",
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color=get_color_tuple("text_primary"))
        title_label.pack(anchor="w", padx=10, pady=(5, 2))
        
        msg_label = ctk.CTkLabel(msg_frame, text=message,
                                font=ctk.CTkFont(size=10),
                                text_color=get_color_tuple("text_secondary"),
                                wraplength=600, justify="left")
        msg_label.pack(anchor="w", padx=10, pady=(2, 5))
    
    # Função interna _get_message_color(msg_type): executa lógica relacionada a get message color.
    def _get_message_color(self, msg_type):
        """Retorna cor da mensagem."""
        colors = {
            "success": "#2d5f2f",
            "error": "#5f2d2d",
            "warning": "#5f4f2d",
            "info": "#2d4f5f"
        }
        return colors.get(msg_type, colors["info"])
    
    # Função clear(): executa lógica relacionada a clear.
    def clear(self):
        """Limpa mensagens."""
        for widget in self.message_frame.winfo_children():
            widget.destroy()


# Classe ModelManagerFrame: define comportamento e estrutura desta parte do aplicativo.
class ModelManagerFrame(ScreenBase):
    """Componente de gerenciamento de modelos para UI limpa e modular."""

    TAGS = [
        ("Ofício", "{NUM_OFICIO}"),
        ("SEI Ofício", "{SEI_OFICIO}"),
        ("Manifestação", "{SEI_MANIFESTACAO}"),
        ("Protocolo", "{PROTOCOLO}"),
        ("Resumo", "{RESUMO}"),
        ("Prazo", "{PRAZO}")
    ]

    def __init__(
        self,
        parent,
        theme_manager: ThemeManager,
        engine: SEIEngine,
        on_update_callback,
        **kwargs
    ):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        self.engine = engine
        self.on_update_callback = on_update_callback
        self.listbox: Optional[tk.Listbox] = None
        self.text_editor: Optional[ctk.CTkTextbox] = None
        self.selected_label: Optional[ctk.CTkLabel] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói UI de gerenciamento de modelos."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color=get_color_tuple("background"))
        container.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        container.grid_rowconfigure(0, weight=0)  # Header não expande
        container.grid_rowconfigure(1, weight=0)  # Label não expande
        container.grid_rowconfigure(2, weight=1)  # Listbox expande
        container.grid_rowconfigure(3, weight=0)  # Tags não expandem
        container.grid_rowconfigure(4, weight=0)  # Label não expande
        container.grid_rowconfigure(5, weight=0)  # Label não expande
        container.grid_rowconfigure(6, weight=1)  # Editor expande com prioridade
        container.grid_rowconfigure(7, weight=0)  # Botões não expandem
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)

        header = ctk.CTkLabel(
            container,
            text="Gerenciar Modelos",
            font=get_font(16, "bold"),
            text_color=get_color_tuple("text_primary")
        )
        header.grid(row=0, column=0, sticky='w', pady=(0, 15))

        ctk.CTkLabel(
            container,
            text="Modelos Disponíveis:",
            font=get_font(11, "bold"),
            text_color=get_color_tuple("text_secondary")
        ).grid(row=1, column=0, sticky='w', pady=(0, 5))

        self.model_search_var = tk.StringVar(value="")
        search_entry = ctk.CTkEntry(
            container,
            placeholder_text="Buscar modelo...",
            textvariable=self.model_search_var,
            font=get_font(11),
            height=32,
            border_width=1,
            corner_radius=8,
            fg_color=get_color_tuple("background")
        )
        search_entry.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        self.model_search_var.trace_add("write", lambda *args: self._refresh_listbox())

        listbox_frame = ctk.CTkFrame(
            container,
            border_width=1,
            border_color=get_color_tuple("border"),
            corner_radius=6,
            fg_color=get_color_tuple("surface")
        )
        listbox_frame.grid(row=2, column=0, sticky='nsew', pady=(0, 15))
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.SINGLE,
            bg=self.theme_manager.get_color("background"),
            fg=self.theme_manager.get_color("text_primary"),
            borderwidth=0,
            highlightthickness=0,
            font=("Consolas", 11)
        )
        self.listbox.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        tag_bar = ctk.CTkFrame(container, fg_color=get_color_tuple("surface"))
        tag_bar.grid(row=3, column=0, sticky='ew', pady=(4, 10))

        for idx, (label, token) in enumerate(self.TAGS):
            btn = ctk.CTkButton(
                tag_bar,
                text=label,
                width=100,
                height=28,
                fg_color=get_color_tuple("primary"),
                hover_color=get_color_tuple("secondary"),
                text_color=get_color_tuple("text_primary"),
                corner_radius=14,
                font=get_font(10, "bold"),
                command=lambda t=token: self._insert_tag(t)
            )
            btn.grid(row=0, column=idx, padx=4, pady=2)

        self.selected_label = ctk.CTkLabel(
            container,
            text="Selecione um modelo para editar",
            font=get_font(10),
            text_color=self.theme_manager.get_color("text_secondary")
        )
        self.selected_label.grid(row=4, column=0, sticky='w', pady=(8, 5))

        ctk.CTkLabel(
            container,
            text="Editar Código:",
            font=get_font(11, "bold"),
            text_color=self.theme_manager.get_color("text_secondary")
        ).grid(row=5, column=0, sticky='w', pady=(0, 5))

        self.text_editor = ctk.CTkTextbox(
            container,
            corner_radius=6,
            border_width=1,
            font=get_font(14, family="Consolas"),
            wrap="word",
            fg_color=self.theme_manager.get_color("background"),
            text_color=self.theme_manager.get_color("text_primary"),
            height=300
        )
        self.text_editor.grid(row=6, column=0, sticky='nsew', pady=(0, 15))
        text_editor = self.text_editor

        # Scrollbar com transições de cor
        self.model_scroll = ctk.CTkScrollbar(container, orientation='vertical', 
                                          command=self.text_editor.yview)
        self.model_scroll.grid(row=6, column=1, sticky='ns', pady=(0, 15), padx=(5, 0))
        self.text_editor.configure(yscrollcommand=self.model_scroll.set)

        # Bind focus events para transições
        # Função on_editor_focus_in(e): executa lógica relacionada a on editor focus in.
        def on_editor_focus_in(e):
            text_editor.configure(border_color=self.theme_manager.get_focus_border_color())
            self.model_scroll.configure(button_color=self.theme_manager.get_color("primary"))

        # Função on_editor_focus_out(e): executa lógica relacionada a on editor focus out.
        def on_editor_focus_out(e):
            text_editor.configure(border_color=get_color_tuple("border"))
            self.model_scroll.configure(button_color=get_color_tuple("border"))

        self.text_editor.bind("<FocusIn>", on_editor_focus_in)
        self.text_editor.bind("<FocusOut>", on_editor_focus_out)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky='ew', pady=10)

        ctk.CTkButton(
            btn_frame,
            text="➕ Adicionar",
            command=self._adicionar,
            height=32,
            font=get_font(11, "bold"),
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Deletar",
            command=self._deletar,
            height=32,
            font=get_font(11, "bold"),
            width=120
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="💾 Salvar",
            command=self._salvar,
            height=32,
            font=get_font(11, "bold"),
            fg_color=get_color_tuple("success"),
            width=200
        ).pack(side="right", padx=5)

        self._refresh_listbox()

    def _insert_tag(self, tag: str) -> None:
        """Insere token no cursor do editor."""
        if not self.text_editor:
            return
        index = self.text_editor.index(tk.INSERT)
        self.text_editor.insert(index, tag)
        self.text_editor.focus_set()

    def _refresh_listbox(self) -> None:
        """Recarrega lista de nomes de modelos."""
        if not self.listbox:
            return
        self.listbox.delete(0, tk.END)
        for nome in sorted(self.engine.get_modelos_list()):
            self.listbox.insert(tk.END, nome)

    def _on_select(self, event=None) -> None:
        """Mostra conteúdo do modelo selecionado no editor."""
        if not self.listbox or not self.text_editor:
            return
        selection = self.listbox.curselection()
        if not selection:
            return

        nome = self.listbox.get(selection[0])
        self._set_selected_label(f"Editando: {nome}")

        modelo = self.engine.modelos.get(nome)
        texto = ""
        if callable(modelo):
            texto = modelo("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFESTACAO", "OUV-XXXX", "RESUMO", "PRAZO")
        elif isinstance(modelo, str):
            texto = modelo

        self.text_editor.configure(state="normal")
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", texto)

    def _set_selected_label(self, text: str) -> None:
        if self.selected_label is not None:
            self.selected_label.configure(text=text)

    def _adicionar(self) -> None:
        """Cria diálogo com novo modelo para adicionar."""
        dialog = tk.Toplevel(self)
        dialog.title("Novo Modelo")
        dialog.geometry("600x380")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nome:", font=get_font(11)).pack(anchor="w", padx=10, pady=(10, 0))
        name_entry = ctk.CTkEntry(dialog, width=500, font=get_font(11), height=32)
        name_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(dialog, text="Código/Template:", font=get_font(11)).pack(anchor="w", padx=10, pady=(5, 0))
        code_text = ctk.CTkTextbox(dialog, height=220, font=get_font(13, family="Consolas"))
        code_text.pack(padx=10, pady=(0, 15), fill="both", expand=True)

        # Função salvar(): executa lógica relacionada a salvar.
        def salvar():
            nome = name_entry.get().strip()
            codigo = code_text.get("1.0", tk.END).strip()
            if not nome or not codigo:
                return
            if self.engine.add_custom_modelo(nome, codigo):
                self._refresh_listbox()
                self.on_update_callback()
                dialog.destroy()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(footer, text="Salvar", command=salvar, width=150, height=32, font=get_font(11, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="Cancelar", command=dialog.destroy, width=150, height=32, font=get_font(11, "bold")).pack(side="left", padx=5)

    def _salvar(self) -> None:
        """Atualiza modelo já existente e salva no engine."""
        if not self.listbox or not self.text_editor:
            return
        selection = self.listbox.curselection()
        if not selection:
            return

        nome = self.listbox.get(selection[0])
        novo_texto = self.text_editor.get("1.0", tk.END).strip()

        if novo_texto and self.engine.update_modelo(nome, novo_texto):
            self._set_selected_label(f"✅ {nome} salvo!")
            self.on_update_callback()
            self.after(1500, lambda: self._set_selected_label(f"Editando: {nome}"))

    def _deletar(self) -> None:
        """Remove modelo do engine."""
        if not self.listbox:
            return
        selection = self.listbox.curselection()
        if not selection:
            return

        nome = self.listbox.get(selection[0])
        if self.engine.delete_modelo(nome):
            self._refresh_listbox()
            if self.text_editor:
                self.text_editor.delete("1.0", tk.END)
            if self.selected_label is not None:
                self.selected_label.configure(text="Modelo deletado")
            self.on_update_callback()

    def _on_theme_change(self, is_dark: bool) -> None:
        """Aplica alterações no tema."""
        if self.listbox:
            self.listbox.configure(
                bg=self.theme_manager.get_color("background"),
                fg=self.theme_manager.get_color("text_primary")
            )
        self.configure(fg_color=self.theme_manager.get_color("background"))


# Classe GeradorSEIApp: define comportamento e estrutura desta parte do aplicativo.
class GeradorSEIApp(ctk.CTk):
    """Aplicação principal com navegação por sidebar elegante."""
    
    # Função interna __init__(): executa lógica relacionada a init.
    def __init__(self):
        super().__init__()
        self.title("Gerador de Despacho SEI")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        
        # Config
        self.dados_file = "dados_ultimo.json"
        self.config_file = "config.json"
        self.modelos_file = "modelos_custom.json"
        self.historico = []
        
        # Assets e ícones
        self.assets_dir = os.path.join(os.getcwd(), "assets")
        self._ensure_assets_folder()
        self.icons = self._load_icons()
        
        # Theme
        is_dark = self._carregar_config()
        self.theme_manager = ThemeManager(is_dark)
        configure_appearance(is_dark)

        # Engine
        self.engine = SEIEngine(self.modelos_file)
        self.modelos = self.engine.modelos
        
        # Screens
        self.screens = {}
        self.current_screen = None
        self.nav_buttons = {}
        
        # Build
        self._build_ui()
        self._setup_shortcuts()
        self.theme_manager.register_observer(self._on_theme_change)
    
    # Função interna _ensure_assets_folder(): executa lógica relacionada a ensure assets folder.
    def _ensure_assets_folder(self):
        """Garante que a pasta assets existe."""
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
    
    # Função interna _load_icons(): executa lógica relacionada a load icons.
    def _load_icons(self):
        """Carrega ícones da pasta assets."""
        icons = {}
        icon_files = {
            "gerar": "play.png",
            "modelos": "file_text.png", 
            "historico": "message.png",
            "mensagens": "settings.png"
        }
        
        missing_icons = []
        for key, filename in icon_files.items():
            icon_path = os.path.join(self.assets_dir, filename)
            if os.path.exists(icon_path):
                try:
                    pil_image = Image.open(icon_path).resize((20, 20))
                    icons[key] = ctk.CTkImage(pil_image, size=(20, 20))
                except Exception as e:
                    missing_icons.append(filename)
            else:
                missing_icons.append(filename)
        
        if missing_icons:
            # Mensagem discreta na tela de mensagens
            self.after(1000, lambda: self._show_icon_warning(missing_icons))
        
        return icons
    
    # Função interna _show_icon_warning(missing_icons): executa lógica relacionada a show icon warning.
    def _show_icon_warning(self, missing_icons):
        """Mostra aviso discreto sobre ícones faltantes."""
        if "mensagens" in self.screens:
            self.screens["mensagens"].add_message(
                "Atenção", 
                f"Ícones não encontrados em /assets: {', '.join(missing_icons)}. O programa funcionará sem eles.",
                "warning"
            )
    
    # Função interna _carregar_config(): executa lógica relacionada a carregar config.
    def _carregar_config(self):
        """Carrega configurações."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f).get("dark_mode", True)
            except:
                pass
        return True
    
    # Função interna _salvar_config(): executa lógica relacionada a salvar config.
    def _salvar_config(self):
        """Salva configurações."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"dark_mode": self.theme_manager.is_dark}, f)
        except:
            pass
    
    # Função interna _carregar_modelos_custom(): executa lógica relacionada a carregar modelos custom.
    def _carregar_modelos_custom(self):
        """Carrega modelos customizados."""
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except:
                pass
    
    # Função interna _build_ui(): executa lógica relacionada a build ui.
    def _build_ui(self):
        """Constrói interface moderna com sidebar elegante e status bar."""
        # Força o app a ser responsivo ao redimensionar
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container principal
        main_container = ctk.CTkFrame(self, fg_color=get_color_tuple("background"))
        main_container.grid(row=0, column=0, sticky='nsew')
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_rowconfigure(2, weight=0)  # Status bar
        main_container.grid_columnconfigure(0, weight=1)

        # Header elegante
        self._create_header(main_container)

        # Área de conteúdo
        content_area = ctk.CTkFrame(main_container, fg_color=get_color_tuple("background"))
        content_area.grid(row=1, column=0, sticky='nsew')
        content_area.grid_rowconfigure(0, weight=1)
        content_area.grid_columnconfigure(0, weight=0)
        content_area.grid_columnconfigure(1, weight=1)
        
        # Sidebar elegante
        self._create_sidebar(content_area)
        
        # Container de telas
        self.screen_container = ctk.CTkFrame(content_area, fg_color=get_color_tuple("background"))
        self.screen_container.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        self.screen_container.grid_rowconfigure(0, weight=1)
        self.screen_container.grid_columnconfigure(0, weight=1)
        
        # Status Bar
        self._create_status_bar(main_container)
        
        # Criar telas
        self._create_screens()
        
    # Função interna _create_header(parent): executa lógica relacionada a create header.
    def _create_header(self, parent):
        """Cria header elegante."""
        header = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                             height=70, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky='ew')
        header.grid_propagate(False)
        
        self.sidebar_toggle_btn = ctk.CTkButton(header, text="☰",
                                       width=45, height=45, command=self._toggle_sidebar,
                                       fg_color="transparent", hover_color=get_color_tuple("surface"),
                                       border_width=1, border_color=get_color_tuple("border"),
                                       corner_radius=8)
        self.sidebar_toggle_btn.pack(side="left", padx=15, pady=12)

        title = ctk.CTkLabel(header, text="Gerador SEI", 
                            font=ctk.CTkFont(size=20, weight="bold"),
                            text_color=get_color_tuple("text_primary"))
        title.pack(side="left", padx=10, pady=20)
        
        self.theme_btn = ctk.CTkButton(header, text="☀️" if self.theme_manager.is_dark else "🌙",
                                       width=45, height=45, command=self._toggle_theme,
                                       fg_color="transparent", hover_color=get_color_tuple("surface"),
                                       border_width=1, border_color=get_color_tuple("border"),
                                       corner_radius=8)
        self.theme_btn.pack(side="right", padx=25, pady=12)
    
    # Função interna _create_status_bar(parent): executa lógica relacionada a create status bar.
    def _create_status_bar(self, parent):
        """Cria status bar no rodapé."""
        status_bar = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                 height=30, corner_radius=0)
        status_bar.grid(row=2, column=0, sticky='ew')
        status_bar.grid_propagate(False)
        
        # Versão do app
        version_label = ctk.CTkLabel(status_bar, text="v1.0.0",
                                    font=get_font(9),
                                    text_color=get_color_tuple("text_secondary"))
        version_label.pack(side="left", padx=15, pady=5)
        
        # Tema atual
        self.theme_status_label = ctk.CTkLabel(status_bar, 
                                              text=f"Tema: {'Escuro' if self.theme_manager.is_dark else 'Claro'}",
                                              font=get_font(9),
                                              text_color=get_color_tuple("text_secondary"))
        self.theme_status_label.pack(side="right", padx=15, pady=5)
    
    # Função interna _create_sidebar(parent): executa lógica relacionada a create sidebar.
    def _create_sidebar(self, parent):
        """Cria sidebar elegante com hover distintos e indicador animado."""
        self.sidebar = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                   width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='nsw', padx=0, pady=0)
        self.sidebar.grid_propagate(False)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=0)
        
        # Indicador animado
        from ui_animations import UIAnimations
        self.nav_indicator = UIAnimations.create_indicator_line(
            self.sidebar, height=50, width=4, 
            color=self.theme_manager.get_color("primary")
        )
        self.nav_indicator.place(x=0, y=50)  # Posição inicial
        
        # Título da sidebar
        sidebar_title = ctk.CTkLabel(self.sidebar, text="NAVEGAÇÃO", 
                                    font=ctk.CTkFont(size=10, weight="bold"),
                                    text_color=get_color_tuple("text_secondary"))
        sidebar_title.pack(padx=20, pady=(25, 15))
        
        # Botões de navegação
        self.nav_items = [
            ("Gerar Despacho", "gerar"),
            ("Gerenciar Modelos", "modelos"),
            ("Histórico", "historico"),
            ("Mensagens", "mensagens")
        ]
        
        self.nav_buttons = {}
        for idx, (text, screen_name) in enumerate(self.nav_items):
            icon = self.icons.get(screen_name)
            btn = ctk.CTkButton(self.sidebar, text=text, height=50, 
                               font=ctk.CTkFont(size=11, weight="bold"),
                               fg_color="transparent", 
                               hover_color=self.theme_manager.get_hover_color("primary"),
                               text_color=get_color_tuple("text_primary"),
                               border_width=0, corner_radius=8, image=icon,
                               command=lambda s=screen_name, i=idx: self._switch_screen(s, i))
            btn.pack(fill="x", padx=15, pady=5)
            
            # Hover effect mais distinto
            # Função on_enter(e, b=btn, i=idx): executa lógica relacionada a on enter.
            def on_enter(e, b=btn, i=idx):
                if b != self.nav_buttons.get(self.current_screen):
                    b.configure(fg_color=self.theme_manager.get_hover_color("surface"), 
                              text_color=self.theme_manager.get_color("primary"),
                              border_width=1, border_color=self.theme_manager.get_color("primary"))
            
            # Função on_leave(e, b=btn, i=idx): executa lógica relacionada a on leave.
            def on_leave(e, b=btn, i=idx):
                if b != self.nav_buttons.get(self.current_screen):
                    b.configure(fg_color="transparent", 
                              text_color=get_color_tuple("text_primary"),
                              border_width=0)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            self.nav_buttons[screen_name] = btn
    
    # Função interna _create_screens(): executa lógica relacionada a create screens.
    def _create_screens(self):
        """Cria todas as telas."""
        self.screens["gerar"] = GenerarScreen(
            self.screen_container,
            self.theme_manager,
            self.engine,
            self._show_message,
            self.icons,
            fg_color=get_color_tuple("background")
        )

        self.screens["modelos"] = ModelManagerFrame(
            self.screen_container,
            self.theme_manager,
            self.engine,
            self._on_modelos_update,
            fg_color=get_color_tuple("background")
        )

        self.screens["historico"] = HistoricoScreen(
            self.screen_container,
            self.theme_manager,
            self.historico,
            fg_color=get_color_tuple("background")
        )

        self.screens["mensagens"] = MensagensScreen(
            self.screen_container,
            self.theme_manager,
            fg_color=get_color_tuple("background")
        )
    
    # Função interna _setup_shortcuts(): executa lógica relacionada a setup shortcuts.
    def _setup_shortcuts(self):
        """Configura atalhos."""
        self.bind("<Control-s>", lambda e: self.screens["gerar"]._on_salvar())
        self.bind("<Control-l>", lambda e: self.screens["gerar"]._on_carregar())
        self.bind("<Control-e>", lambda e: self.screens["gerar"]._on_pdf())
        self.bind("<Control-g>", lambda e: self.screens["gerar"]._on_gerar())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<F11>", lambda e: self._toggle_theme())
    
    # Função interna _switch_screen(screen_name, button_index=None): executa lógica relacionada a switch screen.
    def _switch_screen(self, screen_name, button_index=None):
        """Muda tela ativa com efeitos visuais e indicador animado."""
        if self.current_screen == screen_name:
            return
            
        from ui_animations import UIAnimations
        
        # Fade out tela atual
        if self.current_screen:
            UIAnimations.fade_out(self.screens[self.current_screen], duration=200, 
                                on_complete=lambda: self._show_new_screen(screen_name))
        else:
            self._show_new_screen(screen_name)
        
        # Animação do indicador
        if button_index is not None and hasattr(self, 'nav_indicator'):
            target_y = 50 + (button_index * 60)  # Ajustar baseado no layout
            UIAnimations.animate_indicator_move(self.nav_indicator, target_y, duration=300)
        
        # Atualizar botões de navegação
        for name, btn in self.nav_buttons.items():
            if name == screen_name:
                btn.configure(fg_color=self.theme_manager.get_color("primary"),
                             text_color="white")
            else:
                btn.configure(fg_color="transparent",
                             text_color=get_color_tuple("text_primary"))
        
        self.current_screen = screen_name
        
        # Refresh histórico se necessário
        if screen_name == "historico":
            self.screens["historico"]._refresh()
    
    # Função interna _show_new_screen(screen_name): executa lógica relacionada a show new screen.
    def _show_new_screen(self, screen_name):
        """Mostra nova tela com fade-in."""
        from ui_animations import UIAnimations
        self.screens[screen_name].show()
        UIAnimations.fade_in(self.screens[screen_name], duration=300)
    
    # Função interna _show_message(title, message, msg_type="info"): executa lógica relacionada a show message.
    def _show_message(self, title, message, msg_type="info"):
        """Mostra mensagem com CTkMessagebox e adiciona à tela de mensagens."""
        # Mapeia tipos para ícones do CTkMessagebox
        icon_map = {
            "info": "info",
            "success": "check",
            "warning": "warning", 
            "error": "cancel"
        }
        
        # Mostra CTkMessagebox
        from CTkMessagebox import CTkMessagebox
        msg = CTkMessagebox(title=title, message=message, icon=icon_map.get(msg_type, "info"))
        
        # Também adiciona à tela de mensagens para histórico
        self.screens["mensagens"].add_message(title, message, msg_type)
    
    # Função interna _reutilizar_dados(item): executa lógica relacionada a reutilizar dados.
    def _reutilizar_dados(self, item):
        """Tenta extrair dados do texto gerado e preencher campos."""
        gerar_screen = self.screens["gerar"]
        dados_extraidos = {}

        if isinstance(item, dict):
            dados_extraidos = {
                "oficio": item.get("oficio", ""),
                "prazo": item.get("prazo", ""),
                "sei_oficio": item.get("sei_oficio", ""),
                "sei_manifestacao": item.get("sei", ""),
                "protocolo": item.get("protocolo", ""),
                "resumo": item.get("resumo", "")
            }
            texto = item.get("texto", "")
        else:
            texto = item
            # Esta é uma implementação simplificada de fallback para string
            for line in texto.split("\n"):
                line = line.strip()
                if "Ofício" in line and any(char.isdigit() for char in line):
                    match = re.search(r"(\d+/\d{4})", line)
                    if match:
                        dados_extraidos["oficio"] = match.group(1)
                elif "SEI" in line and any(char.isdigit() for char in line):
                    match = re.search(r"(\d+)", line)
                    if match and "Manifestação" in line:
                        dados_extraidos["sei_manifestacao"] = match.group(1)
                    elif match and "Ofício" in line:
                        dados_extraidos["sei_oficio"] = match.group(1)
                elif "OUV-" in line:
                    match = re.search(r"(OUV-\d+/\d{4})", line)
                    if match:
                        dados_extraidos["protocolo"] = match.group(1)
                elif "Prazo" in line or "até" in line.lower():
                    match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
                    if match:
                        dados_extraidos["prazo"] = match.group(1)

        for idx, key in enumerate(["oficio", "prazo", "sei_oficio", "sei_manifestacao", "protocolo", "resumo"]):
            if key in dados_extraidos and idx < len(gerar_screen.inputs):
                value = dados_extraidos[key]
                if value is not None:
                    gerar_screen.inputs[idx].delete(0, tk.END)
                    gerar_screen.inputs[idx].insert(0, value)

        gerar_screen.text_saida.configure(state="normal")
        gerar_screen.text_saida.delete("1.0", ctk.END)
        gerar_screen.text_saida.insert("1.0", texto)

        self._switch_screen("gerar")
        self._show_message("Sucesso", "Dados reutilizados! Verifique e ajuste se necessário.", "success")
    
    # Função interna _on_modelos_update(): executa lógica relacionada a on modelos update.
    def _on_modelos_update(self):
        """Callback quando modelos são atualizados."""
        self.screens["gerar"].model_select.configure(values=self.engine.get_modelos_list())
        self.engine._save_custom_modelos()

        if "modelos" in self.screens:
            self.screens["modelos"]._refresh_listbox()

        # Feedback UX claro na tela de geração
        self.screens["gerar"].status_label.configure(
            text="Modelos atualizados. Selecione um modelo e gere o despacho.",
            text_color=get_color_tuple("success")
        )
    
    # Função interna _on_theme_change(is_dark): executa lógica relacionada a on theme change.
    def _on_theme_change(self, is_dark):
        """Callback quando tema muda."""
        ctk.set_appearance_mode("dark" if is_dark else "light")
        self.theme_btn.configure(text="☀️" if is_dark else "🌙")
        self.theme_status_label.configure(text=f"Tema: {'Escuro' if is_dark else 'Claro'}")
        self._salvar_config()
    
    # Função interna _toggle_theme(): executa lógica relacionada a toggle theme.
    def _toggle_theme(self):
        """Alterna tema."""
        self.theme_manager.toggle_theme()

    # Função interna _toggle_sidebar(): executa lógica relacionada a toggle sidebar.
    def _toggle_sidebar(self):
        """Alterna entre sidebar expandida e recolhida"""
        if getattr(self, 'sidebar_collapsed', False):
            self.sidebar.configure(width=220)
            for label, screen_name in self.nav_items:
                btn = self.nav_buttons.get(screen_name)
                if btn:
                    btn.configure(text=label, width=220)
            self.sidebar_collapsed = False
        else:
            self.sidebar.configure(width=70)
            for _, screen_name in self.nav_items:
                btn = self.nav_buttons.get(screen_name)
                if btn:
                    btn.configure(text="", width=56)
            self.sidebar_collapsed = True

    # Função copiar_para_clipboard(texto: Optional[str] = None): executa lógica relacionada a copiar para clipboard.
    def copiar_para_clipboard(self, texto: Optional[str] = None):
        """Copia despacho para clipboard."""
        if texto is None:
            texto = self.screens["gerar"].text_saida.get("1.0", ctk.END).strip()
        texto = texto.strip() if isinstance(texto, str) else ""

        if not texto or texto == "O despacho gerado aparecerá aqui após preencher os dados acima.":
            self._show_message("Erro", "Nada para copiar.", "error")
            return

        self.clipboard_clear()
        self.clipboard_append(texto)
        self._show_message("Sucesso", "Copiado para área de transferência!", "success")
    
    # NOTE: _on_modelos_update is defined earlier to sync with the model manager and engine.


if __name__ == "__main__":
    app = GeradorSEIApp()
    app.mainloop()
