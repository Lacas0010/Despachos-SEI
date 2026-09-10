import html
import re
import ctypes
from typing import Any, Optional, Dict, List
import tkinter as tk
import customtkinter as ctk
from theme_config import get_color_tuple, get_font, configure_appearance

def get_color(key: str, mode: str = "light") -> str:
    """Retorna cor do tema acessível usando theme_config."""
    color_tuple = get_color_tuple(key)
    return color_tuple[1] if mode.lower() == "dark" else color_tuple[0]

def configure_theme():
    """Configura o tema de aparência no CustomTkinter."""
    current = "dark" if ctk.get_appearance_mode().lower() == "dark" else "light"
    configure_appearance(current == "dark")
    return current

def setup_markdown_tags(text_widget: Any, is_dark: bool = True, base_size: int = 14):
    """Configura todas as tags de estilo e markdown no widget de texto."""
    target = getattr(text_widget, "_textbox", text_widget)
    try:
        target.tag_config("md_h1", font=get_font(base_size + 4, "bold"), foreground="#3B82F6" if is_dark else "#1D4ED8", spacing1=8, spacing3=4)
        target.tag_config("md_h2", font=get_font(base_size + 2, "bold"), foreground="#60A5FA" if is_dark else "#2563EB", spacing1=6, spacing3=3)
        target.tag_config("md_h3", font=get_font(base_size + 1, "bold"), foreground="#93C5FD" if is_dark else "#1E40AF", spacing1=4, spacing3=2)
        target.tag_config("md_bold", font=get_font(base_size, "bold"), foreground="#F8FAFC" if is_dark else "#0F172A")
        target.tag_config("md_italic", font=get_font(base_size, "italic"))
        target.tag_config("md_bold_italic", font=get_font(base_size, "bold"))
        target.tag_config("md_code", font=get_font(base_size - 1, family="Consolas"), foreground="#F43F5E", background="#334155" if is_dark else "#F1F5F9")
        target.tag_config("md_bullet", font=get_font(base_size, "bold"), foreground="#6366F1" if is_dark else "#4F46E5")
        target.tag_config("md_quote", font=get_font(base_size, "italic"), foreground="#94A3B8" if is_dark else "#64748B")
        target.tag_config("md_divider", font=get_font(base_size - 2), foreground="#475569" if is_dark else "#CBD5E1")
        
        target.tag_config("sei_num", foreground="#EA580C", background="#FEF08A" if not is_dark else "#7C2D12", font=get_font(base_size, "bold"))
        target.tag_config("date_expr", foreground="#10B981" if is_dark else "#059669", underline=True)
        target.tag_config("alert_prazo", foreground="#EF4444" if is_dark else "#B91C1C", background="#450A0A" if is_dark else "#FEE2E2", font=get_font(base_size, "bold"))
        target.tag_config("keyword", foreground="#38BDF8" if is_dark else "#0284C7", font=get_font(base_size, "bold"))
        target.tag_config("role_user", foreground="#818CF8" if is_dark else "#4F46E5", font=get_font(base_size, "bold"))
        target.tag_config("role_ollama", foreground="#34D399" if is_dark else "#059669", font=get_font(base_size, "bold"))
        target.tag_config("role_system", foreground="#FBBF24" if is_dark else "#D97706", font=get_font(base_size, "bold"))
    except Exception:
        pass

