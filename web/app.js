/**
 * Gerador SEI - Frontend Application Controller
 * Modern SPA with Real-time SSE Streaming, Markdown Rendering, and Native SEI Clipboard.
 */

// Application State
const state = {
  activeProcessText: '',
  activeProcessName: '',
  currentDocumentText: '',
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
  uploadProgress: document.getElementById('upload-progress'),
  selectMolde: document.getElementById('select-molde'),
  btnGerarAnalise: document.getElementById('btn-gerar-analise'),
  
  // Chat
  chatMessages: document.getElementById('chat-messages'),
  chatInput: document.getElementById('chat-input'),
  btnSendChat: document.getElementById('btn-send-chat'),
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
  initChat();
  initActions();
  initHistorico();
  initShortcuts();
  checkSystemStatus();
  loadHistorico();
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

// --- Status & Healthcheck ---
async function checkSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    
    if (data.ollama_conectado) {
      elements.ollamaStatus.className = 'status-pill status-online';
      elements.ollamaStatusText.textContent = `IA Online (${data.modelo_ativo})`;
    } else {
      elements.ollamaStatus.className = 'status-pill status-offline';
      elements.ollamaStatusText.textContent = 'IA Offline (Inicie o Ollama)';
    }
  } catch (err) {
    elements.ollamaStatus.className = 'status-pill status-offline';
    elements.ollamaStatusText.textContent = 'Servidor Desconectado';
  }
}

// --- Dropzone & File Upload ---
function initDropzones() {
  // Main Process Dropzone
  const dropzone = elements.dropzone;
  const fileInput = elements.fileInput;

  dropzone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files?.length) handleFileUpload(e.target.files[0]);
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

  dropzone.addEventListener('drop', (e) => {
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

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  setStatus(`Lendo arquivo: ${file.name}...`);
  elements.uploadProgress.classList.remove('hidden');
  const progressFill = elements.uploadProgress.querySelector('.progress-fill');
  progressFill.style.width = '60%';

  try {
    const res = await fetch('/api/upload-processo', { method: 'POST', body: formData });
    const data = await res.json();
    progressFill.style.width = '100%';

    if (data.sucesso) {
      state.activeProcessText = data.texto_processo;
      state.activeProcessName = data.nome_processo;

      // Update Badge
      elements.activeProcessName.textContent = data.nome_processo;
      elements.activeProcessBadge.classList.remove('hidden');

      // Update Autos Inspector
      elements.autosInfoText.textContent = `📄 ${data.nome_processo} (${data.tamanho_caracteres.toLocaleString()} caracteres extraídos)`;
      elements.autosRawContent.value = data.texto_processo;

      appendChatMessage('bot', `Processo **${data.nome_processo}** carregado com sucesso!\n\nVocê já pode selecionar um molde e clicar em **Gerar Análise / Minuta** ou fazer perguntas aqui no chat.`);
      showToast(`Processo carregado: ${data.nome_processo}`, 'success');
      setStatus('Processo carregado e pronto para análise.');
    } else {
      showToast(data.detail || 'Erro ao carregar arquivo.', 'error');
      setStatus('Erro no carregamento.');
    }
  } catch (err) {
    showToast(`Falha no upload: ${err.message}`, 'error');
    setStatus('Falha no upload.');
  } finally {
    setTimeout(() => {
      elements.uploadProgress.classList.add('hidden');
      progressFill.style.width = '0%';
    }, 600);
  }
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

  const molde = elements.selectMolde.value;
  setStatus(`Ollama gerando [${molde}]...`);
  elements.btnGerarAnalise.disabled = true;

  // Switch to Formatted View tab
  document.querySelector('.doc-tab[data-view="formatted"]')?.click();
  elements.docRenderContent.innerHTML = '<div class="streaming-loading"><div class="spinner-sm"></div> Gerando documento com IA...</div>';

  try {
    const res = await fetch('/api/analisar-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        texto_processo: state.activeProcessText,
        nome_processo: state.activeProcessName,
        molde: molde
      })
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
              let clean = payload.full_text;
              if (clean.includes('</think>')) clean = clean.split('</think>')[1].trim();
              else if (clean.includes('<think>')) clean = 'Pensando...';
              
              state.currentDocumentText = clean;
              renderDocument(clean);
              updateDocStats();
            } else if (payload.type === 'done') {
              if (payload.sucesso) {
                state.currentDocumentText = payload.texto_gerado;
                renderDocument(payload.texto_gerado);
                updateDocStats();
                showToast(`[${payload.tipo_documento}] gerado com sucesso!`, 'success');
                setStatus('Documento concluído e salvo no histórico.');
                loadHistorico();
              } else {
                showToast(payload.erro || 'Erro na geração.', 'error');
                setStatus('Erro na geração da IA.');
              }
            }
          } catch (e) {}
        }
      }
    }
  } catch (err) {
    showToast(`Erro de conexão: ${err.message}`, 'error');
    setStatus('Falha na comunicação.');
  } finally {
    state.isStreaming = false;
    elements.btnGerarAnalise.disabled = false;
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
  setStatus('Ollama pensando...');

  const botBubble = appendChatMessage('bot', '...', true);

  try {
    const res = await fetch('/api/chat-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: msg,
        texto_processo: state.activeProcessText,
        nome_processo: state.activeProcessName,
        modo: state.chatMode,
        texto_atual_documento: state.currentDocumentText
      })
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
              let clean = payload.full_text;
              if (clean.includes('</think>')) clean = clean.split('</think>')[1].trim();
              else if (clean.includes('<think>')) clean = 'Pensando...';
              
              botBubble.innerHTML = window.marked ? window.marked.parse(clean) : clean;
              elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            } else if (payload.type === 'done') {
              if (payload.sucesso) {
                botBubble.innerHTML = window.marked ? window.marked.parse(payload.texto_gerado) : payload.texto_gerado;
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
    botBubble.innerHTML = `<span style="color: var(--danger);">Falha de conexão: ${err.message}</span>`;
    setStatus('Falha de conexão.');
  } finally {
    state.isStreaming = false;
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
    const res = await fetch('/api/converter-sei-html', {
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
  renderDocument('');
  updateDocStats();
  showToast('Documento limpo.', 'info');
}

// --- Export Files ---
async function exportDocx() {
  if (!state.currentDocumentText) return showToast('Nada para exportar.', 'error');
  try {
    const res = await fetch('/api/exportar/docx', {
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
    const res = await fetch('/api/exportar/pdf', {
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
      const res = await fetch('/api/converter-sei-html', {
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
      await fetch(`/api/historico/${state.selectedHistoryItem.id}`, { method: 'DELETE' });
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
    const url = search ? `/api/historico?busca=${encodeURIComponent(search)}` : '/api/historico';
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
          <span class="badge-tag"><i data-lucide="${icon}"></i> ${item.doc_type || 'Minuta'}${hasAutos ? ' 📁' : ''}</span>
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
  elements.loteStatusMsg.textContent = `Triando processos em: ${file.name}...`;

  try {
    const res = await fetch('/api/triagem-lote', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.sucesso) {
      state.loteResultados = data.resultados;
      renderLoteCards(data.resultados);
      elements.btnExportLoteCsv.classList.remove('hidden');
      showToast(`Triagem concluída: ${data.total_processados} processos analisados!`, 'success');
    } else {
      showToast(data.detail || 'Erro na triagem em lote.', 'error');
    }
  } catch (err) {
    showToast(`Falha no lote: ${err.message}`, 'error');
  } finally {
    elements.loteStatusContainer.classList.add('hidden');
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
    const res = await fetch('/api/exportar/csv', {
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
