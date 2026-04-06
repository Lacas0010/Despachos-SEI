# Arquivo comentado em português para explicar cada parte do código.
# As anotações foram adicionadas antes de classes e funções para facilitar o entendimento.

"""
Teste das melhorias implementadas no Gerador SEI
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Função test_imports(): executa lógica relacionada a test imports.
def test_imports():
    """Testa se todos os módulos podem ser importados."""
    try:
        from gerador_sei import GeradorSEIApp, GenerarScreen, HistoricoScreen
        from engine import SEIEngine
        from theme_config import ThemeManager
        print("✅ Todos os imports funcionam")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

# Função test_engine(): executa lógica relacionada a test engine.
def test_engine():
    """Testa funcionalidades básicas do engine."""
    try:
        from engine import SEIEngine
        engine = SEIEngine()
        # Testa geração básica
        data = {
            "oficio": "123/2026",
            "prazo": "15/04/2026",
            "sei_oficio": "123456789",
            "sei_manifestacao": "987654321",
            "protocolo": "OUV-001/2026",
            "resumo": "Teste de funcionalidade",
            "modelo": "HVeP - Atendimento/HVeP"
        }
        texto = engine.generate_despacho(data)
        if texto and len(texto) > 50:
            print("✅ Engine gera despachos corretamente")
            return True
        else:
            print("❌ Engine não gera texto adequado")
            return False
    except Exception as e:
        print(f"❌ Erro no engine: {e}")
        return False

# Função test_theme(): executa lógica relacionada a test theme.
def test_theme():
    """Testa funcionalidades do theme manager."""
    try:
        from theme_config import ThemeManager
        tm = ThemeManager()
        tm.toggle_theme()
        print("✅ Theme manager funciona")
        return True
    except Exception as e:
        print(f"❌ Erro no theme: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando melhorias do Gerador SEI...")
    print()

    results = []
    results.append(test_imports())
    results.append(test_engine())
    results.append(test_theme())

    print()
    if all(results):
        print("🎉 Todas as melhorias estão funcionando!")
    else:
        print("⚠️  Algumas melhorias podem ter problemas.")
