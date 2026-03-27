import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import customtkinter as ctk

from sei_utils import formatar_prazo, validar_sei, formatar_sei_link, get_color, configure_theme
from sei_templates import (
    PREFIXO_DOCUMENTO, RESUMO_CRONOGRAMA,
    modelo_hvep, modelo_castracao, modelo_condicoes_hvep, modelo_cronograma_castracao
)


class Tooltip:
    """Tooltips simples para widgets Tkinter/CustomTkinter."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 10))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# Constantes
TEXT_WIDTH = 90


class GeradorSEIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Despacho SEI")
        self.geometry("1020x760")
        self.minsize(960, 700)

        self.is_dark_mode = True
        self.historico = []
        self.dados_file = "dados_ultimo.json"
        self.config_file = "config.json"
        self.modelos_file = "modelos_custom.json"

        self._carregar_config()
        configure_theme()
        ctk.set_appearance_mode("dark" if self.is_dark_mode else "light")
        ctk.set_default_color_theme("blue")

        self.modelos = {
            "HVeP - Atendimento/HVeP": modelo_hvep,
            "Castração de Cães e Gatos": modelo_castracao,
            "Condições de exames e cirurgia HVeP": modelo_condicoes_hvep,
            "Demanda de Ouvidoria - Ausência de Cronograma Castração": modelo_cronograma_castracao
        }
        self._carregar_modelos_custom()

        self._create_menu()
        self._build_ui()
        self._setup_shortcuts()

    def _carregar_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    cfg = json.load(f)
                self.is_dark_mode = cfg.get("dark_mode", True)
            except Exception:
                self.is_dark_mode = True

    def _salvar_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"dark_mode": self.is_dark_mode}, f)
        except Exception:
            pass

    def _carregar_modelos_custom(self):
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except Exception:
                pass

    def _salvar_modelos_custom(self):
        defaults = {
            "HVeP - Atendimento/HVeP",
            "Castração de Cães e Gatos",
            "Condições de exames e cirurgia HVeP",
            "Demanda de Ouvidoria - Ausência de Cronograma Castração"
        }
        custom = {k: v for k, v in self.modelos.items() if k not in defaults}
        try:
            with open(self.modelos_file, "w", encoding="utf-8") as f:
                json.dump(custom, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        ctk.set_appearance_mode("dark" if self.is_dark_mode else "light")
        self.theme_btn.configure(text="☀️ Light" if self.is_dark_mode else "🌙 Dark")
        self._salvar_config()

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salvar Dados", command=self._salvar_dados, accelerator="Ctrl+S")
        file_menu.add_command(label="Carregar Dados", command=self._carregar_dados, accelerator="Ctrl+L")
        file_menu.add_command(label="Exportar PDF", command=self._exportar_pdf, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Arquivo", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Gerar Despacho", command=self.gerar_despacho, accelerator="Ctrl+G")
        edit_menu.add_command(label="Copiar para Clipboard", command=self.copiar_para_clipboard, accelerator="Ctrl+C")
        edit_menu.add_command(label="Histórico", command=self._mostrar_historico, accelerator="Ctrl+H")
        edit_menu.add_command(label="Gerenciar Modelos", command=self._gerenciar_modelos, accelerator="Ctrl+M")
        menubar.add_cascade(label="Editar", menu=edit_menu)

        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Alternar Tema", command=self._toggle_theme, accelerator="F11")
        menubar.add_cascade(label="Tema", menu=theme_menu)

    def _setup_shortcuts(self):
        self.bind("<Control-s>", lambda e: self._salvar_dados())
        self.bind("<Control-l>", lambda e: self._carregar_dados())
        self.bind("<Control-e>", lambda e: self._exportar_pdf())
        self.bind("<Control-g>", lambda e: self.gerar_despacho())
        self.bind("<Control-c>", lambda e: self.copiar_para_clipboard())
        self.bind("<Control-h>", lambda e: self._mostrar_historico())
        self.bind("<Control-m>", lambda e: self._gerenciar_modelos())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<F11>", lambda e: self._toggle_theme())

    def _build_ui(self):
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color=get_color("background", "dark" if self.is_dark_mode else "light"))
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        # Título minimalista
        title = ctk.CTkLabel(self.main_frame, text="Gerador SEI", font=ctk.CTkFont(size=18, weight="bold"), text_color=get_color("text_primary", "dark" if self.is_dark_mode else "light"))
        title.pack(pady=(0, 15))

        # Botão tema no canto superior direito
        self.theme_btn = ctk.CTkButton(self.main_frame, text="☀️" if self.is_dark_mode else "🌙", width=40, height=30, command=self._toggle_theme, fg_color="transparent", border_width=1, border_color=get_color("border", "dark" if self.is_dark_mode else "light"))
        self.theme_btn.pack(anchor=ctk.NE, pady=(0, 10))

        self._build_form()

        # Separador sutil
        sep = ctk.CTkFrame(self.main_frame, height=1, fg_color=get_color("border", "dark" if self.is_dark_mode else "light"))
        sep.pack(fill="x", pady=15)

        self._build_output()

        # Status discreto
        self.status_label = ctk.CTkLabel(self.main_frame, text="Pronto", text_color=get_color("text_secondary", "dark" if self.is_dark_mode else "light"), font=ctk.CTkFont(size=11))
        self.status_label.pack(fill="x", padx=10, pady=(10, 0))

    def _build_form(self):
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", border_width=1, border_color=get_color("border", "dark" if self.is_dark_mode else "light"), corner_radius=8)
        self.form_frame.pack(fill="x", padx=10, pady=5)

        fields = [
            ("Ofício", "778/2026"),
            ("SEI Ofício", "198654234"),
            ("SEI Manifestação", "220622554"),
            ("Protocolo OUV", "OUV-078543/2026"),
            ("Resumo", "Falta de vagas de castração"),
            ("Prazo", "27/03/2026")
        ]

        self.inputs = {}
        self.field_vars = {}

        for idx, (label_text, placeholder) in enumerate(fields):
            # Label compacto
            label = ctk.CTkLabel(self.form_frame, text=label_text, font=ctk.CTkFont(size=11), text_color=get_color("text_secondary", "dark" if self.is_dark_mode else "light"))
            label.grid(row=idx, column=0, sticky="w", padx=10, pady=4)

            # Input
            if idx == 5:
                var = tk.StringVar(value=placeholder)
                entry = DateEntry(self.form_frame, width=18, date_pattern="dd/mm/yyyy", font=("Arial", 10))
                entry.set_date(placeholder)
            else:
                var = tk.StringVar(value="")
                entry = ctk.CTkEntry(self.form_frame, width=400, placeholder_text=placeholder, font=ctk.CTkFont(size=11), height=28)
            entry.grid(row=idx, column=1, padx=10, pady=4, sticky="ew")
            self.form_frame.grid_columnconfigure(1, weight=1)
            self.inputs[idx] = entry
            self.field_vars[idx] = var
            entry.bind("<KeyRelease>", self._validate_live)
            entry.bind("<FocusOut>", self._validate_live)
            Tooltip(entry, f"{label_text}.")

        # Modelo
        ctk.CTkLabel(self.form_frame, text="Modelo", font=ctk.CTkFont(size=11), text_color=get_color("text_secondary", "dark" if self.is_dark_mode else "light")).grid(row=6, column=0, sticky="w", padx=10, pady=6)
        self.template_var = tk.StringVar(value="HVeP - Atendimento/HVeP")
        self.model_select = ctk.CTkComboBox(self.form_frame, values=list(self.modelos.keys()), variable=self.template_var, state="readonly", width=400, height=28, font=ctk.CTkFont(size=11))
        self.model_select.grid(row=6, column=1, padx=10, pady=6, sticky="ew")
        self.model_select.bind("<<ComboboxSelected>>", self._on_template_selected)
        Tooltip(self.model_select, "Selecionar modelo.")

        # Botões compactos
        buttons_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        buttons_frame.grid(row=7, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        actions = [
            ("Gerar", self.gerar_despacho),
            ("Salvar", self._salvar_dados),
            ("Carregar", self._carregar_dados),
            ("PDF", self._exportar_pdf),
            ("Copiar", self.copiar_para_clipboard),
            ("Histórico", self._mostrar_historico),
            ("Modelos", self._gerenciar_modelos)
        ]

        for i, (text, cmd) in enumerate(actions):
            btn = ctk.CTkButton(buttons_frame, text=text, command=cmd, width=70, height=28, font=ctk.CTkFont(size=10))
            btn.grid(row=0, column=i, padx=3, pady=2, sticky="ew")
            buttons_frame.grid_columnconfigure(i, weight=1)
            Tooltip(btn, f"{text}.")

    def _build_output(self):
        self.output_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", border_width=1, border_color=get_color("border", "dark" if self.is_dark_mode else "light"), corner_radius=8)
        self.output_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Label sutil
        label = ctk.CTkLabel(self.output_frame, text="Saída", font=ctk.CTkFont(size=12, weight="bold"), text_color=get_color("text_primary", "dark" if self.is_dark_mode else "light"))
        label.pack(anchor="w", padx=10, pady=(8, 4))

        self.text_saida = ctk.CTkTextbox(
            self.output_frame,
            wrap="word",
            font=ctk.CTkFont(family="Courier", size=11),
            corner_radius=6,
            border_width=0,
            fg_color=get_color("background", "dark" if self.is_dark_mode else "light"),
            text_color=get_color("text_primary", "dark" if self.is_dark_mode else "light")
        )
        self.text_saida.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._atualizar_text_saida("Texto gerado aparecerá aqui.")

    def _atualizar_text_saida(self, texto):
        self.text_saida.configure(state="normal")
        self.text_saida.delete("1.0", ctk.END)
        self.text_saida.insert("1.0", texto)
        self.text_saida.configure(state="disabled")

    def _validate_live(self, event=None):
        erros = self._validar_campos(silent=True)
        if erros:
            self.status_label.configure(text=f"{len(erros)} problemas no formulário", text_color=get_color("warning", "dark" if self.is_dark_mode else "light"))
        else:
            self.status_label.configure(text="Todos os campos válidos", text_color=get_color("success", "dark" if self.is_dark_mode else "light"))

    def _validar_campos(self, silent=False):
        erros = []
        num_oficio = self.inputs[0].get().strip()
        sei_oficio = self.inputs[1].get().strip()
        sei_manifestacao = self.inputs[2].get().strip()
        protocolo_ouv = self.inputs[3].get().strip()
        assunto_resumido = self.inputs[4].get().strip()
        prazo = self.inputs[5].get().strip()

        if not num_oficio:
            erros.append("Número do Ofício é obrigatório.")
        if not validar_sei(sei_oficio):
            erros.append("Número SEI do Ofício deve ser numérico ou no formato #{numero|id}#.")
        if not validar_sei(sei_manifestacao):
            erros.append("Número SEI da Manifestação deve ser numérico ou no formato #{numero|id}#.")
        if not protocolo_ouv or not protocolo_ouv.startswith("OUV-"):
            erros.append("Protocolo OUV deve começar com 'OUV-'.")
        if not assunto_resumido:
            erros.append("Resumo da demanda é obrigatório.")
        try:
            data = datetime.datetime.strptime(prazo, "%d/%m/%Y").date()
            hoje = datetime.date.today()
            if data < hoje:
                erros.append("Prazo não pode ser no passado.")
        except ValueError:
            erros.append("Formato de data inválido (use dd/mm/yyyy).")

        if not silent and erros:
            messagebox.showerror("Erros de Validação", "\n".join(erros))

        return erros

    def gerar_despacho(self):
        erros = self._validar_campos()
        if erros:
            self.status_label.configure(text="Corrija os erros antes de gerar.", text_color=get_color("error", "dark" if self.is_dark_mode else "light"))
            return

        num_oficio = self.inputs[0].get().strip()
        sei_oficio = formatar_sei_link(self.inputs[1].get().strip())
        sei_manifestacao = formatar_sei_link(self.inputs[2].get().strip())
        protocolo_ouv = self.inputs[3].get().strip()
        assunto_resumido = self.inputs[4].get().strip()
        prazo_formatado = formatar_prazo(self.inputs[5].get().strip())

        modelo = self.modelos.get(self.template_var.get(), modelo_hvep)
        corpo = modelo(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo_formatado)
        texto_final = PREFIXO_DOCUMENTO + corpo.strip()

        self._atualizar_text_saida(texto_final)

        self.historico.append(texto_final)
        if len(self.historico) > 20:
            self.historico.pop(0)

        self.status_label.configure(text="Despacho gerado com sucesso.", text_color=get_color("success", "dark" if self.is_dark_mode else "light"))

    def _on_template_selected(self, event=None):
        modelo = self.template_var.get()
        if modelo == "Demanda de Ouvidoria - Ausência de Cronograma Castração":
            self.inputs[4].delete(0, tk.END)
            self.inputs[4].insert(0, RESUMO_CRONOGRAMA)
            self.inputs[4].configure(state="disabled")
        else:
            self.inputs[4].configure(state="normal")

    def _salvar_dados(self):
        valores = {f"campo_{i}": self.inputs[i].get().strip() for i in range(6)}
        valores["modelo"] = self.template_var.get()
        try:
            with open(self.dados_file, "w", encoding="utf-8") as f:
                json.dump(valores, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")

    def _carregar_dados(self):
        if not os.path.exists(self.dados_file):
            messagebox.showwarning("Aviso", "Nenhum dado salvo encontrado.")
            return
        try:
            with open(self.dados_file, "r", encoding="utf-8") as f:
                valores = json.load(f)
            for i in range(6):
                self.inputs[i].delete(0, tk.END)
                self.inputs[i].insert(0, valores.get(f"campo_{i}", ""))
            self.template_var.set(valores.get("modelo", "HVeP - Atendimento/HVeP"))
            self._on_template_selected()
            messagebox.showinfo("Sucesso", "Dados carregados com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

    def _exportar_pdf(self):
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto:
            messagebox.showwarning("Atenção", "Não há texto para exportar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            for line in texto.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
                else:
                    story.append(Spacer(1, 12))
            doc.build(story)
            messagebox.showinfo("Sucesso", f"PDF exportado para {file_path}.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {e}")

    def _mostrar_historico(self):
        if not self.historico:
            messagebox.showinfo("Histórico", "Nenhum despacho gerado ainda.")
            return
        hist_window = tk.Toplevel(self)
        hist_window.title("Histórico de Despachos")
        hist_window.geometry("600x400")

        listbox = tk.Listbox(hist_window, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for i, item in enumerate(self.historico[-20:]):
            listbox.insert(tk.END, f"{len(self.historico)-len(self.historico[-20:]) + i + 1}. {item[:60]}...")

        def carregar_selecionado():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                texto = self.historico[-20 + idx]
                self.text_saida.delete("1.0", ctk.END)
                self.text_saida.insert("1.0", texto)
                hist_window.destroy()

        ctk.CTkButton(hist_window, text="Carregar Selecionado", command=carregar_selecionado).pack(pady=8)

    def _gerenciar_modelos(self):
        manage_window = tk.Toplevel(self)
        manage_window.title("Gerenciar Modelos")
        manage_window.geometry("700x520")

        listbox = tk.Listbox(manage_window, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for modelo in self.modelos.keys():
            listbox.insert(tk.END, modelo)

        def adicionar():
            nome = tk.simpledialog.askstring("Novo Modelo", "Nome do modelo:")
            if nome and nome not in self.modelos:
                self.modelos[nome] = lambda *args: ""
                listbox.insert(tk.END, nome)
                self.model_select.configure(values=list(self.modelos.keys()))
                self._salvar_modelos_custom()

        def editar():
            sel = listbox.curselection()
            if not sel:
                return
            nome = listbox.get(sel[0])
            editar_modelo(nome)

        def deletar():
            sel = listbox.curselection()
            if not sel:
                return
            nome = listbox.get(sel[0])
            if nome in ["HVeP - Atendimento/HVeP", "Castração de Cães e Gatos", "Condições de exames e cirurgia HVeP", "Demanda de Ouvidoria - Ausência de Cronograma Castração"]:
                messagebox.showwarning("Aviso", "Não é possível deletar modelos padrão.")
                return
            del self.modelos[nome]
            listbox.delete(sel[0])
            self.model_select.configure(values=list(self.modelos.keys()))
            self._salvar_modelos_custom()

        def editar_modelo(nome):
            if nome not in self.modelos:
                return
            edit_window = tk.Toplevel(manage_window)
            edit_window.title(f"Editar Modelo: {nome}")
            edit_window.geometry("720x520")

            text_area = ctk.CTkTextbox(edit_window, wrap="word", font=ctk.CTkFont(family="Courier", size=12))
            text_area.pack(fill="both", expand=True, padx=10, pady=10)

            if callable(self.modelos[nome]):
                texto = self.modelos[nome]("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFEST", "PROTOCOLO", "ASSUNTO", "PRAZO")
            else:
                texto = self.modelos[nome]
            text_area.insert("1.0", texto)

            def salvar():
                novo_texto = text_area.get("1.0", ctk.END).strip()

                def modelo_func(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
                    return novo_texto.format(
                        num_oficio=num_oficio, sei_oficio=sei_oficio, sei_manifestacao=sei_manifestacao,
                        protocolo_ouv=protocolo_ouv, assunto_resumido=assunto_resumido, prazo=prazo
                    )

                self.modelos[nome] = modelo_func
                self.model_select.configure(values=list(self.modelos.keys()))
                self._salvar_modelos_custom()
                edit_window.destroy()

            ctk.CTkButton(edit_window, text="Salvar", command=salvar).pack(pady=8)

        action_frame = ctk.CTkFrame(manage_window)
        action_frame.pack(fill="x", pady=10)
        ctk.CTkButton(action_frame, text="➕ Adicionar", command=adicionar).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text="✏️ Editar", command=editar).pack(side="left", padx=4)
        ctk.CTkButton(action_frame, text="🗑️ Deletar", command=deletar).pack(side="left", padx=4)

    def copiar_para_clipboard(self):
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto:
            messagebox.showinfo("Erro", "Não há texto para copiar.")
            return
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.status_label.configure(text="Copiado para área de transferência.", text_color=get_color("success", "dark" if self.is_dark_mode else "light"))


if __name__ == "__main__":
    app = GeradorSEIApp()
    app.mainloop()
