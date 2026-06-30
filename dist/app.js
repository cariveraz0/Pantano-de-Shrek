/* ═══════════════════════════════════════════════
   app.js — Reino del Pantano — Lógica completa
   ═══════════════════════════════════════════════ */

(() => {
  'use strict';

  // ── Persistence helpers (localStorage) ────
  const STORAGE_KEY = 'pantano_users';
  const FACES_KEY   = 'pantano_faces';

  function loadUsers() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
  }

  function saveUsers(db) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  }

  function loadFaces() {
    try {
      const raw = localStorage.getItem(FACES_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
  }

  function saveFaces(db) {
    localStorage.setItem(FACES_KEY, JSON.stringify(db));
  }

  let USERS_DB = loadUsers();
  let FACES_DB = loadFaces(); // username -> base64 image

  // ── State ─────────────────────────────────
  let currentUser = null;
  let simulatedCode = null;
  let forgotCredentials = { user: '', pass: '' };
  let capturedFaceB64 = null;
  let cameraStream = null;

  // face-api state
  let faceApiLoaded = false;
  let faceApiLoading = false;

  // ── DOM refs ──────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // Views
  const views = {
    login:    $('#view-login'),
    register: $('#view-register'),
    forgot:   $('#view-forgot'),
    welcome:  $('#view-welcome'),
  };

  // Snackbar
  const snackbar = $('#snackbar');

  // Modal
  const modalOverlay  = $('#modal-overlay');
  const modalTitle    = $('#modal-title-text');
  const modalActions  = $('#modal-actions');
  const cameraVideo   = $('#camera-video');
  const cameraCanvas  = $('#camera-canvas');
  const cameraSnap    = $('#camera-snapshot');
  const scanStatus    = $('#scan-status');
  const scanOverlay   = $('#scan-overlay');

  // Alert
  const alertOverlay = $('#alert-overlay');
  const alertTitle   = $('#alert-title');
  const alertMessage = $('#alert-message');
  const alertActions = $('#alert-actions');

  // Simulator
  const simMailbox = $('#sim-mailbox');
  const simBtn     = $('#sim-btn');
  const simBody    = $('#sim-mailbox-body');

  // ── Navigation ────────────────────────────
  function navigateTo(viewName) {
    Object.entries(views).forEach(([name, el]) => {
      if (name === viewName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Hide simulator when leaving forgot
    if (viewName !== 'forgot') {
      simBtn.classList.add('hidden');
      simMailbox.classList.add('hidden');
    }
  }

  // ── Snackbar ──────────────────────────────
  function showSnack(message, isError = false) {
    snackbar.textContent = message;
    snackbar.className = 'snackbar show ' + (isError ? 'error' : 'success');
    clearTimeout(snackbar._timer);
    snackbar._timer = setTimeout(() => {
      snackbar.classList.remove('show');
    }, 3000);
  }

  // ── Alert dialog ──────────────────────────
  function showAlert(title, message, actions) {
    alertTitle.textContent = title;
    alertMessage.textContent = message;
    alertActions.innerHTML = '';
    actions.forEach(({ label, color, onClick }) => {
      const btn = document.createElement('button');
      btn.textContent = label;
      btn.style.color = color || 'var(--text-muted)';
      btn.addEventListener('click', () => {
        alertOverlay.classList.add('hidden');
        if (onClick) onClick();
      });
      alertActions.appendChild(btn);
    });
    alertOverlay.classList.remove('hidden');
  }

  // ── Field validation helpers ──────────────
  function setFieldError(wrapperId, errorId, msg) {
    const wrapper = $('#' + wrapperId);
    const errorEl = $('#' + errorId);
    if (msg) {
      wrapper.classList.add('has-error');
      errorEl.textContent = msg;
      errorEl.classList.add('visible');
    } else {
      wrapper.classList.remove('has-error');
      errorEl.textContent = '';
      errorEl.classList.remove('visible');
    }
  }

  function clearFieldError(wrapperId, errorId) {
    setFieldError(wrapperId, errorId, '');
  }

  // Auto-clear errors on input
  function autoClear(inputId, wrapperId, errorId) {
    const input = $('#' + inputId);
    input.addEventListener('input', () => clearFieldError(wrapperId, errorId));
  }

  // ── Toggle password visibility ────────────
  $$('.toggle-pass').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = $('#' + btn.dataset.target);
      const icon = btn.querySelector('.material-icons-round');
      if (target.type === 'password') {
        target.type = 'text';
        icon.textContent = 'visibility_off';
      } else {
        target.type = 'password';
        icon.textContent = 'visibility';
      }
    });
  });

  // ═══════════════════════════════════════════
  //  LOGIN
  // ═══════════════════════════════════════════
  autoClear('login-user', 'login-user-wrapper', 'login-user-error');
  autoClear('login-pass', 'login-pass-wrapper', 'login-pass-error');

  $('#btn-login').addEventListener('click', doLogin);
  $('#login-pass').addEventListener('keydown', (e) => { if (e.key === 'Enter') doLogin(); });

  function doLogin() {
    const u = $('#login-user').value.trim();
    const p = $('#login-pass').value.trim();
    let hasError = false;

    if (!u) { setFieldError('login-user-wrapper', 'login-user-error', 'El usuario es obligatorio'); hasError = true; }
    if (!p) { setFieldError('login-pass-wrapper', 'login-pass-error', 'La clave es obligatoria'); hasError = true; }
    if (hasError) return;

    USERS_DB = loadUsers(); // Refresh

    if (USERS_DB[u]) {
      const stored = USERS_DB[u];
      const actualPass = typeof stored === 'string' ? stored : stored.password;
      if (actualPass === p) {
        currentUser = u;
        enterWelcome(u);
        return;
      } else {
        showSnack('Clave incorrecta.', true);
        return;
      }
    }

    // User not found
    showAlert(
      '¡Alto ahí, Intruso! 🐊',
      'No hemos encontrado a ninguna criatura con ese nombre en nuestro registro. ¿Acaso vienes de Muy Muy Lejano?\n\nRegístrate para poder entrar al pantano.',
      [
        { label: 'Registrarse', color: 'var(--gold)', onClick: () => navigateTo('register') },
        { label: 'Intentar de nuevo', color: 'var(--text-muted)' },
      ]
    );
  }

  // ═══════════════════════════════════════════
  //  REGISTER
  // ═══════════════════════════════════════════
  autoClear('reg-user',    'reg-user-wrapper',    'reg-user-error');
  autoClear('reg-email',   'reg-email-wrapper',   'reg-email-error');
  autoClear('reg-pass',    'reg-pass-wrapper',    'reg-pass-error');
  autoClear('reg-confirm', 'reg-confirm-wrapper', 'reg-confirm-error');

  $('#btn-register').addEventListener('click', doRegister);

  function doRegister() {
    const u  = $('#reg-user').value.trim();
    const em = $('#reg-email').value.trim();
    const p  = $('#reg-pass').value.trim();
    const c  = $('#reg-confirm').value.trim();
    let hasError = false;

    USERS_DB = loadUsers();

    if (!u) {
      setFieldError('reg-user-wrapper', 'reg-user-error', 'Usuario obligatorio'); hasError = true;
    } else if (USERS_DB[u]) {
      setFieldError('reg-user-wrapper', 'reg-user-error', 'Ese usuario ya existe'); hasError = true;
    }

    const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
    if (!em || !emailRegex.test(em)) {
      setFieldError('reg-email-wrapper', 'reg-email-error', 'Correo inválido'); hasError = true;
    }

    if (p.length < 4) {
      setFieldError('reg-pass-wrapper', 'reg-pass-error', 'Muy corta'); hasError = true;
    }

    if (p !== c) {
      setFieldError('reg-confirm-wrapper', 'reg-confirm-error', 'No coinciden'); hasError = true;
    }

    if (hasError) return;

    USERS_DB[u] = { password: p, email: em, tasks: [] };
    saveUsers(USERS_DB);

    // Save face if captured
    if (capturedFaceB64) {
      FACES_DB[u] = capturedFaceB64;
      saveFaces(FACES_DB);
    }

    // Reset form
    $('#reg-user').value = '';
    $('#reg-email').value = '';
    $('#reg-pass').value = '';
    $('#reg-confirm').value = '';
    clearFacePreview();

    showSnack('¡Usuario registrado exitosamente! Ya puedes entrar al pantano.');
    navigateTo('login');
  }

  // ── Face capture (register) ───────────────
  function clearFacePreview() {
    capturedFaceB64 = null;
    $('#face-preview-row').classList.add('hidden');
    $('#btn-link-face').classList.remove('hidden');
  }

  $('#btn-remove-face').addEventListener('click', clearFacePreview);

  $('#btn-link-face').addEventListener('click', () => {
    openCameraModal('capture');
  });

  // ═══════════════════════════════════════════
  //  FORGOT PASSWORD
  // ═══════════════════════════════════════════
  autoClear('forgot-email', 'forgot-email-wrapper', 'forgot-email-error');
  autoClear('forgot-code',  'forgot-code-wrapper',  'forgot-code-error');

  $('#btn-send-code').addEventListener('click', () => {
    const em = $('#forgot-email').value.trim();
    const emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;

    if (!em || !emailRegex.test(em)) {
      setFieldError('forgot-email-wrapper', 'forgot-email-error', 'Ingresa un correo válido');
      return;
    }

    USERS_DB = loadUsers();
    let foundUser = null, foundPass = null;
    for (const [username, data] of Object.entries(USERS_DB)) {
      if (typeof data === 'object' && data.email === em) {
        foundUser = username;
        foundPass = data.password;
        break;
      }
    }

    if (!foundUser) {
      setFieldError('forgot-email-wrapper', 'forgot-email-error', 'Este correo no existe en el reino');
      return;
    }

    forgotCredentials = { user: foundUser, pass: foundPass };
    simulatedCode = String(Math.floor(100000 + Math.random() * 900000));

    // Show in simulator
    simBody.textContent = `De: seguridad@pantano.com\nPara: ${em}\n\nCódigo de seguridad solicitado:\n👉 ${simulatedCode} 👈`;

    // Toggle UI
    $('#forgot-step-email').classList.add('hidden');
    $('#forgot-step-code').classList.remove('hidden');
    simBtn.classList.remove('hidden');

    showSnack('¡Código enviado al simulador flotante!');
  });

  $('#btn-verify-code').addEventListener('click', () => {
    const entered = $('#forgot-code').value.trim();
    if (entered === simulatedCode) {
      $('#forgot-step-code').classList.add('hidden');
      $('#recovered-user').textContent = forgotCredentials.user;
      $('#recovered-pass').textContent = forgotCredentials.pass;
      $('#forgot-step-result').classList.remove('hidden');
      simBtn.classList.add('hidden');
      simMailbox.classList.add('hidden');
    } else {
      setFieldError('forgot-code-wrapper', 'forgot-code-error', 'Código incorrecto');
    }
  });

  // Reset forgot view when navigating to it
  function resetForgotView() {
    $('#forgot-step-email').classList.remove('hidden');
    $('#forgot-step-code').classList.add('hidden');
    $('#forgot-step-result').classList.add('hidden');
    $('#forgot-email').value = '';
    $('#forgot-code').value = '';
    clearFieldError('forgot-email-wrapper', 'forgot-email-error');
    clearFieldError('forgot-code-wrapper', 'forgot-code-error');
  }

  // ── Simulator toggle ─────────────────────
  simBtn.addEventListener('click', () => {
    simMailbox.classList.toggle('hidden');
  });

  // ═══════════════════════════════════════════
  //  WELCOME / KANBAN
  // ═══════════════════════════════════════════
  function enterWelcome(username) {
    currentUser = username;
    USERS_DB = loadUsers();

    if (!USERS_DB[username]) {
      USERS_DB[username] = { password: '', email: '', tasks: [] };
    } else if (typeof USERS_DB[username] === 'string') {
      USERS_DB[username] = { password: USERS_DB[username], email: '', tasks: [] };
    }
    if (!USERS_DB[username].tasks) {
      USERS_DB[username].tasks = [];
    }

    $('#sidebar-username').textContent = username;
    navigateTo('welcome');
    refreshBoard();
  }

  // Add task
  $('#btn-add-task').addEventListener('click', () => {
    const title = $('#task-title').value.trim();
    const desc = $('#task-desc').value.trim();
    const status = $('#task-status').value;

    if (!title) {
      showSnack('La misión necesita un nombre', true);
      return;
    }

    USERS_DB = loadUsers();
    if (!USERS_DB[currentUser].tasks) USERS_DB[currentUser].tasks = [];

    USERS_DB[currentUser].tasks.push({
      id: String(Math.floor(100000 + Math.random() * 900000)),
      title,
      desc: desc || 'Sin descripción especial del pantano.',
      status,
    });

    saveUsers(USERS_DB);

    $('#task-title').value = '';
    $('#task-desc').value = '';
    $('#task-status').value = 'todo';

    refreshBoard();
    showSnack(`Misión '${title}' agregada al pantano. 🌲`);
  });

  function moveTask(taskId, direction) {
    USERS_DB = loadUsers();
    const tasks = USERS_DB[currentUser].tasks;
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    if (direction === 'right') {
      if (task.status === 'todo') task.status = 'in_progress';
      else if (task.status === 'in_progress') task.status = 'dont_do';
    } else {
      if (task.status === 'dont_do') task.status = 'in_progress';
      else if (task.status === 'in_progress') task.status = 'todo';
    }

    saveUsers(USERS_DB);
    refreshBoard();
  }

  function deleteTask(taskId) {
    USERS_DB = loadUsers();
    USERS_DB[currentUser].tasks = USERS_DB[currentUser].tasks.filter(t => t.id !== taskId);
    saveUsers(USERS_DB);
    refreshBoard();
    showSnack('Misión arrojada a la ciénaga. 🐊');
  }

  function buildTaskCard(task) {
    const statusClass = task.status === 'todo' ? 'todo' :
                        task.status === 'in_progress' ? 'progress' : 'dont';

    const card = document.createElement('div');
    card.className = `task-card task-card--${statusClass}`;

    let actionsHTML = '';

    if (task.status !== 'todo') {
      actionsHTML += `<button class="task-action-left" data-id="${task.id}" data-dir="left" title="Mover a la izquierda">
        <span class="material-icons-round">arrow_back</span>
      </button>`;
    }

    actionsHTML += `<button class="task-action-delete" data-id="${task.id}" title="Tirar a la ciénaga">
      <span class="material-icons-round">delete</span>
    </button>`;

    if (task.status !== 'dont_do') {
      actionsHTML += `<button class="task-action-right" data-id="${task.id}" data-dir="right" title="Mover a la derecha">
        <span class="material-icons-round">arrow_forward</span>
      </button>`;
    }

    card.innerHTML = `
      <div class="task-card__title">${escapeHtml(task.title)}</div>
      <div class="task-card__desc">${escapeHtml(task.desc)}</div>
      <div class="task-card__divider"></div>
      <div class="task-card__actions">${actionsHTML}</div>
    `;

    // Bind actions
    card.querySelectorAll('.task-action-left, .task-action-right').forEach(btn => {
      btn.addEventListener('click', () => moveTask(btn.dataset.id, btn.dataset.dir));
    });
    card.querySelectorAll('.task-action-delete').forEach(btn => {
      btn.addEventListener('click', () => deleteTask(btn.dataset.id));
    });

    return card;
  }

  function refreshBoard() {
    USERS_DB = loadUsers();
    const tasks = (USERS_DB[currentUser] && USERS_DB[currentUser].tasks) || [];

    const colTodo     = $('#col-todo');
    const colProgress = $('#col-progress');
    const colDont     = $('#col-dont');

    colTodo.innerHTML = '';
    colProgress.innerHTML = '';
    colDont.innerHTML = '';

    let todoCount = 0, progressCount = 0, dontCount = 0;

    tasks.forEach(task => {
      const card = buildTaskCard(task);
      if (task.status === 'todo') { colTodo.appendChild(card); todoCount++; }
      else if (task.status === 'in_progress') { colProgress.appendChild(card); progressCount++; }
      else { colDont.appendChild(card); dontCount++; }
    });

    $('#col-header-todo').textContent     = `Misiones Pendientes (${todoCount})`;
    $('#col-header-progress').textContent = `En el Caldero (${progressCount})`;
    $('#col-header-dont').textContent     = `¡FUERA DE MI PANTANO! (${dontCount})`;
  }

  // Logout
  $('#btn-logout').addEventListener('click', () => {
    currentUser = null;
    navigateTo('login');
    $('#login-user').value = '';
    $('#login-pass').value = '';
  });

  // ═══════════════════════════════════════════
  //  CAMERA MODAL (Face capture & recognition)
  // ═══════════════════════════════════════════

  // mode: 'capture' (register) or 'recognize' (login)
  let cameraMode = null;

  async function openCameraModal(mode) {
    cameraMode = mode;

    // Reset state
    cameraSnap.classList.add('hidden');
    cameraVideo.classList.remove('hidden');
    scanStatus.textContent = 'Iniciando escáner...';
    scanStatus.style.color = 'var(--text-muted)';
    setScanCornerState('default');

    if (mode === 'capture') {
      modalTitle.textContent = 'Registrar Rostro 📸';
      $('#btn-take-photo').classList.remove('hidden');
      $('#btn-confirm-photo').classList.add('hidden');
      $('#btn-retry-photo').classList.add('hidden');
    } else {
      modalTitle.textContent = 'Escáner Facial del Reino 👁️';
      $('#btn-take-photo').classList.add('hidden');
      $('#btn-confirm-photo').classList.add('hidden');
      $('#btn-retry-photo').classList.add('hidden');
    }

    modalOverlay.classList.remove('hidden');

    // Start camera
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' }
      });
      cameraVideo.srcObject = cameraStream;
      await cameraVideo.play();
      scanStatus.textContent = mode === 'capture' ? 'Buscando rostro... Presiona "Tomar Foto" cuando estés listo.' : 'Cargando modelo de reconocimiento...';

      if (mode === 'recognize') {
        startFaceRecognition();
      } else {
        startFaceDetectionLoop();
      }
    } catch (err) {
      scanStatus.textContent = 'Error: No se pudo acceder a la cámara.';
      scanStatus.style.color = 'var(--error)';
    }
  }

  function closeCameraModal() {
    modalOverlay.classList.add('hidden');
    stopCamera();
    cameraMode = null;
  }

  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
      cameraStream = null;
    }
    cameraVideo.srcObject = null;
  }

  // Cancel button (static one in HTML)
  $('#btn-modal-cancel').addEventListener('click', closeCameraModal);
  $('#btn-take-photo').addEventListener('click', takePhoto);
  $('#btn-confirm-photo').addEventListener('click', confirmPhoto);
  $('#btn-retry-photo').addEventListener('click', retryPhoto);

  // ── Face Detection Loop (capture mode) ────
  let detectionLoopId = null;

  async function startFaceDetectionLoop() {
    await loadFaceApi();
    if (!faceApiLoaded) {
      scanStatus.textContent = 'Error: No se pudo cargar el modelo facial.';
      scanStatus.style.color = 'var(--error)';
      return;
    }

    scanStatus.textContent = 'Buscando rostro... Presiona "Tomar Foto"';
    scanStatus.style.color = 'var(--text-muted)';

    const detect = async () => {
      if (!cameraMode || cameraVideo.paused) return;
      try {
        const detections = await faceapi.detectAllFaces(
          cameraVideo,
          new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 })
        );
        if (detections.length > 0) {
          setScanCornerState('detecting');
          scanStatus.textContent = '¡Rostro detectado! Presiona "Tomar Foto"';
          scanStatus.style.color = 'var(--success)';
        } else {
          setScanCornerState('default');
          scanStatus.textContent = 'Buscando rostro...';
          scanStatus.style.color = 'var(--text-muted)';
        }
      } catch { /* ignore */ }
      if (cameraMode === 'capture') {
        detectionLoopId = requestAnimationFrame(detect);
      }
    };
    detect();
  }

  function takePhoto() {
    const canvas = cameraCanvas;
    canvas.width = cameraVideo.videoWidth || 320;
    canvas.height = cameraVideo.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    cameraSnap.src = dataUrl;
    cameraSnap.classList.remove('hidden');
    cameraVideo.classList.add('hidden');

    capturedFaceB64 = dataUrl;

    // Stop detection loop
    cancelAnimationFrame(detectionLoopId);
    stopCamera();

    scanStatus.textContent = '¡Rostro capturado con éxito!';
    scanStatus.style.color = 'var(--gold)';

    $('#btn-take-photo').classList.add('hidden');
    const confirmBtn = $('#btn-confirm-photo');
    const retryBtn = $('#btn-retry-photo');
    if (confirmBtn) confirmBtn.classList.remove('hidden');
    if (retryBtn) retryBtn.classList.remove('hidden');
  }

  function confirmPhoto() {
    // Set preview
    $('#face-preview-img').src = capturedFaceB64;
    $('#face-preview-row').classList.remove('hidden');
    $('#btn-link-face').classList.add('hidden');
    closeCameraModal();
  }

  async function retryPhoto() {
    capturedFaceB64 = null;
    cameraSnap.classList.add('hidden');
    cameraVideo.classList.remove('hidden');

    $('#btn-take-photo').classList.remove('hidden');
    const confirmBtn = $('#btn-confirm-photo');
    const retryBtn = $('#btn-retry-photo');
    if (confirmBtn) confirmBtn.classList.add('hidden');
    if (retryBtn) retryBtn.classList.add('hidden');

    scanStatus.textContent = 'Iniciando escáner...';
    scanStatus.style.color = 'var(--text-muted)';

    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' }
      });
      cameraVideo.srcObject = cameraStream;
      await cameraVideo.play();
      startFaceDetectionLoop();
    } catch {
      scanStatus.textContent = 'Error: No se pudo acceder a la cámara.';
      scanStatus.style.color = 'var(--error)';
    }
  }

  // ── Face Recognition (login mode) ─────────
  $('#btn-facial-login').addEventListener('click', () => {
    FACES_DB = loadFaces();
    if (Object.keys(FACES_DB).length === 0) {
      showSnack('¡Ningún habitante tiene rostro registrado!', true);
      return;
    }
    openCameraModal('recognize');
  });

  async function startFaceRecognition() {
    await loadFaceApi();
    if (!faceApiLoaded) {
      scanStatus.textContent = 'Error: No se pudo cargar el modelo facial.';
      scanStatus.style.color = 'var(--error)';
      return;
    }

    scanStatus.textContent = 'Construyendo perfiles faciales...';
    scanStatus.style.color = 'var(--text-muted)';

    FACES_DB = loadFaces();
    USERS_DB = loadUsers();

    // Build face descriptors for all registered faces
    const labeledDescriptors = [];

    for (const [username, imgB64] of Object.entries(FACES_DB)) {
      if (!USERS_DB[username]) continue;
      try {
        const img = await loadImage(imgB64);
        const detection = await faceapi
          .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.5 }))
          .withFaceLandmarks()
          .withFaceDescriptor();

        if (detection) {
          labeledDescriptors.push(
            new faceapi.LabeledFaceDescriptors(username, [detection.descriptor])
          );
        }
      } catch { /* skip */ }
    }

    if (labeledDescriptors.length === 0) {
      scanStatus.textContent = 'No se encontraron rostros válidos registrados.';
      scanStatus.style.color = 'var(--error)';
      return;
    }

    const matcher = new faceapi.FaceMatcher(labeledDescriptors, 0.5);

    scanStatus.textContent = 'Buscando coincidencia...';
    let matchCounts = {};
    const REQUIRED_MATCHES = 8;

    const recognizeLoop = async () => {
      if (cameraMode !== 'recognize' || cameraVideo.paused) return;

      try {
        const detection = await faceapi
          .detectSingleFace(cameraVideo, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
          .withFaceLandmarks()
          .withFaceDescriptor();

        if (detection) {
          const match = matcher.findBestMatch(detection.descriptor);

          if (match.label !== 'unknown') {
            const user = match.label;
            matchCounts[user] = (matchCounts[user] || 0) + 1;
            const pct = Math.min(Math.round((matchCounts[user] / REQUIRED_MATCHES) * 100), 100);

            setScanCornerState('matched');
            scanStatus.textContent = `¡Rostro reconocido (${user})! (${pct}%)`;
            scanStatus.style.color = 'var(--success)';

            if (matchCounts[user] >= REQUIRED_MATCHES) {
              scanStatus.textContent = `¡Acceso Concedido! Bienvenido, ${user}. 🌱`;
              await sleep(1200);
              closeCameraModal();
              enterWelcome(user);
              return;
            }
          } else {
            setScanCornerState('no-match');
            scanStatus.textContent = 'Buscando coincidencia...';
            scanStatus.style.color = 'var(--error)';
          }
        } else {
          setScanCornerState('default');
          scanStatus.textContent = 'Buscando rostro...';
          scanStatus.style.color = 'var(--text-muted)';
        }
      } catch { /* ignore */ }

      if (cameraMode === 'recognize') {
        requestAnimationFrame(recognizeLoop);
      }
    };

    recognizeLoop();
  }

  // ── face-api.js loader ────────────────────
  async function loadFaceApi() {
    if (faceApiLoaded) return;
    if (faceApiLoading) {
      // Wait for it
      while (faceApiLoading) await sleep(100);
      return;
    }
    faceApiLoading = true;

    try {
      if (typeof faceapi === 'undefined') {
        scanStatus.textContent = 'Error: face-api.js no se cargó.';
        scanStatus.style.color = 'var(--error)';
        faceApiLoading = false;
        return;
      }

      const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/model/';

      scanStatus.textContent = 'Descargando modelos faciales...';
      scanStatus.style.color = 'var(--gold)';

      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
      ]);

      faceApiLoaded = true;
    } catch (err) {
      console.error('Error loading face-api models:', err);
      scanStatus.textContent = 'Error al cargar modelos faciales.';
      scanStatus.style.color = 'var(--error)';
    }
    faceApiLoading = false;
  }

  // ── Scan corner styling ───────────────────
  function setScanCornerState(state) {
    const corners = scanOverlay.querySelectorAll('.scan-corner');
    corners.forEach(c => {
      c.classList.remove('detecting', 'matched', 'no-match');
      if (state !== 'default') c.classList.add(state);
    });
  }

  // ── Helpers ───────────────────────────────
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  // ═══════════════════════════════════════════
  //  NAVIGATION BINDINGS
  // ═══════════════════════════════════════════
  $('#btn-goto-register').addEventListener('click', () => navigateTo('register'));
  $('#btn-goto-login-from-reg').addEventListener('click', () => navigateTo('login'));
  $('#btn-goto-forgot').addEventListener('click', () => {
    resetForgotView();
    navigateTo('forgot');
  });
  $('#btn-goto-login-from-forgot').addEventListener('click', () => navigateTo('login'));

  // ═══════════════════════════════════════════
  //  INIT
  // ═══════════════════════════════════════════
  navigateTo('login');
})();
