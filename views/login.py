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
    import os

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    faces_list = []
    labels_list = []
    label_map = {}  # int_label -> username
    
    if not os.path.exists("Image"):
        return None, None

    for idx, filename in enumerate(os.listdir("Image")):
        if not filename.endswith(".png"):
            continue
        username = filename[:-4]
        filepath = os.path.join("Image", filename)
        try:
            img_gray = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
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
            self.mode = "real"

    scan_ctrl = ScanController()

    def start_real_camera(image_ctrl, status_ctrl, close_callback, recognizer=None, label_map=None):
        scan_ctrl.is_running = True
        scan_ctrl.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not scan_ctrl.cap.isOpened():
            scan_ctrl.cap = cv2.VideoCapture(0)

        if not scan_ctrl.cap.isOpened():
            status_ctrl.value = "Error: No se detectó cámara."
            status_ctrl.color = COLORS["error"]
            page.update()
            return

        face_cascade = None
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception:
            pass

        match_counts = {}
        consecutive_noface = 0

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
                        if confidence < 80 and pred_user:
                            match_counts[pred_user] = match_counts.get(pred_user, 0) + 1
                            frame_color = (55, 212, 125)   # verde: coincide
                            pct = min(match_counts[pred_user] * 10, 100)
                            status_ctrl.value = f"¡Rostro reconocido ({pred_user})! ({pct}%)"
                            status_ctrl.color = COLORS["success"]
                            
                            if match_counts[pred_user] >= 10:
                                status_ctrl.value = f"¡Acceso Concedido! Bienvenido, {pred_user}. 🌱"
                                status_ctrl.color = COLORS["success"]
                                page.update()
                                time.sleep(1.2)
                                scan_ctrl.is_running = False
                                if scan_ctrl.cap:
                                    scan_ctrl.cap.release()
                                close_callback()
                                nav["welcome"](pred_user)
                                return
                        else:
                            frame_color = (55, 55, 212)    # rojo-azul: no coincide
                            status_ctrl.value = f"Buscando coincidencia..."
                            status_ctrl.color = COLORS["error"]
                    except Exception:
                        status_ctrl.value = "Error en reconocimiento. Intenta de nuevo."
                        status_ctrl.color = COLORS["error"]
                else:
                    # Sin reconocedor no podemos iniciar sesión automáticamente
                    frame_color = (55, 55, 212)
                    status_ctrl.value = "Ningún rostro registrado."
                    status_ctrl.color = COLORS["error"]

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
                status_ctrl.value = "Buscando rostro..."
                status_ctrl.color = COLORS["text_muted"]

            _, buffer = cv2.imencode('.jpg', frame_resized)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            image_ctrl.src = f"data:image/jpeg;base64,{img_base64}"
            page.update()

            time.sleep(0.03)

        if scan_ctrl.cap:
            scan_ctrl.cap.release()

    def do_facial_login(e):
        import os
        if not os.path.exists("Image") or not any(f.endswith(".png") for f in os.listdir("Image")):
            show_snack(page, "¡Ningún habitante tiene rostro registrado!", error=True)
            return

        scan_ctrl.mode = "real"
        
        scan_image = ft.Image(
            src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
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

        def start_scan():
            status_text.value = "Iniciando escáner..."
            status_text.color = COLORS["text_muted"]
            page.update()

            rec, lmap = build_face_recognizer()
            if not rec:
                status_text.value = "Error al entrenar el modelo. No hay rostros válidos."
                status_text.color = COLORS["error"]
                page.update()
                return
            
            threading.Thread(
                target=start_real_camera,
                args=(scan_image, status_text, close_scan_dialog),
                kwargs={"recognizer": rec, "label_map": lmap},
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
                ft.Container(expand=True)
            ]),
            content=ft.Container(
                width=400,
                height=380,
                content=ft.Column([
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