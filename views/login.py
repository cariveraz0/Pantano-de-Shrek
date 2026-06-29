# ─────────────────────────────────────────
#  views/login.py — Página de inicio de sesión
# ─────────────────────────────────────────
import flet as ft
import threading
import time
import base64
from constants import USERS_DB, COLORS
from components import make_field, show_snack, build_left_panel, build_action_button

# Intentar importar cv2 y numpy para detección/reconocimiento facial real
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    LBPH_AVAILABLE = hasattr(cv2, 'face') and hasattr(cv2.face, 'LBPHFaceRecognizer_create')
except ImportError:
    OPENCV_AVAILABLE = False
    LBPH_AVAILABLE = False


def build_face_recognizer():
    """
    Entrena un reconocedor LBPH con las fotos de rostro guardadas en USERS_DB.
    Solo procesa imágenes JPEG reales (no SVG simuladas).
    Retorna (recognizer, label_map) o (None, None) si no es posible.
    """
    if not LBPH_AVAILABLE:
        return None, None

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    faces_list = []
    labels_list = []
    label_map = {}  # int_label -> username

    for idx, (username, data) in enumerate(USERS_DB.items()):
        if not isinstance(data, dict):
            continue
        face_data_str = data.get("face_data", "")
        # Solo imágenes JPEG reales; las SVG son simuladas y no sirven para reconocimiento
        if not face_data_str or not face_data_str.startswith("data:image/jpeg;base64,"):
            continue
        try:
            img_b64 = face_data_str.split(",", 1)[1]
            img_bytes = base64.b64decode(img_b64)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img_gray = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if img_gray is None:
                continue
            detected = face_cascade.detectMultiScale(img_gray, 1.1, 4)
            if len(detected) > 0:
                x, y, w, h = detected[0]
                face_roi = cv2.resize(img_gray[y:y+h, x:x+w], (100, 100))
            else:
                face_roi = cv2.resize(img_gray, (100, 100))
            faces_list.append(face_roi)
            labels_list.append(idx)
            label_map[idx] = username
        except Exception:
            continue

    if not faces_list:
        return None, None

    recognizer.train(faces_list, np.array(labels_list, dtype=np.int32))
    return recognizer, label_map


