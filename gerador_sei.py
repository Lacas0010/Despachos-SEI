"""
Gerador SEI - Main Application
Modern interface for SEI document generation
"""

import datetime
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


class ScreenBase(ctk.CTkFrame):
    """Classe base para todas as telas com suporte a tema."""

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
    
    def show(self):
        """Mostra a tela."""
        self.grid(row=0, column=0, sticky='nsew')
    
    def hide(self):
        """Esconde a tela."""
        self.grid_forget()


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

        self._build_ui()
    
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

    def _create_form(self, parent):
        """Cria formulário com layout em grid."""
        # Frame do formulário
        form_frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                 corner_radius=12)
        form_frame.grid(row=1, column=0, sticky='ew', padx=20, pady=(0, 30))
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        hoje = datetime.date.today()
        prazo_inicial = hoje.strftime("%d/%m/%Y")
        
        # Campos em grid: 2 colunas para campos menores
        fields = [
            ("Ofício", "778/2026", 0, 0),
            ("Prazo", prazo_inicial, 0, 1),
            ("SEI Ofício", "198654234", 1, 0),
            ("SEI Manifestação", "220622554", 1, 1),
            ("Protocolo OUV", "OUV-078543/2026", 2, 0),
            ("Resumo", "Falta de vagas de castração", 3, 0, 2)  # Span 2 colunas
        ]
        
        for field in fields:
            label_text, placeholder, row, col = field[:4]
            colspan = field[4] if len(field) > 4 else 1
            
            # Label
            label = ctk.CTkLabel(form_frame, text=label_text, 
                                font=get_font(12, "bold"),
                                text_color=get_color_tuple("text_secondary"))
            label.grid(row=row*2, column=col, sticky="w", padx=20, pady=(20, 5))
            
            # Input
            if label_text == "Prazo":
                # Frame para entrada + botão calendário
                date_frame = ctk.CTkFrame(form_frame, fg_color=get_color_tuple("transparent"), height=42)
                date_frame.grid(row=row*2+1, column=col, columnspan=colspan, sticky="ew", 
                               padx=20, pady=(0, 10))
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
            else:
                entry = ctk.CTkEntry(form_frame, placeholder_text=placeholder,
                                    font=get_font(12), height=42,
                                    border_width=1, corner_radius=10,
                                    fg_color=get_color_tuple("background"))
                entry.grid(row=row*2+1, column=col, columnspan=colspan, sticky="ew", 
                          padx=20, pady=(0, 10))
                if colspan == 1:
                    form_frame.grid_columnconfigure(col, weight=1)
            
            self.inputs[len(self.inputs)] = entry
            entry.bind("<KeyRelease>", self._validate_live)
            entry.bind("<FocusOut>", self._validate_live)

            # Sem formatação automática para SEI Ofício / SEI Manifestação.
            # O usuário cola texto diretamente, inclusive tags manuais como #{...|...}#.
            Tooltip(entry, label_text)
        
        # Modelo
        model_label = ctk.CTkLabel(form_frame, text="Modelo", 
                                  font=get_font(12, "bold"),
                                  text_color=get_color_tuple("text_secondary"))
        model_label.grid(row=8, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.model_select = ctk.CTkComboBox(form_frame, values=self.engine.get_modelos_list(),
                                           variable=self.template_var, state="readonly",
                                           height=42, font=get_font(12),
                                           border_width=1, corner_radius=10,
                                           fg_color=get_color_tuple("background"))
        self.model_select.grid(row=9, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        self.model_select.bind("<<ComboboxSelected>>", self._on_template_selected)
        Tooltip(self.model_select, "Selecionar modelo")
        
        # Botões
        self._create_buttons(form_frame)
    
    def _create_buttons(self, parent):
        """Cria botões diferenciados."""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20))
        
        # Botão Gerar (primário)
        gerar_icon = self.icons.get("gerar")
        gerar_btn = ctk.CTkButton(buttons_frame, text="Gerar Despacho", command=self._on_gerar,
                                 height=45, font=get_font(12, "bold"),
                                 fg_color=get_color_tuple("primary"),
                                 hover_color="#0056CC", corner_radius=10, image=gerar_icon)
        gerar_btn.pack(side="left", padx=(0, 10), expand=True)
        
        # Botões secundários
        actions = [("💾 Salvar", self._on_salvar), ("📥 Carregar", self._on_carregar),
                  ("📄 PDF", self._on_pdf)]
        
        for text, cmd in actions:
            btn = ctk.CTkButton(buttons_frame, text=text, command=cmd, height=45,
                               font=get_font(11, "bold"),
                               fg_color=get_color_tuple("transparent"), border_width=1,
                               border_color=get_color_tuple("border"),
                               corner_radius=8)
            btn.pack(side="left", padx=5)
            Tooltip(btn, text)
    
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
                                   text_color=get_color_tuple("text_primary"))
        result_label.grid(row=0, column=0, sticky='w')
        
        copy_btn = ctk.CTkButton(header_frame, text="📋 Copiar", command=self._on_copiar,
                                height=35, width=100, font=get_font(11, "bold"),
                                fg_color=get_color_tuple("success"),
                                hover_color="#059669", corner_radius=8)
        copy_btn.grid(row=0, column=1, sticky='e')
        
        # Textbox com fonte mono
        self.text_saida = ctk.CTkTextbox(output_frame, wrap="word",
                                        font=get_font(11, family="Courier New"),
                                        corner_radius=10, border_width=1,
                                        fg_color=get_color_tuple("background"),
                                        text_color=get_color_tuple("text_primary"),
                                        height=300)
        self.text_saida.grid(row=1, column=0, sticky='nsew', padx=(20, 0), pady=(0, 20))

        # Scrollbar associada ao textarea do resultado
        output_scroll = ctk.CTkScrollbar(output_frame, orientation="vertical",
                                         command=self.text_saida.yview)
        output_scroll.grid(row=1, column=1, sticky='ns', padx=(0, 20), pady=(0, 20))
        self.text_saida.configure(yscrollcommand=output_scroll.set)
        # Manter em estado normal para poder rolar mesmo com visualização somente
        self.text_saida.configure(state="normal")

        # Grid responsivo do output_frame
        output_frame.grid_rowconfigure(0, weight=0)
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_rowconfigure(2, weight=0)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_columnconfigure(1, weight=0)

        self.text_saida.insert("1.0", "O resultado do despacho aparecerá aqui...")
        # comentário: mantenha em normal para rolagem funcionar
        self.text_saida.configure(state="normal")

        # Status
        self.status_label = ctk.CTkLabel(output_frame, text="Pronto para gerar",
                                        text_color=get_color_tuple("text_secondary"),
                                        font=get_font(11))
        self.status_label.grid(row=2, column=0, sticky='w', padx=20, pady=(0, 20))
    
    def _open_date_picker(self, entry):
        """Abre seletor de data customizado."""
        # Janela do date picker
        picker = ctk.CTkToplevel(self)
        picker.title("")
        picker.geometry("300x350")
        picker.resizable(False, False)
        picker.transient(self.master.master.master)
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
    
    def _select_date(self, day, year, month, entry, picker):
        """Seleciona data."""
        selected_date = datetime.date(year, month, day)
        entry.delete(0, tk.END)
        entry.insert(0, selected_date.strftime("%d/%m/%Y"))
        picker.destroy()
        self._validate_live()
    
    def _select_today(self, entry, picker):
        """Seleciona data de hoje."""
        today = datetime.date.today()
        entry.delete(0, tk.END)
        entry.insert(0, today.strftime("%d/%m/%Y"))
        picker.destroy()
        self._validate_live()
    
    def _on_theme_change(self, is_dark):
        """Atualiza cores ao mudar tema."""
        self.configure(fg_color=get_color_tuple("background"))
        # As cores dos frames e inputs serão atualizadas automaticamente pelo ThemeManager
    
    def _validate_live(self, event=None):
        """Validação ao vivo com feedback visual."""
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
    
    def _on_gerar(self):
        """Gera despacho e copia automaticamente."""
        if self._validar_campos():
            return
        
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
            
            self.text_saida.configure(state="normal")
            self.text_saida.delete("1.0", ctk.END)
            self.text_saida.insert("1.0", texto)
            # deixar em estado normal para permitir seleção e scroll contínuos
            self.text_saida.configure(state="normal")
            
            # Copia automaticamente para clipboard
            self.master.master.master.clipboard_clear()
            self.master.master.master.clipboard_append(texto)
            
            # Atualiza status
            self.status_label.configure(text="Despacho gerado e copiado!",
                                       text_color=get_color_tuple("success"))
            self.after(3000, lambda: self._validate_live())  # Reset status after 3s
            
            self.on_show_message("Sucesso", "Despacho gerado e copiado automaticamente!", "success")
        except Exception as e:
            self.on_show_message("Erro", f"Erro na geração: {str(e)}", "error")
    
    def _on_template_selected(self, event=None):
        """Atualiza resumo quando modelo muda."""
        modelo = self.template_var.get()
        if modelo == "Demanda de Ouvidoria - Ausência de Cronograma Castração":
            self.inputs[4].delete(0, tk.END)
            self.inputs[4].insert(0, RESUMO_CRONOGRAMA)
            self.inputs[4].configure(state="disabled")
        else:
            self.inputs[4].configure(state="normal")
    
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
    
    def _on_pdf(self):
        """Exporta PDF."""
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
    
    def _on_copiar(self):
        """Copia para clipboard com feedback."""
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto or texto == "O resultado do despacho aparecerá aqui...":
            self.on_show_message("Aviso", "Nada para copiar", "warning")
            return
        self.master.master.master.clipboard_clear()
        self.master.master.master.clipboard_append(texto)
        self.status_label.configure(text="Copiado para área de transferência!",
                                   text_color=get_color_tuple("success"))
        self.after(2000, lambda: self._validate_live())  # Reset status after 2s


