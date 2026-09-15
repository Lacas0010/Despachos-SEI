/**
 * Gerador SEI - Frontend Application Controller
 * Modern SPA with Real-time SSE Streaming, Markdown Rendering, and Native SEI Clipboard.
 */

// Base URL da API para garantir compatibilidade via http://127.0.0.1:8000 ou arquivo local file://
const API_BASE = (window.location.protocol === 'file:' || !window.location.host) 
  ? 'http://127.0.0.1:8000' 
  : '';

// Application State
const state = {
  activeProcessText: '',
  activeProcessName: '',
  currentDocumentText: '',
  currentDocumentThinking: '',
  selectedHistoryItem: null,
  chatMode: 'Auto',
  theme: localStorage.getItem('theme') || 'dark',
  isStreaming: false,
  loteResultados: []
};

// DOM Elements
const elements = {
  app: document.getElementById('app'),
  btnThemeToggle: document.getElementById('btn-theme-toggle'),
  ollamaStatus: document.getElementById('ollama-status'),
  ollamaStatusText: document.getElementById('ollama-status-text'),
  selectAiModel: document.getElementById('select-ai-model'),
  activeProcessBadge: document.getElementById('active-process-badge'),
  activeProcessName: document.getElementById('active-process-name'),
  btnClearActive: document.getElementById('btn-clear-active'),
  
  // Tabs
  navTabs: document.querySelectorAll('.nav-tab'),
  tabPanes: document.querySelectorAll('.tab-pane'),
  docTabs: document.querySelectorAll('.doc-tab'),
  viewPanes: document.querySelectorAll('.view-pane'),
  
  // Dropzone & Generator
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('file-input'),
  folderInput: document.getElementById('folder-input'),
  btnSelectFolder: document.getElementById('btn-select-folder'),
  btnSelectFile: document.getElementById('btn-select-file'),
  uploadProgress: document.getElementById('upload-progress'),
  uploadProgressText: document.getElementById('upload-progress-text'),
  uploadProgressPercent: document.getElementById('upload-progress-percent'),
  uploadProgressFill: document.getElementById('upload-progress-fill'),
  selectMolde: document.getElementById('select-molde'),
  btnGerarAnalise: document.getElementById('btn-gerar-analise'),
  btnCancelarAnalise: document.getElementById('btn-cancelar-analise'),
  
  // AI Live Generation Banner
  generationBanner: document.getElementById('generation-progress-banner'),
  genProgressTitle: document.getElementById('gen-progress-title'),
  genProgressSubtitle: document.getElementById('gen-progress-subtitle'),
  genTimer: document.getElementById('gen-timer'),
  genCharsCount: document.getElementById('gen-chars-count'),
  genProgressFill: document.getElementById('gen-progress-fill'),
  btnCancelGen: document.getElementById('btn-cancel-gen'),
  
  // Deep Thinking (Chain of Thought / Raciocínio)
  btnToggleThinking: document.getElementById('btn-toggle-thinking'),
  thinkingPanel: document.getElementById('thinking-panel'),
  thinkingBadge: document.getElementById('thinking-badge'),
  thinkingBadgeText: document.getElementById('thinking-badge-text'),
  thinkingBody: document.getElementById('thinking-body'),
  thinkingContent: document.getElementById('thinking-content'),
  btnCopyThinking: document.getElementById('btn-copy-thinking'),
  btnCollapseThinking: document.getElementById('btn-collapse-thinking'),
  iconCollapseThinking: document.getElementById('icon-collapse-thinking'),
  btnCloseThinking: document.getElementById('btn-close-thinking'),

  // Chat
  chatMessages: document.getElementById('chat-messages'),
  chatInput: document.getElementById('chat-input'),
  btnSendChat: document.getElementById('btn-send-chat'),
  btnCancelChat: document.getElementById('btn-cancel-chat'),
  chatGeneratingIndicator: document.getElementById('chat-generating-indicator'),
  btnCancelChatTop: document.getElementById('btn-cancel-chat-top'),
  chatModePills: document.querySelectorAll('.mode-pill'),
  
  // Document Views
  docRenderContent: document.getElementById('doc-render-content'),
  docRawEditor: document.getElementById('doc-raw-editor'),
  autosRawContent: document.getElementById('autos-raw-content'),
  autosInfoText: document.getElementById('autos-info-text'),
  
  // Actions
  btnCopySei: document.getElementById('btn-copy-sei'),
  btnCopyPlain: document.getElementById('btn-copy-plain'),
  btnExportDocx: document.getElementById('btn-export-docx'),
  btnExportPdf: document.getElementById('btn-export-pdf'),
  btnClearDoc: document.getElementById('btn-clear-doc'),
  
  // Histórico
  historicoSearch: document.getElementById('historico-search'),
  historicoList: document.getElementById('historico-list'),
  histDetailActions: document.getElementById('hist-detail-actions'),
  histSelectedTitle: document.getElementById('hist-selected-title'),
  btnHistLoad: document.getElementById('btn-hist-load'),
  btnHistChat: document.getElementById('btn-hist-chat'),
  btnHistCopySei: document.getElementById('btn-hist-copy-sei'),
  btnHistDel: document.getElementById('btn-hist-del'),
  
  // Triagem em Lote
  loteDropzone: document.getElementById('lote-dropzone'),
  loteFileInput: document.getElementById('lote-file-input'),
  loteStatusContainer: document.getElementById('lote-status-container'),
  loteStatusMsg: document.getElementById('lote-status-msg'),
  loteProgressFill: document.getElementById('lote-progress-fill'),
  btnCancelarLote: document.getElementById('btn-cancelar-lote'),
  loteResultsList: document.getElementById('lote-results-list'),
  btnExportLoteCsv: document.getElementById('btn-export-lote-csv'),
  
  // Status Bar
  appStatusMessage: document.getElementById('app-status-message'),
  docStats: document.getElementById('doc-stats'),
  toastContainer: document.getElementById('toast-container')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initLucide();
  initTabs();
  initDropzones();
  initThinking();
  initChat();
  initActions();
  initHistorico();
  initShortcuts();
  initModelSelector();
  checkSystemStatus();
  loadHistorico();
  setInterval(checkSystemStatus, 8000);
});

