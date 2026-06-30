# ─────────────────────────────────────────
#  views/register.py — Página de registro
# ─────────────────────────────────────────
import flet as ft
import re
import threading
import time
import base64
import os
from constants import USERS_DB, COLORS
from components import make_field, show_snack, build_left_panel, build_action_button

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False





def build_register_view(page, nav):
    state = {
        "face_data": None
    }

    reg_user    = make_field(page, "Nombre de usuario",  ft.Icons.PERSON_ROUNDED,      helper="* Campo obligatorio")
    reg_email   = make_field(page, "Correo",             ft.Icons.EMAIL_ROUNDED,        helper="* Campo obligatorio")
    reg_pass    = make_field(page, "Clave Nueva",        ft.Icons.LOCK_ROUNDED,         password=True, helper="* Mínimo 4 caracteres")
    reg_confirm = make_field(page, "Confirmar Clave",    ft.Icons.LOCK_RESET_ROUNDED,   password=True, helper="* Repita su clave")

    class CaptureController:
        def __init__(self):
            self.is_running = False
            self.cap = None
            self.mode = "real"
            self.captured_image_b64 = None

    cap_ctrl = CaptureController()

    def clear_face_data():
        state["face_data"] = None
        face_preview_container.visible = False
        link_face_btn.visible = True
        page.update()

    def do_facial_capture(e):
        cap_ctrl.captured_image_b64 = None
        cap_ctrl.mode = "real"

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

        capture_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.CAMERA_ROUNDED, color="#1a2e10", size=18),
                ft.Text("Tomar Foto", color="#1a2e10", size=14, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=COLORS["gold"],
            height=44,
            width=150,
        )

        confirm_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="white", size=18),
                ft.Text("Confirmar Rostro", color="white", size=14, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=COLORS["success"],
            height=44,
            width=170,
            visible=False,
        )

        retry_btn = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.REFRESH_ROUNDED, color=COLORS["gold"], size=18),
                ft.Text("Reintentar", color=COLORS["gold"], size=14, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER),
            height=44,
            width=130,
            visible=False,
        )



        def trigger_capture(e):
            if cap_ctrl.is_running:
                ret, frame = cap_ctrl.cap.read()
                if ret and frame is not None:
                    frame = cv2.flip(frame, 1)
                    frame_resized = cv2.resize(frame, (320, 240))
                    _, buffer = cv2.imencode('.jpg', frame_resized)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    cap_ctrl.captured_image_b64 = f"data:image/jpeg;base64,{img_base64}"
                    
                    cap_ctrl.is_running = False
                    if cap_ctrl.cap:
                        cap_ctrl.cap.release()
                        cap_ctrl.cap = None

                    scan_image.src = cap_ctrl.captured_image_b64
                    status_text.value = "¡Rostro capturado con éxito!"
                    status_text.color = COLORS["gold"]
                    
                    capture_btn.visible = False
                    confirm_btn.visible = True
                    retry_btn.visible = True
                    page.update()

        capture_btn.on_click = trigger_capture

        def trigger_confirm(e):
            state["face_data"] = cap_ctrl.captured_image_b64
            face_preview.src = state["face_data"]
            face_preview_container.visible = True
            link_face_btn.visible = False
            close_scan_dialog()
            page.update()

        confirm_btn.on_click = trigger_confirm

        def trigger_retry(e):
            cap_ctrl.captured_image_b64 = None
            capture_btn.visible = True
            confirm_btn.visible = False
            retry_btn.visible = False
            status_text.value = "Iniciando escáner..."
            status_text.color = COLORS["text_muted"]
            page.update()
            start_scan()

        retry_btn.on_click = trigger_retry

        def start_scan():
            if not OPENCV_AVAILABLE:
                status_text.value = "Error: OpenCV no está disponible."
                status_text.color = COLORS["error"]
                page.update()
                return
            threading.Thread(
                target=start_real_camera_capture,
                args=(scan_image, status_text),
                daemon=True
            ).start()

        def start_real_camera_capture(image_ctrl, status_ctrl):
            cap_ctrl.is_running = True
            cap_ctrl.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap_ctrl.cap.isOpened():
                cap_ctrl.cap = cv2.VideoCapture(0)
            if not cap_ctrl.cap.isOpened():
                status_ctrl.value = "Error: No se detectó cámara."
                status_ctrl.color = COLORS["error"]
                page.update()
                return

            face_cascade = None
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception:
                pass

            while cap_ctrl.is_running:
                ret, frame = cap_ctrl.cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

                frame = cv2.flip(frame, 1)
                frame_resized = cv2.resize(frame, (320, 240))
                gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

                faces = []
                if face_cascade is not None and not face_cascade.empty():
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame_resized, (x, y), (x+w, y+h), (212, 175, 55), 2)
                    d = 10
                    cv2.line(frame_resized, (x, y), (x+d, y), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x, y), (x, y+d), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x+w, y), (x+w-d, y), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x+w, y), (x+w, y+d), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x, y+h), (x+d, y+h), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x, y+h), (x, y+h-d), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x+w, y+h), (x+w-d, y+h), (212, 175, 55), 3)
                    cv2.line(frame_resized, (x+w, y+h), (x+w, y+h-d), (212, 175, 55), 3)

                if len(faces) > 0:
                    status_ctrl.value = "¡Rostro detectado! Presiona 'Tomar Foto'"
                    status_ctrl.color = COLORS["success"]
                else:
                    status_ctrl.value = "Buscando rostro..."
                    status_ctrl.color = COLORS["text_muted"]

                _, buffer = cv2.imencode('.jpg', frame_resized)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                image_ctrl.src = f"data:image/jpeg;base64,{img_base64}"
                page.update()
                time.sleep(0.03)

            if cap_ctrl.cap:
                cap_ctrl.cap.release()



        def close_scan_dialog(e=None):
            cap_ctrl.is_running = False
            if cap_ctrl.cap:
                cap_ctrl.cap.release()
                cap_ctrl.cap = None
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("Registrar Rostro 📸", color=COLORS["gold"], size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True)
            ]),
            content=ft.Container(
                width=360,
                height=320,
                content=ft.Column([
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
                ft.Row([
                    retry_btn,
                    confirm_btn,
                    capture_btn,
                    ft.TextButton(
                        content=ft.Text("Cancelar", color=COLORS["error"], weight=ft.FontWeight.BOLD),
                        on_click=close_scan_dialog
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ],
            bgcolor=COLORS["bg_panel"],
            shape=ft.RoundedRectangleBorder(radius=16),
        )

        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()
        start_scan()

    face_preview = ft.Image(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
        width=44,
        height=44,
        fit="cover",
        border_radius=22,
    )
    
    face_preview_container = ft.Container(
        content=ft.Row([
            face_preview,
            ft.Text("¡Rostro Vinculado!", color=COLORS["success"], size=14, weight=ft.FontWeight.BOLD),
            ft.IconButton(
                icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                icon_color=COLORS["error"],
                tooltip="Eliminar rostro",
                on_click=lambda _: clear_face_data()
            )
        ], alignment=ft.MainAxisAlignment.CENTER),
        visible=False,
    )

    link_face_btn = ft.OutlinedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ADD_A_PHOTO_ROUNDED, color=COLORS["gold"], size=18),
                ft.Text("Vincular Rostro Místico", color=COLORS["gold"], size=14, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        height=48,
        width=408,
        on_click=do_facial_capture,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            side=ft.BorderSide(1.5, COLORS["gold"]),
        ),
    )

    def do_register(e):
        u  = reg_user.value.strip()
        em = reg_email.value.strip()
        p  = reg_pass.value.strip()
        c  = reg_confirm.value.strip()

        has_error = False
        if not u:
            reg_user.error = "Usuario obligatorio"
            has_error = True
        elif u in USERS_DB:
            reg_user.error = "Ese usuario ya existe"
            has_error = True

        if not em or not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", em):
            reg_email.error = "Correo inválido"
            has_error = True

        if len(p) < 4:
            reg_pass.error = "Muy corta"
            has_error = True

        if p != c:
            reg_confirm.error = "No coinciden"
            has_error = True

        if has_error:
            page.update()
            return

        face_path = None
        if state["face_data"] and state["face_data"].startswith("data:image/jpeg;base64,"):
            try:
                if not os.path.exists("Image"):
                    os.makedirs("Image")
                img_b64 = state["face_data"].split(",", 1)[1]
                img_bytes = base64.b64decode(img_b64)
                face_path = f"Image/{u}.png"
                with open(face_path, "wb") as f:
                    f.write(img_bytes)
            except Exception as e:
                print(f"Error guardando imagen: {e}")

        USERS_DB[u] = {"password": p, "email": em, "tasks": [], "face_path": face_path}
        show_snack(page, "¡Usuario registrado exitosamente! Ya puedes entrar al pantano.")
        nav["login"]()

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
                    ft.Text("Crear Cuenta", size=30, weight=ft.FontWeight.BOLD, color=COLORS["text_light"]),
                    ft.Text("Completa tus datos para registrarte", size=15, color=COLORS["text_muted"]),
                    ft.Container(height=15),
                    reg_user,
                    ft.Container(height=8),
                    reg_email,
                    ft.Container(height=8),
                    reg_pass,
                    ft.Container(height=8),
                    reg_confirm,
                    ft.Container(height=10),
                    link_face_btn,
                    face_preview_container,
                    ft.Container(height=15),
                    build_action_button("Unirme al reino", ft.Icons.APP_REGISTRATION_ROUNDED, do_register),
                    ft.Container(height=16),
                    ft.Row(
                        [
                            ft.Text("¿Ya tienes cuenta?", color=COLORS["text_muted"], size=15),
                            ft.TextButton(
                                content=ft.Text("Inicia sesión", color=COLORS["gold"], weight=ft.FontWeight.BOLD, size=15),
                                on_click=lambda _: nav["login"](),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
        )
    )

    return ft.Container(
        content=ft.Row([
            build_left_panel("Únete al Reino", "Toda criatura del pantano\nes bienvenida"),
            right_panel,
        ], spacing=0, expand=True),
        expand=True,
        border_radius=0,
    )