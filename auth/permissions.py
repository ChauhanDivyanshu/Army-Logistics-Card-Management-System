# auth/permissions.py
# 🛡️ PERMISSIONS MANAGER - Role-based access control
# Updated to use Session getter methods

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import ROLE_PERMISSIONS, ROLES
from auth.session import Session


# ═══════════════════════════════════════════════════════════
# MODULE → DISPLAY NAME MAPPING
# ═══════════════════════════════════════════════════════════

MODULE_NAMES = {
    "warehouse_app":    "🏭 Warehouse Management",
    "container_app":    "📦 Container Management",
    "box_app":          "🗃 Box / Item Management",
    "soldier_app":      "🪖 Soldier Management",
    "gate_app":         "🎯 Gate Verification",
    "unit_app":         "🏛 Unit Management",
    "conductor_app":    "🚛 Conductor Management",
    "user_management":  "👥 User Management",
    "uhf_writer_app":   "📡 UHF Tag Writer", 
    "dashboard":        "📊 System Dashboard",
}


# ═══════════════════════════════════════════════════════════
# PERMISSION CHECKS
# ═══════════════════════════════════════════════════════════

def has_permission(module_name, role=None):
    """
    Check if a role has permission to access a module.
    
    Args:
        module_name: Module key (e.g., 'warehouse_app')
        role:        Role to check (default: current Session role)
    
    Returns:
        True if allowed, False otherwise
    """
    if role is None:
        role = Session.get_role()

    if role is None:
        return False

    if role not in ROLE_PERMISSIONS:
        return False

    return module_name in ROLE_PERMISSIONS[role]


def get_allowed_modules(role=None):
    """Get list of all modules a role can access."""
    if role is None:
        role = Session.get_role()

    if role is None or role not in ROLE_PERMISSIONS:
        return []

    return ROLE_PERMISSIONS[role]


def get_denied_modules(role=None):
    """Get list of modules a role CANNOT access."""
    if role is None:
        role = Session.get_role()

    all_modules = list(MODULE_NAMES.keys())
    allowed = get_allowed_modules(role)
    return [m for m in all_modules if m not in allowed]


# ═══════════════════════════════════════════════════════════
# REQUIRE PERMISSION (Hard checks)
# ═══════════════════════════════════════════════════════════

def require_permission(module_name, parent_window=None):
    """
    Check permission and show error dialog if denied.
    Use at the start of each app.
    
    Returns:
        True if allowed, False if denied
    """
    # Check if logged in
    if not Session.is_logged_in():
        _show_error(
            "Not Logged In",
            "Please login first to access this module.",
            parent_window
        )
        return False

    # Check permission
    if not has_permission(module_name):
        current_role = Session.get_role()
        role_label = ROLES.get(current_role, {}).get("label", current_role)
        module_label = MODULE_NAMES.get(module_name, module_name)

        _show_error(
            "Access Denied",
            f"❌ Permission Denied\n\n"
            f"Module:  {module_label}\n"
            f"Your Role: {role_label}\n\n"
            f"You don't have permission to access this module.\n"
            f"Contact your administrator.",
            parent_window
        )
        return False

    return True


def require_role(allowed_roles, parent_window=None):
    """
    Check if current user has one of the specified roles.
    
    Args:
        allowed_roles: List of role names, e.g., ['ADMIN', 'GATE']
    
    Returns:
        True if user has allowed role, False otherwise
    """
    if not Session.is_logged_in():
        _show_error(
            "Not Logged In",
            "Please login first.",
            parent_window
        )
        return False

    current_role = Session.get_role()
    if current_role not in allowed_roles:
        roles_str = ", ".join(allowed_roles)
        _show_error(
            "Access Denied",
            f"❌ This feature requires one of these roles:\n\n"
            f"{roles_str}\n\n"
            f"Your role: {current_role}",
            parent_window
        )
        return False

    return True


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _show_error(title, message, parent=None):
    """Show error message box."""
    try:
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=parent)
    except Exception:
        print(f"❌ {title}: {message}")


def get_module_label(module_name):
    """Get pretty display name for a module."""
    return MODULE_NAMES.get(module_name, module_name)


# ═══════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  PERMISSIONS MANAGER - TEST MODE")
    print("=" * 60)

    test_roles = ["ADMIN", "GATE", "UNIT", "WAREHOUSE"]

    for role in test_roles:
        print(f"\n🎭 ROLE: {role}")
        print("─" * 50)

        allowed = get_allowed_modules(role)
        denied  = get_denied_modules(role)

        print(f"  ✅ ALLOWED ({len(allowed)} modules):")
        for m in allowed:
            print(f"     • {MODULE_NAMES.get(m, m)}")

        print(f"  ❌ DENIED ({len(denied)} modules):")
        for m in denied:
            print(f"     • {MODULE_NAMES.get(m, m)}")

    print("\n" + "=" * 60)
    print("  PERMISSION CHECKS")
    print("=" * 60)

    test_cases = [
        ("ADMIN",     "warehouse_app"),
        ("GATE",      "warehouse_app"),
        ("GATE",      "gate_app"),
        ("UNIT",      "soldier_app"),
        ("UNIT",      "gate_app"),
        ("WAREHOUSE", "container_app"),
        ("WAREHOUSE", "soldier_app"),
    ]

    for role, module in test_cases:
        result = has_permission(module, role)
        icon = "✅" if result else "❌"
        print(f"  {icon} {role:10} → {module:18} = {result}")

    print("\n" + "=" * 60)
    print("  ✅ PERMISSION TESTS COMPLETED")
    print("=" * 60)