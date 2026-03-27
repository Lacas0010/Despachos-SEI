import datetime
import re
import customtkinter as ctk

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

COLOR_PALETTE = {
    "background": {"light": "#FFFFFF", "dark": "#1F2937"},
    "surface": {"light": "#F8FAFC", "dark": "#374151"},
    "primary": {"light": "#1D4ED8", "dark": "#3B82F6"},
    "secondary": {"light": "#6B7280", "dark": "#9CA3AF"},
    "success": {"light": "#16A34A", "dark": "#22C55E"},
    "warning": {"light": "#D97706", "dark": "#F59E0B"},
    "error": {"light": "#DC2626", "dark": "#EF4444"},
    "text_primary": {"light": "#0F172A", "dark": "#F8FAFC"},
    "text_secondary": {"light": "#475569", "dark": "#CBD5E1"},
    "border": {"light": "#E2E8F0", "dark": "#4B5563"}
}


def get_color(key: str, mode: str = "light") -> str:
    """Retorna cor do tema acessível."""
    return COLOR_PALETTE.get(key, {}).get(mode, "#000000")


def configure_theme():
    """Configura o tema de aparência no CustomTkinter."""
    theme = ctk.get_appearance_mode().lower()
    ctk.set_default_color_theme("blue")
    return theme


def formatar_prazo(data_str: str) -> str:
    """Converte data dd/mm/yyyy para formato textual brasileiro."""
    try:
        data = datetime.datetime.strptime(data_str, "%d/%m/%Y")
    except ValueError:
        return data_str

    dia = data.day
    mes = MESES[data.month - 1]
    ano = data.year
    dia_str = "1º" if dia == 1 else str(dia)
    return f"{dia_str} de {mes} de {ano}"


def validar_sei(value: str) -> bool:
    """Valida entrada de SEI: numérico ou #{orig|id}#."""
    if value.isdigit():
        return True
    return bool(re.match(r"^#\{\d+\|\d+\}#$", value))


def formatar_sei_link(value: str) -> str:
    """Retorna o valor já formatado como markup ou converte número para markup."""
    m = re.match(r"^#\{(\d+)\|(\d+)\}#$", value)
    if m:
        return f"#{{{m.group(1)}|{m.group(2)}}}#"
    if value.isdigit():
        return f"#{{{value}|{value}}}#"
    return value
