# 🎯 Gerador SEI - IA Edition (Local RAG)

Uma aplicação desktop moderna e inteligente para geração, análise e refinamento de despachos SEI (Sistema Eletrônico de Informações). Esta versão é impulsionada por **Inteligência Artificial Local** (LLaMA 3.2 via Ollama), garantindo automação inteligente com **100% de privacidade** e segurança dos dados, sem envio de informações para a nuvem.

## ✨ Funcionalidades

### 🧠 Inteligência Artificial (Ollama + LLaMA)
- **Análise de Processos**: Extração automática de contexto a partir de pastas inteiras contendo PDFs (com suporte a OCR via bibliotecas externas), arquivos do Word (DOCX), HTML e TXT.
- **Assistente Interativo (Chat)**: Converse com a IA para refinar, alterar o tom ou corrigir documentos gerados com comandos em linguagem natural (Ex: "Troque a data de hoje para amanhã").
- **Privacidade e Segurança**: O processamento (Inferência e Embeddings) é feito offline na máquina do usuário, protegendo dados sensíveis do governo.
- **Redação Padronizada GDF**: A IA é configurada com 12 regras estritas de formatação e redação (ex: numeração de parágrafos, formatação de datas, padronização de siglas e proibição de cópias literais).

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

2. **Escolha do Molde IA**: No painel do assistente, deixe a opção **AUTO** para que a IA decida o formato ou obrigue a um estilo específico (ex: `OUVIDORIA MINUTA`, `DILACAO`).

3. **Análise de Processo**: Clique em **📁 Analisar Processo (Pasta)** e selecione o diretório com os arquivos baixados do SEI (PDFs, Word, HTML).

4. **Revisão Natural**: A IA processará tudo e preencherá a tela de "Resultado". Se precisar de ajustes, peça livremente no chat (Ex: *"Mude o prazo para 10 dias úteis"*).

5. **Finalização**: Com a minuta aprovada, utilize os botões **📋 Copiar e Limpar** ou **📄 PDF** diretamente no rodapé da aplicação.

## 🏗️ Arquitetura

```
gerador_sei/
├── gerador_sei.py      # Aplicação principal (GUI)
├── engine.py           # Lógica de negócio e validações
├── theme_config.py     # Configuração de temas e cores
├── sei_templates.py    # Modelos de despacho pré-definidos
├── requirements.txt    # Dependências Python
├── dlls/               # Dependências nativas e bibliotecas dinâmicas do Windows (opcional)
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
- `vetores_ia.json`: Banco de dados nativo RAG contendo memórias de aprendizado (TinyVectorDB)
- `modelos_custom.json`: Modelos personalizados criados pelo usuário

### Formato dos Arquivos JSON

**modelos_custom.json**
```json
{
  "Meu Modelo": "Conteúdo do {SEI_OFICIO} com placeholders..."
}
```
