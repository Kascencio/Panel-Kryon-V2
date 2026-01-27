/* external-ui/app.js
   JS mínimo para interacción visual (tabs, selección, timer simulado).
*/

function qs(sel, root = document) { return root.querySelector(sel); }
function qsa(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

function setupTabs() {
  const tabs = qsa('[data-tabs]');
  tabs.forEach((tabsRoot) => {
    const triggers = qsa('[data-tab]', tabsRoot);
    const panels = qsa('[data-panel]', tabsRoot.parentElement);

    function activate(name) {
      triggers.forEach((t) => t.classList.toggle('active', t.dataset.tab === name));
      panels.forEach((p) => p.classList.toggle('hidden', p.dataset.panel !== name));
    }

    triggers.forEach((t) => {
      t.addEventListener('click', () => activate(t.dataset.tab));
    });

    const initial = triggers.find((t) => t.classList.contains('active'))?.dataset.tab || triggers[0]?.dataset.tab;
    if (initial) activate(initial);
  });
}

function setupTherapySelection() {
  const list = qs('[data-therapy-list]');
  if (!list) return;

  const items = qsa('[data-therapy]', list);
  const selectedName = qs('[data-selected-name]');
  const selectedDesc = qs('[data-selected-desc]');
  const selectedBadge = qs('[data-selected-badge]');

  function select(el) {
    items.forEach((i) => i.classList.remove('selected'));
    el.classList.add('selected');

    const name = el.dataset.name || 'Terapia';
    const desc = el.dataset.desc || '';
    const freq = el.dataset.freq || 'general';

    if (selectedName) selectedName.textContent = name;
    if (selectedDesc) selectedDesc.textContent = desc;
    if (selectedBadge) selectedBadge.textContent = freq;
  }

  items.forEach((el) => el.addEventListener('click', () => select(el)));
  if (items[0]) select(items[0]);
}

function setupLoadingMock() {
  const bar = qs('[data-loading-bar]');
  const label = qs('[data-loading-label]');
  const state = qs('[data-loading-state]');
  const msgText = qs('[data-loading-message-text]');
  const msgIcon = qs('[data-loading-message-icon]');
  const msgRoot = qs('.loading-message');
  const particlesRoot = qs('[data-loading-particles]');
  if (!bar) return;

  const messages = [
    { icon: '⚛︎', text: 'Calibrando sistema cuántico...' },
    { icon: '⚡', text: 'Iniciando sistema bioenergético...' },
    { icon: '📦', text: 'Cargando terapias...' },
    { icon: '〰️', text: 'Sincronizando frecuencias...' },
    { icon: '✨', text: 'Preparando entorno virtual...' },
    { icon: '🧠', text: 'Inicializando simulador...' },
  ];

  // progreso automático estilo “splash”
  let v = 0;
  const id = setInterval(() => {
    // crecimiento suave con un poco de aleatoriedad
    v = Math.min(100, v + (Math.random() * 7 + 2));
    bar.style.width = `${Math.floor(v)}%`;
    if (label) label.textContent = `${Math.round(v)}%`;
    if (state) state.textContent = v >= 100 ? 'Listo' : 'Inicializando';
    if (v >= 100) {
      clearInterval(id);
      onLoadingComplete();
    }
  }, 240);

  // mensajes rotativos (1s) con pulso
  let mi = 0;
  if (msgText) {
    setInterval(() => {
      mi = (mi + 1) % messages.length;
      const m = messages[mi];
      if (msgIcon) msgIcon.textContent = m.icon;
      msgText.textContent = m.text;

      if (msgRoot) {
        msgRoot.classList.add('pulse');
        setTimeout(() => msgRoot.classList.remove('pulse'), 300);
      }
    }, 1000);
  }

  // partículas decorativas
  if (particlesRoot && particlesRoot.children.length === 0) {
    const count = 30;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('div');
      p.className = 'particle';
      p.style.top = `${Math.random() * 100}%`;
      p.style.left = `${Math.random() * 100}%`;
      p.style.opacity = String(Math.random() * 0.5 + 0.1);
      const dur = Math.random() * 10 + 10;
      const delay = Math.random() * 5;
      p.style.animation = `float ${dur}s linear infinite`;
      p.style.animationDelay = `${delay}s`;
      particlesRoot.appendChild(p);
    }
  }

  async function onLoadingComplete() {
    try {
      await openExternalWindowOnSecondary();
    } catch (e) {
      console.warn('External screen open failed:', e);
    }

    const next = sessionStorage.getItem('postLoginRedirect') || 'selection.html';
    sessionStorage.removeItem('postLoginRedirect');
    setTimeout(() => {
      window.location.href = next;
    }, 400);
  }
}