def insert_markdown_text(text_widget: ctk.CTkTextbox, text: str, is_dark: bool = True, base_size: int = 14):
    """
    Insere texto com formatação Markdown visual (negrito, itálico, títulos, códigos, listas, tags SEI)
    removendo a marcação crua (como ** ou *) e aplicando os estilos nativos do Tkinter.
    """
    setup_markdown_tags(text_widget, is_dark=is_dark, base_size=base_size)
    
    lines = text.split("\n")
    
    pattern = re.compile(
        r'(?P<bold_italic>\*\*\*[^*]+\*\*\*|___[^_]+___)|'
        r'(?P<bold>\*\*[^*]+\*\*|__[^_]+__)|'
        r'(?P<italic>\*[^*]+\*|_[^_]+_)|'
        r'(?P<code>`[^`]+`)|'
        r'(?P<alert>\b(SUJEITO A PRAZO|EXPIRADO|TEMPESTIVO|NÃO CONFORME|URGENTE|ATENDIMENTO INTEGRAL|ATENDIMENTO PARCIAL|NÃO ATENDIDO)\b)|'
        r'(?P<keyword>\b(MINUTA|Despacho|Ao Gabinete|RESUMO EXECUTIVO|IDENTIFICAÇÃO DO PROCESSO|OBJETO DA DEMANDA|HISTÓRICO E TRAMITAÇÃO|PONTOS TÉCNICOS|SITUAÇÃO ATUAL|LINHA DO TEMPO|RELATÓRIO DE AUDITORIA|CHECKLIST)\b)|'
        r'(?P<sei_num>\b\d{6,}\b)|'
        r'(?P<date>\b\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4}\b)'
    )
    
    for line_idx, line in enumerate(lines):
        raw_line = line
        
        # Divisores (ex: === ou ---)
        if re.match(r'^[=\-]{5,}$', raw_line.strip()):
            text_widget.insert(tk.END, "─" * 45 + "\n", ("md_divider",))
            continue
            
        # Título H1 (# Título)
        if raw_line.startswith("# "):
            text_widget.insert(tk.END, raw_line[2:].strip() + "\n", ("md_h1",))
            continue
        # Título H2 (## Subtítulo)
        elif raw_line.startswith("## "):
            text_widget.insert(tk.END, raw_line[3:].strip() + "\n", ("md_h2",))
            continue
        # Título H3 (### Tópico)
        elif raw_line.startswith("### "):
            text_widget.insert(tk.END, raw_line[4:].strip() + "\n", ("md_h3",))
            continue
            
        # Lista com marcador
        if raw_line.strip().startswith(('• ', '- ', '* ')):
            text_widget.insert(tk.END, "  • ", ("md_bullet",))
            line_to_parse = re.sub(r'^\s*[•\-\*]\s*', '', raw_line)
        elif raw_line.startswith("> "):
            text_widget.insert(tk.END, "┃ ", ("md_quote",))
            line_to_parse = raw_line[2:]
        else:
            line_to_parse = raw_line
            
        # Parse inline tokens
        last_idx = 0
        for match in pattern.finditer(line_to_parse):
            start, end = match.span()
            if start > last_idx:
                text_widget.insert(tk.END, line_to_parse[last_idx:start])
                
            kind = match.lastgroup
            content = match.group()
            
            if kind == 'bold_italic':
                clean = content[3:-3]
                text_widget.insert(tk.END, clean, ("md_bold_italic",))
            elif kind == 'bold':
                clean = content[2:-2]
                text_widget.insert(tk.END, clean, ("md_bold",))
            elif kind == 'italic':
                clean = content[1:-1]
                text_widget.insert(tk.END, clean, ("md_italic",))
            elif kind == 'code':
                clean = content[1:-1]
                text_widget.insert(tk.END, clean, ("md_code",))
            elif kind == 'alert':
                text_widget.insert(tk.END, content, ("alert_prazo",))
            elif kind == 'keyword':
                text_widget.insert(tk.END, content, ("keyword",))
            elif kind == 'sei_num':
                text_widget.insert(tk.END, content, ("sei_num",))
            elif kind == 'date':
                text_widget.insert(tk.END, content, ("date_expr",))
                
            last_idx = end
            
        if last_idx < len(line_to_parse):
            text_widget.insert(tk.END, line_to_parse[last_idx:])
            
        if line_idx < len(lines) - 1:
            text_widget.insert(tk.END, "\n")

