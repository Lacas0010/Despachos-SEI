# 🎯 Gerador SEI - IA Edition (Local RAG)

Uma aplicação desktop moderna e inteligente para geração, análise e refinamento de despachos SEI (Sistema Eletrônico de Informações). Esta versão é impulsionada por **Inteligência Artificial Local** (LLaMA 3.2 via Ollama), garantindo automação inteligente com **100% de privacidade** e segurança dos dados, sem envio de informações para a nuvem.

## ✨ Funcionalidades

### 🧠 Inteligência Artificial (Ollama + LLaMA)
- **Análise de Processos**: Extração automática de contexto a partir de pastas inteiras contendo PDFs (com suporte a OCR via bibliotecas externas), arquivos do Word (DOCX), HTML e TXT.
- **Assistente Interativo (Chat)**: Converse com a IA para refinar, alterar o tom ou corrigir documentos gerados com comandos em linguagem natural (Ex: "Troque a data de hoje para amanhã").
- **Privacidade e Segurança**: O processamento (Inferência e Embeddings) é feito offline na máquina do usuário, protegendo dados sensíveis do governo.

### 📚 Aprendizado Contínuo (RAG Local)
- **Memória de Processos**: O aplicativo lê pastas com processos anteriores e aprende o padrão e formato dos despachos.
- **TinyVectorDB**: Banco de dados vetorial leve, construído de forma nativa e otimizado para não causar falhas (segfaults) em ambientes Windows.

### 🎨 Interface Moderna e Integrada
- **Single-Page Application**: Interface unificada dividida inteligentemente entre Chat da IA, Resultado e Histórico.
- **Tema Dark/Light**: Alternância suave de tema com persistência de preferências do usuário.
- **Histórico Visual**: Navegue em cards com as últimas gerações ou refinamentos e reutilize textos passados com um clique.
- **Copiar para Clipboard**: Ações de um clique para "Copiar e Limpar" ou exportar diretamente para PDF formatado.
- **Copiar para Clipboard**: Cópia automática com feedback visual

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Ollama instalado em sua máquina.

### Passo a Passo de Instalação
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/gerador-sei.git
cd gerador-sei

# Crie e ative um ambiente virtual (Opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate

# Instale as dependências do Python
pip install -r requirements.txt

# Baixe o modelo LLM do Ollama para o seu computador
ollama run llama3.2
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
| `Ctrl+Q` | Sair da aplicação |
| `F11` | Alternar Tema (Dark/Light) |
| `.` (data picker) | Abrir calendário |

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
- `config.json`: Configurações da aplicação (tema ativo, preferências de UI)
- `dados_ultimo.json`: Últimos dados inseridos (para carregamento rápido)
- `modelos_custom.json`: Modelos personalizados criados pelo usuário

### Formato dos Arquivos JSON

**dados_ultimo.json**
```json
{
  "campo_0": "778/2026",
  "campo_1": "01/05/2026",
  "campo_2": "198654234",
  "campo_3": "220622554",
  "campo_4": "OUV-078543/2026",
  "campo_5": "Falta de vagas de castração",
  "modelo": "HVeP - Atendimento/HVeP"
}
```

**modelos_custom.json**
```json
{
  "Meu Modelo": "Conteúdo do {SEI_OFICIO} com placeholders..."
}
```

### Placeholders Disponíveis
- `{NUM_OFICIO}` - Número do ofício
- `{SEI_OFICIO}` - SEI do ofício
- `{SEI_MANIFESTACAO}` - SEI da manifestação
- `{PROTOCOLO}` - Protocolo OUV
- `{PROTOCOLO}` - Resumo da manifestação
- `{PRAZO}` - Data de prazo calculada
```

## 📋 Changelog (v2.0)

### Novo
- ✨ Atalhos de prazo (`+5d`, `+15d`, `+30d`) para cálculo rápido
- ✨ Cards modernos para exibição do histórico
- ✨ Validação visual em tempo real (cores na borda dos campos)
- ✨ Sidebar retrátil para economia de espaço
- ✨ Busca instantânea de modelos
- ✨ Duplicar modelo existente
- ✨ Botão "Copiar e Limpar" combinado
- ✨ Feedback visual de processamento
- ✨ Função `calcular_data_prazo()` centralizada

### Melhorado
- 🔧 Layout em blocos de seções (Documento, Manifestação, etc.)
- 🔧 Fonte monoespaciada (Consolas) para melhor legibilidade de despachos
- 🔧 Validação de SEI e Protocolo com regex
- 🔧 Status bar com informações de processamento
- 🔧 Histórico com ações diretas (reutilizar, copiar)
- 🔧 Atalhos de teclado expandidos

### Corrigido
- 🐛 Problemas de layout com sobreposição de campos
- 🐛 Erros de tipos no analyzer (Pylance/mypy)
- 🐛 Tratamento de atributos opcional (`None`)

## 🚀 Performance

- ⚡ Carregamento instantâneo de modelos
- ⚡ Filtro de busca sem lag
- ⚡ Renderização de cards otimizada
- ⚡ Cálculo de datas eficiente

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
- [PIL](https://python-pillow.org/) - Processamento de imagens

---

**Desenvolvido com ❤️ para facilitar o trabalho com SEI**