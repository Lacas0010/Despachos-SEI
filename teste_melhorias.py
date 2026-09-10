import sys
import os
import tempfile

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    try:
        from gerador_sei import GeradorSEIApp
        from engine import SEIEngine
        from sei_templates import (
            MOLDE_RESUMO_EXECUTIVO, MOLDE_LINHA_TEMPO, MOLDE_AUDITORIA_CONFORMIDADE
        )
        from sei_utils import convert_text_to_sei_html, copy_html_to_clipboard
        from theme_config import ThemeManager
        print("  [OK] Todos os imports funcionam")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro nos imports: {e}")
        return False

def test_engine_basic():
    """Testa funcionalidades básicas do engine."""
    try:
        from engine import SEIEngine
        engine = SEIEngine()
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
            print("  [OK] Engine gera despachos corretamente")
            return True
        else:
            print("  [ERRO] Engine não gera texto adequado")
            return False
    except Exception as e:
        print(f"  [ERRO] Erro no engine: {e}")
        return False

def test_novos_moldes():
    """Testa presença dos novos moldes de Resumão, Linha do Tempo e Auditoria."""
    try:
        from sei_templates import MOLDE_RESUMO_EXECUTIVO, MOLDE_LINHA_TEMPO, MOLDE_AUDITORIA_CONFORMIDADE
        assert "RESUMO EXECUTIVO DO PROCESSO SEI" in MOLDE_RESUMO_EXECUTIVO
        assert "LINHA DO TEMPO / CRONOLOGIA DO PROCESSO SEI" in MOLDE_LINHA_TEMPO
        assert "RELATÓRIO DE AUDITORIA, PRAZOS E CONFORMIDADE SEI" in MOLDE_AUDITORIA_CONFORMIDADE
        print("  [OK] Moldes de Resumão, Linha do Tempo e Auditoria configurados")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro nos moldes: {e}")
        return False

def test_export_docx_pdf():
    """Testa exportação de DOCX e PDF."""
    try:
        from engine import SEIEngine
        engine = SEIEngine()
        texto_teste = "Governo do Distrito Federal\nSecretaria Extraordinária de Proteção Animal\n\nDespacho - SEPAN/GAB/ASSESP\n\n1. Trata-se de teste.\n\nAtenciosamente,"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, "teste.docx")
            pdf_path = os.path.join(tmpdir, "teste.pdf")
            
            suc_docx, err_docx = engine.export_to_docx(texto_teste, docx_path)
            assert suc_docx and os.path.exists(docx_path)
            
            suc_pdf, err_pdf = engine.export_to_pdf(texto_teste, pdf_path)
            assert suc_pdf and os.path.exists(pdf_path)
            
        print("  [OK] Exportações DOCX e PDF funcionam perfeitamente")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro nas exportações: {e}")
        return False

def test_sei_html_converter():
    """Testa conversão para HTML oficial do SEI."""
    try:
        from sei_utils import convert_text_to_sei_html
        texto = "Governo do Distrito Federal\nDespacho - SEPAN/GAB/ASSESP\n\n1. Trata-se de demanda de Ouvidoria.\n\n• Processo SEI nº: 123456\n• Interessado: Cidadão\n\nAtenciosamente,"
        html_out = convert_text_to_sei_html(texto)
        assert "<p " in html_out and "<strong>" in html_out
        print("  [OK] Conversor de HTML para SEI funciona")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro no conversor HTML: {e}")
        return False

def test_theme():
    """Testa funcionalidades do theme manager."""
    try:
        from theme_config import ThemeManager
        tm = ThemeManager()
        tm.toggle_theme()
        print("  [OK] Theme manager funciona")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro no theme: {e}")
        return False

def test_history_db():
    """Testa persistência, contexto dos autos, busca e exclusão no banco de histórico."""
    try:
        from engine import HistoryDB
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = os.path.join(tmpdir, "test_hist.db")
            db = HistoryDB(test_db_path)
            
            # 1. Inserção com contexto de autos
            entry_id = db.add_entry(
                doc_type="RESUMÃO",
                subject="Processo SEI 00010-00001234/2026-99",
                full_text="# Resumo do Processo\nTrata-se de análise...",
                process_context="CONTEÚDO COMPLETO DOS AUTOS DO PROCESSO SEI..."
            )
            assert entry_id > 0, "Falha ao inserir histórico"
            
            # 2. Leitura
            entries = db.get_all_entries()
            assert len(entries) == 1
            item = entries[0]
            assert item["doc_type"] == "RESUMÃO"
            assert item["process_context"] == "CONTEÚDO COMPLETO DOS AUTOS DO PROCESSO SEI..."
            
            # 3. Busca
            search_res = db.search_entries("00001234")
            assert len(search_res) == 1
            
            # 4. Exclusão
            deleted = db.delete_entry(entry_id)
            assert deleted is True
            assert len(db.get_all_entries()) == 0
            
            db.close()
            
        print("  [OK] Banco de Histórico (Contexto de autos, busca, persistência, exclusão) 100% validado")
        return True
    except Exception as e:
        print(f"  [ERRO] Erro no HistoryDB: {e}")
        return False

if __name__ == "__main__":
    print("Testando Suíte Avançada do Gerador SEI...")
    print()

    results = []
    results.append(test_imports())
    results.append(test_engine_basic())
    results.append(test_novos_moldes())
    results.append(test_export_docx_pdf())
    results.append(test_sei_html_converter())
    results.append(test_theme())
    results.append(test_history_db())

    print()
    if all(results):
        print("Todas as funcionalidades estao funcionando com sucesso!")
    else:
        print("Algumas funcionalidades apresentaram problemas.")
