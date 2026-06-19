# ─────────────────────────────────────────
#  views/forgot.py — Página de recuperación
# ─────────────────────────────────────────
import flet as ft
import re
import random
from constants import USERS_DB, COLORS
import constants
from components import make_field, show_snack, build_left_panel, build_action_button


def build_forgot_view(page, nav, simulator_button, simulator_mailbox, text_ref):
    forgot_email       = make_field(page, "Correo",              ft.Icons.EMAIL_ROUNDED,    helper="* Tu correo registrado")
    verification_field = make_field(page, "Introduce el código", ft.Icons.SECURITY_ROUNDED, helper="* Mira el Simulador abajo")

    input_container        = ft.Column([forgot_email, ft.Container(height=15)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    verification_container = ft.Column([verification_field, ft.Container(height=15)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)
    result_container       = ft.Column(visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    credentials_holder = {"user": "", "pass": ""}

    def do_send_code(e):
        em = forgot_email.value.strip() if forgot_email.value else ""
        if not em or not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", em):
            forgot_email.error = "Ingresa un correo válido"
            page.update()
            return

        found_user, found_pass = None, None
        for username, data in USERS_DB.items():
            if isinstance(data, dict) and data.get("email") == em:
                found_user = username
                found_pass = data.get("password")
                break

        if not found_user:
            forgot_email.error = "Este correo no existe en el reino"
            page.update()
            return

        credentials_holder["user"] = found_user
        credentials_holder["pass"] = found_pass
        constants.CURRENT_SIMULATED_CODE = f"{random.randint(100000, 999999)}"

        text_ref.current.value = (
            f"De: seguridad@pantano.com\n"
            f"Para: {em}\n\n"
            f"Código de seguridad solicitado:\n👉 {constants.CURRENT_SIMULATED_CODE} 👈"
        )

        simulator_button.visible = True
        input_container.visible = False
        verification_container.visible = True
        send_btn.visible = False
        verify_btn.visible = True

        page.update()
        show_snack(page, "¡Código enviado al simulador flotante!")

    def do_verify_code(e):
        entered = verification_field.value.strip() if verification_field.value else ""
        if entered == constants.CURRENT_SIMULATED_CODE:
            verification_container.visible = False
            verify_btn.visible = False

            result_container.controls.extend([
                ft.Icon(ft.Icons.KEY_ROUNDED, color=COLORS["gold"], size=48),
                ft.Text("Credenciales Recuperadas", size=22, weight=ft.FontWeight.BOLD, color=COLORS["gold_light"]),
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Text("Usuario:", color=COLORS["text_muted"]), ft.Text(credentials_holder["user"], color=COLORS["text_light"], weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(color=COLORS["border"]),
                        ft.Row([ft.Text("Clave:", color=COLORS["text_muted"]), ft.Text(credentials_holder["pass"], color=COLORS["text_light"], weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]),
                    padding=16, border=ft.Border.all(1, COLORS["border"]), border_radius=12, bgcolor=COLORS["bg_field"], width=320,
                ),
            ])
            result_container.visible = True
            simulator_button.visible = False
            simulator_mailbox.visible = False
            page.update()
        else:
            verification_field.error = "Código incorrecto"
            page.update()

    send_btn  = build_action_button("Enviar Instrucciones",  ft.Icons.SEND_ROUNDED,          do_send_code)
    verify_btn = build_action_button("Verificar Código",     ft.Icons.CHECK_CIRCLE_ROUNDED,  do_verify_code)
    verify_btn.visible = False

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
                    ft.Text("Recuperación", size=30, weight=ft.FontWeight.BOLD, color=COLORS["text_light"]),
                    ft.Text("Digita tu correo para generar un token", size=15, color=COLORS["text_muted"]),
                    ft.Container(height=25),
                    input_container,
                    verification_container,
                    result_container,
                    ft.Container(height=15),
                    send_btn,
                    verify_btn,
                    ft.Container(height=16),
                    ft.TextButton(
                        content=ft.Text("Volver al Inicio de Sesión", color=COLORS["gold"], weight=ft.FontWeight.BOLD, size=15),
                        on_click=lambda _: nav["login"](),
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
            build_left_panel("Recuperar Cuenta", "Verifica tu identidad\npara regresar al reino"),
            right_panel,
        ], spacing=0, expand=True),
        expand=True,
        border_radius=0,
    )