async function openExternalWindowOnSecondary() {
  try {
    if (!('getScreenDetails' in window)) return false;

    const permissionStatus = await navigator.permissions.query({ name: 'window-management' });
    if (permissionStatus.state === 'denied') return false;

    const screenDetails = await window.getScreenDetails();
    const currentScreen = screenDetails.currentScreen;
    const secondaryScreen = screenDetails.screens.find((s) => s !== currentScreen);

    if (!secondaryScreen) return false;

    const width = secondaryScreen.availWidth;
    const height = secondaryScreen.availHeight;
    const left = secondaryScreen.availLeft;
    const top = secondaryScreen.availTop;
    const features = `left=${left},top=${top},width=${width},height=${height},menubar=no,toolbar=no,location=no,status=no,fullscreen=yes`;

    window.open('external-screen.html', 'KryonExternalScreen', features);
    return true;
  } catch (error) {
    return false;
  }
}

function setupSessionMock() {
  const startBtn = qs('[data-session-start]');
  const pauseBtn = qs('[data-session-pause]');
  const stopBtn = qs('[data-session-stop]');
  const restartBtn = qs('[data-session-restart]');

  const timeCur = qs('[data-time-current]');
  const timeTot = qs('[data-time-total]');
  const progress = qs('[data-progress]');

  const intensity = qs('[data-intensity]');
  const intensityVal = qs('[data-intensity-val]');

  if (!timeCur || !timeTot || !progress) return;

  const total = 4 * 60; // mock
  let cur = 0;
  let active = false;
  let paused = false;
  let timer = null;

  function fmt(s) {
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    return `${mm} : ${ss}`;
  }

  function render() {
    timeCur.textContent = fmt(cur);
    timeTot.textContent = fmt(total);
    progress.style.width = `${Math.floor((cur / total) * 100)}%`;

    if (startBtn) startBtn.disabled = active;
    if (pauseBtn) pauseBtn.disabled = !active;
    if (stopBtn) stopBtn.disabled = !active;
    if (restartBtn) restartBtn.disabled = !active;

    if (pauseBtn) pauseBtn.textContent = paused ? 'Reanudar' : 'Pausar';
  }

  function tick() {
    if (!active || paused) return;
    cur += 1;
    if (cur >= total) {
      stop();
      return;
    }
    render();
  }

  function start() {
    if (active) return;
    active = true;
    paused = false;
    cur = 0;
    render();
    timer = setInterval(tick, 1000);
  }

  function stop() {
    active = false;
    paused = false;
    cur = 0;
    if (timer) clearInterval(timer);
    timer = null;
    render();
  }

  function restart() {
    stop();
    start();
  }

  function togglePause() {
    if (!active) return;
    paused = !paused;
    render();
  }

  startBtn?.addEventListener('click', start);
  pauseBtn?.addEventListener('click', togglePause);
  stopBtn?.addEventListener('click', stop);
  restartBtn?.addEventListener('click', restart);

  intensity?.addEventListener('input', () => {
    if (intensityVal) intensityVal.textContent = `${intensity.value}%`;
  });

  render();
}

function setupWindowManagerMock() {
  const fab = qs('[data-fab]');
  const panel = qs('[data-panel]');
  const close = qs('[data-panel-close]');
  if (!fab || !panel) return;

  function toggle() {
    panel.classList.toggle('hidden');
  }

  fab.addEventListener('click', toggle);
  close?.addEventListener('click', toggle);
}

document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupTherapySelection();
  setupLoadingMock();
  setupSessionMock();
  setupWindowManagerMock();
});
