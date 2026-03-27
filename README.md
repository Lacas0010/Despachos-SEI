# Gerador de Despacho SEI

Aplicação GUI em Python para gerar despachos SEI com modelos pré-definidos, utilizando Tkinter e ttk.

## Funcionalidades

- **Modelos de Despacho**: 4 modelos pré-configurados + possibilidade de adicionar/editar modelos customizados via interface.
- **Gerenciar Modelos**: Adicione, edite ou delete modelos diretamente no programa (menu Editar > Gerenciar Modelos).
- **Validação de Entrada**: Verificação de formato dos campos (SEI numérico, protocolo OUV, data válida e futura).
- **Tema Dark/Light**: Alternância entre modos com salvamento automático da preferência.
- **Salvar/Carregar Dados**: Persistência dos dados inseridos em JSON.
- **Exportar para PDF**: Geração de arquivo PDF formatado com o despacho.
- **Histórico**: Visualização e carregamento de despachos anteriores (últimos 20).
- **Tooltips**: Dicas nos campos de entrada.
- **Menu e Atalhos**: Menu principal com atalhos de teclado (Ctrl+S, Ctrl+G, F11, etc.).
- **Copiar para Clipboard**: Copia o texto gerado para a área de transferência.

## Requisitos

- Python 3.x
- Bibliotecas: tkinter, tkcalendar, reportlab, json, os

Instale as dependências:
```
pip install tkcalendar reportlab
```

## Como Usar

1. Execute o script: `python gerador_sei.py`
2. Preencha os campos obrigatórios.
3. Selecione o modelo.
4. Clique em "Gerar Despacho".
5. Use os botões para salvar, exportar ou copiar.

## Atalhos de Teclado

- Ctrl+S: Salvar Dados
- Ctrl+L: Carregar Dados
- Ctrl+E: Exportar PDF
- Ctrl+G: Gerar Despacho
- Ctrl+C: Copiar para Clipboard
- Ctrl+H: Histórico
- Ctrl+M: Gerenciar Modelos
- F11: Alternar Tema

## Arquivos Gerados

- `dados_ultimo.json`: Últimos dados inseridos.
- `config.json`: Configurações (tema).
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