def render_markdown_inplace(text_widget: ctk.CTkTextbox, is_dark: bool = True, base_size: int = 14):
    """Lê o texto atual do widget e o reescreve com formatação markdown renderizada."""
    current_text = text_widget.get("1.0", tk.END).strip()
    if not current_text:
        return
    text_widget.configure(state="normal")
    text_widget.delete("1.0", tk.END)
    insert_markdown_text(text_widget, current_text, is_dark=is_dark, base_size=base_size)
    text_widget.configure(state="normal")

def convert_text_to_sei_html(text: str) -> str:
    """
    Converte texto puro do despacho/resumo para HTML formatado segundo o padrão do SEI-GDF.
    Aplica tipografia Segoe UI/Arial, recuos de parágrafo, alinhamento justificado e cabeçalhos.
    """
    if not text:
        return ""
        
    lines = text.strip().split("\n")
    html_parts = []
    in_list = False
    
    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
            
        # Limpeza de markdown de cabeçalhos
        if raw_line.startswith("# "):
            raw_line = raw_line[2:].strip()
        elif raw_line.startswith("## "):
            raw_line = raw_line[3:].strip()
        elif raw_line.startswith("### "):
            raw_line = raw_line[4:].strip()
            
        escaped = html.escape(raw_line)
        
        # Converte marcações markdown em HTML
        escaped = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', escaped)
        escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
        escaped = re.sub(r'__(.+?)__', r'<strong>\1</strong>', escaped)
        escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)
        escaped = re.sub(r'`(.+?)`', r'<code>\1</code>', escaped)
        
        # Destaque de negrito em padrões chave
        escaped = re.sub(r'^(Governo do Distrito Federal|Secretaria Extraordinária de Proteção Animal.*?|Gabinete|Assessoria Especial)', r'<strong>\1</strong>', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'^(Despacho\s*-\s*[^\n]+)', r'<strong>\1</strong>', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'^(Assunto:\s*[^\n]+)', r'<strong>\1</strong>', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'^(SUJEITO A PRAZO)', r'<strong><span style="color: #c00000;">\1</span></strong>', escaped, flags=re.IGNORECASE)
        escaped = re.sub(r'^(MINUTA)', r'<div style="text-align: center; margin: 18pt 0 12pt 0;"><strong>MINUTA</strong></div>', escaped, flags=re.IGNORECASE)
        
        # Linhas divisórias (ex: === ou ---)
        if re.match(r'^[=\-]{5,}$', raw_line):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append('<hr style="border: none; border-top: 1px solid #cbd5e1; margin: 15pt 0;" />')
            continue
            
        # Títulos de Seção de Resumo / Linha do Tempo / Auditoria (ex: 1. IDENTIFICAÇÃO DO PROCESSO)
        if re.match(r'^\d+\.\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s\/\-]+$', raw_line) or raw_line in ("ORDEM CRONOLÓGICA DE ATOS E DOCUMENTOS", "RESUMO DA FASE ATUAL:"):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<p style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; font-weight: bold; color: #1e3a8a; margin-top: 14pt; margin-bottom: 6pt;">{escaped}</p>')
            continue
            
        # Itens com Marcadores (Bullets)
        if raw_line.startswith(('•', '-', '*')) or re.match(r'^[a-z]\)', raw_line):
            if not in_list:
                html_parts.append('<ul style="margin: 4pt 0 8pt 25pt; padding: 0;">')
                in_list = True
            clean_item = re.sub(r'^[•\-\*]\s*', '', escaped)
            clean_item = re.sub(r'^([^:]+:)', r'<strong>\1</strong>', clean_item)
            html_parts.append(f'<li style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; line-height: 1.4; margin-bottom: 4pt;">{clean_item}</li>')
            continue
            
        if in_list:
            html_parts.append("</ul>")
            in_list = False
            
        # Cabeçalhos centralizados ou alinhados
        if raw_line in ("Governo do Distrito Federal", "Despacho - SEPAN/GAB/ASSESP", "SUJEITO A PRAZO") or "Secretaria Extraordinária" in raw_line:
            align = "center" if raw_line in ("Governo do Distrito Federal", "SUJEITO A PRAZO") else "left"
            html_parts.append(f'<p style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; line-height: 1.3; text-align: {align}; margin: 2pt 0;">{escaped}</p>')
        elif raw_line.startswith("Brasília,") or raw_line.startswith("Ao ") or raw_line.startswith("À ") or raw_line.startswith("Senhor "):
            html_parts.append(f'<p style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; line-height: 1.4; margin: 8pt 0 4pt 0;">{escaped}</p>')
        elif raw_line.startswith("Atenciosamente"):
            html_parts.append(f'<p style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; line-height: 1.4; margin: 18pt 0 8pt 0;">{escaped}</p>')
        else:
            indent = "25pt" if re.match(r'^\d+\.', raw_line) or raw_line.startswith("Encaminha-se") or raw_line.startswith("Trata-se") else "0pt"
            html_parts.append(f'<p style="font-family: \'Segoe UI\', Arial, sans-serif; font-size: 11pt; line-height: 1.5; text-align: justify; text-indent: {indent}; margin: 6pt 0;">{escaped}</p>')

    if in_list:
        html_parts.append("</ul>")
        
    return "\n".join(html_parts)

