# ─────────────────────────────────────────
#  main.py — Entrada principal del Reino
# ─────────────────────────────────────────
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flet as ft
from components import build_simulator
from views.login    import build_login_view
from views.register import build_register_view
from views.forgot   import build_forgot_view
from views.welcome  import build_welcome_view


def main(page: ft.Page):
    page.title = "Reino del Pantano"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0e1a0a"
    page.padding = 0
    page.fonts = {
        "MedievalSharp": "https://raw.githubusercontent.com/google/fonts/main/ofl/medievalsharp/MedievalSharp.ttf"
    }
    page.theme = ft.Theme(font_family="MedievalSharp")

    # ── Simulador de correo flotante ──────────
    simulator_mailbox, simulator_button, text_ref = build_simulator(page)

    # ── Diccionario de navegación ─────────────
    # Cada vista recibe 'nav' para poder cambiar de página sin depender de page.go()
    nav = {}

    def navigate_to(view_builder):
        simulator_button.visible = False
        simulator_mailbox.visible = False
        view = view_builder()
        view.top = 0
        view.left = 0
        view.right = 0
        view.bottom = 0
        main_layout.controls[0] = view
        page.update()

    nav["login"]    = lambda:    navigate_to(lambda: build_login_view(page, nav))
    nav["register"] = lambda:    navigate_to(lambda: build_register_view(page, nav))
    nav["forgot"]   = lambda:    navigate_to(lambda: build_forgot_view(page, nav, simulator_button, simulator_mailbox, text_ref))
    nav["welcome"]  = lambda u:  navigate_to(lambda: build_welcome_view(page, nav, u))

    # ── Layout base ───────────────────────────
    main_layout = ft.Stack(
        [ft.Container(expand=True), simulator_mailbox, simulator_button],
        expand=True,
    )

    page.add(main_layout)
    nav["login"]()


ft.run(main=main, view=ft.AppView.WEB_BROWSER, port=8551, host="0.0.0.0")