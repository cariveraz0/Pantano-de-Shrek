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