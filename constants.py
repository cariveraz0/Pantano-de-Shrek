# ─────────────────────────────────────────
#  constants.py — Datos globales del Reino
# ─────────────────────────────────────────

# Base de datos temporal en memoria
USERS_DB = {}

# Estado global del código de verificación simulado
CURRENT_SIMULATED_CODE = None

# Ícono original de ogro con corona dorada
OGRE_SVG = """
<svg width="130" height="130" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M 25 35 L 10 10 L 38 28 Z" fill="#4a7c2e" stroke="#2d4d1a" stroke-width="2"/>
  <path d="M 95 35 L 110 10 L 82 28 Z" fill="#4a7c2e" stroke="#2d4d1a" stroke-width="2"/>
  <ellipse cx="60" cy="62" rx="42" ry="40" fill="#5a9c3e" stroke="#2d4d1a" stroke-width="2"/>
  <ellipse cx="32" cy="70" rx="10" ry="8" fill="#6cb350" opacity="0.6"/>
  <ellipse cx="88" cy="70" rx="10" ry="8" fill="#6cb350" opacity="0.6"/>
  <path d="M 35 48 Q 42 42 50 47" stroke="#2d4d1a" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M 70 47 Q 78 42 85 48" stroke="#2d4d1a" stroke-width="4" fill="none" stroke-linecap="round"/>
  <circle cx="44" cy="58" r="6" fill="white"/>
  <circle cx="76" cy="58" r="6" fill="white"/>
  <circle cx="45" cy="59" r="3" fill="#2d2d2d"/>
  <circle cx="75" cy="59" r="3" fill="#2d2d2d"/>
  <ellipse cx="60" cy="72" rx="8" ry="6" fill="#4a7c2e"/>
  <path d="M 45 85 Q 60 95 75 85" stroke="#2d4d1a" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M 56 84 L 56 90 L 62 90 L 62 84 Z" fill="white" stroke="#2d4d1a" stroke-width="1"/>
  <path d="M 38 30 L 44 14 L 52 26 L 60 10 L 68 26 L 76 14 L 82 30 Z" fill="#d4af37" stroke="#a37e1f" stroke-width="2"/>
  <circle cx="60" cy="10" r="4" fill="#f5d76e"/>
</svg>
"""

# Paleta de colores del reino
COLORS = {
    "bg_dark":      "#0e1a0a",
    "bg_panel":     "#142410",
    "bg_field":     "#16240f",
    "border":       "#3a5c2e",
    "gold":         "#d4af37",
    "gold_light":   "#f5d76e",
    "text_light":   "#e8f5d8",
    "text_muted":   "#8aa07a",
    "gradient":     ["#1f3d12", "#3a5c1f", "#1a2e10"],
    "success":      "#2a9d8f",
    "error":        "#e63946",
}