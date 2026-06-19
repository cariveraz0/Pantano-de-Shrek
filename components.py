# ─────────────────────────────────────────
#  components.py — Componentes reutilizables
# ─────────────────────────────────────────
import flet as ft
from constants import OGRE_SVG, COLORS


def show_snack(page, message: str, error: bool = False):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="white"),
        bgcolor=COLORS["error"] if error else COLORS["success"],
    )
    page.snack_bar.open = True
    page.update()


def make_field(page, label, icon, password=False, helper="", on_submit_action=None):
    def clear_error(e):
        if e.control.error:
            e.control.error = None
            page.update()

    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        prefix_icon=icon,
        border_color=COLORS["border"],
        focused_border_color=COLORS["gold"],
        color=COLORS["text_light"],
        label_style=ft.TextStyle(color=COLORS["gold"]),
        bgcolor=COLORS["bg_field"],
        border_radius=12,
        on_change=clear_error,
        helper=helper,
        helper_style=ft.TextStyle(color=COLORS["text_muted"], size=10),
        on_submit=on_submit_action,
    )


def build_left_panel(title: str, subtitle: str, expand=True):
    """Panel izquierdo decorativo reutilizable en todas las vistas."""
    return ft.Container(
        expand=expand,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=COLORS["gradient"],
        ),
        border_radius=0,
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Image(
                        src=f"data:image/svg+xml;utf8,{OGRE_SVG}",
                        width=156,
                        height=156,
                    ),
                    bgcolor="#0e1a0a55",
                    border_radius=100,
                    padding=12,
                ),
                ft.Text(title, size=30, weight=ft.FontWeight.BOLD, color=COLORS["gold_light"]),
                ft.Text(subtitle, size=16, color="#d8e8c8", text_align=ft.TextAlign.CENTER),
                ft.Container(height=16),
                ft.Container(width=84, height=5, bgcolor=COLORS["gold"], border_radius=10),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
        ),
    )


def build_action_button(label: str, icon, on_click):
    """Botón dorado principal reutilizable."""
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(icon, color="#1a2e10", size=20),
                ft.Text(label, color="#1a2e10", size=17, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=COLORS["gold"],
        height=58,
        width=408,
        on_click=on_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )


def build_simulator(page):
    """
    Construye el simulador de correo flotante.
    Retorna (simulator_mailbox, simulator_button, text_ref)
    """
    text_ref = ft.Ref[ft.Text]()

    mailbox = ft.Container(
        visible=False,
        bottom=85,
        right=24,
        width=340,
        height=220,
        bgcolor=COLORS["bg_panel"],
        border=ft.Border.all(2, COLORS["border"]),
        border_radius=16,
        padding=16,
        shadow=ft.BoxShadow(blur_radius=30, color="#000000cc"),
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.MARK_EMAIL_READ_ROUNDED, color=COLORS["gold"]),
                ft.Text("Mailbox (Simulado)", color=COLORS["gold"], weight=ft.FontWeight.BOLD),
            ]),
            ft.Divider(color=COLORS["border"]),
            ft.Text(ref=text_ref, value="", color=COLORS["text_light"], size=13),
        ]),
    )

    def toggle(e):
        mailbox.visible = not mailbox.visible
        page.update()

    button = ft.Container(
        visible=False,
        bottom=24,
        right=24,
        content=ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.EMAIL_ROUNDED, color=COLORS["gold"]),
                ft.Text("Simulador de Correo", color=COLORS["text_light"]),
            ]),
            bgcolor=COLORS["bg_field"],
            height=48,
            on_click=toggle,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=24),
                side=ft.BorderSide(1.5, COLORS["gold"]),
            ),
        ),
    )

    return mailbox, button, text_ref