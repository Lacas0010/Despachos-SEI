# Gerador SEI - Gerador de Despachos

Uma aplicação desktop moderna e intuitiva para geração de despachos SEI (Sistema Eletrônico de Informações), desenvolvida em Python com interface gráfica elegante usando CustomTkinter.

![Interface](assets/screenshot.png)

## ✨ Funcionalidades

### 📝 Geração de Despachos
- **4 Modelos Pré-definidos**: HVEP, Castração, Condições HVEP e Cronograma
- **Modelos Customizáveis**: Adicione, edite ou remova modelos personalizados
- **Campos Validados**: Validação automática de SEI, protocolos OUV e datas
- **Template Engine**: Sistema de placeholders inteligentes ({NUM_OFICIO}, {SEI_OFICIO}, etc.)

### 🎨 Interface Moderna
- **Design Responsivo**: Layout que se adapta ao tamanho da janela
- **Tema Dark/Light**: Alternância automática com salvamento de preferência
- **Sidebar Navegação**: Navegação intuitiva entre telas
- **Tooltips Informativos**: Dicas contextuais em todos os campos

### 📊 Gerenciamento Avançado
- **Histórico Completo**: Visualização dos últimos despachos gerados
- **Persistência de Dados**: Salvamento automático em JSON
- **Exportação PDF**: Geração de documentos formatados
- **Copiar para Clipboard**: Cópia rápida do texto gerado

### 🛠️ Recursos Técnicos
- **Validação Robusta**: Verificação de formatos e dados obrigatórios
- **Calendário Integrado**: Seleção visual de datas
- **Atalhos de Teclado**: Navegação rápida (Ctrl+G, Ctrl+S, F11, etc.)
- **Logs e Mensagens**: Sistema de feedback visual

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação Automática
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/gerador-sei.git
cd gerador-sei

# Instale as dependências
pip install -r requirements.txt
```

### Instalação Manual
```bash
# Instale as bibliotecas necessárias
pip install customtkinter tkcalendar reportlab pandas openpyxl matplotlib
```

## 📖 Como Usar

1. **Execute a aplicação**:
   ```bash
   python gerador_sei.py
   ```

2. **Preencha os campos**:
   - Ofício, Prazo, SEI Ofício, SEI Manifestação, Protocolo OUV, Resumo

3. **Selecione o modelo** e clique em "Gerar Despacho"

4. **Utilize as funcionalidades**:
   - 📋 Copiar texto
   - 💾 Salvar dados
   - 📄 Exportar PDF
   - 📚 Ver histórico

## ⌨️ Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| `Ctrl+G` | Gerar Despacho |
| `Ctrl+S` | Salvar Dados |
| `Ctrl+L` | Carregar Dados |
| `Ctrl+E` | Exportar PDF |
| `Ctrl+C` | Copiar para Clipboard |
| `Ctrl+H` | Histórico |
| `Ctrl+M` | Gerenciar Modelos |
| `F11` | Alternar Tema |

## 🏗️ Arquitetura

```
gerador_sei/
├── gerador_sei.py      # Aplicação principal (GUI)
├── engine.py           # Lógica de negócio e validações
├── theme_config.py     # Configuração de temas e cores
├── sei_templates.py    # Modelos de despacho pré-definidos
├── sei_utils.py        # Utilitários diversos
├── requirements.txt    # Dependências Python
└── README.md          # Esta documentação
```

### Componentes Principais

- **GeradorSEIApp**: Classe principal da aplicação
- **SEIEngine**: Motor de geração de despachos
- **ThemeManager**: Gerenciador de temas dark/light
- **Screen Classes**: Telas modulares (GenerarScreen, HistoricoScreen, etc.)

## 📁 Estrutura de Dados

### Arquivos de Configuração
- `config.json`: Configurações da aplicação (tema, preferências)
- `dados_ultimo.json`: Últimos dados inseridos
- `modelos_custom.json`: Modelos personalizados criados pelo usuário

### Formato dos Templates
```python
# Exemplo de template
MODELO_HVEP = """
Prezado(a) {NOME_DESTINATARIO},

Informamos que o Ofício nº {NUM_OFICIO}, SEI {SEI_OFICIO},
protocolado em {PROTOCOLO}, trata sobre {RESUMO}.

O prazo para atendimento é {PRAZO}.

Atenciosamente,
Equipe SEI
"""
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🐛 Reportar Problemas

Encontrou um bug ou tem uma sugestão? Abra uma [issue](https://github.com/seu-usuario/gerador-sei/issues) no GitHub.

## 🙏 Agradecimentos

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Framework de interface moderna
- [tkcalendar](https://github.com/j4321/tkcalendar) - Widget de calendário
- [ReportLab](https://www.reportlab.com/) - Geração de PDFs

---

**Desenvolvido com ❤️ para facilitar o trabalho com SEI**
- `modelos_custom.json`: Modelos customizados adicionados pelo usuário.
- Arquivos PDF exportados conforme solicitado.

## Melhorias Implementadas

- Validação robusta de campos.
- Persistência de dados e configurações.
- Exportação para PDF.
- Interface aprimorada com tooltips e menu.
- Histórico de despachos.
- Gerenciamento dinâmico de modelos via interface (adicionar, editar, deletar).
- Atalhos de teclado para produtividade.