class HistoricoScreen(ScreenBase):
    """Tela de histórico de despachos."""
    
    def __init__(self, parent, theme_manager, historico, **kwargs):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        self.historico = historico
        self.listbox = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Constrói interface."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, fg_color=get_color_tuple("background"))
        container.grid(row=0, column=0, sticky='nsew', padx=15, pady=15)
        container.grid_rowconfigure(0, weight=0)  # Header não expande
        container.grid_rowconfigure(2, weight=1)  # Listbox expande
        container.grid_rowconfigure(3, weight=0)  # Botões não expandem
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(container, text="Histórico de Despachos",
                             font=ctk.CTkFont(size=16, weight="bold"),
                             text_color=get_color_tuple("text_primary"))
        header.grid(row=0, column=0, sticky='w', pady=(0, 15))

        listbox_frame = ctk.CTkFrame(container, border_width=1,
                                     border_color=get_color_tuple("border"),
                                     corner_radius=6)
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
            font=("Arial", 10),
            height=20
        )
        self.listbox.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky='ew', pady=10)
        
        ctk.CTkButton(btn_frame, text="📂 Carregar", command=self._on_carregar,
                     height=32, font=ctk.CTkFont(size=10, weight="bold"),
                     width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Limpar", command=self._on_limpar,
                     height=32, font=ctk.CTkFont(size=10, weight="bold"),
                     width=150).pack(side="left", padx=5)
        
        self._refresh()
    
    def _on_theme_change(self, is_dark):
        """Atualiza cores."""
        if self.listbox:
            self.listbox.configure(
                bg=get_color_tuple("background"),
                fg=get_color_tuple("text_primary")
            )
        self.configure(fg_color=get_color_tuple("background"))
    
    def _refresh(self):
        """Atualiza listbox."""
        self.listbox.delete(0, tk.END)
        for i, item in enumerate(self.historico[-20:]):
            idx = len(self.historico) - 20 + i + 1
            self.listbox.insert(tk.END, f"{idx}. {item[:80]}...")
    
    def _on_carregar(self):
        """Carrega item selecionado."""
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            texto = self.historico[-20 + idx]
            self.master.master.master._load_despacho(texto)
    
    def _on_limpar(self):
        """Limpa histórico."""
        self.historico.clear()
        self._refresh()


