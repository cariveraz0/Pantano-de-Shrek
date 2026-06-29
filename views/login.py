# ─────────────────────────────────────────
#  views/login.py — Página de inicio de sesión
# ─────────────────────────────────────────
import flet as ft
import threading
import time
import base64
from constants import USERS_DB, COLORS
from components import make_field, show_snack, build_left_panel, build_action_button

# Intentar importar cv2 para detección facial real
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


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

    def start_real_camera(image_ctrl, status_ctrl, selected_user, close_callback):
        scan_ctrl.is_running = True
        # Usar DirectShow en Windows para evitar demoras de inicio
        scan_ctrl.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not scan_ctrl.cap.isOpened():
            # Intentar abrir con el driver por defecto si falla
            scan_ctrl.cap = cv2.VideoCapture(0)
            
        if not scan_ctrl.cap.isOpened():
            status_ctrl.value = "Error: No se detectó cámara. Iniciando modo simulación..."
            status_ctrl.color = COLORS["error"]
            page.update()
            time.sleep(1.5)
            # Cambiar a simulación
            scan_ctrl.mode = "simulated"
            start_simulation(image_ctrl, status_ctrl, selected_user, close_callback)
            return

        face_cascade = None
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception:
            pass

        consecutive_faces = 0
        
        while scan_ctrl.is_running:
            ret, frame = scan_ctrl.cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            
            # Redimensionar para optimizar ancho de banda de actualización
            frame_resized = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            faces = []
            if face_cascade is not None and not face_cascade.empty():
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Dibujar recuadro dorado sci-fi en las caras detectadas
            for (x, y, w, h) in faces:
                cv2.rectangle(frame_resized, (x, y), (x+w, y+h), (55, 175, 212), 2)
                d = 10
                cv2.line(frame_resized, (x, y), (x+d, y), (55, 175, 212), 3)
                cv2.line(frame_resized, (x, y), (x, y+d), (55, 175, 212), 3)
                cv2.line(frame_resized, (x+w, y), (x+w-d, y), (55, 175, 212), 3)
                cv2.line(frame_resized, (x+w, y), (x+w, y+d), (55, 175, 212), 3)
                cv2.line(frame_resized, (x, y+h), (x+d, y+h), (55, 175, 212), 3)
                cv2.line(frame_resized, (x, y+h), (x, y+h-d), (55, 175, 212), 3)
                cv2.line(frame_resized, (x+w, y+h), (x+w-d, y+h), (55, 175, 212), 3)
                cv2.line(frame_resized, (x+w, y+h), (x+w, y+h-d), (55, 175, 212), 3)

            if len(faces) > 0:
                consecutive_faces += 1
                status_ctrl.value = f"¡Rostro detectado! Verificando linaje ({consecutive_faces * 10}%)"
                status_ctrl.color = COLORS["gold"]
            else:
                consecutive_faces = max(0, consecutive_faces - 1)
                status_ctrl.value = "Buscando rostro de ogro..."
                status_ctrl.color = COLORS["text_muted"]

            # Codificar a base64 y actualizar imagen en Flet
            _, buffer = cv2.imencode('.jpg', frame_resized)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            image_ctrl.src = f"data:image/jpeg;base64,{img_base64}"
            page.update()

            if consecutive_faces >= 10:
                status_ctrl.value = f"¡Acceso Concedido! Bienvenido, {selected_user}."
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
            "¡Acceso Concedido! Bienvenido, noble criatura."
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

        # Recargar opciones por si hay usuarios nuevos
        user_dropdown.options = [ft.dropdown.Option(u) for u in USERS_DB.keys()]
        user_dropdown.value = list(USERS_DB.keys())[0]
        
        # Modo por defecto según disponibilidad de OpenCV
        # (Se puede alternar dinámicamente si el usuario lo desea)
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
                # Comprobar dinámicamente si cv2 se importó correctamente a posteriori
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
                
            if scan_ctrl.mode == "real":
                threading.Thread(
                    target=start_real_camera, 
                    args=(scan_image, status_text, selected, close_scan_dialog), 
                    daemon=True
                ).start()
            else:
                threading.Thread(
                    target=start_simulation, 
                    args=(scan_image, status_text, selected, close_scan_dialog), 
                    daemon=True
                ).start()

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
                width=360,
                height=390,
                content=ft.Column([
                    user_dropdown,
                    ft.Container(height=10),
                    ft.Container(
                        content=scan_image,
                        border=ft.Border.all(2, COLORS["border"]),
                        border_radius=12,
                        bgcolor=COLORS["bg_field"],
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

    user_options = [ft.dropdown.Option(u) for u in USERS_DB.keys()]
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