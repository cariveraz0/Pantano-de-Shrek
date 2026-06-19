# ─────────────────────────────────────────
#  views/welcome.py — Gestor de Tareas del Pantano
# ─────────────────────────────────────────
import flet as ft
import random
from constants import COLORS, USERS_DB
from components import show_snack


def build_welcome_view(page, nav, username: str):
    # Asegurar estructura correcta en la base de datos temporal
    if username not in USERS_DB:
        USERS_DB[username] = {"password": "", "email": "", "tasks": []}
    elif not isinstance(USERS_DB[username], dict):
        password_str = USERS_DB[username]
        USERS_DB[username] = {"password": password_str, "email": "", "tasks": []}
    
    if "tasks" not in USERS_DB[username]:
        USERS_DB[username]["tasks"] = []
        
    user_tasks = USERS_DB[username]["tasks"]

    # ── Controles de entrada del formulario ──
    title_field = ft.TextField(
        label="Nombre de la Misión",
        prefix_icon=ft.Icons.ASSIGNMENT_SHARP,
        border_color=COLORS["border"],
        focused_border_color=COLORS["gold"],
        color=COLORS["text_light"],
        bgcolor=COLORS["bg_field"],
        border_radius=12,
        label_style=ft.TextStyle(color=COLORS["gold"]),
    )
    
    desc_field = ft.TextField(
        label="Detalles / Descripción",
        prefix_icon=ft.Icons.DESCRIPTION_ROUNDED,
        multiline=True,
        min_lines=2,
        max_lines=3,
        border_color=COLORS["border"],
        focused_border_color=COLORS["gold"],
        color=COLORS["text_light"],
        bgcolor=COLORS["bg_field"],
        border_radius=12,
        label_style=ft.TextStyle(color=COLORS["gold"]),
    )
    
    status_dropdown = ft.Dropdown(
        label="Estado Inicial",
        border_color=COLORS["border"],
        focused_border_color=COLORS["gold"],
        color=COLORS["text_light"],
        bgcolor=COLORS["bg_field"],
        border_radius=12,
        label_style=ft.TextStyle(color=COLORS["gold"]),
        options=[
            ft.dropdown.Option("todo", "Por Hacer (Pendiente)"),
            ft.dropdown.Option("in_progress", "En Progreso (En Caldero)"),
            ft.dropdown.Option("dont_do", "No Hacer (¡Fuera de mi Pantano!)"),
        ],
        value="todo"
    )

    # ── Listas de controles para el Tablero Kanban ──
    todo_list = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    in_progress_list = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
    dont_do_list = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Lógica de control de tareas ──
    def move_task(task_id, direction):
        for task in user_tasks:
            if task["id"] == task_id:
                current_status = task["status"]
                if direction == "right":
                    if current_status == "todo":
                        task["status"] = "in_progress"
                    elif current_status == "in_progress":
                        task["status"] = "dont_do"
                elif direction == "left":
                    if current_status == "dont_do":
                        task["status"] = "in_progress"
                    elif current_status == "in_progress":
                        task["status"] = "todo"
                break
        refresh_board()

    def delete_task(task_id):
        for i, task in enumerate(user_tasks):
            if task["id"] == task_id:
                user_tasks.pop(i)
                break
        refresh_board()
        show_snack(page, "Misión arrojada a la ciénaga. 🐊")

    def add_task(e):
        title = title_field.value.strip()
        desc = desc_field.value.strip()
        status = status_dropdown.value
        
        if not title:
            title_field.error_text = "La misión necesita un nombre"
            page.update()
            return
            
        title_field.error_text = None
        
        new_task = {
            "id": str(random.randint(100000, 999999)),
            "title": title,
            "desc": desc if desc else "Sin descripción especial del pantano.",
            "status": status
        }
        user_tasks.append(new_task)
        
        # Limpiar formulario
        title_field.value = ""
        desc_field.value = ""
        status_dropdown.value = "todo"
        
        refresh_board()
        show_snack(page, f"Misión '{title}' agregada al pantano. 🌲")

    def build_task_card(task):
        status = task["status"]
        task_id = task["id"]
        
        # Personalizar encabezado según el estado
        if status == "todo":
            header_color = COLORS["gold_light"]
            border_color = COLORS["border"]
        elif status == "in_progress":
            header_color = "#e5c158"
            border_color = "#3a3c20"
        else: # dont_do
            header_color = "#cf5c5c"
            border_color = "#4c2626"

        buttons = []
        
        # Botón mover a la izquierda
        if status != "todo":
            buttons.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_ROUNDED,
                    icon_color=COLORS["gold"],
                    tooltip="Mover a la izquierda",
                    on_click=lambda _: move_task(task_id, "left"),
                    icon_size=18,
                )
            )
            
        # Botón tirar a la ciénaga
        buttons.append(
            ft.IconButton(
                icon=ft.Icons.DELETE_ROUNDED,
                icon_color="#e63946",
                tooltip="Tirar a la ciénaga (Borrar)",
                on_click=lambda _: delete_task(task_id),
                icon_size=18,
            )
        )
        
        # Botón mover a la derecha
        if status != "dont_do":
            buttons.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                    icon_color=COLORS["gold"],
                    tooltip="Mover a la derecha",
                    on_click=lambda _: move_task(task_id, "right"),
                    icon_size=18,
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Text(task["title"], size=16, weight=ft.FontWeight.BOLD, color=header_color),
                ft.Text(task["desc"], size=12, color=COLORS["text_muted"]),
                ft.Divider(color=COLORS["border"], height=1),
                ft.Row(buttons, alignment=ft.MainAxisAlignment.END, spacing=4)
            ], spacing=6),
            bgcolor=COLORS["bg_field"],
            padding=12,
            border_radius=10,
            border=ft.Border.all(1, border_color),
            shadow=ft.BoxShadow(blur_radius=5, color="#00000033")
        )

    def refresh_board():
        todo_list.controls.clear()
        in_progress_list.controls.clear()
        dont_do_list.controls.clear()
        
        todo_count = 0
        in_progress_count = 0
        dont_do_count = 0
        
        for task in user_tasks:
            card = build_task_card(task)
            if task["status"] == "todo":
                todo_list.controls.append(card)
                todo_count += 1
            elif task["status"] == "in_progress":
                in_progress_list.controls.append(card)
                in_progress_count += 1
            elif task["status"] == "dont_do":
                dont_do_list.controls.append(card)
                dont_do_count += 1
                
        todo_header.value = f"Misiones Pendientes ({todo_count})"
        in_progress_header.value = f"En el Caldero ({in_progress_count})"
        dont_do_header.value = f"¡FUERA DE MI PANTANO! ({dont_do_count})"
        
        page.update()

    # Controles de encabezados
    todo_header = ft.Text("Misiones Pendientes (0)", size=18, weight=ft.FontWeight.BOLD, color=COLORS["gold_light"])
    in_progress_header = ft.Text("En el Caldero (0)", size=18, weight=ft.FontWeight.BOLD, color="#e5c158")
    dont_do_header = ft.Text("¡FUERA DE MI PANTANO! (0)", size=18, weight=ft.FontWeight.BOLD, color="#cf5c5c")

    # ── PANEL LATERAL (Sidebar de Creación y Perfil) ──
    sidebar = ft.Container(
        width=320,
        bgcolor=COLORS["bg_panel"],
        border=ft.Border(right=ft.BorderSide(1.5, COLORS["border"])),
        padding=24,
        content=ft.Column([
            # Identidad del ogro activo
            ft.Row([
                ft.Icon(ft.Icons.PERSON_2_ROUNDED, color=COLORS["gold"], size=28),
                ft.Column([
                    ft.Text("Ogro Activo", size=11, color=COLORS["text_muted"]),
                    ft.Text(username, size=18, weight=ft.FontWeight.BOLD, color=COLORS["gold_light"]),
                ], spacing=1)
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Divider(color=COLORS["border"], height=30),
            
            # Formulario de nueva tarea
            ft.Text("Nueva Misión 📝", size=18, weight=ft.FontWeight.BOLD, color=COLORS["gold"]),
            ft.Text("Asigna deberes al Reino", size=13, color=COLORS["text_muted"]),
            ft.Container(height=10),
            
            title_field,
            ft.Container(height=6),
            desc_field,
            ft.Container(height=6),
            status_dropdown,
            ft.Container(height=16),
            
            # Botón de añadir
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_ROUNDED, color="#1a2e10", size=20),
                    ft.Text("Crear Misión", color="#1a2e10", size=15, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=COLORS["gold"],
                height=48,
                on_click=add_task,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            
            ft.Container(expand=True),
            
            ft.Divider(color=COLORS["border"], height=30),
            
            # Botón de salir
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, color="#cf5c5c", size=20),
                    ft.Text("Salir del Pantano", color="#cf5c5c", size=15, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                on_click=lambda _: nav["login"](),
            )
        ], spacing=10, expand=True)
    )

    # ── TABLERO DE TAREAS KANBAN ──
    board = ft.Container(
        expand=True,
        padding=24,
        content=ft.Column([
            # Encabezado del Tablero
            ft.Text("Tablero del Reino del Pantano 🌲", size=26, weight=ft.FontWeight.BOLD, color=COLORS["text_light"]),
            ft.Text("Maneja tus actividades antes de que invadan tu ciénaga", size=14, color=COLORS["text_muted"]),
            ft.Container(height=15),
            
            # Fila con las tres columnas Kanban
            ft.Row([
                # Columna: Todo
                ft.Container(
                    expand=True,
                    bgcolor="#101c0c",
                    border_radius=16,
                    border=ft.Border.all(1, COLORS["border"]),
                    padding=16,
                    content=ft.Column([
                        todo_header,
                        ft.Divider(color=COLORS["border"]),
                        todo_list
                    ], spacing=10, expand=True)
                ),
                # Columna: In Progress
                ft.Container(
                    expand=True,
                    bgcolor="#17190c",
                    border_radius=16,
                    border=ft.Border.all(1, "#3a3c20"),
                    padding=16,
                    content=ft.Column([
                        in_progress_header,
                        ft.Divider(color="#3a3c20"),
                        in_progress_list
                    ], spacing=10, expand=True)
                ),
                # Columna: Don't Do
                ft.Container(
                    expand=True,
                    bgcolor="#1c1010",
                    border_radius=16,
                    border=ft.Border.all(1, "#4c2626"),
                    padding=16,
                    content=ft.Column([
                        dont_do_header,
                        ft.Divider(color="#4c2626"),
                        dont_do_list
                    ], spacing=10, expand=True)
                ),
            ], spacing=16, expand=True)
        ], spacing=5, expand=True)
    )

    # Cargar tablero inicialmente
    refresh_board()

    # Retornar contenedor completo
    return ft.Container(
        expand=True,
        bgcolor=COLORS["bg_dark"],
        content=ft.Row([
            sidebar,
            board
        ], spacing=0, expand=True)
    )