class MensagensScreen(ScreenBase):
    """Tela de mensagens."""
    
    def __init__(self, parent, theme_manager, **kwargs):
        super().__init__(parent, theme_manager=theme_manager, **kwargs)
        
        self._build_ui()
    
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
    
    def _on_theme_change(self, is_dark):
        """Atualiza cores."""
        self.configure(fg_color=get_color_tuple("background"))
        if self.message_frame:
            self.message_frame.configure(
                fg_color=get_color_tuple("background"),
                border_color=get_color_tuple("border")
            )
    
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
    
    def _get_message_color(self, msg_type):
        """Retorna cor da mensagem."""
        colors = {
            "success": "#2d5f2f",
            "error": "#5f2d2d",
            "warning": "#5f4f2d",
            "info": "#2d4f5f"
        }
        return colors.get(msg_type, colors["info"])
    
    def clear(self):
        """Limpa mensagens."""
        for widget in self.message_frame.winfo_children():
            widget.destroy()


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
            text_color=get_color_tuple("text_secondary")
        )
        self.selected_label.grid(row=4, column=0, sticky='w', pady=(8, 5))

        ctk.CTkLabel(
            container,
            text="Editar Código:",
            font=get_font(11, "bold"),
            text_color=get_color_tuple("text_secondary")
        ).grid(row=5, column=0, sticky='w', pady=(0, 5))

        self.text_editor = ctk.CTkTextbox(
            container,
            corner_radius=6,
            border_width=1,
            font=get_font(14, family="Consolas"),
            wrap="word",
            fg_color=get_color_tuple("background"),
            text_color=get_color_tuple("text_primary"),
            height=300
        )
        self.text_editor.grid(row=6, column=0, sticky='nsew', pady=(0, 15))

        model_scroll = ctk.CTkScrollbar(container, orientation='vertical', command=self.text_editor.yview)
        model_scroll.grid(row=6, column=1, sticky='ns', pady=(0, 15), padx=(5, 0))
        self.text_editor.configure(yscrollcommand=model_scroll.set)

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
        self.selected_label.configure(text=f"Editando: {nome}")

        modelo = self.engine.modelos.get(nome)
        texto = ""
        if callable(modelo):
            texto = modelo("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFESTACAO", "OUV-XXXX", "RESUMO", "PRAZO")
        elif isinstance(modelo, str):
            texto = modelo

        self.text_editor.configure(state="normal")
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", texto)

    def _adicionar(self) -> None:
        """Cria diálogo com novo modelo para adicionar."""
        dialog = tk.Toplevel(self)
        dialog.title("Novo Modelo")
        dialog.geometry("600x380")
        dialog.transient(self.master)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Nome:", font=get_font(11)).pack(anchor="w", padx=10, pady=(10, 0))
        name_entry = ctk.CTkEntry(dialog, width=500, font=get_font(11), height=32)
        name_entry.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(dialog, text="Código/Template:", font=get_font(11)).pack(anchor="w", padx=10, pady=(5, 0))
        code_text = ctk.CTkTextbox(dialog, height=220, font=get_font(13, family="Consolas"))
        code_text.pack(padx=10, pady=(0, 15), fill="both", expand=True)

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
            self.selected_label.configure(text=f"✅ {nome} salvo!")
            self.on_update_callback()
            self.after(1500, lambda: self.selected_label.configure(text=f"Editando: {nome}"))

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


