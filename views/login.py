# ─────────────────────────────────────────
#  views/login.py — Página de inicio de sesión
# ─────────────────────────────────────────
import flet as ft
from constants import USERS_DB, COLORS
from components import make_field, show_snack, build_left_panel, build_action_button


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

        show_snack(page, "Usuario o clave incorrectos.", error=True)

    right_panel = ft.Container(
        expand=True,
        bgcolor=COLORS["bg_panel"],
        border_radius=ft.BorderRadius(0, 20, 20, 0),
        padding=ft.Padding(58, 0, 58, 0),
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

    return ft.Container(
        content=ft.Row([
            build_left_panel("Reino del Pantano", "Solo los nobles ogros\npueden entrar aquí"),
            right_panel,
        ], spacing=0),
        width=1032,
        height=624,
        border_radius=20,
    )