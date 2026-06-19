# ─────────────────────────────────────────
#  views/welcome.py — Página de bienvenida
# ─────────────────────────────────────────
import flet as ft
from constants import COLORS


def build_welcome_view(page, nav, username: str):
    return ft.Container(
        expand=True,
        content=ft.Column(
            [
                ft.Text(
                    f"¡Bienvenido, {username}! 🐊",
                    size=36,
                    color=COLORS["gold_light"],
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "Salir del pantano",
                    on_click=lambda _: nav["login"](),
                    bgcolor=COLORS["gold"],
                    color="#1a2e10",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    height=46,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
    )