class GeradorSEIApp(ctk.CTk):
    """Aplicação principal com navegação por sidebar elegante."""
    
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
    
    def _ensure_assets_folder(self):
        """Garante que a pasta assets existe."""
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
    
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
    
    def _show_icon_warning(self, missing_icons):
        """Mostra aviso discreto sobre ícones faltantes."""
        if "mensagens" in self.screens:
            self.screens["mensagens"].add_message(
                "Atenção", 
                f"Ícones não encontrados em /assets: {', '.join(missing_icons)}. O programa funcionará sem eles.",
                "warning"
            )
    
    def _carregar_config(self):
        """Carrega configurações."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f).get("dark_mode", True)
            except:
                pass
        return True
    
    def _salvar_config(self):
        """Salva configurações."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"dark_mode": self.theme_manager.is_dark}, f)
        except:
            pass
    
    def _carregar_modelos_custom(self):
        """Carrega modelos customizados."""
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except:
                pass
    
    def _build_ui(self):
        """Constrói interface moderna com sidebar elegante."""
        # Força o app a ser responsivo ao redimensionar
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Container principal
        main_container = ctk.CTkFrame(self, fg_color=get_color_tuple("background"))
        main_container.grid(row=0, column=0, sticky='nsew')
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=1)
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
        
        # Criar telas
        self._create_screens()
        
    def _create_header(self, parent):
        """Cria header elegante."""
        header = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                             height=70, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky='ew')
        header.grid_propagate(False)
        
        title = ctk.CTkLabel(header, text="Gerador SEI", 
                            font=ctk.CTkFont(size=20, weight="bold"),
                            text_color=get_color_tuple("text_primary"))
        title.pack(side="left", padx=25, pady=20)
        
        self.theme_btn = ctk.CTkButton(header, text="☀️" if self.theme_manager.is_dark else "🌙",
                                       width=45, height=45, command=self._toggle_theme,
                                       fg_color="transparent", hover_color=get_color_tuple("surface"),
                                       border_width=1, border_color=get_color_tuple("border"),
                                       corner_radius=8)
        self.theme_btn.pack(side="right", padx=25, pady=12)
    
    def _create_sidebar(self, parent):
        """Cria sidebar elegante."""
        self.sidebar = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"),
                                   width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='nsw', padx=0, pady=0)
        self.sidebar.grid_propagate(False)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=0)
        
        # Título da sidebar
        sidebar_title = ctk.CTkLabel(self.sidebar, text="NAVEGAÇÃO", 
                                    font=ctk.CTkFont(size=10, weight="bold"),
                                    text_color=get_color_tuple("text_secondary"))
        sidebar_title.pack(padx=20, pady=(25, 15))
        
        # Botões de navegação
        nav_items = [
            ("Gerar Despacho", "gerar"),
            ("Gerenciar Modelos", "modelos"),
            ("Histórico", "historico"),
            ("Mensagens", "mensagens")
        ]
        
        for text, screen_name in nav_items:
            icon = self.icons.get(screen_name)
            btn = ctk.CTkButton(self.sidebar, text=text, height=50, 
                               font=ctk.CTkFont(size=11, weight="bold"),
                               fg_color="transparent", hover_color=get_color_tuple("primary"),
                               border_width=0, corner_radius=8, image=icon,
                               command=lambda s=screen_name: self._switch_screen(s))
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[screen_name] = btn
    
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
    
    def _setup_shortcuts(self):
        """Configura atalhos."""
        self.bind("<Control-s>", lambda e: self.screens["gerar"]._on_salvar())
        self.bind("<Control-l>", lambda e: self.screens["gerar"]._on_carregar())
        self.bind("<Control-e>", lambda e: self.screens["gerar"]._on_pdf())
        self.bind("<Control-g>", lambda e: self.screens["gerar"]._on_gerar())
        self.bind("<Control-c>", lambda e: self.screens["gerar"]._on_copiar())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<F11>", lambda e: self._toggle_theme())
    
    def _switch_screen(self, screen_name):
        """Muda tela ativa com efeitos visuais."""
        if self.current_screen:
            self.screens[self.current_screen].hide()
        
        self.current_screen = screen_name
        self.screens[screen_name].show()
        
        # Atualizar botões de navegação
        for name, btn in self.nav_buttons.items():
            if name == screen_name:
                btn.configure(fg_color=get_color_tuple("primary"),
                             text_color="white")
            else:
                btn.configure(fg_color="transparent",
                             text_color=get_color_tuple("text_primary"))
        
        # Refresh histórico se necessário
        if screen_name == "historico":
            self.screens["historico"]._refresh()
    
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
    
    def _load_despacho(self, texto):
        """Carrega despacho na tela de geração."""
        self.screens["gerar"].text_saida.configure(state="normal")
        self.screens["gerar"].text_saida.delete("1.0", ctk.END)
        self.screens["gerar"].text_saida.insert("1.0", texto)
        self.screens["gerar"].text_saida.configure(state="normal")
        self.historico.append(texto)
        self._switch_screen("gerar")
    
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
    
    def _on_theme_change(self, is_dark):
        """Callback quando tema muda."""
        ctk.set_appearance_mode("dark" if is_dark else "light")
        self.theme_btn.configure(text="☀️" if is_dark else "🌙")
        self._salvar_config()
    
    def _toggle_theme(self):
        """Alterna tema."""
        self.theme_manager.toggle_theme()
    

    
    def copiar_para_clipboard(self):
        """Copia despacho para clipboard."""
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto or texto == "Texto gerado aparecerá aqui.":
            self._show_message("Erro", "Nada para copiar.", "error")
            return
        
        self.clipboard_clear()
        self.clipboard_append(texto)
        self._show_message("Sucesso", "Copiado para área de transferência!", "success")
    
    # NOTE: _on_modelos_update is defined earlier to sync with the model manager and engine.


if __name__ == "__main__":
    app = GeradorSEIApp()
    app.mainloop()