// --- Theme Management ---
function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  elements.btnThemeToggle.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    initLucide();
  });
}

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// --- Tabs Management ---
function initTabs() {
  // Sidebar Tabs
  elements.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      elements.navTabs.forEach(t => t.classList.remove('active'));
      elements.tabPanes.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(targetTab)?.classList.add('active');
      initLucide();
    });
  });

  // Document Views Tabs
  elements.docTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const view = tab.getAttribute('data-view');
      elements.docTabs.forEach(t => t.classList.remove('active'));
      elements.viewPanes.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(`view-${view}`)?.classList.add('active');
      
      if (view === 'editor') {
        elements.docRawEditor.value = state.currentDocumentText;
      }
      initLucide();
    });
  });

  // Editor Real-time Sync
  elements.docRawEditor.addEventListener('input', (e) => {
    state.currentDocumentText = e.target.value;
    renderDocument(state.currentDocumentText);
    updateDocStats();
  });
}

// --- Model Selector & Healthcheck ---
function initModelSelector() {
  if (!elements.selectAiModel) return;
  elements.selectAiModel.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;
    try {
      const res = await fetch(`${API_BASE}/api/selecionar-modelo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelo: selectedModel })
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`Modelo ativo alterado para ${data.modelo_ativo}`, 'success');
        checkSystemStatus();
      } else {
        showToast('Erro ao trocar modelo de IA.', 'error');
      }
    } catch (err) {
      showToast('Falha na comunicação com o servidor.', 'error');
    }
  });
}

async function checkSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    if (data.ollama_conectado) {
      elements.ollamaStatus.className = 'status-pill status-online';
      elements.ollamaStatusText.textContent = `IA Online (${data.modelo_ativo})`;
      
      // Atualiza dropdown de modelos se disponível
      if (elements.selectAiModel && data.modelos_ollama && data.modelos_ollama.length > 0) {
        const activeModel = data.modelo_ativo || 'llama3.2';
        
        // Verifica se a lista de opções mudou antes de recriar
        const existingValues = Array.from(elements.selectAiModel.options).map(o => o.value);
        const newValues = data.modelos_ollama.map(m => m.split(':')[0]);
        
        const isDifferent = existingValues.length !== newValues.length || !existingValues.every((v, i) => v === newValues[i]);
        if (isDifferent) {
          elements.selectAiModel.innerHTML = '';
          data.modelos_ollama.forEach(m => {
            const opt = document.createElement('option');
            const cleanName = m.split(':')[0];
            opt.value = cleanName;
            opt.textContent = cleanName === 'llama3.2' ? 'LLaMA 3.2 (Recomendado)' : (cleanName === 'gemma4' ? 'Gemma 4 (8B)' : cleanName);
            elements.selectAiModel.appendChild(opt);
          });
        }
        elements.selectAiModel.value = activeModel;
      }
    } else {
      elements.ollamaStatus.className = 'status-pill status-offline';
      elements.ollamaStatusText.textContent = 'IA Offline (Inicie o Ollama)';
    }
  } catch (err) {
    elements.ollamaStatus.className = 'status-pill status-offline';
    elements.ollamaStatusText.textContent = 'Servidor Desconectado';
  }
}

// --- Dropzone & File/Folder Upload ---
function initDropzones() {
  // Main Process Dropzone & Inputs
  const dropzone = elements.dropzone;
  const fileInput = elements.fileInput;
  const folderInput = elements.folderInput;

  // Botões de Seleção Específicos (Abrem seletor do navegador instantaneamente)
  elements.btnSelectFolder?.addEventListener('click', (e) => {
    e.stopPropagation();
    folderInput.click();
  });

  elements.btnSelectFile?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('change', (e) => {
    if (e.target.files?.length) handleFileUpload(e.target.files[0]);
  });

  folderInput.addEventListener('change', (e) => {
    if (e.target.files?.length) handleFolderUpload(e.target.files);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    
    // Tratamento avançado de Drag & Drop de Pasta ou Arquivo
    const items = e.dataTransfer.items;
    if (items && items.length > 0) {
      const entry = items[0].webkitGetAsEntry ? items[0].webkitGetAsEntry() : null;
      if (entry && entry.isDirectory) {
        // Usuário arrastou uma pasta completa
        const files = await scanDirectoryFiles(entry);
        if (files.length > 0) {
          handleFolderUpload(files);
          return;
        }
      }
    }

    if (e.dataTransfer.files?.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // Triagem em Lote Dropzone
  const loteDropzone = elements.loteDropzone;
  const loteFileInput = elements.loteFileInput;

  loteDropzone.addEventListener('click', () => loteFileInput.click());
  loteFileInput.addEventListener('change', (e) => {
    if (e.target.files?.length) handleLoteUpload(e.target.files[0]);
  });

  loteDropzone.addEventListener('dragover', (e) => { e.preventDefault(); loteDropzone.classList.add('dragover'); });
  loteDropzone.addEventListener('dragleave', () => loteDropzone.classList.remove('dragover'));
  loteDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    loteDropzone.classList.remove('dragover');
    if (e.dataTransfer.files?.length) handleLoteUpload(e.dataTransfer.files[0]);
  });

  elements.btnCancelarLote?.addEventListener('click', (e) => {
    e.stopPropagation();
    cancelarProcessoIA('lote');
  });

  // Clear Active Process
  elements.btnClearActive.addEventListener('click', (e) => {
    e.stopPropagation();
    state.activeProcessText = '';
    state.activeProcessName = '';
    elements.activeProcessBadge.classList.add('hidden');
    elements.autosInfoText.textContent = 'Nenhum processo carregado';
    elements.autosRawContent.value = '';
    showToast('Processo descarregado.', 'info');
  });
}

// --- Progress & Activity Controllers ---
let genTimerInterval = null;
let genStartTime = null;
let currentAbortController = null;

function showUploadProgress(message = 'Processando documentos...', percent = null, isIndeterminate = false) {
  if (!elements.uploadProgress) return;
  elements.uploadProgress.classList.remove('hidden');
  if (elements.uploadProgressText) elements.uploadProgressText.textContent = message;
  
  if (elements.uploadProgressFill) {
    if (isIndeterminate) {
      elements.uploadProgressFill.classList.add('indeterminate');
      if (elements.uploadProgressPercent) elements.uploadProgressPercent.textContent = '...';
    } else {
      elements.uploadProgressFill.classList.remove('indeterminate');
      const pct = Math.max(0, Math.min(100, percent || 0));
      elements.uploadProgressFill.style.width = `${pct}%`;
      if (elements.uploadProgressPercent) elements.uploadProgressPercent.textContent = `${pct}%`;
    }
  }
}

function hideUploadProgress(delay = 600) {
  setTimeout(() => {
    if (elements.uploadProgress) {
      elements.uploadProgress.classList.add('hidden');
      if (elements.uploadProgressFill) {
        elements.uploadProgressFill.classList.remove('indeterminate');
        elements.uploadProgressFill.style.width = '0%';
      }
    }
  }, delay);
}

function startGenerationProgress(title = 'Gerando Documento com IA...', subtitle = 'Ollama processando autos e formatando redação oficial') {
  if (elements.generationBanner) {
    elements.generationBanner.classList.remove('hidden');
    if (elements.genProgressTitle) elements.genProgressTitle.textContent = title;
    if (elements.genProgressSubtitle) elements.genProgressSubtitle.textContent = subtitle;
    if (elements.genCharsCount) elements.genCharsCount.innerHTML = '<i data-lucide="activity"></i> 0 caracteres';
  }
  
  // Inicia contador de tempo ao vivo
  genStartTime = Date.now();
  if (genTimerInterval) clearInterval(genTimerInterval);
  genTimerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - genStartTime) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const secs = String(elapsed % 60).padStart(2, '0');
    if (elements.genTimer) {
      elements.genTimer.innerHTML = `<i data-lucide="clock"></i> ${mins}:${secs}s`;
      if (window.lucide) window.lucide.createIcons();
    }
  }, 1000);
  
  if (elements.btnGerarAnalise) {
    elements.btnGerarAnalise.classList.add('hidden');
  }
  if (elements.btnCancelarAnalise) {
    elements.btnCancelarAnalise.classList.remove('hidden');
  }
  initLucide();
}

function updateGenerationProgress(charsReceived) {
  if (elements.genCharsCount) {
    elements.genCharsCount.innerHTML = `<i data-lucide="activity"></i> ${charsReceived.toLocaleString()} caracteres`;
  }
  setStatus(`Ollama redigindo: ${charsReceived.toLocaleString()} caracteres gerados...`);
}

function stopGenerationProgress(success = true) {
  if (genTimerInterval) {
    clearInterval(genTimerInterval);
    genTimerInterval = null;
  }
  
  if (elements.btnGerarAnalise) {
    elements.btnGerarAnalise.classList.remove('hidden');
    elements.btnGerarAnalise.disabled = false;
    elements.btnGerarAnalise.innerHTML = '<i data-lucide="sparkles"></i> <span>Gerar Análise / Minuta</span>';
  }
  if (elements.btnCancelarAnalise) {
    elements.btnCancelarAnalise.classList.add('hidden');
  }
  
  const delay = success === false ? 200 : 1200;
  setTimeout(() => {
    if (elements.generationBanner && !state.isStreaming) {
      elements.generationBanner.classList.add('hidden');
    }
  }, delay);
  
  initLucide();
}

function startChatGenerating() {
  if (elements.chatGeneratingIndicator) elements.chatGeneratingIndicator.classList.remove('hidden');
  if (elements.btnSendChat) elements.btnSendChat.classList.add('hidden');
  if (elements.btnCancelChat) elements.btnCancelChat.classList.remove('hidden');
  initLucide();
}

function stopChatGenerating() {
  if (elements.chatGeneratingIndicator) elements.chatGeneratingIndicator.classList.add('hidden');
  if (elements.btnSendChat) elements.btnSendChat.classList.remove('hidden');
  if (elements.btnCancelChat) elements.btnCancelChat.classList.add('hidden');
  initLucide();
}

async function cancelarProcessoIA(origem = 'geral') {
  if (!state.isStreaming && !currentAbortController) {
    return;
  }

  setStatus('Cancelando processo da IA...');

  // 1. Aborta o fetch SSE local imediatamente
  if (currentAbortController) {
    try {
      currentAbortController.abort();
    } catch (e) {}
    currentAbortController = null;
  }

  // 2. Notifica o backend para interromper o loop com o Ollama
  try {
    fetch(`${API_BASE}/api/cancelar-ia`, { method: 'POST' }).catch(() => {});
  } catch (e) {}

  state.isStreaming = false;

  // 3. Atualiza componentes visuais
  stopGenerationProgress(false);
  stopChatGenerating();

  if (elements.loteStatusContainer) {
    elements.loteStatusContainer.classList.add('hidden');
  }

  setStatus('Processamento de IA cancelado pelo usuário.');
  showToast('Processamento cancelado com sucesso.', 'info');
  initLucide();
}

// 1. Seleção de Pasta Nativa do Windows (Direto pelo Explorer)
async function handleSelectFolderNative() {
  setStatus('Aguardando seleção da pasta no Explorer...');
  showUploadProgress('Aguardando seleção da pasta no Windows Explorer...', null, true);
  
  try {
    const res = await fetch(`${API_BASE}/api/selecionar-pasta-local`, { method: 'POST' });
    showUploadProgress('Lendo documentos e extraindo texto integral dos autos...', 70, false);
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      showToast(errData.detail || 'Erro ao carregar pasta.', 'error');
      hideUploadProgress(100);
      elements.folderInput.click();
      return;
    }
    const data = await res.json();
    if (data.cancelado) {
      setStatus('Seleção cancelada.');
      hideUploadProgress(100);
      return;
    }
    if (data.sucesso) {
      showUploadProgress(`Concluído! ${data.tamanho_caracteres.toLocaleString()} caracteres extraídos.`, 100, false);
      applyProcessoLoaded(data);
      hideUploadProgress(700);
    } else {
      showToast(data.detail || data.erro || 'Erro ao carregar pasta.', 'error');
      hideUploadProgress(100);
    }
  } catch (err) {
    hideUploadProgress(100);
    elements.folderInput.click();
  }
}

// 2. Seleção de Arquivo Nativa do Windows
async function handleSelectFileNative() {
  setStatus('Aguardando seleção de arquivo no Explorer...');
  showUploadProgress('Aguardando seleção de arquivo no Windows Explorer...', null, true);
  
  try {
    const res = await fetch(`${API_BASE}/api/selecionar-arquivo-local`, { method: 'POST' });
    showUploadProgress('Extraindo texto do arquivo selecionado...', 70, false);
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      showToast(errData.detail || 'Erro ao carregar arquivo.', 'error');
      hideUploadProgress(100);
      elements.fileInput.click();
      return;
    }
    const data = await res.json();
    if (data.cancelado) {
      setStatus('Seleção cancelada.');
      hideUploadProgress(100);
      return;
    }
    if (data.sucesso) {
      showUploadProgress(`Concluído! ${data.tamanho_caracteres.toLocaleString()} caracteres extraídos.`, 100, false);
      applyProcessoLoaded(data);
      hideUploadProgress(700);
    } else {
      showToast(data.detail || data.erro || 'Erro ao carregar arquivo.', 'error');
      hideUploadProgress(100);
    }
  } catch (err) {
    hideUploadProgress(100);
    elements.fileInput.click();
  }
}

// 3. Upload de Múltiplos Arquivos de uma Pasta (via Web)
async function handleFolderUpload(files) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const path = file.webkitRelativePath || file.name;
    formData.append('files', file, path);
  }

  setStatus(`Lendo pasta com ${files.length} arquivos...`);
  showUploadProgress(`Enviando e extraindo ${files.length} arquivos da pasta...`, 40, false);

  try {
    const res = await fetch(`${API_BASE}/api/upload-pasta-multipla`, { method: 'POST', body: formData });
    showUploadProgress('Processando autos e documentos no servidor...', 80, false);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `Erro HTTP ${res.status}` }));
      showToast(errData.detail || 'Erro ao processar pasta.', 'error');
      setStatus('Erro no carregamento.');
      hideUploadProgress(100);
      return;
    }
    const data = await res.json();
    showUploadProgress('Processamento concluído!', 100, false);

    if (data.sucesso) {
      applyProcessoLoaded(data);
      hideUploadProgress(800);
    } else {
      showToast(data.detail || data.erro || 'Erro ao processar pasta.', 'error');
      hideUploadProgress(100);
    }
  } catch (err) {
    showToast(`Falha no upload da pasta: ${err.message}. Verifique se o servidor backend está iniciado.`, 'error');
    setStatus('Falha no upload.');
    hideUploadProgress(100);
  }
}

// 4. Upload de Arquivo Único (.zip, .pdf, .docx)
async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  setStatus(`Lendo arquivo: ${file.name}...`);
  showUploadProgress(`Enviando ${file.name}...`, 40, false);

  try {
    const res = await fetch(`${API_BASE}/api/upload-processo`, { method: 'POST', body: formData });
    showUploadProgress('Extraindo texto integral dos autos...', 80, false);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: `Erro HTTP ${res.status}` }));
      showToast(errData.detail || 'Erro ao carregar arquivo.', 'error');
      setStatus('Erro no carregamento.');
      hideUploadProgress(100);
      return;
    }
    const data = await res.json();
    showUploadProgress('Arquivo processado com sucesso!', 100, false);

    if (data.sucesso) {
      applyProcessoLoaded(data);
      hideUploadProgress(800);
    } else {
      showToast(data.detail || data.erro || 'Erro ao carregar arquivo.', 'error');
      setStatus('Erro no carregamento.');
      hideUploadProgress(100);
    }
  } catch (err) {
    showToast(`Falha no upload: ${err.message}. Verifique se o servidor backend está iniciado.`, 'error');
    setStatus('Falha no upload.');
    hideUploadProgress(100);
  }
}

// Helper: Aplica os dados do processo carregado no estado e interface
function applyProcessoLoaded(data) {
  state.activeProcessText = data.texto_processo;
  state.activeProcessName = data.nome_processo;

  // Atualiza Badge
  elements.activeProcessName.textContent = data.nome_processo;
  elements.activeProcessBadge.classList.remove('hidden');

  // Atualiza Inspetor de Autos
  elements.autosInfoText.textContent = `📄 ${data.nome_processo} (${data.tamanho_caracteres.toLocaleString()} caracteres extraídos)`;
  elements.autosRawContent.value = data.texto_processo;

  appendChatMessage('bot', `Processo **${data.nome_processo}** carregado com sucesso!\n\nVocê já pode selecionar um molde e clicar em **Gerar Análise / Minuta** ou fazer perguntas aqui no chat.`);
  showToast(`Processo carregado: ${data.nome_processo}`, 'success');
  setStatus('Processo carregado e pronto para análise.');
}

// Helper: Varre recursivamente arquivos de diretório arrastado no browser
async function scanDirectoryFiles(entry) {
  const files = [];
  async function readEntries(dirReader) {
    return new Promise((resolve) => {
      dirReader.readEntries((entries) => resolve(entries), () => resolve([]));
    });
  }
  async function traverse(item) {
    if (item.isFile) {
      const file = await new Promise((resolve) => item.file((f) => resolve(f)));
      files.push(file);
    } else if (item.isDirectory) {
      const dirReader = item.createReader();
      let entries = await readEntries(dirReader);
      while (entries.length > 0) {
        for (const e of entries) {
          await traverse(e);
        }
        entries = await readEntries(dirReader);
      }
    }
  }
  await traverse(entry);
  return files;
}

// --- Deep Thinking (Raciocínio IA) Controller ---
function initThinking() {
  elements.btnToggleThinking?.addEventListener('click', () => {
    const isHidden = elements.thinkingPanel.classList.contains('hidden');
    if (isHidden) {
      elements.thinkingPanel.classList.remove('hidden');
      elements.btnToggleThinking.classList.add('active');
    } else {
      elements.thinkingPanel.classList.add('hidden');
      elements.btnToggleThinking.classList.remove('active');
    }
  });

  elements.btnCollapseThinking?.addEventListener('click', () => {
    elements.thinkingPanel.classList.toggle('collapsed');
    const isCollapsed = elements.thinkingPanel.classList.contains('collapsed');
    if (elements.iconCollapseThinking) {
      elements.iconCollapseThinking.setAttribute('data-lucide', isCollapsed ? 'chevron-down' : 'chevron-up');
    }
    initLucide();
  });

  elements.btnCloseThinking?.addEventListener('click', () => {
    elements.thinkingPanel.classList.add('hidden');
    elements.btnToggleThinking.classList.remove('active');
  });

  elements.btnCopyThinking?.addEventListener('click', () => {
    if (!state.currentDocumentThinking) return showToast('Nenhum raciocínio para copiar.', 'info');
    navigator.clipboard.writeText(state.currentDocumentThinking);
    showToast('Raciocínio copiado com sucesso!', 'success');
  });
}

function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return String(unsafe)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function processStreamingThinking(rawText) {
  if (!rawText) return { clean: '', thinking: '', isThinking: false, isDone: true };

  if (rawText.includes('<think>')) {
    if (rawText.includes('</think>')) {
      const parts = rawText.split('</think>');
      const thinking = parts[0].replace('<think>', '').trim();
      const clean = parts[1].trim();
      return { clean, thinking, isThinking: true, isDone: true };
    } else {
      const thinking = rawText.substring(rawText.indexOf('<think>') + 7).trim();
      return { clean: '', thinking, isThinking: true, isDone: false };
    }
  }

  return { clean: rawText, thinking: '', isThinking: false, isDone: true };
}

function updateThinkingDisplay(thinkingText, isDone = false) {
  state.currentDocumentThinking = thinkingText;
  if (!thinkingText) {
    elements.thinkingPanel?.classList.add('hidden');
    elements.btnToggleThinking?.classList.remove('active', 'pulse-glow');
    return;
  }

  elements.thinkingPanel?.classList.remove('hidden');

  if (!isDone) {
    elements.btnToggleThinking?.classList.add('pulse-glow', 'active');
    if (elements.thinkingBadge) {
      elements.thinkingBadge.className = 'thinking-badge-live';
      elements.thinkingBadge.innerHTML = '<span class="thinking-pulse-dot"></span> <span id="thinking-badge-text">Raciocinando em tempo real...</span>';
    }
    if (elements.thinkingContent) {
      elements.thinkingContent.textContent = thinkingText;
      if (elements.thinkingBody) elements.thinkingBody.scrollTop = elements.thinkingBody.scrollHeight;
    }
  } else {
    elements.btnToggleThinking?.classList.remove('pulse-glow');
    const words = thinkingText.trim().split(/\s+/).filter(Boolean).length;
    if (elements.thinkingBadge) {
      elements.thinkingBadge.className = 'thinking-badge-done';
      elements.thinkingBadge.innerHTML = `<i data-lucide="check-circle-2"></i> <span id="thinking-badge-text">Raciocínio Concluído (${words} palavras)</span>`;
    }
    if (elements.thinkingContent) {
      elements.thinkingContent.textContent = thinkingText;
    }
    initLucide();
  }
}

function clearDocumentThinking() {
  state.currentDocumentThinking = '';
  if (elements.thinkingPanel) elements.thinkingPanel.classList.add('hidden');
  if (elements.btnToggleThinking) {
    elements.btnToggleThinking.classList.remove('active', 'pulse-glow');
  }
  if (elements.thinkingContent) elements.thinkingContent.innerHTML = '<em>Nenhum raciocínio capturado para este documento ainda.</em>';
}

// --- Generator & Streaming Analysis ---
function initActions() {
  elements.btnGerarAnalise.addEventListener('click', () => {
    if (!state.activeProcessText) {
      showToast('Carregue primeiro um processo (.zip, .pdf, .docx)', 'error');
      return;
    }
    gerarAnaliseStream();
  });

  elements.btnCancelarAnalise?.addEventListener('click', () => {
    cancelarProcessoIA('painel');
  });

  elements.btnCancelGen?.addEventListener('click', () => {
    cancelarProcessoIA('banner');
  });

  elements.btnCopySei.addEventListener('click', copyToSeiHtml);
  elements.btnCopyPlain.addEventListener('click', copyPlain);
  elements.btnExportDocx.addEventListener('click', exportDocx);
  elements.btnExportPdf.addEventListener('click', exportPdf);
  elements.btnClearDoc.addEventListener('click', clearDocument);
  elements.btnExportLoteCsv.addEventListener('click', exportLoteCsv);
}

async function gerarAnaliseStream() {
  if (state.isStreaming) return;
  state.isStreaming = true;
  currentAbortController = new AbortController();

  const molde = elements.selectMolde.value;
  startGenerationProgress(`Gerando [${molde}] com Inteligência Artificial...`, 'Ollama conectado • Analisando autos e redigindo minuta oficial');
  setStatus(`Ollama gerando [${molde}]...`);

  // Switch to Formatted View tab
  document.querySelector('.doc-tab[data-view="formatted"]')?.click();
  elements.docRenderContent.innerHTML = '<div class="streaming-loading"><div class="spinner-sm"></div> Processando autos e gerando documento com IA...</div>';
  clearDocumentThinking();

  try {
    const res = await fetch(`${API_BASE}/api/analisar-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        texto_processo: state.activeProcessText,
        nome_processo: state.activeProcessName,
        molde: molde
      }),
      signal: currentAbortController.signal
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop(); // keep partial chunk

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.substring(6));
            if (payload.type === 'stream') {
              const parsed = processStreamingThinking(payload.full_text);
              if (parsed.isThinking) {
                updateThinkingDisplay(parsed.thinking, parsed.isDone);
                if (!parsed.isDone) {
                  elements.docRenderContent.innerHTML = `
                    <div class="streaming-loading">
                      <div class="spinner-sm"></div>
                      <strong style="color: var(--primary);">IA analisando os autos e construindo o raciocínio...</strong>
                      <div style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
                        Acompanhe o <strong>Deep Thinking</strong> em tempo real na janela acima ☝️
                      </div>
                    </div>`;
                  updateGenerationProgress(parsed.thinking.length);
                } else {
                  state.currentDocumentText = parsed.clean;
                  renderDocument(parsed.clean);
                  updateDocStats();
                  updateGenerationProgress(parsed.clean.length);
                }
              } else {
                state.currentDocumentText = parsed.clean;
                renderDocument(parsed.clean);
                updateDocStats();
                updateGenerationProgress(parsed.clean.length);
              }
            } else if (payload.type === 'done') {
              if (payload.cancelado) {
                showToast('Geração cancelada.', 'info');
                setStatus('Geração cancelada pelo usuário.');
                stopGenerationProgress(false);
              } else if (payload.sucesso) {
                state.currentDocumentText = payload.texto_gerado;
                if (payload.raciocinio) {
                  updateThinkingDisplay(payload.raciocinio, true);
                }
                renderDocument(payload.texto_gerado);
                updateDocStats();
                showToast(`[${payload.tipo_documento}] gerado com sucesso!`, 'success');
                setStatus('Documento concluído e salvo no histórico.');
                loadHistorico();
                stopGenerationProgress(true);
              } else {
                showToast(payload.erro || 'Erro na geração.', 'error');
                setStatus('Erro na geração da IA.');
                stopGenerationProgress(false);
              }
            }
          } catch (e) {}
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      setStatus('Geração cancelada pelo usuário.');
      showToast('Geração cancelada.', 'info');
    } else {
      showToast(`Erro de conexão: ${err.message}`, 'error');
      setStatus('Falha na comunicação.');
    }
    stopGenerationProgress(false);
  } finally {
    state.isStreaming = false;
    currentAbortController = null;
    stopGenerationProgress();
  }
}

