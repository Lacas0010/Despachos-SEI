import customtkinter as ctk

COLOR_PALETTE = {
    "background": {"light": "#FFFFFF", "dark": "#1A1A1A"},
    "surface": {"light": "#F5F5F5", "dark": "#252525"},
    "primary": {"light": "#2563EB", "dark": "#007BFF"},
    "secondary": {"light": "#64748B", "dark": "#94A3B8"},
    "success": {"light": "#10B981", "dark": "#34D399"},
    "warning": {"light": "#F59E0B", "dark": "#FBBF24"},
    "error": {"light": "#EF4444", "dark": "#F87171"},
    "text_primary": {"light": "#1F2937", "dark": "#F1F5F9"},
    "text_secondary": {"light": "#6B7280", "dark": "#CBD5E1"},
    "border": {"light": "#E5E7EB", "dark": "#374151"}
}


def get_color(key: str, mode: str = "light") -> str:
    """Retorna cor do tema acessível."""
    return COLOR_PALETTE.get(key, {}).get(mode, "#000000")


def configure_theme():
    """Configura o tema de aparência no CustomTkinter."""
    theme = ctk.get_appearance_mode().lower()
    ctk.set_default_color_theme("blue")
    return theme
