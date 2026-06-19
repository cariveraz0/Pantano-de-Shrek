# ─────────────────────────────────────────
#  views/register.py — Página de registro
# ─────────────────────────────────────────
import flet as ft
import re
from constants import USERS_DB, COLORS
from components import make_field, show_snack, build_left_panel, build_action_button


def build_register_view(page, nav):
    reg_user    = make_field(page, "Nombre de usuario",  ft.Icons.PERSON_ROUNDED,      helper="* Campo obligatorio")
    reg_email   = make_field(page, "Correo",             ft.Icons.EMAIL_ROUNDED,        helper="* Campo obligatorio")
    reg_pass    = make_field(page, "Clave Nueva",        ft.Icons.LOCK_ROUNDED,         password=True, helper="* Mínimo 4 caracteres")
    reg_confirm = make_field(page, "Confirmar Clave",    ft.Icons.LOCK_RESET_ROUNDED,   password=True, helper="* Repita su clave")

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

        USERS_DB[u] = {"password": p, "email": em}
        show_snack(page, "¡Usuario registrado exitosamente! Ya puedes entrar al pantano.")
        nav["login"]()

    right_panel = ft.Container(
        expand=True,
        bgcolor=COLORS["bg_panel"],
        border_radius=ft.BorderRadius(0, 20, 20, 0),
        padding=ft.Padding(58, 0, 58, 0),
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
                ft.Container(height=20),
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

    return ft.Container(
        content=ft.Row([
            build_left_panel("Únete al Reino", "Toda criatura del pantano\nes bienvenida"),
            right_panel,
        ], spacing=0),
        width=1032,
        height=672,
        border_radius=20,
    )