def copy_html_to_clipboard(html_body: str, plain_text: str) -> bool:
    """
    Copia texto formatado em HTML (padrão CF_HTML do Windows) e texto plano para o clipboard.
    Permite colar diretamente no editor Web do SEI com formatação rica intacta.
    """
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        CF_HTML = user32.RegisterClipboardFormatW("HTML Format")
        CF_UNICODETEXT = 13
        
        header_template = (
            "Version:0.9\r\n"
            "StartHTML:{:08d}\r\n"
            "EndHTML:{:08d}\r\n"
            "StartFragment:{:08d}\r\n"
            "EndFragment:{:08d}\r\n"
        )
        html_prefix = "<!DOCTYPE html><html><body><!--StartFragment-->"
        html_suffix = "<!--EndFragment--></body></html>"
        
        dummy = header_template.format(0, 0, 0, 0).encode('utf-8')
        start_html = len(dummy)
        start_fragment = start_html + len(html_prefix.encode('utf-8'))
        end_fragment = start_fragment + len(html_body.encode('utf-8'))
        end_html = end_fragment + len(html_suffix.encode('utf-8'))
        
        header_str = header_template.format(start_html, end_html, start_fragment, end_fragment)
        full_html_bytes = (header_str + html_prefix + html_body + html_suffix).encode('utf-8') + b'\x00'
        
        if not user32.OpenClipboard(None):
            return False
            
        user32.EmptyClipboard()
        
        # 1. Unicode Plain Text
        unicode_bytes = (plain_text + '\x00').encode('utf-16le')
        h_mem_text = kernel32.GlobalAlloc(0x0042, len(unicode_bytes))
        p_mem_text = kernel32.GlobalLock(h_mem_text)
        ctypes.memmove(p_mem_text, unicode_bytes, len(unicode_bytes))
        kernel32.GlobalUnlock(h_mem_text)
        user32.SetClipboardData(CF_UNICODETEXT, h_mem_text)
        
        # 2. HTML Format
        h_mem_html = kernel32.GlobalAlloc(0x0042, len(full_html_bytes))
        p_mem_html = kernel32.GlobalLock(h_mem_html)
        ctypes.memmove(p_mem_html, full_html_bytes, len(full_html_bytes))
        kernel32.GlobalUnlock(h_mem_html)
        user32.SetClipboardData(CF_HTML, h_mem_html)
        
        user32.CloseClipboard()
        return True
    except Exception:
        return False