// --- Chat & Q&A / Refine ---
function initChat() {
  // Mode selection
  elements.chatModePills.forEach(pill => {
    pill.addEventListener('click', () => {
      elements.chatModePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.chatMode = pill.getAttribute('data-mode');
    });
  });

  elements.btnSendChat.addEventListener('click', sendChatMessage);
  elements.btnCancelChat?.addEventListener('click', () => cancelarProcessoIA('chat'));
  elements.btnCancelChatTop?.addEventListener('click', () => cancelarProcessoIA('chat-top'));

  elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || !e.shiftKey)) {
      e.preventDefault();
      sendChatMessage();
    }
  });
}

async function sendChatMessage() {
  const msg = elements.chatInput.value.trim();
  if (!msg || state.isStreaming) return;

  elements.chatInput.value = '';
  appendChatMessage('user', msg);

  state.isStreaming = true;
  currentAbortController = new AbortController();
  startChatGenerating();
  setStatus('Ollama pensando...');

  const botBubble = appendChatMessage('bot', '...', true);

  try {
    const res = await fetch(`${API_BASE}/api/chat-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: msg,
        texto_processo: state.activeProcessText,
        nome_processo: state.activeProcessName,
        modo: state.chatMode,
        texto_atual_documento: state.currentDocumentText
      }),
      signal: currentAbortController.signal
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.substring(6));
            if (payload.type === 'stream') {
              const parsed = processStreamingThinking(payload.full_text);
              if (parsed.isThinking) {
                if (!parsed.isDone) {
                  botBubble.innerHTML = `
                    <details class="chat-thinking-accordion" open>
                      <summary class="chat-thinking-summary">
                        <div class="chat-thinking-badge">
                          <div class="spinner-sm" style="width: 12px; height: 12px;"></div>
                          <span>Raciocinando (Deep Thinking)...</span>
                        </div>
                        <span style="font-size: 10px; color: #F59E0B; font-weight: 700;">Ao vivo</span>
                      </summary>
                      <div class="chat-thinking-content">${escapeHtml(parsed.thinking)}</div>
                    </details>`;
                } else {
                  const words = parsed.thinking.trim().split(/\s+/).filter(Boolean).length;
                  const parsedMd = parsed.clean ? (window.marked ? window.marked.parse(parsed.clean) : parsed.clean) : '<em>Redigindo resposta...</em>';
                  botBubble.innerHTML = `
                    <details class="chat-thinking-accordion">
                      <summary class="chat-thinking-summary">
                        <div class="chat-thinking-badge">
                          <i data-lucide="brain"></i>
                          <span>Raciocínio do Modelo (${words} palavras)</span>
                        </div>
                        <span style="font-size: 10px; opacity: 0.75;">Ver Raciocínio</span>
                      </summary>
                      <div class="chat-thinking-content">${escapeHtml(parsed.thinking)}</div>
                    </details>
                    <div class="chat-bubble-main-content">${parsedMd}</div>`;
                  initLucide();
                }
              } else {
                botBubble.innerHTML = window.marked ? window.marked.parse(parsed.clean) : parsed.clean;
              }
              elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            } else if (payload.type === 'done') {
              if (payload.cancelado) {
                botBubble.innerHTML += '<div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;"><em>⏹️ Resposta interrompida pelo usuário.</em></div>';
                setStatus('Resposta cancelada pelo usuário.');
                showToast('Resposta cancelada.', 'info');
              } else if (payload.sucesso) {
                const finalThinking = payload.raciocinio || '';
                const finalAnswer = payload.texto_gerado || '';
                if (finalThinking) {
                  const words = finalThinking.trim().split(/\s+/).filter(Boolean).length;
                  const parsedMd = window.marked ? window.marked.parse(finalAnswer) : finalAnswer;
                  botBubble.innerHTML = `
                    <details class="chat-thinking-accordion">
                      <summary class="chat-thinking-summary">
                        <div class="chat-thinking-badge">
                          <i data-lucide="brain"></i>
                          <span>Raciocínio do Modelo (${words} palavras)</span>
                        </div>
                        <span style="font-size: 10px; opacity: 0.75;">Ver Raciocínio</span>
                      </summary>
                      <div class="chat-thinking-content">${escapeHtml(finalThinking)}</div>
                    </details>
                    <div class="chat-bubble-main-content">${parsedMd}</div>`;
                  initLucide();
                } else {
                  botBubble.innerHTML = window.marked ? window.marked.parse(finalAnswer) : finalAnswer;
                }
                if (payload.is_refinement) {
                  state.currentDocumentText = payload.texto_gerado;
                  renderDocument(payload.texto_gerado);
                  updateDocStats();
                  showToast('Documento atualizado com as instruções!', 'success');
                }
                setStatus('Resposta concluída.');
                loadHistorico();
              } else {
                botBubble.innerHTML = `<span style="color: var(--danger);">${payload.erro || 'Erro'}</span>`;
                setStatus('Erro na resposta.');
              }
            }
          } catch (e) {}
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      botBubble.innerHTML += '<div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;"><em>⏹️ Resposta interrompida pelo usuário.</em></div>';
      setStatus('Resposta cancelada pelo usuário.');
      showToast('Resposta cancelada.', 'info');
    } else {
      botBubble.innerHTML = `<span style="color: var(--danger);">Falha de conexão: ${err.message}</span>`;
      setStatus('Falha de conexão.');
    }
  } finally {
    state.isStreaming = false;
    currentAbortController = null;
    stopChatGenerating();
    initLucide();
  }
}

function appendChatMessage(role, text, returnElement = false) {
  const welcome = elements.chatMessages.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  const author = document.createElement('div');
  author.className = 'chat-bubble-author';
  author.textContent = role === 'user' ? 'Você' : 'Ollama (IA)';
  bubble.appendChild(author);

  const content = document.createElement('div');
  content.className = 'chat-bubble-content';
  content.innerHTML = window.marked ? window.marked.parse(text) : text;
  bubble.appendChild(content);

  elements.chatMessages.appendChild(bubble);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  initLucide();

  return returnElement ? content : bubble;
}

// --- Document Rendering & Stats ---
function renderDocument(markdownText) {
  if (!markdownText) {
    elements.docRenderContent.innerHTML = `
      <div class="empty-doc-placeholder">
        <i data-lucide="file-signature"></i>
        <h2>Área de Documento & Análise</h2>
        <p>Arraste um processo no painel à esquerda ou selecione um item no <strong>Histórico</strong> para começar.</p>
      </div>`;
    initLucide();
    return;
  }

  // Parse Markdown using marked.js
  let html = window.marked ? window.marked.parse(markdownText) : markdownText;
  
  // Highlight SEI numbers and dates
  html = html.replace(/\b(\d{6,})\b/g, '<span class="sei-num-tag">$1</span>');
  html = html.replace(/\b(SUJEITO A PRAZO|EXPIRADO|TEMPESTIVO|NÃO CONFORME|URGENTE)\b/g, '<span class="sei-alert-tag">$1</span>');

  elements.docRenderContent.innerHTML = html;
  elements.docRawEditor.value = markdownText;
}

function updateDocStats() {
  const text = state.currentDocumentText || '';
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const chars = text.length;
  elements.docStats.textContent = `${words} palavras | ${chars} caracteres`;
}

// --- Clipboard & Native SEI Copy ---
async function copyToSeiHtml() {
  const text = state.currentDocumentText;
  if (!text) {
    showToast('Não há documento para copiar.', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/converter-sei-html`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto: text })
    });
    const data = await res.json();
    const htmlFormatted = data.html || text;

    // Use modern Clipboard API for text/html format
    const blobHtml = new Blob([htmlFormatted], { type: 'text/html' });
    const blobText = new Blob([text], { type: 'text/plain' });
    const item = new ClipboardItem({
      'text/html': blobHtml,
      'text/plain': blobText
    });

    await navigator.clipboard.write([item]);

    // Visual Feedback
    const origText = elements.btnCopySei.innerHTML;
    elements.btnCopySei.innerHTML = '<i data-lucide="check"></i> Copiado p/ SEI!';
    elements.btnCopySei.style.backgroundColor = 'var(--accent)';
    initLucide();

    setTimeout(() => {
      elements.btnCopySei.innerHTML = origText;
      elements.btnCopySei.style.backgroundColor = '';
      initLucide();
    }, 1800);

    showToast('Copiado com formatação oficial do SEI!', 'success');
  } catch (err) {
    // Fallback to plain text copy
    navigator.clipboard.writeText(text);
    showToast('Copiado em texto puro.', 'info');
  }
}

