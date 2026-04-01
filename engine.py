"""
Engine module for Gerador SEI
Contains business logic for text generation, validation, and data processing
"""

import datetime
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from sei_templates import (
    PREFIXO_DOCUMENTO, RESUMO_CRONOGRAMA,
    MODELO_HVEP, MODELO_CASTRACAO, MODELO_CONDICOES_HVEP, MODELO_CRONOGRAMA_CASTRACAO
)

class SEIEngine:
    """Business logic engine for SEI document generation."""

    def __init__(self, modelos_file: str = "modelos_custom.json"):
        self.modelos_file = modelos_file
        self.modelos: Dict[str, Any] = {
            "HVeP - Atendimento/HVeP": MODELO_HVEP,
            "Castração de Cães e Gatos": MODELO_CASTRACAO,
            "Condições de exames e cirurgia HVeP": MODELO_CONDICOES_HVEP,
            "Demanda de Ouvidoria - Ausência de Cronograma Castração": MODELO_CRONOGRAMA_CASTRACAO
        }
        self._load_custom_modelos()

    def _load_custom_modelos(self) -> None:
        """Load custom models from file."""
        if os.path.exists(self.modelos_file):
            try:
                with open(self.modelos_file, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                self.modelos.update(custom)
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults if file is corrupted

    def _save_custom_modelos(self) -> None:
        """Save custom models to file."""
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
        except IOError:
            pass

    def validate_sei(self, sei: str) -> bool:
        """Validate SEI field input; accept user-provided expression (no auto-format)."""
        return bool(str(sei).strip())

    def validate_form_data(self, data: Any) -> List[str]:
        """Validate form data and return list of errors."""
        # suporte a lista ou dicionário (compatibilidade com código legado)
        if isinstance(data, list):
            data = {
                "oficio": data[0] if len(data) > 0 else "",
                "sei_oficio": data[1] if len(data) > 1 else "",
                "sei_manifestacao": data[2] if len(data) > 2 else "",
                "protocolo": data[3] if len(data) > 3 else "",
                "resumo": data[4] if len(data) > 4 else "",
                "prazo": data[5] if len(data) > 5 else ""
            }

        errors = []

        if not data.get("oficio", "").strip():
            errors.append("Ofício obrigatório")

        sei_oficio = data.get("sei_oficio", "").strip()
        if not self.validate_sei(sei_oficio):
            errors.append("SEI Ofício inválido")

        sei_manifestacao = data.get("sei_manifestacao", "").strip()
        if not self.validate_sei(sei_manifestacao):
            errors.append("SEI Manifestação inválido")

        protocolo = data.get("protocolo", "").strip()
        if not protocolo.startswith("OUV-"):
            errors.append("Protocolo OUV inválido")

        if not data.get("resumo", "").strip():
            errors.append("Resumo obrigatório")

        try:
            prazo_date = datetime.datetime.strptime(data.get("prazo", ""), "%d/%m/%Y").date()
            if prazo_date < datetime.date.today():
                errors.append("Prazo não pode ser no passado")
        except ValueError:
            errors.append("Data de prazo inválida")

        return errors

    def format_prazo(self, prazo: str) -> str:
        """Formata prazo no padrão: 3 de abril de 2026."""
        if not prazo:
            return ""

        # aceita entrada dd/mm/yyyy ou '3 de abril de 2026'
        try:
            # formato esperado dd/mm/yyyy
            data = datetime.datetime.strptime(prazo.strip(), "%d/%m/%Y").date()
            meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                     "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            return f"{data.day} de {meses[data.month - 1]} de {data.year}"
        except ValueError:
            # Se já estiver no formato extenso, retorna como está
            return prazo.strip()

    def generate_despacho(self, data: Dict[str, str]) -> str:
        """Generate SEI dispatch text using named tag placeholders."""
        modelo = self.modelos.get(data.get("modelo", "HVeP - Atendimento/HVeP"), MODELO_HVEP)

        context = {
            "NUM_OFICIO": data.get("oficio", ""),
            "SEI_OFICIO": data.get("sei_oficio", ""),
            "SEI_MANIFESTACAO": data.get("sei_manifestacao", ""),
            "PROTOCOLO": data.get("protocolo", ""),
            "RESUMO": data.get("resumo", ""),
            "PRAZO": self.format_prazo(data.get("prazo", ""))
        }

        if isinstance(modelo, str):
            try:
                corpo = modelo.format(**context)
            except Exception:
                corpo = modelo
        elif callable(modelo):
            corpo = modelo(
                context["NUM_OFICIO"],
                context["SEI_OFICIO"],
                context["SEI_MANIFESTACAO"],
                context["PROTOCOLO"],
                context["RESUMO"],
                context["PRAZO"]
            )
        else:
            corpo = ""

        return PREFIXO_DOCUMENTO + corpo.strip()

    def export_to_pdf(self, text: str, filepath: str) -> Tuple[bool, str]:
        """Export text to PDF, retornando status e mensagem de erro quando aplicável."""
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            for line in text.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
                else:
                    story.append(Spacer(1, 12))

            doc.build(story)
            return True, ""
        except Exception as err:
            return False, str(err)

    def add_custom_modelo(self, nome: str, template: str) -> bool:
        """Add custom model string template with tag placeholders."""
        if nome and template and nome not in self.modelos:
            self.modelos[nome] = template
            self._save_custom_modelos()
            return True
        return False

    def update_modelo(self, nome: str, template: str) -> bool:
        """Update existing model with tag-based template."""
        if nome in self.modelos and template:
            self.modelos[nome] = template
            self._save_custom_modelos()
            return True
        return False

    def delete_modelo(self, nome: str) -> bool:
        """Delete custom model."""
        defaults = {
            "HVeP - Atendimento/HVeP",
            "Castração de Cães e Gatos",
            "Condições de exames e cirurgia HVeP",
            "Demanda de Ouvidoria - Ausência de Cronograma Castração"
        }

        if nome in self.modelos and nome not in defaults:
            del self.modelos[nome]
            self._save_custom_modelos()
            return True
        return False

    def get_modelos_list(self) -> List[str]:
        """Get list of available models."""
        return list(self.modelos.keys())

    def calcular_data_prazo(self, dias: int) -> str:
        """Calcula prazo a partir de hoje (dias) e retorna no formato dd/mm/YYYY."""
        hoje = datetime.date.today()
        data_prazo = hoje + datetime.timedelta(days=dias)
        return data_prazo.strftime("%d/%m/%Y")