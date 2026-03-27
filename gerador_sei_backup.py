import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import customtkinter as ctk

# Constantes
MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

# Largura da área de texto para centralização
TEXT_WIDTH = 90

# Prefixo fixo do documento
PREFIXO_DOCUMENTO = (
    "À Subsecretaria de Bem-estar Animal (Suban),\n\n" +
    "SUJEITO A PRAZO".center(TEXT_WIDTH) + "\n\n"
)

# Resumo fixo para o modelo de cronograma
RESUMO_CRONOGRAMA = (
    "atualização do cronograma e disponibilização de novas vagas para castração, "
    "tendo em vista o relato de desatualização das informações no portal oficial"
)


class Tooltip:
    """Classe simples para tooltips em widgets Tkinter."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def formatar_prazo(data_str):
    """
    Converte data no formato dd/mm/yyyy para '02 de março de 2026'.
    Retorna a string original se inválida.
    """
    try:
        data = datetime.datetime.strptime(data_str, "%d/%m/%Y")
    except ValueError:
        return data_str

    dia = data.day
    mes = MESES[data.month - 1]
    ano = data.year
    dia_str = "1º" if dia == 1 else str(dia)
    return f"{dia_str} de {mes} de {ano}"


class GeradorSEIApp:
    """
    Aplicação GUI para gerar despachos SEI com modelos pré-definidos.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Despacho SEI")
        self.root.geometry("1000x750")  # Aumentado para layout profissional
        self.is_dark_mode = True  # Valor padrão
        self.historico = []  # Lista de despachos gerados
        self.dados_file = "dados_ultimo.json"
        self.config_file = "config.json"
        self.modelos_file = "modelos_custom.json"
        self._carregar_config()
        ctk.set_appearance_mode("dark" if self.is_dark_mode else "light")  # Tema inicial
        ctk.set_default_color_theme("blue")  # Tema de cor
        self._carregar_modelos_custom()
        self.modelos = {
            "HVeP - Atendimento/HVeP": self._modelo_hvep,
            "Castração de Cães e Gatos": self._modelo_castracao,
            "Condições de exames e cirurgia HVeP": self._modelo_condicoes_hvep,
            "Demanda de Ouvidoria - Ausência de Cronograma Castração": self._modelo_cronograma_castracao
        }
        self._create_menu()
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface do usuário."""
        # Frame principal com scroll se necessário
        self.main_frame = ctk.CTkScrollableFrame(self.root)
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(self.main_frame, text="Gerador de Despacho SEI", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(0, 20))

        # Botão de toggle tema
        self.theme_btn = ctk.CTkButton(self.main_frame, text="🌙 Dark Mode" if self.is_dark_mode else "☀️ Light Mode", command=self._toggle_theme, width=120)
        self.theme_btn.pack(anchor=ctk.NE, pady=(0, 10))

        # Separador
        ctk.CTkFrame(self.main_frame, height=2).pack(fill=ctk.X, pady=(0, 20))

        # Container para inputs
        input_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        input_frame.pack(fill=ctk.X, pady=(0, 20))

        self.inputs = {}
        self._create_input_fields(input_frame)
        self._create_model_selector(input_frame)
        self._create_buttons(input_frame)

        # Separador
        ctk.CTkFrame(self.main_frame, height=2).pack(fill=ctk.X, pady=(0, 20))

        # Container para output
        output_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        output_frame.pack(fill=ctk.BOTH, expand=True, pady=(0, 20))

        self._create_output_area(output_frame)

    def _toggle_theme(self):
        """Alterna entre dark e light mode."""
        self.is_dark_mode = not self.is_dark_mode
        ctk.set_appearance_mode("dark" if self.is_dark_mode else "light")
        self.theme_btn.configure(text="🌙 Dark Mode" if self.is_dark_mode else "☀️ Light Mode")
        self._salvar_config()

    def _validar_campos(self):
        """Valida os campos de entrada e retorna lista de erros."""
        erros = []
        valores = [self.inputs[i].get().strip() for i in range(6)]
        num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo = valores

        if not num_oficio:
            erros.append("Número do Ofício é obrigatório.")
        if not sei_oficio.isdigit():
            erros.append("Número SEI do Ofício deve conter apenas números.")
        if not sei_manifestacao.isdigit():
            erros.append("Número SEI da Manifestação deve conter apenas números.")
        if not protocolo_ouv or not protocolo_ouv.startswith("OUV-"):
            erros.append("Protocolo OUV deve começar com 'OUV-'.")
        if not assunto_resumido:
            erros.append("Resumo da demanda é obrigatório.")
        try:
            data = datetime.datetime.strptime(prazo, "%d/%m/%Y")
            if data < datetime.datetime.now():
                erros.append("Prazo não pode ser no passado.")
        except ValueError:
            erros.append("Formato de data inválido (use dd/mm/yyyy).")

        return erros

    def _salvar_dados(self):
        """Salva os dados atuais em um arquivo JSON."""
        valores = {f"campo_{i}": self.inputs[i].get().strip() for i in range(6)}
        valores["modelo"] = self.template_var.get()
        try:
            with open(self.dados_file, "w", encoding="utf-8") as f:
                json.dump(valores, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Sucesso", "Dados salvos com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")

    def _carregar_dados(self):
        """Carrega dados de um arquivo JSON."""
        if not os.path.exists(self.dados_file):
            messagebox.showwarning("Aviso", "Nenhum dado salvo encontrado.")
            return
        try:
            with open(self.dados_file, "r", encoding="utf-8") as f:
                valores = json.load(f)
            for i in range(6):
                self.inputs[i].delete(0, tk.END)
                self.inputs[i].insert(0, valores.get(f"campo_{i}", ""))
            modelo = valores.get("modelo", "HVeP - Atendimento/HVeP")
            self.template_var.set(modelo)
            self._on_template_selected()
            messagebox.showinfo("Sucesso", "Dados carregados com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

    def _exportar_pdf(self):
        """Exporta o texto gerado para um arquivo PDF."""
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
                    p = Paragraph(line, styles["Normal"])
                    story.append(p)
                else:
                    story.append(Spacer(1, 12))
            doc.build(story)
            messagebox.showinfo("Sucesso", f"PDF exportado para {file_path}.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {e}")

    def _mostrar_historico(self):
        """Mostra uma janela com o histórico de despachos."""
        if not self.historico:
            messagebox.showinfo("Histórico", "Nenhum despacho gerado ainda.")
            return

        hist_window = tk.Toplevel(self.root)
        hist_window.title("Histórico de Despachos")
        hist_window.geometry("600x400")

        listbox = tk.Listbox(hist_window, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, item in enumerate(self.historico[-10:]):  # Últimos 10
            listbox.insert(tk.END, f"{i+1}. {item[:50]}...")

        def carregar_selecionado():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                texto = self.historico[-10 + idx]
                self.text_saida.delete("1.0", ctk.END)
                self.text_saida.insert("1.0", texto)
                hist_window.destroy()

        btn_carregar = ctk.CTkButton(hist_window, text="Carregar Selecionado", command=carregar_selecionado)
        btn_carregar.pack(pady=5)

    def _salvar_config(self):
        """Salva configurações (tema) em JSON."""
        config = {"dark_mode": self.is_dark_mode}
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
        except:
            pass  # Ignorar erros de salvamento de config

    def _carregar_config(self):
        """Carrega configurações de JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                self.is_dark_mode = config.get("dark_mode", True)
            except:
                pass

    def _carregar_modelos_custom(self):
        """Carrega modelos customizados de JSON."""
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except:
                pass

    def _salvar_modelos_custom(self):
        """Salva modelos customizados em JSON."""
        custom = {k: v for k, v in self.modelos.items() if k not in [
            "HVeP - Atendimento/HVeP", "Castração de Cães e Gatos",
            "Condições de exames e cirurgia HVeP", "Demanda de Ouvidoria - Ausência de Cronograma Castração"
        ]}
        try:
            with open(self.modelos_file, "w", encoding="utf-8") as f:
                json.dump(custom, f, ensure_ascii=False, indent=4)
        except:
            pass

    def _gerenciar_modelos(self):
        """Abre janela para gerenciar modelos."""
        manage_window = tk.Toplevel(self.root)
        manage_window.title("Gerenciar Modelos")
        manage_window.geometry("600x500")

        listbox = tk.Listbox(manage_window, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for modelo in self.modelos.keys():
            listbox.insert(tk.END, modelo)

        button_frame = ctk.CTkFrame(manage_window)
        button_frame.pack(fill=ctk.X, pady=10)

        def adicionar():
            nome = tk.simpledialog.askstring("Novo Modelo", "Nome do modelo:")
            if nome and nome not in self.modelos:
                self.modelos[nome] = lambda *args: ""  # Placeholder
                listbox.insert(tk.END, nome)
                editar_modelo(nome)
                self._salvar_modelos_custom()
                # Atualizar combobox
                self.combo_modelos['values'] = list(self.modelos.keys())

        def editar():
            selection = listbox.curselection()
            if selection:
                nome = listbox.get(selection[0])
                editar_modelo(nome)

        def deletar():
            selection = listbox.curselection()
            if selection:
                nome = listbox.get(selection[0])
                if nome in ["HVeP - Atendimento/HVeP", "Castração de Cães e Gatos",
                            "Condições de exames e cirurgia HVeP", "Demanda de Ouvidoria - Ausência de Cronograma Castração"]:
                    messagebox.showwarning("Aviso", "Não é possível deletar modelos padrão.")
                    return
                del self.modelos[nome]
                listbox.delete(selection[0])
                self._salvar_modelos_custom()
                # Atualizar combobox
                self.combo_modelos['values'] = list(self.modelos.keys())

        def editar_modelo(nome):
            edit_window = tk.Toplevel(manage_window)
            edit_window.title(f"Editar Modelo: {nome}")
            edit_window.geometry("700x500")

            text_area = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, font=("Courier", 10))
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Carregar texto atual se for função
            if callable(self.modelos[nome]):
                # Para modelos padrão, mostrar exemplo ou placeholder
                if nome == "HVeP - Atendimento/HVeP":
                    texto = self._modelo_hvep("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFEST", "PROTOCOLO", "ASSUNTO", "PRAZO")
                elif nome == "Castração de Cães e Gatos":
                    texto = self._modelo_castracao("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFEST", "PROTOCOLO", "ASSUNTO", "PRAZO")
                elif nome == "Condições de exames e cirurgia HVeP":
                    texto = self._modelo_condicoes_hvep("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFEST", "PROTOCOLO", "ASSUNTO", "PRAZO")
                elif nome == "Demanda de Ouvidoria - Ausência de Cronograma Castração":
                    texto = self._modelo_cronograma_castracao("NUM_OFICIO", "SEI_OFICIO", "SEI_MANIFEST", "PROTOCOLO", "ASSUNTO", "PRAZO")
                else:
                    texto = ""  # Para custom
                text_area.insert(tk.END, texto)
            else:
                text_area.insert(tk.END, self.modelos[nome])

            def salvar():
                novo_texto = text_area.get("1.0", tk.END).strip()
                # Criar função lambda que substitui placeholders
                def modelo_func(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
                    return novo_texto.format(
                        num_oficio=num_oficio, sei_oficio=sei_oficio, sei_manifestacao=sei_manifestacao,
                        protocolo_ouv=protocolo_ouv, assunto_resumido=assunto_resumido, prazo=prazo
                    )
                self.modelos[nome] = modelo_func
                self._salvar_modelos_custom()
                # Atualizar combobox
                self.combo_modelos['values'] = list(self.modelos.keys())
                edit_window.destroy()

            ttk.Button(edit_window, text="Salvar", command=salvar).pack(pady=5)

        ttk.Button(button_frame, text="➕ Adicionar", command=adicionar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✏️ Editar", command=editar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Deletar", command=deletar).pack(side=tk.LEFT, padx=5)
    def _create_menu(self):
        """Cria o menu da aplicação."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Salvar Dados", command=self._salvar_dados, accelerator="Ctrl+S")
        file_menu.add_command(label="Carregar Dados", command=self._carregar_dados, accelerator="Ctrl+L")
        file_menu.add_command(label="Exportar PDF", command=self._exportar_pdf, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        # Menu Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Gerar Despacho", command=self.gerar_despacho, accelerator="Ctrl+G")
        edit_menu.add_command(label="Copiar para Clipboard", command=self.copiar_para_clipboard, accelerator="Ctrl+C")
        edit_menu.add_command(label="Histórico", command=self._mostrar_historico, accelerator="Ctrl+H")
        edit_menu.add_command(label="Gerenciar Modelos", command=self._gerenciar_modelos, accelerator="Ctrl+M")

        # Menu Tema
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tema", menu=theme_menu)
        theme_menu.add_command(label="Alternar Tema", command=self._toggle_theme, accelerator="F11")

        # Bind atalhos
        self.root.bind("<Control-s>", lambda e: self._salvar_dados())
        self.root.bind("<Control-l>", lambda e: self._carregar_dados())
        self.root.bind("<Control-e>", lambda e: self._exportar_pdf())
        self.root.bind("<Control-g>", lambda e: self.gerar_despacho())
        self.root.bind("<Control-c>", lambda e: self.copiar_para_clipboard())
        self.root.bind("<Control-h>", lambda e: self._mostrar_historico())
        self.root.bind("<Control-m>", lambda e: self._gerenciar_modelos())
        self.root.bind("<F11>", lambda e: self._toggle_theme())
    def _build_ui(self):
        """Constrói a interface do usuário."""
        self.frame = ttk.Frame(self.root, padding=20, style="TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(self.frame, text="Gerador de Despacho SEI", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Botão de toggle tema
        self.theme_btn = ttk.Button(self.frame, text="🌙 Dark Mode", command=self._toggle_theme)
        self.theme_btn.pack(anchor=tk.NE, pady=(0, 10))

        # Container para inputs
        self.input_frame = ttk.Frame(self.frame, padding=10, relief="raised", borderwidth=2)
        self.input_frame.pack(fill=tk.X, pady=(0, 20))

        self.inputs = {}
        self._create_input_fields(self.input_frame)
        self._create_model_selector(self.input_frame)
        self._create_buttons(self.input_frame)
        # Container para output
        output_frame = ttk.Frame(self.frame, padding=10, relief="raised", borderwidth=2)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 20))

        self._create_output_area(output_frame)
        self._apply_theme()  # Aplicar tema inicial

    def _create_input_fields(self, parent):
        """Cria os campos de entrada."""
        labels = [
            "Número do Ofício (ex: 778/2026)",
            "Número SEI do Ofício (apenas números)",
            "Número SEI da Manifestação (ícone vermelho)",
            "Protocolo OUV (ex: OUV-078543/2026)",
            "Resumo da demanda (ex: falta de vagas de castração)",
            "Prazo de resposta (selecione data)"
        ]
        tooltips = [
            "Número completo do ofício, incluindo ano.",
            "Código SEI numérico do ofício.",
            "Código SEI numérico da manifestação.",
            "Protocolo no formato OUV-XXXXXX/YYYY.",
            "Descrição breve da demanda.",
            "Data limite para resposta."
        ]

        for i, (label_text, tooltip_text) in enumerate(zip(labels, tooltips)):
            label = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12))
            label.grid(row=i, column=0, sticky=ctk.W, pady=8, padx=10)
            Tooltip(label, tooltip_text)
            if i == 5:  # Campo de data
                entry = DateEntry(parent, width=18, date_pattern="dd/mm/yyyy")
            else:
                entry = ctk.CTkEntry(parent, width=400, font=ctk.CTkFont(size=12))
            entry.grid(row=i, column=1, sticky=ctk.W, pady=8, padx=10)
            self.inputs[i] = entry

        self.resumo_entry = self.inputs[4]

    def _create_model_selector(self, parent):
        """Cria o seletor de modelos."""
        ctk.CTkLabel(parent, text="Modelo de texto", font=ctk.CTkFont(size=12)).grid(row=6, column=0, sticky=ctk.W, pady=8, padx=10)
        self.template_var = tk.StringVar(value="HVeP - Atendimento/HVeP")
        self.combo_modelos = ctk.CTkComboBox(
            parent, variable=self.template_var,
            values=list(self.modelos.keys()), state="readonly", width=400, font=ctk.CTkFont(size=12)
        )
        self.combo_modelos.grid(row=6, column=1, sticky=ctk.W, pady=8, padx=10)
        self.combo_modelos.bind("<<ComboboxSelected>>", self._on_template_selected)

    def _create_buttons(self, parent):
        """Cria os botões de ação."""
        ctk.CTkButton(parent, text="📝 Gerar Despacho", command=self.gerar_despacho, font=ctk.CTkFont(size=12)).grid(row=7, column=0, pady=10, padx=10, sticky=ctk.W)
        ctk.CTkButton(parent, text="💾 Salvar Dados", command=self._salvar_dados, font=ctk.CTkFont(size=12)).grid(row=7, column=1, pady=10, padx=10, sticky=ctk.W)
        ctk.CTkButton(parent, text="📂 Carregar Dados", command=self._carregar_dados, font=ctk.CTkFont(size=12)).grid(row=8, column=0, pady=10, padx=10, sticky=ctk.W)
        ctk.CTkButton(parent, text="📄 Exportar PDF", command=self._exportar_pdf, font=ctk.CTkFont(size=12)).grid(row=8, column=1, pady=10, padx=10, sticky=ctk.W)
        ctk.CTkButton(parent, text="📋 Copiar para Clipboard", command=self.copiar_para_clipboard, font=ctk.CTkFont(size=12)).grid(row=9, column=0, pady=10, padx=10, sticky=ctk.W)
        ctk.CTkButton(parent, text="📜 Histórico", command=self._mostrar_historico, font=ctk.CTkFont(size=12)).grid(row=9, column=1, pady=10, padx=10, sticky=ctk.W)

    def _create_output_area(self, parent):
        """Cria a área de saída de texto."""
        self.text_saida = ctk.CTkTextbox(parent, width=800, height=300, wrap="word", font=ctk.CTkFont(family="Courier", size=12))
        self.text_saida.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

    def gerar_despacho(self):
        """Gera o texto do despacho baseado nos inputs."""
        erros = self._validar_campos()
        if erros:
            messagebox.showerror("Erros de Validação", "\n".join(erros))
            return

        valores = [self.inputs[i].get().strip() for i in range(6)]
        num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo = valores
        prazo_formatado = formatar_prazo(prazo)

        modelo = self.modelos.get(self.template_var.get(), self._modelo_hvep)
        corpo = modelo(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo_formatado)

        texto_final = PREFIXO_DOCUMENTO + corpo.strip()
        self.text_saida.delete("1.0", ctk.END)
        self.text_saida.insert("1.0", texto_final)

        # Adicionar ao histórico
        self.historico.append(texto_final)
        if len(self.historico) > 20:  # Limitar a 20 entradas
            self.historico.pop(0)

    def _on_template_selected(self, event=None):
        """Manipula mudança de modelo, bloqueando resumo se necessário."""
        modelo = self.template_var.get()
        if modelo == "Demanda de Ouvidoria - Ausência de Cronograma Castração":
            self.resumo_entry.delete(0, tk.END)
            self.resumo_entry.insert(0, RESUMO_CRONOGRAMA)
            self.resumo_entry.config(state="disabled")
        else:
            self.resumo_entry.config(state="normal")

    def _modelo_hvep(self, num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
        return f"""
Trata-se do Ofício nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal encaminha a denúncia contida na Manifestação - Reclamação {sei_manifestacao} (SEI nº {sei_oficio}), oriundo do Sistema de Ouvidoria - OUV-DF, para conhecimento e providências cabíveis. A Reclamação da solicitante, em síntese, versa sobre {assunto_resumido}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a esta Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""

    def _modelo_castracao(self, num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
        return f"""
Trata-se do Ofício {num_oficio} ({sei_oficio}) encaminhado pela Ouvidoria da Casa Civil do Distrito Federal, por meio do qual se solicita análise e manifestação acerca da demanda registrada na Ouvidoria do Governo do Distrito Federal, sob o Protocolo {protocolo_ouv} ({sei_manifestacao}).

A demanda refere-se a reclamação apresentada por cidadão que relata {assunto_resumido}.

Encaminho os autos para conhecimento, análise e adoção das providências cabíveis, observando-se que o prazo para resposta a esta Secretaria Executiva é, impreterivelmente, até {prazo}, nos termos do art. 5º da Lei nº 4.896, de 31 de julho de 2012.
"""

    def _modelo_condicoes_hvep(self, num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
        return f"""
Trata-se do Ofício nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto às {assunto_resumido}, conforme especifica na Manifestação ({sei_manifestacao}), referente ao Protocolo: {protocolo_ouv}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""

    def _modelo_cronograma_castracao(self, num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
        return f"""
Trata-se do Ofício Nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto à atualização do cronograma e disponibilização de novas vagas para castração, tendo em vista o relato de desatualização das informações no portal oficial, conforme especifica na Manifestação ({sei_manifestacao}), referente ao Protocolo: {protocolo_ouv}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""

    def copiar_para_clipboard(self):
        """Copia o texto gerado para a área de transferência."""
        texto = self.text_saida.get("1.0", ctk.END).strip()
        if not texto:
            messagebox.showinfo("Erro", "Não há texto para copiar.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        messagebox.showinfo("Sucesso", "Texto copiado para a área de transferência.")


if __name__ == "__main__":
    root = ctk.CTk()
    app = GeradorSEIApp(root)
    root.mainloop()