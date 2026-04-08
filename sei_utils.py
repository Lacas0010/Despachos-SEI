import customtkinter as ctk
from theme_config import get_color_tuple, get_font, configure_appearance

# NOTE: sei_utils é mantido como fachada leve para compatibilidade.
# Toda lógica de cores fontes e aparências fica centralizada em theme_config.

def get_color(key: str, mode: str = "light") -> str:
    """Retorna cor do tema acessível usando theme_config."""
    color_tuple = get_color_tuple(key)
    return color_tuple[1] if mode.lower() == "dark" else color_tuple[0]


# Função configure_theme(): executa lógica relacionada a configure theme.
def configure_theme():
    """Configura o tema de aparência no CustomTkinter."""
    # Retorna o modo atual (light/dark)
    current = "dark" if ctk.get_appearance_mode().lower() == "dark" else "light"
    configure_appearance(current == "dark")
    return current