function copyPlain() {
  const text = state.currentDocumentText;
  if (!text) return;
  navigator.clipboard.writeText(text);
  showToast('Texto puro copiado.', 'success');
}

function clearDocument() {
  state.currentDocumentText = '';
  clearDocumentThinking();
  renderDocument('');
  updateDocStats();
  showToast('Documento limpo.', 'info');
}

// --- Export Files ---
async function exportDocx() {
  if (!state.currentDocumentText) return showToast('Nada para exportar.', 'error');
  try {
    const res = await fetch(`${API_BASE}/api/exportar/docx`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto: state.currentDocumentText, nome_arquivo: state.activeProcessName || 'documento' })
    });
    const blob = await res.blob();
    downloadBlob(blob, `${state.activeProcessName || 'documento'}.docx`);
    showToast('Documento Word (.docx) baixado!', 'success');
  } catch (e) {
    showToast('Erro ao exportar Word.', 'error');
  }
}

async function exportPdf() {
  if (!state.currentDocumentText) return showToast('Nada para exportar.', 'error');
  try {
    const res = await fetch(`${API_BASE}/api/exportar/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto: state.currentDocumentText, nome_arquivo: state.activeProcessName || 'documento' })
    });
    const blob = await res.blob();
    downloadBlob(blob, `${state.activeProcessName || 'documento'}.pdf`);
    showToast('Documento PDF baixado!', 'success');
  } catch (e) {
    showToast('Erro ao exportar PDF.', 'error');
  }
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// --- Histórico Management ---
function initHistorico() {
  elements.historicoSearch.addEventListener('input', (e) => {
    loadHistorico(e.target.value.trim());
  });

  // Action Buttons
  elements.btnHistLoad.addEventListener('click', () => {
    if (!state.selectedHistoryItem) return;
    loadHistoryItemAsActive(state.selectedHistoryItem);
  });

  elements.btnHistChat.addEventListener('click', () => {
    if (!state.selectedHistoryItem) return;
    loadHistoryItemAsActive(state.selectedHistoryItem);
    document.querySelector('.nav-tab[data-tab="tab-assistente"]')?.click();
    elements.chatInput.focus();
  });

  elements.btnHistCopySei.addEventListener('click', async () => {
    if (!state.selectedHistoryItem) return;
    const text = state.selectedHistoryItem.full_text;
    try {
      const res = await fetch(`${API_BASE}/api/converter-sei-html`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: text })
      });
      const data = await res.json();
      const item = new ClipboardItem({
        'text/html': new Blob([data.html || text], { type: 'text/html' }),
        'text/plain': new Blob([text], { type: 'text/plain' })
      });
      await navigator.clipboard.write([item]);
      showToast('Copiado do histórico p/ SEI!', 'success');
    } catch (e) {
      navigator.clipboard.writeText(text);
      showToast('Copiado em texto puro.', 'info');
    }
  });

  elements.btnHistDel.addEventListener('click', async () => {
    if (!state.selectedHistoryItem) return;
    try {
      await fetch(`${API_BASE}/api/historico/${state.selectedHistoryItem.id}`, { method: 'DELETE' });
      state.selectedHistoryItem = null;
      elements.histDetailActions.classList.add('hidden');
      loadHistorico();
      showToast('Item excluído do histórico.', 'success');
    } catch (e) {
      showToast('Erro ao excluir item.', 'error');
    }
  });
}

async function loadHistorico(search = '') {
  try {
    const url = search ? `${API_BASE}/api/historico?busca=${encodeURIComponent(search)}` : `${API_BASE}/api/historico`;
    const res = await fetch(url);
    const items = await res.json();

    elements.historicoList.innerHTML = '';
    if (!items.length) {
      elements.historicoList.innerHTML = '<div class="empty-state"><span>Nenhum item no histórico.</span></div>';
      return;
    }

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = `hist-card ${state.selectedHistoryItem?.id === item.id ? 'selected' : ''}`;
      
      const icon = item.doc_type?.includes('Resum') ? 'zap' : (item.doc_type?.includes('Tempo') ? 'clock' : (item.doc_type?.includes('Audit') ? 'scale' : 'file-text'));
      const hasAutos = Boolean(item.process_context);

      card.innerHTML = `
        <div class="card-top">
          <span class="badge-tag"><i data-lucide="${icon}"></i> ${item.doc_type || 'Minuta'}${hasAutos ? ' 📁' : ''}${item.raciocinio ? ' 🧠' : ''}</span>
          <span class="card-date">${formatDate(item.timestamp)}</span>
        </div>
        <div class="card-subject">${item.subject || 'Documento Gerado'}</div>
      `;

      card.addEventListener('click', () => selectHistoryItem(item, card));
      card.addEventListener('dblclick', () => loadHistoryItemAsActive(item));

      elements.historicoList.appendChild(card);
    });

    initLucide();
  } catch (err) {
    elements.historicoList.innerHTML = '<div class="empty-state"><span>Erro ao carregar histórico.</span></div>';
  }
}

function selectHistoryItem(item, cardElement) {
  state.selectedHistoryItem = item;
  document.querySelectorAll('.hist-card').forEach(c => c.classList.remove('selected'));
  cardElement.classList.add('selected');

  elements.histSelectedTitle.textContent = `📌 ${item.subject || 'Item'}`;
  elements.histDetailActions.classList.remove('hidden');

  // Preview in Raw editor or render
  renderDocument(item.full_text);
  if (item.raciocinio) {
    updateThinkingDisplay(item.raciocinio, true);
  } else {
    clearDocumentThinking();
  }
  updateDocStats();
  initLucide();
}

function loadHistoryItemAsActive(item) {
  state.selectedHistoryItem = item;
  state.activeProcessText = item.process_context || item.full_text || '';
  state.activeProcessName = item.subject || 'Processo do Histórico';

  // Update Badge & Workspace
  elements.activeProcessName.textContent = state.activeProcessName;
  elements.activeProcessBadge.classList.remove('hidden');

  elements.autosInfoText.textContent = `📄 ${state.activeProcessName} (Contexto do histórico)`;
  elements.autosRawContent.value = state.activeProcessText;

  state.currentDocumentText = item.full_text || '';
  renderDocument(state.currentDocumentText);
  if (item.raciocinio) {
    updateThinkingDisplay(item.raciocinio, true);
  } else {
    clearDocumentThinking();
  }
  updateDocStats();

  showToast(`Contexto '${state.activeProcessName}' ativado para perguntas e edição!`, 'success');
  setStatus('Processo do histórico carregado como ativo.');
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  } catch (e) {
    return dateStr;
  }
}

// --- Triagem em Lote ---
async function handleLoteUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  elements.loteStatusContainer.classList.remove('hidden');
  elements.loteStatusMsg.textContent = `Triando e classificando processos em: ${file.name}...`;
  if (elements.loteProgressFill) {
    elements.loteProgressFill.classList.add('indeterminate');
  }

  state.isStreaming = true;
  currentAbortController = new AbortController();

  try {
    const res = await fetch(`${API_BASE}/api/triagem-lote`, {
      method: 'POST',
      body: formData,
      signal: currentAbortController.signal
    });
    const data = await res.json();

    if (data.sucesso) {
      if (data.cancelado) {
        showToast('Triagem cancelada.', 'info');
        setStatus('Triagem cancelada pelo usuário.');
      } else {
        showToast(`Triagem concluída: ${data.total_processados} processos analisados!`, 'success');
      }
      state.loteResultados = data.resultados || [];
      renderLoteCards(state.loteResultados);
      if (state.loteResultados.length > 0) {
        elements.btnExportLoteCsv.classList.remove('hidden');
      }
    } else {
      showToast(data.detail || 'Erro na triagem em lote.', 'error');
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      showToast('Triagem em lote cancelada.', 'info');
      setStatus('Triagem cancelada.');
    } else {
      showToast(`Falha no lote: ${err.message}`, 'error');
    }
  } finally {
    state.isStreaming = false;
    currentAbortController = null;
    setTimeout(() => {
      elements.loteStatusContainer.classList.add('hidden');
    }, 600);
    initLucide();
  }
}

function renderLoteCards(resultados) {
  elements.loteResultsList.innerHTML = '';
  if (!resultados.length) {
    elements.loteResultsList.innerHTML = '<div class="empty-state"><span>Nenhum processo encontrado.</span></div>';
    return;
  }

  resultados.forEach(item => {
    const card = document.createElement('div');
    card.className = 'lote-card';
    
    const prio = item.prioridade || 'Normal';
    const prioColor = prio === 'Urgente' ? 'var(--danger)' : (prio === 'Alta' ? 'var(--warning)' : 'var(--primary)');

    card.innerHTML = `
      <div class="card-top">
        <strong>${item.arquivo || 'Processo'}</strong>
        <span class="badge-tag" style="color: ${prioColor}; border-color: ${prioColor};">[${prio}]</span>
      </div>
      <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">
        <div><strong>Interessado:</strong> ${item.interessado || '-'}</div>
        <div><strong>Assunto:</strong> ${item.assunto || '-'}</div>
        <div><strong>Prazo:</strong> ${item.prazo || '-'}</div>
        <div><strong>Encaminhamento:</strong> ${item.encaminhamento || '-'}</div>
      </div>
    `;
    elements.loteResultsList.appendChild(card);
  });
  initLucide();
}

async function exportLoteCsv() {
  if (!state.loteResultados.length) return;
  try {
    const res = await fetch(`${API_BASE}/api/exportar/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resultados: state.loteResultados, nome_arquivo: 'triagem_processos.csv' })
    });
    const blob = await res.blob();
    downloadBlob(blob, 'triagem_processos.csv');
    showToast('Planilha CSV exportada com sucesso!', 'success');
  } catch (e) {
    showToast('Erro ao exportar CSV.', 'error');
  }
}

// --- Keyboard Shortcuts & Utilities ---
function initShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Escape -> Cancela geração de IA em andamento
    if (e.key === 'Escape' && state.isStreaming) {
      e.preventDefault();
      cancelarProcessoIA('teclado');
      return;
    }
    // Ctrl+Shift+C -> Copy SEI
    if (e.ctrlKey && e.shiftKey && (e.key === 'C' || e.key === 'c')) {
      e.preventDefault();
      copyToSeiHtml();
    }
  });
}

function setStatus(msg) {
  elements.appStatusMessage.textContent = msg;
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? 'check-circle' : (type === 'error' ? 'alert-circle' : 'info');
  toast.innerHTML = `<i data-lucide="${icon}"></i> <span>${message}</span>`;

  elements.toastContainer.appendChild(toast);
  initLucide();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
