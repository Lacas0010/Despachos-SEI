# Arquivo comentado em português para explicar cada parte do código.
# As anotações foram adicionadas antes de classes e funções para facilitar o entendimento.

"""
UI Animations module for Gerador SEI
Provides smooth transitions and micro-interactions for enhanced UX
"""

import customtkinter as ctk
from typing import Callable, Any, Optional, cast
import time

# Classe UIAnimations: define comportamento e estrutura desta parte do aplicativo.
class UIAnimations:
    """Centralized animation utilities for UI components."""

    @staticmethod
    def fade_in(widget: ctk.CTkBaseClass, duration: int = 300, steps: int = 10) -> None:
        """Fade in a widget by gradually increasing opacity."""
        if not hasattr(widget, 'attributes'):
            # For widgets that don't support alpha, use a simple show
            widget.grid()
            return

        widget_any = cast(Any, widget)
        step_duration = duration // steps
        alpha_step = 1.0 / steps

        # Função animate(current_alpha: float): executa lógica relacionada a animate.
        def animate(current_alpha: float):
            if current_alpha >= 1.0:
                widget_any.attributes("-alpha", 1.0)
                return
            widget_any.attributes("-alpha", current_alpha)
            widget_any.after(step_duration, lambda: animate(current_alpha + alpha_step))

        widget_any.attributes("-alpha", 0.0)
        widget.grid()
        animate(alpha_step)

    @staticmethod
    def fade_out(widget: ctk.CTkBaseClass, duration: int = 300, steps: int = 10, on_complete: Optional[Callable] = None) -> None:
        """Fade out a widget by gradually decreasing opacity."""
        if not hasattr(widget, 'attributes'):
            widget.grid_remove()
            if on_complete:
                on_complete()
            return

        widget_any = cast(Any, widget)
        step_duration = duration // steps
        alpha_step = 1.0 / steps

        # Função animate(current_alpha: float): executa lógica relacionada a animate.
        def animate(current_alpha: float):
            if current_alpha <= 0.0:
                widget.grid_remove()
                widget_any.attributes("-alpha", 1.0)  # Reset for future use
                if on_complete:
                    on_complete()
                return
            widget_any.attributes("-alpha", current_alpha)
            widget_any.after(step_duration, lambda: animate(current_alpha - alpha_step))

        animate(1.0 - alpha_step)

    @staticmethod
    def slide_in_right(widget: ctk.CTkBaseClass, duration: int = 400, steps: int = 20) -> None:
        """Slide widget in from the right."""
        original_x = widget.winfo_x()
        width = widget.winfo_width() or 400  # Default width if not yet rendered

        step_duration = duration // steps
        x_step = width // steps

        # Função animate(current_x: int): executa lógica relacionada a animate.
        def animate(current_x: int):
            if current_x <= original_x:
                widget.place(x=original_x)
                return
            widget.place(x=current_x)
            widget.after(step_duration, lambda: animate(current_x - x_step))

        widget.place(x=original_x + width)
        animate(original_x + width - x_step)

    @staticmethod
    def button_press_animation(button: ctk.CTkButton, duration: int = 150) -> None:
        """Create a button press animation (shrink and return)."""
        original_width = button.cget("width")
        original_height = button.cget("height")

        if original_width == "auto" or original_height == "auto":
            # Get actual dimensions
            button.update_idletasks()
            original_width = button.winfo_width()
            original_height = button.winfo_height()

        shrink_width = max(1, int(original_width * 0.95))
        shrink_height = max(1, int(original_height * 0.95))

        # Função shrink(): executa lógica relacionada a shrink.
        def shrink():
            button.configure(width=shrink_width, height=shrink_height)
            button.after(duration // 2, expand)

        # Função expand(): executa lógica relacionada a expand.
        def expand():
            button.configure(width=original_width, height=original_height)

        shrink()

    @staticmethod
    def color_transition(widget: ctk.CTkBaseClass, start_color: str, end_color: str,
                        duration: int = 200, steps: int = 10,
                        color_attr: str = "fg_color") -> None:
        """Smooth color transition for widgets that support fg_color."""
        if not hasattr(widget, 'configure'):
            return

        widget_any = cast(Any, widget)
        # Simple color interpolation (basic implementation)
        # For more complex colors, would need proper color parsing
        step_duration = duration // steps

        # Função animate(step: int): executa lógica relacionada a animate.
        def animate(step: int):
            if step >= steps:
                widget_any.configure(**{color_attr: end_color})
                return

            # Simple linear interpolation for basic colors
            # This is a simplified version - real implementation would parse hex colors
            progress = step / steps
            widget_any.configure(**{color_attr: start_color})  # Placeholder
            widget_any.after(step_duration, lambda: animate(step + 1))

        animate(0)

    @staticmethod
    def create_indicator_line(parent: ctk.CTkFrame, height: int = 40, width: int = 4,
                           color: str = "#2563EB") -> ctk.CTkFrame:
        """Create an animated indicator line for navigation."""
        indicator = ctk.CTkFrame(parent, width=width, height=height,
                               fg_color=color, corner_radius=2)
        return indicator

    @staticmethod
    def animate_indicator_move(indicator: ctk.CTkFrame, target_y: int,
                             duration: int = 300, steps: int = 15) -> None:
        """Animate indicator line moving to new position."""
        current_y = indicator.winfo_y()
        step_duration = duration // steps
        y_step = (target_y - current_y) / steps

        # Função animate(current_step: int): executa lógica relacionada a animate.
        def animate(current_step: int):
            if current_step >= steps:
                indicator.place(y=target_y)
                return
            new_y = current_y + (y_step * current_step)
            indicator.place(y=new_y)
            indicator.after(step_duration, lambda: animate(current_step + 1))

        animate(1)

    @staticmethod
    def card_hover_effect(card: ctk.CTkFrame, is_hover: bool,
                         original_bg: str, hover_bg: str,
                         original_border: str, hover_border: str,
                         duration: int = 150) -> None:
        """Apply hover effect to cards with smooth transitions."""
        if is_hover:
            card.configure(fg_color=hover_bg, border_color=hover_border)
        else:
            card.configure(fg_color=original_bg, border_color=original_border)

    @staticmethod
    def text_fade_in(text_widget: ctk.CTkTextbox, text: str, duration: int = 500) -> None:
        """Fade in text content gradually."""
        text_widget.configure(state="normal")
        text_widget.delete("1.0", ctk.END)

        chars_per_step = max(1, len(text) // 20)  # Show in about 20 steps
        step_duration = duration // (len(text) // chars_per_step + 1)

        # Função animate(current_pos: int): executa lógica relacionada a animate.
        def animate(current_pos: int):
            if current_pos >= len(text):
                text_widget.insert(ctk.END, text[current_pos:])
                return

            end_pos = min(len(text), current_pos + chars_per_step)
            text_widget.insert(ctk.END, text[current_pos:end_pos])
            text_widget.after(step_duration, lambda: animate(end_pos))

        animate(0)

    @staticmethod
    def icon_swap_animation(button: ctk.CTkButton, original_text: str, temp_text: str,
                          duration: int = 1000) -> None:
        """Temporarily change button text/icon then revert."""
        button.configure(text=temp_text)
        button.after(duration, lambda: button.configure(text=original_text))
