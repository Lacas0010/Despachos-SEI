﻿"""
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
from PIL import Image
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
        
        self.historico = []
        
        import queue
        self.task_queue = queue.Queue()
        self._process_queue()
        
        from concurrent.futures import ThreadPoolExecutor
        self.ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AI_Worker")
        
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=get_color_tuple("surface"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        
        ctk.CTkLabel(header, text="Gerador de Despacho SEI (IA)", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20)
        
        self.theme_btn = ctk.CTkButton(header, text="☀️" if self.theme_manager.is_dark else "🌙", width=40, command=self._toggle_theme, fg_color="transparent", border_width=1)
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

    def _build_chat_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=12)
        frame.grid(row=0, column=col, sticky="nsew", padx=(0, 10))
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text="🤖 Assistente de IA", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", pady=(10, 10), padx=10)
        
        ctk.CTkButton(frame, text="📁 Analisar Processo (Pasta)", command=self._on_analisar_pasta, height=40, font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.chat_history = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=13), wrap="word", state="disabled")
        self.chat_history.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
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
        ctk.CTkLabel(header, text="📝 Resultado", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        self.text_saida = ctk.CTkTextbox(frame, font=ctk.CTkFont(size=14, family="Consolas"), wrap="word")
        self.text_saida.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.text_saida.insert("1.0", "O documento gerado aparecerá aqui...")
        
        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.status_label = ctk.CTkLabel(footer, text="Pronto.", text_color=get_color_tuple("success"))
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(footer, mode="indeterminate", width=200)
        self.progress_bar.set(0)
        
        ctk.CTkButton(footer, text="📋 Copiar e Limpar", command=self._on_copiar_limpar, height=35).pack(side="right")
        ctk.CTkButton(footer, text="📄 PDF", command=self._on_pdf, height=35, fg_color="transparent", border_width=1).pack(side="right", padx=10)

    def _build_historico(self, parent, col):
        frame = ctk.CTkFrame(parent, fg_color=get_color_tuple("surface"), corner_radius=12)
        frame.grid(row=0, column=col, sticky="nsew", padx=(10, 0))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        ctk.CTkLabel(header, text="📚 Histórico", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Alimentar IA", command=self._on_alimentar_ia, width=100, height=28, fg_color=get_color_tuple("secondary")).pack(side="right")
        
        self.historico_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.historico_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _show_progress(self, mode="indeterminate"):
        self.progress_bar.configure(mode=mode)
        self.progress_bar.pack(side="left", padx=15)
        if mode == "indeterminate":
            self.progress_bar.start()

    def _hide_progress(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def _add_to_chat(self, role, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, f"{role}: {text}\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see(tk.END)

    def _on_stream_update(self, full_text):
        def update():
            output_text = full_text.strip()
            if output_text:
                self.text_saida.delete("1.0", tk.END)
                self.text_saida.insert("1.0", output_text)
                self.text_saida.see(tk.END)
        self.schedule_task(update)

    def _on_enviar_chat(self):
        msg = self.chat_input.get().strip()
        if not msg: return
        
        self.chat_input.delete(0, tk.END)
        self._add_to_chat("Você", msg)
        
        texto_atual = self.text_saida.get("1.0", tk.END).strip()
        if not texto_atual or texto_atual == "O despacho gerado aparecerá aqui...":
            self._add_to_chat("IA", "Por favor, primeiro analise um processo (ZIP) para termos um texto base.")
            return
            
        self.status_label.configure(text="IA pensando...", text_color=get_color_tuple("warning"))
        self._show_progress()
        self.ai_executor.submit(self._process_chat, msg, texto_atual)

    def _process_chat(self, msg, texto_atual):
        res = self.engine.refinar_texto_com_ia(texto_atual, msg, stream_callback=self._on_stream_update)
        self.schedule_task(lambda: self._apply_chat_result(res))
        
    def _apply_chat_result(self, res):
        self._hide_progress()
        if res.get("sucesso"):
            novo_texto = res.get("texto_gerado", "")
            self.text_saida.delete("1.0", tk.END)
            self.text_saida.insert("1.0", novo_texto)
            self._add_to_chat("IA", "Texto atualizado conforme sua solicitação!")
            self.status_label.configure(text="Texto refinado!", text_color=get_color_tuple("success"))
            
            self.historico.append({
                "resumo": "Texto refinado via chat", 
                "texto": novo_texto, 
                "data": datetime.datetime.now().strftime("%d/%m %H:%M")
            })
            self._refresh_historico()
        else:
            self._show_message("Erro IA", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha no chat", text_color=get_color_tuple("error"))

    def _refresh_historico(self):
        for widget in self.historico_scroll.winfo_children():
            widget.destroy()
            
        for item in reversed(self.historico[-10:]):
            card = ctk.CTkFrame(self.historico_scroll, corner_radius=8, border_width=1)
            card.pack(fill="x", pady=5)
            
            resumo = item.get("resumo", "Documento Gerado")
            if len(resumo) > 40: resumo = resumo[:37] + "..."
            ctk.CTkLabel(card, text=resumo, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(card, text=f"{item['data']}", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=10)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(btn_frame, text="Reutilizar", height=24, width=80, command=lambda i=item: self._reutilizar_dados(i)).pack(side="left")

    def _reutilizar_dados(self, item):
        dados = item if isinstance(item, dict) else {"texto": item}
            
        if "texto" in dados:
            self.text_saida.delete("1.0", tk.END)
            self.text_saida.insert("1.0", dados["texto"])
            self._add_to_chat("Sistema", "Texto carregado do histórico.")

    def _on_analisar_pasta(self):
        path = filedialog.askdirectory(title="Selecione a pasta do processo")
        if not path: return
        self.status_label.configure(text="Analisando IA...", text_color=get_color_tuple("warning"))
        self._show_progress()
        self.ai_executor.submit(self._process_ia, path)

    def _process_ia(self, path):
        res = self.engine.processar_pasta_com_ia(path, stream_callback=self._on_stream_update)
        self.schedule_task(lambda: self._apply_ia_result(res))

    def _apply_ia_result(self, res):
        self._hide_progress()
        if res.get("sucesso"):
            tipo_doc = res.get("tipo_documento", "Documento")
            if "texto_gerado" in res:
                self.text_saida.delete("1.0", tk.END)
                self.text_saida.insert("1.0", res["texto_gerado"])
                self._add_to_chat("Sistema", f"[{tipo_doc}] gerado com sucesso a partir da análise do processo.")
            self.status_label.configure(text="Análise concluída!", text_color=get_color_tuple("success"))
            
            self.historico.append({
                "resumo": f"[{tipo_doc}] {res.get('resumo', 'Arquivo analisado pela IA')}", 
                "texto": res.get("texto_gerado", ""), 
                "data": datetime.datetime.now().strftime("%d/%m %H:%M")
            })
            self._refresh_historico()
        else:
            self._show_message("Erro IA", res.get("erro", "Erro desconhecido"), "error")
            self.status_label.configure(text="Falha IA", text_color=get_color_tuple("error"))

    def _on_alimentar_ia(self):
        from tkinter import messagebox
        messagebox.showinfo("Treinar IA", "Selecione a pasta principal.\n\nCada subpasta dentro dela será reconhecida pela IA como um processo diferente.")
        path = filedialog.askdirectory(title="Selecione a pasta principal com os processos")
        if not path: return
        self.status_label.configure(text="Alimentando IA...", text_color=get_color_tuple("warning"))
        self._show_progress("determinate")
        self.progress_bar.set(0)
        self.ai_executor.submit(self._process_alimentar_ia, path)

    def _process_alimentar_ia(self, path):
        def cb(cur, tot, f):
            self.schedule_task(lambda: self.status_label.configure(text=f"Lendo {cur}/{tot}: {f}"))
            self.schedule_task(lambda: self.progress_bar.set(cur / tot if tot > 0 else 0))
        suc, err = self.engine.alimentar_banco_ia_por_pastas(path, cb)
        self.schedule_task(lambda: self._show_message("IA Alimentada", f"Processos aprendidos: {suc}\nErros: {err}", "success" if suc > 0 else "error"))
        self.schedule_task(lambda: self.status_label.configure(text="IA Atualizada!", text_color=get_color_tuple("success")))
        self.schedule_task(lambda: self._hide_progress())

    def _on_copiar_limpar(self):
        texto = self.text_saida.get("1.0", tk.END).strip()
        if texto and texto != "O despacho gerado aparecerá aqui...":
            self.clipboard_clear()
            self.clipboard_append(texto)
        self.text_saida.delete("1.0", tk.END)
        self.status_label.configure(text="Copiado e limpo!", text_color=get_color_tuple("success"))
        
        self.thinking_box.delete("1.0", tk.END)
        self.thinking_box.insert("1.0", "Raciocínio da IA (Deep Thinking) aparecerá aqui...")
        
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
        self.theme_btn.configure(text="☀️" if self.theme_manager.is_dark else "🌙")
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
    app = GeradorSEIApp()
    app.mainloop()