def build_login_view(page, nav):
    login_user = make_field(page, "Usuario", ft.Icons.PERSON_ROUNDED, helper="* Campo obligatorio")
    login_pass = make_field(page, "Clave", ft.Icons.LOCK_ROUNDED, password=True, helper="* Campo obligatorio")

    def do_login(e):
        u = login_user.value.strip()
        p = login_pass.value.strip()

        has_error = False
        if not u:
            login_user.error = "El usuario es obligatorio"
            has_error = True
        if not p:
            login_pass.error = "La clave es obligatoria"
            has_error = True
        if has_error:
            page.update()
            return

        if u in USERS_DB:
            stored = USERS_DB[u]
            actual_pass = stored if isinstance(stored, str) else stored.get("password")
            if actual_pass == p:
                nav["welcome"](u)
                return
            else:
                show_snack(page, "Clave incorrecta.", error=True)
                return

        def close_dialog(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("¡Alto ahí, Intruso! 🐊", color=COLORS["gold"], size=22, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "No hemos encontrado a ninguna criatura con ese nombre en nuestro registro. "
                "¿Acaso vienes de Muy Muy Lejano?\n\n"
                "Regístrate para poder entrar al pantano.",
                color=COLORS["text_light"],
                size=16
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Registrarse", color=COLORS["gold"], weight=ft.FontWeight.BOLD),
                    on_click=lambda e: [close_dialog(e), nav["register"]()]
                ),
                ft.TextButton(
                    content=ft.Text("Intentar de nuevo", color=COLORS["text_muted"]),
                    on_click=close_dialog
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=COLORS["bg_panel"],
            shape=ft.RoundedRectangleBorder(radius=16),
        )

        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ── LÓGICA DE INICIO DE SESIÓN FACIAL ──
    class ScanController:
        def __init__(self):
            self.is_running = False
            self.cap = None
            self.mode = "real" if OPENCV_AVAILABLE else "simulated"

    scan_ctrl = ScanController()

    def start_real_camera(image_ctrl, status_ctrl, selected_user, close_callback, recognizer=None, label_map=None):
        scan_ctrl.is_running = True
        scan_ctrl.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not scan_ctrl.cap.isOpened():
            scan_ctrl.cap = cv2.VideoCapture(0)

        if not scan_ctrl.cap.isOpened():
            status_ctrl.value = "Error: No se detectó cámara. Iniciando modo simulación..."
            status_ctrl.color = COLORS["error"]
            page.update()
            time.sleep(1.5)
            scan_ctrl.mode = "simulated"
            start_simulation(image_ctrl, status_ctrl, selected_user, close_callback)
            return

        face_cascade = None
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception:
            pass

        consecutive_matches = 0    # frames donde el rostro coincide con el usuario
        consecutive_noface = 0     # frames sin rostro (para resetear aviso)

        while scan_ctrl.is_running:
            ret, frame = scan_ctrl.cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            frame_resized = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

            faces = []
            if face_cascade is not None and not face_cascade.empty():
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Color del marco según estado
            frame_color = (55, 175, 212)   # azul: buscando

            if len(faces) > 0:
                consecutive_noface = 0
                x, y, w, h = faces[0]

                if recognizer is not None and label_map is not None:
                    # ── Reconocimiento real con LBPH ──
                    try:
                        face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
                        pred_label, confidence = recognizer.predict(face_roi)
                        pred_user = label_map.get(pred_label, "")
                        # LBPH: menor confidence = mejor coincidencia. < 80 es una buena coincidencia
                        if pred_user == selected_user and confidence < 80:
                            consecutive_matches += 1
                            frame_color = (55, 212, 125)   # verde: coincide
                            pct = min(consecutive_matches * 10, 100)
                            status_ctrl.value = f"¡Rostro reconocido! Verificando identidad ({pct}%)"
                            status_ctrl.color = COLORS["success"]
                        else:
                            consecutive_matches = max(0, consecutive_matches - 1)
                            frame_color = (55, 55, 212)    # rojo-azul: no coincide
                            status_ctrl.value = f"⛔ Rostro no reconocido — Acceso denegado"
                            status_ctrl.color = COLORS["error"]
                    except Exception:
                        # Si LBPH falla por alguna razón, no conceder acceso
                        consecutive_matches = 0
                        status_ctrl.value = "Error en reconocimiento. Intenta de nuevo."
                        status_ctrl.color = COLORS["error"]
                else:
                    # Sin reconocedor: simplemente detecta presencia (fallback)
                    consecutive_matches += 1
                    frame_color = (55, 212, 125)
                    status_ctrl.value = f"¡Rostro detectado! Verificando ({consecutive_matches * 10}%)"
                    status_ctrl.color = COLORS["gold"]

                # Dibujar esquinas del marco en el color correspondiente
                d = 10
                for (fx, fy, fw, fh) in faces:
                    cv2.rectangle(frame_resized, (fx, fy), (fx+fw, fy+fh), frame_color, 2)
                    cv2.line(frame_resized, (fx, fy), (fx+d, fy), frame_color, 3)
                    cv2.line(frame_resized, (fx, fy), (fx, fy+d), frame_color, 3)
                    cv2.line(frame_resized, (fx+fw, fy), (fx+fw-d, fy), frame_color, 3)
                    cv2.line(frame_resized, (fx+fw, fy), (fx+fw, fy+d), frame_color, 3)
                    cv2.line(frame_resized, (fx, fy+fh), (fx+d, fy+fh), frame_color, 3)
                    cv2.line(frame_resized, (fx, fy+fh), (fx, fy+fh-d), frame_color, 3)
                    cv2.line(frame_resized, (fx+fw, fy+fh), (fx+fw-d, fy+fh), frame_color, 3)
                    cv2.line(frame_resized, (fx+fw, fy+fh), (fx+fw, fy+fh-d), frame_color, 3)
            else:
                consecutive_noface += 1
                if consecutive_noface > 5:
                    consecutive_matches = max(0, consecutive_matches - 1)
                status_ctrl.value = "Buscando rostro..."
                status_ctrl.color = COLORS["text_muted"]

            _, buffer = cv2.imencode('.jpg', frame_resized)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            image_ctrl.src = f"data:image/jpeg;base64,{img_base64}"
            page.update()

            if consecutive_matches >= 10:
                status_ctrl.value = f"¡Acceso Concedido! Bienvenido, {selected_user}. 🌱"
                status_ctrl.color = COLORS["success"]
                page.update()
                time.sleep(1.2)
                scan_ctrl.is_running = False
                if scan_ctrl.cap:
                    scan_ctrl.cap.release()
                close_callback()
                nav["welcome"](selected_user)
                return

            time.sleep(0.03)

        if scan_ctrl.cap:
            scan_ctrl.cap.release()

    def start_simulation(image_ctrl, status_ctrl, selected_user, close_callback):
        scan_ctrl.is_running = True
        
        messages = [
            "Iniciando escaneo místico de ogro...",
            "Buscando rastros de lodo...",
            "Analizando orejas de trompeta...",
            "Midiendo nivel de cebolla...",
            "Autenticando ADN del pantano...",
            f"¡Acceso Concedido! Bienvenido, {selected_user}."
        ]
        
        for i, msg in enumerate(messages):
            if not scan_ctrl.is_running:
                break
                
            status_ctrl.value = msg
            if i == len(messages) - 1:
                status_ctrl.color = COLORS["success"]
            else:
                status_ctrl.color = COLORS["gold"]
                
            progress = (i + 1) / len(messages)
            pct = int(progress * 100)
            
            color_scan = "#2a9d8f" if i == len(messages) - 1 else "#d4af37"
            svg_scan = f"""
            <svg width="320" height="240" viewBox="0 0 320 240" xmlns="http://www.w3.org/2000/svg">
              <rect width="320" height="240" fill="#142410" rx="12" stroke="#3a5c2e" stroke-width="2"/>
              <line x1="0" y1="120" x2="320" y2="120" stroke="#3a5c2e" stroke-dasharray="5,5" opacity="0.3"/>
              <line x1="160" y1="0" x2="160" y2="240" stroke="#3a5c2e" stroke-dasharray="5,5" opacity="0.3"/>
              
              <circle cx="160" cy="110" r="50" fill="none" stroke="{color_scan}" stroke-width="3" stroke-dasharray="8,4"/>
              <path d="M 125 150 Q 160 175 195 150" fill="none" stroke="{color_scan}" stroke-width="3"/>
              <path d="M 105 100 Q 90 80 112 90" fill="none" stroke="{color_scan}" stroke-width="3"/>
              <path d="M 215 100 Q 230 80 208 90" fill="none" stroke="{color_scan}" stroke-width="3"/>
              
              <line x1="10" y1="{40 + (i*30)}" x2="310" y2="{40 + (i*30)}" stroke="{color_scan}" stroke-width="4" opacity="0.8"/>
              <rect x="10" y="{40 + (i*30) - 10}" width="300" height="20" fill="url(#grad)" opacity="0.15"/>
              
              <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="{color_scan}" stop-opacity="1"/>
                  <stop offset="100%" stop-color="{color_scan}" stop-opacity="0"/>
                </linearGradient>
              </defs>
              
              <text x="160" y="210" font-family="monospace" font-size="14" fill="{color_scan}" text-anchor="middle">
                ESCANEO: {pct}%
              </text>
            </svg>
            """
            svg_b64 = base64.b64encode(svg_scan.strip().encode('utf-8')).decode('utf-8')
            image_ctrl.src = f"data:image/svg+xml;base64,{svg_b64}"
            page.update()
            time.sleep(0.6)
            
        if scan_ctrl.is_running:
            time.sleep(0.5)
            scan_ctrl.is_running = False
            close_callback()
            nav["welcome"](selected_user)

    def do_facial_login(e):
        if not USERS_DB:
            show_snack(page, "No hay habitantes registrados en el pantano. Regístrate primero.", error=True)
            return

        # Recargar opciones: solo usuarios con rostro registrado
        users_with_face = [u for u, d in USERS_DB.items() if isinstance(d, dict) and d.get("face_data")]
        if not users_with_face:
            show_snack(page, "¡Ningún habitante tiene rostro registrado! Regístrate y vincula tu rostro primero.", error=True)
            return

        user_dropdown.options = [ft.dropdown.Option(u) for u in users_with_face]
        user_dropdown.value = users_with_face[0]
        
        # Modo por defecto según disponibilidad de OpenCV
        scan_ctrl.mode = "real" if (OPENCV_AVAILABLE or globals().get('OPENCV_AVAILABLE', False)) else "simulated"
        
        mode_btn = ft.IconButton(
            icon=ft.Icons.VIDEOCAM_ROUNDED if scan_ctrl.mode == "real" else ft.Icons.AUTO_AWESOME_ROUNDED,
            icon_color=COLORS["gold"],
            tooltip="Alternar entre cámara real y simulación mística",
            on_click=None
        )
        
        scan_image = ft.Image(
            src="",
            width=320,
            height=240,
            fit="contain",
            border_radius=12,
        )

        registered_face_image = ft.Image(
            src="",
            width=320,
            height=240,
            fit="contain",
            border_radius=12,
        )
        
        status_text = ft.Text(
            "Iniciando escáner...",
            color=COLORS["text_muted"],
            size=14,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )

        def toggle_mode(e):
            scan_ctrl.is_running = False
            if scan_ctrl.cap:
                scan_ctrl.cap.release()
                scan_ctrl.cap = None
                
            if scan_ctrl.mode == "real":
                scan_ctrl.mode = "simulated"
                mode_btn.icon = ft.Icons.AUTO_AWESOME_ROUNDED
                mode_btn.tooltip = "Usar simulación mística"
            else:
                is_cv2_avail = False
                try:
                    import cv2
                    is_cv2_avail = True
                except ImportError:
                    pass

                if not is_cv2_avail:
                    show_snack(page, "La cámara real requiere OpenCV. Usando modo simulación.", error=True)
                    return
                scan_ctrl.mode = "real"
                mode_btn.icon = ft.Icons.VIDEOCAM_ROUNDED
                mode_btn.tooltip = "Usar cámara real"
                
            page.update()
            time.sleep(0.2)
            start_scan()

        mode_btn.on_click = toggle_mode

        def start_scan():
            selected = user_dropdown.value
            if not selected:
                status_text.value = "Por favor selecciona un habitante"
                status_text.color = COLORS["error"]
                page.update()
                return

            user_data = USERS_DB.get(selected)
            if not isinstance(user_data, dict) or not user_data.get("face_data"):
                status_text.value = "Este habitante no tiene rostro registrado."
                status_text.color = COLORS["error"]
                registered_face_image.src = ""
                # Clear active video feed/scan view
                scan_image.src = ""
                page.update()
                return

            status_text.value = "Iniciando escáner..."
            status_text.color = COLORS["text_muted"]
            page.update()

            # Verificar si el usuario registró con foto real o simulación
            user_data = USERS_DB.get(selected)
            face_str = user_data.get("face_data", "") if isinstance(user_data, dict) else ""
            is_real_face = face_str.startswith("data:image/jpeg;base64,")

            if scan_ctrl.mode == "real":
                # Construir reconocedor LBPH solo si el usuario tiene foto real
                rec, lmap = (build_face_recognizer() if is_real_face else (None, None))
                if not is_real_face:
                    status_text.value = "Rostro registrado en modo simulación. Usa clave normal o re-regístrate con cámara real."
                    status_text.color = COLORS["error"]
                    page.update()
                    return
                threading.Thread(
                    target=start_real_camera,
                    args=(scan_image, status_text, selected, close_scan_dialog),
                    kwargs={"recognizer": rec, "label_map": lmap},
                    daemon=True
                ).start()
            else:
                threading.Thread(
                    target=start_simulation,
                    args=(scan_image, status_text, selected, close_scan_dialog),
                    daemon=True
                ).start()

        def on_user_change(e):
            scan_ctrl.is_running = False
            if scan_ctrl.cap:
                scan_ctrl.cap.release()
                scan_ctrl.cap = None
            time.sleep(0.2)
            start_scan()

        user_dropdown.on_change = on_user_change

        def close_scan_dialog(e=None):
            scan_ctrl.is_running = False
            if scan_ctrl.cap:
                scan_ctrl.cap.release()
                scan_ctrl.cap = None
            scan_dialog.open = False
            page.update()

        scan_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("Escáner Facial del Reino 👁️", color=COLORS["gold"], size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                mode_btn
            ]),
            content=ft.Container(
                width=400,
                height=380,
                content=ft.Column([
                    user_dropdown,
                    ft.Container(height=10),
                    ft.Container(
                        content=scan_image,
                        border=ft.Border.all(2, COLORS["border"]),
                        border_radius=12,
                        bgcolor=COLORS["bg_field"],
                        width=360,
                        height=270,
                        alignment=ft.Alignment(0, 0)
                    ),
                    ft.Container(height=10),
                    ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancelar", color=COLORS["error"], weight=ft.FontWeight.BOLD),
                    on_click=close_scan_dialog
                )
            ],
            bgcolor=COLORS["bg_panel"],
            shape=ft.RoundedRectangleBorder(radius=16),
        )

        if scan_dialog not in page.overlay:
            page.overlay.append(scan_dialog)
        scan_dialog.open = True
        page.update()
        start_scan()

    # Dropdown: solo usuarios con rostro vinculado al inicio
    users_with_face_init = [u for u, d in USERS_DB.items() if isinstance(d, dict) and d.get("face_data")]
    user_options = [ft.dropdown.Option(u) for u in users_with_face_init]
    user_dropdown = ft.Dropdown(
        label="Seleccionar habitante del pantano",
        options=user_options,
        value=user_options[0].key if user_options else None,
        border_color=COLORS["border"],
        focused_border_color=COLORS["gold"],
        color=COLORS["text_light"],
        bgcolor=COLORS["bg_field"],
        border_radius=12,
        label_style=ft.TextStyle(color=COLORS["gold"]),
    )

    def build_facial_login_button():
        return ft.OutlinedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FACE_UNLOCK_ROUNDED, color=COLORS["gold"], size=20),
                    ft.Text("Acceso Facial del Reino", color=COLORS["gold"], size=16, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            height=54,
            width=408,
            on_click=do_facial_login,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                side=ft.BorderSide(1.5, COLORS["gold"]),
            ),
        )

    right_panel = ft.Container(
        expand=True,
        bgcolor=COLORS["bg_panel"],
        border_radius=0,
        padding=ft.Padding(58, 0, 58, 0),
        alignment=ft.Alignment(0, 0),
        content=ft.Container(
            width=408,
            content=ft.Column(
                [
                    ft.Text("Iniciar Sesión", size=30, weight=ft.FontWeight.BOLD, color=COLORS["text_light"]),
                    ft.Text("Ingresa tus credenciales de ogro", size=15, color=COLORS["text_muted"]),
                    ft.Container(height=20),
                    login_user,
                    ft.Container(height=10),
                    login_pass,
                    ft.Row(
                        [ft.TextButton(
                            content=ft.Text("¿Olvidaste tu usuario o contraseña?", color=COLORS["gold"], size=13),
                            on_click=lambda _: nav["forgot"](),
                        )],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Container(height=10),
                    build_action_button("Entrar al pantano", ft.Icons.LOGIN_ROUNDED, do_login),
                    ft.Container(height=10),
                    build_facial_login_button(),
                    ft.Container(height=16),
                    ft.Row(
                        [
                            ft.Text("¿No tienes cuenta?", color=COLORS["text_muted"], size=15),
                            ft.TextButton(
                                content=ft.Text("Únete al reino", color=COLORS["gold"], weight=ft.FontWeight.BOLD, size=15),
                                on_click=lambda _: nav["register"](),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
        )
    )

    return ft.Container(
        content=ft.Row([
            build_left_panel("Reino del Pantano", "Solo los nobles ogros\npueden entrar aquí"),
            right_panel,
        ], spacing=0, expand=True),
        expand=True,
        border_radius=0,
    )