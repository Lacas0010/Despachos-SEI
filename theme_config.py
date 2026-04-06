# Arquivo comentado em português para explicar cada parte do código.
# As anotações foram adicionadas antes de classes e funções para facilitar o entendimento.

"""
Theme configuration for Gerador SEI
Centralized color schemes and appearance settings
"""

from typing import Dict, Tuple, Any, Optional
import customtkinter as ctk

# Color schemes for light and dark modes
COLOR_SCHEME: Dict[str, Tuple[str, str]] = {
    "background": ("#FFFFFF", "#1A1A1A"),
    "surface": ("#F5F5F5", "#252525"),
    "primary": ("#2563EB", "#007BFF"),
    "secondary": ("#64748B", "#94A3B8"),
    "success": ("#10B981", "#34D399"),
    "warning": ("#F59E0B", "#FBBF24"),
    "error": ("#EF4444", "#F87171"),
    "text_primary": ("#1F2937", "#F1F5F9"),
    "text_secondary": ("#6B7280", "#CBD5E1"),
    "border": ("#E5E7EB", "#374151"),
    "hover_primary": ("#1D4ED8", "#0056CC"),
    "hover_surface": ("#E5E7EB", "#2D2D2D"),
    "focus_border": ("#3B82F6", "#0EA5E9")
}

def get_color_tuple(key: str) -> Tuple[str, str]:
    """Get color tuple for light/dark modes."""
    return COLOR_SCHEME.get(key, ("#000000", "#FFFFFF"))

def configure_appearance(is_dark: bool) -> None:
    """Configure CustomTkinter appearance mode."""
    ctk.set_appearance_mode("dark" if is_dark else "light")
    ctk.set_default_color_theme("blue")

def get_font(size: int = 12, weight: str = "normal", family: Optional[str] = None) -> ctk.CTkFont:
    """Get standardized font."""
    if family:
        return ctk.CTkFont(size=size, weight=weight, family=family)
    return ctk.CTkFont(size=size, weight=weight)

def get_hover_color(base_color_key: str, theme_manager) -> str:
    """Get appropriate hover color based on theme."""
    hover_map = {
        "primary": "hover_primary",
        "surface": "hover_surface"
    }
    hover_key = hover_map.get(base_color_key, base_color_key)
    return theme_manager.get_color(hover_key)

def get_focus_border_color(theme_manager) -> str:
    """Get focus border color."""
    return theme_manager.get_color("focus_border")

# Classe ThemeObserver: define comportamento e estrutura desta parte do aplicativo.
class ThemeObserver:
    """Observer pattern for theme changes."""

    # Função interna __init__(): executa lógica relacionada a init.
    def __init__(self):
        self._observers: list = []

    def attach(self, observer) -> None:
        """Attach an observer."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer) -> None:
        """Detach an observer."""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, is_dark: bool) -> None:
        """Notify all observers of theme change."""
        for observer in self._observers:
            try:
                observer.on_theme_change(is_dark)
            except AttributeError:
                # Fallback for objects without on_theme_change method
                pass


# Classe ThemeManager: define comportamento e estrutura desta parte do aplicativo.
class ThemeManager:
    """Theme manager wrapper for compatibility with legacy code."""

    # Função interna __init__(is_dark: bool = True): executa lógica relacionada a init.
    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self._observer = ThemeObserver()
        configure_appearance(self.is_dark)

    def attach(self, observer) -> None:
        self._observer.attach(observer)

    def detach(self, observer) -> None:
        self._observer.detach(observer)

    def register_observer(self, observer) -> None:
        self.attach(observer)

    def unregister_observer(self, observer) -> None:
        self.detach(observer)

    def notify_observers(self) -> None:
        self._observer.notify(self.is_dark)

    def toggle_theme(self) -> None:
        self.is_dark = not self.is_dark
        configure_appearance(self.is_dark)
        self._observer.notify(self.is_dark)

    def get_color(self, key: str) -> str:
        colors = COLOR_SCHEME.get(key, ("#000000", "#FFFFFF"))
        return colors[1] if self.is_dark else colors[0]

    def get_hover_color(self, base_key: str) -> str:
        """Get hover color for given base color key."""
        return get_hover_color(base_key, self)

    def get_focus_border_color(self) -> str:
        """Get focus border color."""
        return get_focus_border_color(self)
