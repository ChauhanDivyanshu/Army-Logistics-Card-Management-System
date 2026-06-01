# shared/theme.py
# 🎖️ INDIAN ARMY - Clean Professional Theme

COLORS = {
    # ─── BACKGROUNDS (Clean & Simple) ───
    "bg":           "#F5F5F5",    # Light gray background
    "bg_card":      "#FFFFFF",    # Pure white cards
    "bg_dark":      "#1B5E20",    # Army green for headers
    "bg_panel":     "#FAFAFA",    # Very light gray for panels
    
    # ─── PRIMARY COLOR (Army Green) ───
    "primary":      "#1B5E20",    # Main army green
    "primary_dark": "#0D3811",    # Darker green
    "primary_light":"#E8F5E9",    # Very light green tint
    
    # ─── ACCENT (Gold - sparingly used) ───
    "accent":       "#FFC107",    # Army gold (only in header)
    
    # ─── STATUS COLORS ───
    "success":      "#2E7D32",    # Green
    "danger":       "#C62828",    # Red
    "warning":      "#F57C00",    # Orange
    "info":         "#1565C0",    # Blue
    
    # ─── TEXT ───
    "text":         "#212121",    # Black text
    "text_white":   "#FFFFFF",    # White text
    "text_muted":   "#757575",    # Gray text
    "text_light":   "#9E9E9E",    # Light gray
    
    # ─── BORDERS & LINES ───
    "border":       "#E0E0E0",    # Light gray border
    "border_dark":  "#1B5E20",    # Army green border (accents)
    
    # ─── INPUTS ───
    "input_bg":     "#FFFFFF",
    "input_border": "#BDBDBD",
    "input_focus":  "#1B5E20",
    
    # ─── COMPATIBILITY (for existing code) ───
    "white":        "#FFFFFF",
    "dark":         "#1B5E20",
    "muted":        "#757575",
    "row_alt":      "#F5F5F5",
    "darker":       "#0A0A0A",
    "secondary":    "#2E7D32",
    "hover_primary":"#2E7D32",
    "hover_danger": "#B71C1C",
    "hover_info":   "#0D47A1",
    "login_bg":     "#1B5E20",
    "login_card":   "#FFFFFF",
    "login_overlay":"#0D3811",
    
    # ─── ROLE COLORS (Simple) ───
    "role_admin":     "#1B5E20",
    "role_gate":      "#1B5E20",
    "role_unit":      "#1B5E20",
    "role_warehouse": "#1B5E20",
    
    # ─── STATUS ───
    "status_active":   "#2E7D32",
    "status_inactive": "#9E9E9E",
    "status_locked":   "#C62828",
}


FONTS = {
    "header":      ("Segoe UI", 16, "bold"),
    "title":       ("Segoe UI", 12, "bold"),
    "subtitle":    ("Segoe UI", 10),
    "body":        ("Segoe UI", 10),
    "body_bold":   ("Segoe UI", 10, "bold"),
    "small":       ("Segoe UI", 9),
    "tiny":        ("Segoe UI", 8),
    "button":      ("Segoe UI", 11, "bold"),
    "mono":        ("Consolas", 9),
    
    # For compatibility
    "login_title":    ("Segoe UI", 22, "bold"),
    "login_subtitle": ("Segoe UI", 10),
    "login_label":    ("Segoe UI", 10, "bold"),
    "login_input":    ("Segoe UI", 11),
    "login_button":   ("Segoe UI", 11, "bold"),
    "role_badge":     ("Segoe UI", 9, "bold"),
    "user_info":      ("Segoe UI", 9),
}


# ═══════════════════════════════════════════════════════════
# ROLES (Simple)
# ═══════════════════════════════════════════════════════════

ROLES = {
    "ADMIN": {
        "label":  "👑 Administrator",
        "color":  COLORS["primary"],
        "icon":   "👑",
        "desc":   "Full access",
    },
    "GATE": {
        "label":  "🎖 Gate Officer",
        "color":  COLORS["primary"],
        "icon":   "🎖",
        "desc":   "Gate verification",
    },
    "UNIT": {
        "label":  "🪖 Unit Manager",
        "color":  COLORS["primary"],
        "icon":   "🪖",
        "desc":   "Trip management",
    },
    "WAREHOUSE": {
        "label":  "📦 Warehouse Manager",
        "color":  COLORS["primary"],
        "icon":   "📦",
        "desc":   "Inventory & loading",
    },
}


ROLE_PERMISSIONS = {
    "ADMIN": [
        "warehouse_app", "container_app", "box_app",
        "trip_card_app", "gate_app", "exit_gate_app",
        "unit_app", "user_management",
        "uhf_writer_app", "reports_app",
        "dashboard"
    ],
    "GATE": [
        "gate_app", "exit_gate_app",
        "dashboard"
    ],
    "UNIT": [
        "trip_card_app", "unit_app",
        "dashboard"
    ],
    "WAREHOUSE": [
        "warehouse_app", "container_app", "box_app",
        "uhf_writer_app",
        "dashboard"
    ],
}


def has_permission(role, module):
    if role not in ROLE_PERMISSIONS:
        return False
    return module in ROLE_PERMISSIONS[role]


def get_role_info(role):
    return ROLES.get(role, {
        "label": "Unknown",
        "color": COLORS["muted"],
        "icon":  "❓",
        "desc":  "No role",
    })