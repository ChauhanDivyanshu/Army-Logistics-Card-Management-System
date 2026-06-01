# auth/login_window.py
# 🔐 LOGIN WINDOW - Professional centered card design
# Returns True on successful login, False otherwise

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import COLORS, FONTS, ROLES
from database.db_helper import DatabaseHelper
from auth.session import Session
from auth.auth_helper import hash_password


# ─── Constants for form sizing ───
FORM_WIDTH = 420   # Fixed width for login card
FORM_PADDING = 35  # Internal padding


class LoginWindow:
    """Professional full-screen login window with centered card."""

    def __init__(self, root):
        self.root = root
        self.db = DatabaseHelper()
        self.login_success = False

        # Window setup - FULL SCREEN
        self.root.title("🎖 Army Logistics — Secure Login")
        self.root.configure(bg=COLORS["login_bg"])
        self.root.geometry("1280x800")
        self.root.minsize(1000, 650)

        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass

        self._build_ui()

        self.username_entry.focus()
        self.root.bind("<Return>", lambda e: self._handle_login())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    # ═══════════════════════════════════════════════════════
    # UI BUILDING
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        """Build login screen with 50-50 split."""
        main = tk.Frame(self.root, bg=COLORS["login_bg"])
        main.pack(fill=tk.BOTH, expand=True)

        # 50-50 grid split
        main.columnconfigure(0, weight=1, uniform="side")
        main.columnconfigure(1, weight=1, uniform="side")
        main.rowconfigure(0, weight=1)

        # LEFT: Branding (green)
        left = tk.Frame(main, bg=COLORS["login_bg"])
        left.grid(row=0, column=0, sticky="nsew")
        self._build_left_panel(left)

        # RIGHT: Login (white with card)
        right = tk.Frame(main, bg=COLORS["white"])
        right.grid(row=0, column=1, sticky="nsew")
        self._build_right_panel(right)

    # ═══════════════════════════════════════════════════════
    # LEFT PANEL (Branding)
    # ═══════════════════════════════════════════════════════

    def _build_left_panel(self, parent):
        """Build branding panel with vertically centered content."""
        # Center container
        center = tk.Frame(parent, bg=COLORS["login_bg"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        tk.Label(center, text="🎖",
                 font=("Segoe UI Emoji", 90),
                 bg=COLORS["login_bg"],
                 fg=COLORS["accent"]).pack(pady=(0, 20))

        # Title
        tk.Label(center, text="ARMY LOGISTICS",
                 font=("Segoe UI", 28, "bold"),
                 bg=COLORS["login_bg"],
                 fg="white").pack()

        tk.Label(center, text="SYSTEM",
                 font=("Segoe UI", 28, "bold"),
                 bg=COLORS["login_bg"],
                 fg=COLORS["accent"]).pack()

        # Divider line
        tk.Frame(center, bg=COLORS["accent"], height=3,
                 width=130).pack(pady=22)

        # Tagline
        tk.Label(center, text="Secure • Reliable • Efficient",
                 font=("Segoe UI", 11, "italic"),
                 bg=COLORS["login_bg"],
                 fg="#C8E6C9").pack()

        # Features
        tk.Label(center,
                 text="MIFARE Classic 1K\nPostgreSQL Database\nCargo Management",
                 font=("Segoe UI", 10),
                 bg=COLORS["login_bg"],
                 fg="#A5D6A7",
                 justify=tk.CENTER).pack(pady=(20, 0))

        # Copyright at bottom
        tk.Label(parent,
                 text="© 2025 Indian Army",
                 font=("Segoe UI", 9),
                 bg=COLORS["login_bg"],
                 fg="#81C784").pack(side=tk.BOTTOM, pady=20)

    # ═══════════════════════════════════════════════════════
    # RIGHT PANEL (Login Card)
    # ═══════════════════════════════════════════════════════

        # ═══════════════════════════════════════════════════════
    # RIGHT PANEL (Login Card)
    # ═══════════════════════════════════════════════════════

    def _build_right_panel(self, parent):
        """Build right panel with centered login card."""
        # Use grid for perfect centering
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=0)  # Card column
        parent.columnconfigure(2, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=0)     # Card row
        parent.rowconfigure(2, weight=1)

        # Card sits in middle cell (1, 1)
        card = tk.Frame(parent, bg=COLORS["white"], width=FORM_WIDTH)
        card.grid(row=1, column=1, sticky="")

        # Build content
        self._build_form_content(card)

    def _build_form_content(self, parent):
        """Build the actual form fields inside the card."""
        # ─── Header ───
        tk.Label(parent, text="🔐",
                 font=("Segoe UI Emoji", 36),
                 bg=COLORS["white"],
                 fg=COLORS["primary"]).pack(pady=(0, 8))

        tk.Label(parent, text="Welcome Back",
                 font=("Segoe UI", 24, "bold"),
                 bg=COLORS["white"],
                 fg=COLORS["primary"]).pack()

        tk.Label(parent,
                 text="Please sign in to access your account",
                 font=("Segoe UI", 10),
                 bg=COLORS["white"],
                 fg=COLORS["muted"]).pack(pady=(4, 25))

        # ─── Username Field ───
        tk.Label(parent, text="👤  USERNAME",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["white"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 5))

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            parent,
            textvariable=self.username_var,
            font=("Segoe UI", 12),
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            relief=tk.SOLID,
            bd=1,
            highlightthickness=2,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["input_focus"],
        )
        self.username_entry.pack(fill=tk.X, ipady=8)

        # ─── Password Field ───
        tk.Label(parent, text="🔑  PASSWORD",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["white"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(15, 5))

        pwd_frame = tk.Frame(parent, bg=COLORS["input_bg"],
                              relief=tk.SOLID, bd=1,
                              highlightthickness=2,
                              highlightbackground=COLORS["input_border"],
                              highlightcolor=COLORS["input_focus"])
        pwd_frame.pack(fill=tk.X)

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            pwd_frame,
            textvariable=self.password_var,
            font=("Segoe UI", 12),
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            show="●"
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.X,
                                  expand=True, ipady=8, padx=4)

        # Show/Hide password
        self.show_pwd = False
        self.toggle_btn = tk.Button(
            pwd_frame, text="👁",
            font=("Segoe UI Emoji", 12),
            bg=COLORS["input_bg"],
            fg=COLORS["muted"],
            relief=tk.FLAT, bd=0,
            cursor="hand2",
            command=self._toggle_password
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=8)

        # ─── Status Message ───
        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(
            parent, textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["white"],
            fg=COLORS["danger"],
            wraplength=FORM_WIDTH - 20
        )
        self.status_lbl.pack(anchor="w", pady=(10, 0))

        # ─── Sign In Button ───
        self.login_btn = tk.Button(
            parent, text="🔓  SIGN IN",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT, bd=0,
            pady=12,
            cursor="hand2",
            activebackground=COLORS["hover_primary"],
            activeforeground="white",
            command=self._handle_login
        )
        self.login_btn.pack(fill=tk.X, pady=(18, 0))

        # Hover effect
        self.login_btn.bind(
            "<Enter>",
            lambda e: self.login_btn.configure(bg=COLORS["hover_primary"])
        )
        self.login_btn.bind(
            "<Leave>",
            lambda e: self.login_btn.configure(bg=COLORS["primary"])
        )

        # ─── Divider ───
        div_frame = tk.Frame(parent, bg=COLORS["white"])
        div_frame.pack(fill=tk.X, pady=(20, 10))

        tk.Frame(div_frame, bg=COLORS["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, pady=8)
        tk.Label(div_frame, text="  DEMO ACCOUNTS  ",
                 font=("Segoe UI", 8, "bold"),
                 bg=COLORS["white"],
                 fg=COLORS["muted"]).pack(side=tk.LEFT)
        tk.Frame(div_frame, bg=COLORS["border"], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, pady=8)

        # ─── Demo Credentials ───
        hints_frame = tk.Frame(parent, bg=COLORS["row_alt"],
                                relief=tk.SOLID, bd=1,
                                highlightthickness=1,
                                highlightbackground=COLORS["border"])
        hints_frame.pack(fill=tk.X, pady=(0, 0))

        hints = [
            ("👑", "Admin",     "admin",      "admin123",    COLORS["role_admin"]),
            ("🚪", "Gate",      "gate1",      "password123", COLORS["role_gate"]),
            ("🏛", "Unit",      "unit1",      "password123", COLORS["role_unit"]),
            ("🏭", "Warehouse", "warehouse1", "password123", COLORS["role_warehouse"]),
        ]

        for icon, role, user, pwd, color in hints:
            row = tk.Frame(hints_frame, bg=COLORS["row_alt"])
            row.pack(fill=tk.X, padx=10, pady=4)

            # Icon
            tk.Label(row, text=icon,
                     font=("Segoe UI Emoji", 11),
                     bg=COLORS["row_alt"]).pack(side=tk.LEFT, padx=(0, 6))

            # Role name
            tk.Label(row, text=role,
                     font=("Segoe UI", 9, "bold"),
                     bg=COLORS["row_alt"],
                     fg=color,
                     width=10, anchor="w").pack(side=tk.LEFT)

            # Credentials
            tk.Label(row, text=f"{user} / {pwd}",
                     font=("Consolas", 8),
                     bg=COLORS["row_alt"],
                     fg=COLORS["muted"]).pack(side=tk.LEFT)

            # Use button
            tk.Button(row, text="Use",
                       font=("Segoe UI", 7, "bold"),
                       bg=color, fg="white",
                       relief=tk.FLAT, bd=0,
                       padx=10, pady=1,
                       cursor="hand2",
                       command=lambda u=user, p=pwd: self._quick_fill(u, p)
                       ).pack(side=tk.RIGHT)

        # ─── Help Text ───
        tk.Label(parent,
                 text="ℹ  Press Enter to sign in  •  Esc to exit",
                 font=("Segoe UI", 8),
                 bg=COLORS["white"],
                 fg=COLORS["muted"]).pack(pady=(15, 0))

    # ═══════════════════════════════════════════════════════
    # LOGIN LOGIC
    # ═══════════════════════════════════════════════════════

    def _toggle_password(self):
        """Show/hide password."""
        self.show_pwd = not self.show_pwd
        if self.show_pwd:
            self.password_entry.configure(show="")
            self.toggle_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="●")
            self.toggle_btn.configure(text="👁")

    def _quick_fill(self, username, password):
        """Quick fill credentials."""
        self.username_var.set(username)
        self.password_var.set(password)
        self.password_entry.focus()

    def _set_status(self, message, is_error=True):
        """Show status message."""
        color = COLORS["danger"] if is_error else COLORS["success"]
        self.status_lbl.configure(fg=color)
        self.status_var.set(message)

    def _handle_login(self):
        """Process login attempt."""
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username:
            self._set_status("⚠  Please enter username")
            self.username_entry.focus()
            return

        if not password:
            self._set_status("⚠  Please enter password")
            self.password_entry.focus()
            return

        self.login_btn.configure(state=tk.DISABLED,
                                  text="🔄  Authenticating...")
        self.root.update()

        db_ok, db_msg = self.db.test_connection()
        if not db_ok:
            self._set_status(f"❌  Database error: {db_msg[:40]}")
            self.login_btn.configure(state=tk.NORMAL, text="🔓  SIGN IN")
            return

        user_check = self.db.get_user_by_username(username)
        if not user_check:
            self._set_status("❌  Invalid username or password")
            self.db.log_login_attempt(None, username, False, "User not found")
            self.login_btn.configure(state=tk.NORMAL, text="🔓  SIGN IN")
            return

        if user_check["status"] == "LOCKED":
            self._set_status("🔒  Account locked. Contact administrator.")
            self.db.log_login_attempt(
                user_check["user_id"], username, False, "Account locked"
            )
            self.login_btn.configure(state=tk.NORMAL, text="🔓  SIGN IN")
            return

        if user_check["status"] == "INACTIVE":
            self._set_status("⚠  Account inactive. Contact administrator.")
            self.login_btn.configure(state=tk.NORMAL, text="🔓  SIGN IN")
            return

        password_hash = hash_password(password)
        user_data = self.db.authenticate_user(username, password_hash)

        if user_data:
            self._set_status("✓  Login successful! Loading...", is_error=False)
            self.root.update()

            self.db.update_last_login(user_data["user_id"])
            self.db.log_login_attempt(user_data["user_id"], username, True)

            Session.login(user_data)
            self.login_success = True

            self.root.after(500, self.root.destroy)
        else:
            self.db.increment_failed_attempts(username)
            self.db.log_login_attempt(
                user_check["user_id"], username, False, "Wrong password"
            )

            remaining = 5 - (user_check["failed_attempts"] + 1)
            if remaining > 0:
                self._set_status(
                    f"❌  Invalid password. {remaining} attempts remaining."
                )
            else:
                self._set_status("🔒  Account locked due to multiple failures.")

            self.password_var.set("")
            self.password_entry.focus()
            self.login_btn.configure(state=tk.NORMAL, text="🔓  SIGN IN")


# ═══════════════════════════════════════════════════════════
#  PUBLIC FUNCTION
# ═══════════════════════════════════════════════════════════

def show_login():
    """Show login window. Returns True if successful."""
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
    return app.login_success


# ═══════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  LOGIN WINDOW - TEST MODE")
    print("=" * 60)

    success = show_login()

    print("\n" + "=" * 60)
    if success:
        print("  ✅ LOGIN SUCCESSFUL")
        print("=" * 60)
        print(f"  👤 User:       {Session.get_full_name()}")
        print(f"  🆔 Username:   {Session.get_username()}")
        print(f"  🎭 Role:       {Session.get_role()}")
        print(f"  📧 Email:      {Session.get_email()}")
        print(f"  🕐 Login Time: {Session.get_login_time()}")
        print(f"  ℹ️  Display:    {Session.get_display_info()}")
        print("=" * 60)
    else:
        print("  ❌ LOGIN CANCELLED OR FAILED")
        print("=" * 60)