# main.py
# 🎖 ARMY LOGISTICS - MAIN LAUNCHER (Role-Based)
# Now with authentication & role-based access control

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from database.db_helper import DatabaseHelper
from shared.theme import COLORS, FONTS, ROLES
from auth.session import Session
from auth.permissions import has_permission, get_allowed_modules
from auth.login_window import show_login


class MainLauncher:

    def __init__(self, root):
        self.root = root
        self.root.title(
            f"🎖 Army Logistics — {Session.get_full_name()} "
            f"({Session.get_role()})"
        )
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.db_connected = False

        self._build_ui()
        self._check_db_connection()
        self._update_time()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # IMPORTANT: Footer first to reserve bottom space
        self._build_footer()
        self._build_header()
        self._build_status_bar()
        self._build_main_content()

    # ═══════════════════════════════════════════════════════
    # HEADER (with user info + logout)
    # ═══════════════════════════════════════════════════════

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=80)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # ─── LEFT: Logo + Title ───
        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, fill=tk.Y)

        logo_row = tk.Frame(left, bg=COLORS["primary"])
        logo_row.pack(expand=True)

        tk.Label(logo_row, text="🎖",
                 font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 14))

        title_box = tk.Frame(logo_row, bg=COLORS["primary"])
        title_box.pack(side=tk.LEFT)

        tk.Label(title_box, text="ARMY LOGISTICS SYSTEM",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")

        tk.Label(title_box,
                 text="MIFARE Classic 1K • PostgreSQL • Cargo Management",
                 font=("Segoe UI", 8),
                 bg=COLORS["primary"], fg="#C8E6C9").pack(anchor="w")

        # ─── RIGHT: User Info + Logout ───
        right = tk.Frame(hdr, bg=COLORS["primary"])
        right.pack(side=tk.RIGHT, padx=20, fill=tk.Y)

        # Time
        self.time_var = tk.StringVar()
        tk.Label(right, textvariable=self.time_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(anchor="e", pady=(8, 4))

        # User info row
        user_row = tk.Frame(right, bg=COLORS["primary"])
        user_row.pack(anchor="e")

        # Role badge
        role_info = ROLES.get(Session.get_role(), {})
        role_color = role_info.get("color", COLORS["muted"])
        role_icon = role_info.get("icon", "👤")

        badge = tk.Frame(user_row, bg=role_color)
        badge.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(badge,
                 text=f"  {role_icon} {Session.get_role()}  ",
                 font=("Segoe UI", 9, "bold"),
                 bg=role_color, fg="white").pack(pady=4)

        # Username
        tk.Label(user_row,
                 text=f"👤 {Session.get_full_name()}",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"],
                 fg="white").pack(side=tk.LEFT, padx=(0, 12))

        # Logout button
        logout_btn = tk.Button(
            user_row, text="🚪 Logout",
            command=self._handle_logout,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="white",
            relief=tk.FLAT, padx=14, pady=4,
            cursor="hand2",
            activebackground=COLORS["hover_danger"],
            activeforeground="white"
        )
        logout_btn.pack(side=tk.LEFT)

    def _update_time(self):
        now = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        self.time_var.set(f"🕐  {now}")
        self.root.after(1000, self._update_time)

    # ═══════════════════════════════════════════════════════
    # STATUS BAR
    # ═══════════════════════════════════════════════════════

    def _build_status_bar(self):
        self.status_frame = tk.Frame(
            self.root, bg=COLORS["muted"], height=28
        )
        self.status_frame.pack(fill=tk.X)
        self.status_frame.pack_propagate(False)

        self.status_dot = tk.Label(
            self.status_frame, text="●",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["muted"], fg="white"
        )
        self.status_dot.pack(side=tk.LEFT, padx=(14, 6))

        self.status_var = tk.StringVar(value="Checking database...")
        self.status_lbl = tk.Label(
            self.status_frame, textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["muted"], fg="white"
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.stats_var = tk.StringVar(value="Loading...")
        self.stats_lbl = tk.Label(
            self.status_frame, textvariable=self.stats_var,
            font=("Segoe UI", 9),
            bg=COLORS["muted"], fg="white"
        )
        self.stats_lbl.pack(side=tk.RIGHT, padx=14)

    # ═══════════════════════════════════════════════════════
    # MAIN CONTENT (Role-based cards)
    # ═══════════════════════════════════════════════════════

    def _build_main_content(self):
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Title row
        title_row = tk.Frame(main, bg=COLORS["bg"])
        title_row.pack(fill=tk.X, pady=(0, 10))

        # Role-specific welcome
        role_info = ROLES.get(Session.get_role(), {})
        role_label = role_info.get("label", "User")

        tk.Label(title_row,
                 text=f"📋  AVAILABLE MODULES — {role_label}",
                 font=("Segoe UI", 12, "bold"),
                 bg=COLORS["bg"],
                 fg=COLORS["primary"]).pack(side=tk.LEFT)

        tk.Button(title_row, text="🔄 Refresh",
                   command=self._check_db_connection,
                   font=("Segoe UI", 9, "bold"),
                   bg=COLORS["info"], fg="white",
                   relief=tk.FLAT, padx=14, pady=5,
                   cursor="hand2").pack(side=tk.RIGHT)

        tk.Frame(main, bg=COLORS["border"], height=1).pack(
            fill=tk.X, pady=(0, 12))

        # Cards grid
        cards_wrap = tk.Frame(main, bg=COLORS["bg"])
        cards_wrap.pack(fill=tk.BOTH, expand=True)

        # ─── ALL MODULES (filtered by role) ───
        all_modules = [
            {
                "key": "warehouse_app",
                "icon": "🏭", "title": "WAREHOUSE OPS",
                "subtitle": "UHF Bulk Scanner",
                "stat_key": "total_warehouses",
                "stat_label": "Warehouses",
                "script": "apps/warehouse_app.py",
                "color": COLORS["warning"],  # Orange
            },
            {
                "key": "container_app",
                "icon": "📦", "title": "CONTAINER",
                "subtitle": "Management",
                "stat_key": "total_containers",
                "stat_label": "Containers",
                "script": "apps/container_app.py",
                "color": COLORS["secondary"],
            },
            {
                "key": "box_app",
                "icon": "🗃", "title": "BOX / ITEM",
                "subtitle": "Management",
                "stat_key": "total_boxes",
                "stat_label": "Boxes",
                "script": "apps/box_app.py",
                "color": COLORS["warning"],
            },
            {
                "key": "trip_card_app",
                "icon": "🚛", "title": "TRIP CARD",
                "subtitle": "Trip Card Manager",
                "stat_key": "total_soldiers",
                "stat_label": "Trips",
                "script": "apps/trip_card_app.py",   # ← New file
                "color": "#7B1FA2",  # Purple
            },
            {
                "key": "gate_app",
                "icon": "🎯", "title": "GATE",
                "subtitle": "VERIFICATION",
                "stat_key": "pending_requests",
                "stat_label": "Pending",
                "script": "apps/gate_app.py",
                "color": COLORS["primary"],
                "featured": True
            },
            {
                "key": "uhf_writer_app",
                "icon": "📡", "title": "UHF WRITER",
                "subtitle": "Tag Management",
                "stat_key": "total_boxes",
                "stat_label": "Tagged Boxes",
                "script": "apps/uhf_writer_app.py",
                "color": "#7B1FA2",  # Purple
            },
            {
                "key": "dashboard",
                "icon": "📊", "title": "DASHBOARD",
                "subtitle": "System Stats",
                "stat_key": "completed_requests",
                "stat_label": "Completed",
                "script": "apps/dashboard_app.py",
                "color": COLORS["muted"],
            }
        ]

        # ─── FILTER: Only show allowed modules ───
        allowed = get_allowed_modules()
        modules = [m for m in all_modules if m["key"] in allowed]

        # ─── Calculate grid layout ───
        num_modules = len(modules)
        cols = 3
        rows = (num_modules + cols - 1) // cols

        for i in range(cols):
            cards_wrap.columnconfigure(i, weight=1, uniform="col")
        for i in range(rows):
            cards_wrap.rowconfigure(i, weight=1, uniform="row")

        # ─── Place cards in grid ───
        self.stat_vars = {}
        for idx, mod in enumerate(modules):
            mod["row"] = idx // cols
            mod["col"] = idx % cols
            self._build_module_card(cards_wrap, mod)

        # If no modules available
        if not modules:
            tk.Label(cards_wrap,
                     text="❌ No modules available for your role",
                     font=("Segoe UI", 14, "bold"),
                     bg=COLORS["bg"],
                     fg=COLORS["danger"]).pack(expand=True, pady=100)

    def _build_module_card(self, parent, mod):
        """Build a compact module card."""
        is_featured = mod.get("featured", False)
        border_color = COLORS["accent"] if is_featured else COLORS["border"]
        border_width = 3 if is_featured else 1

        card = tk.Frame(parent, bg=COLORS["white"],
                        relief=tk.SOLID, bd=border_width,
                        highlightbackground=border_color,
                        highlightthickness=border_width)
        card.grid(row=mod["row"], column=mod["col"],
                  sticky="nsew", padx=8, pady=8)

        # Top color strip
        tk.Frame(card, bg=mod["color"], height=4).pack(fill=tk.X)

        # Featured badge
        if is_featured:
            badge = tk.Frame(card, bg=COLORS["accent"], height=20)
            badge.pack(fill=tk.X)
            badge.pack_propagate(False)
            tk.Label(badge, text="⭐ RECOMMENDED",
                     font=("Segoe UI", 7, "bold"),
                     bg=COLORS["accent"],
                     fg=COLORS["dark"]).pack(pady=2)

        # ─── Launch Button (bottom) ───
        if mod.get("builtin"):
            btn_text = "📊  VIEW DASHBOARD"
            cmd = self._show_dashboard
        else:
            btn_text = f"▶  LAUNCH {mod['title']}"
            cmd = lambda s=mod["script"]: self._launch(s)

        btn = tk.Button(card, text=btn_text,
                         command=cmd,
                         font=("Segoe UI", 10, "bold"),
                         bg=mod["color"], fg="white",
                         relief=tk.FLAT, bd=0,
                         pady=12, cursor="hand2",
                         activebackground=COLORS["dark"],
                         activeforeground="white")
        btn.pack(side=tk.BOTTOM, fill=tk.X)

        def on_enter(_, b=btn):
            b.configure(bg=COLORS["dark"])

        def on_leave(_, b=btn, c=mod["color"]):
            b.configure(bg=c)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        # ─── Content (top) ───
        inner = tk.Frame(card, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        tk.Label(inner, text=mod["icon"],
                 font=("Segoe UI Emoji", 30),
                 bg=COLORS["white"]).pack(pady=(4, 6))

        tk.Label(inner, text=mod["title"],
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["white"],
                 fg=mod["color"]).pack()

        tk.Label(inner, text=mod["subtitle"],
                 font=("Segoe UI", 8),
                 bg=COLORS["white"],
                 fg=COLORS["muted"]).pack(pady=(0, 6))

        tk.Frame(inner, bg=mod["color"], height=2,
                 width=40).pack(pady=(0, 8))

        # Stats
        stat_box = tk.Frame(inner, bg="#F5F5F5", relief=tk.FLAT, bd=0)
        stat_box.pack(fill=tk.X, pady=(4, 0))

        stat_var = tk.StringVar(value="—")
        self.stat_vars[mod["stat_key"]] = stat_var

        tk.Label(stat_box, textvariable=stat_var,
                 font=("Segoe UI", 18, "bold"),
                 bg="#F5F5F5",
                 fg=mod["color"]).pack(pady=(6, 0))

        tk.Label(stat_box, text=mod["stat_label"],
                 font=("Segoe UI", 8),
                 bg="#F5F5F5",
                 fg=COLORS["muted"]).pack(pady=(0, 6))

    # ═══════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        # Left: Copyright
        tk.Label(footer,
                 text="© 2025 Indian Army  |  Army Logistics Card Management System",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg="#B0BEC5").pack(side=tk.LEFT, padx=16, pady=6)

        # Right: System info
        tk.Label(footer,
                 text=f"Logged in as: {Session.get_username()}  |  "
                      f"DB: PostgreSQL  |  Card: MIFARE 1K",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg="#B0BEC5").pack(side=tk.RIGHT, padx=16, pady=6)

    # ═══════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _check_db_connection(self):
        success, msg = self.db.test_connection()

        if success:
            self.db_connected = True
            self._set_status("✓ Database Connected | System Ready",
                              COLORS["success"])
            self._load_stats()
        else:
            self.db_connected = False
            self._set_status(
                "✗ Database Connection Failed", COLORS["danger"])
            self.stats_var.set("Check db_config.py")

    def _load_stats(self):
        stats = self.db.get_system_stats()
        if not stats:
            return

        for key in self.stat_vars:
            if key in stats:
                self.stat_vars[key].set(str(stats[key]))

        self.stats_var.set(
            f"📊 {stats['total_warehouses']} WH | "
            f"{stats['total_containers']} Cont | "
            f"{stats['total_boxes']} Box | "
            f"{stats['total_soldiers']} Sold | "
            f"{stats['pending_requests']} Pending"
        )

    def _set_status(self, text, color):
        self.status_var.set(text)
        for w in [self.status_frame, self.status_dot,
                  self.status_lbl, self.stats_lbl]:
            try:
                w.configure(bg=color)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════
    # MODULE LAUNCHING
    # ═══════════════════════════════════════════════════════

    def _launch(self, script):
        if not self.db_connected:
            messagebox.showerror(
                "Database Error",
                "Cannot launch — Database not connected!"
            )
            return

        try:
            script_path = os.path.join(BASE, script)

            if not os.path.isfile(script_path):
                messagebox.showwarning(
                    "Coming Soon",
                    f"This module is not yet implemented:\n\n{script}\n\n"
                    f"It will be added in the next update."
                )
                return

            subprocess.Popen([sys.executable, script_path])
            self.root.after(2000, self._load_stats)

        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch:\n{script}\n\nError: {e}"
            )

    # ═══════════════════════════════════════════════════════
    # LOGOUT
    # ═══════════════════════════════════════════════════════

    def _handle_logout(self):
        """Handle logout - confirm and restart app."""
        confirm = messagebox.askyesno(
            "Logout Confirmation",
            f"Are you sure you want to logout?\n\n"
            f"User: {Session.get_full_name()}\n"
            f"Role: {Session.get_role()}"
        )

        if confirm:
            Session.logout()
            self.root.destroy()
            # Restart app (back to login)
            python = sys.executable
            os.execl(python, python, *sys.argv)

    def _on_close(self):
        """Handle window close."""
        confirm = messagebox.askyesno(
            "Exit Application",
            "Are you sure you want to exit?"
        )
        if confirm:
            Session.logout()
            self.root.destroy()

    # ═══════════════════════════════════════════════════════
    # DASHBOARD POPUP
    # ═══════════════════════════════════════════════════════

    def _show_dashboard(self):
        popup = tk.Toplevel(self.root)
        popup.title("📊 System Dashboard")
        popup.configure(bg=COLORS["bg"])
        popup.geometry("700x600")
        popup.grab_set()

        hdr = tk.Frame(popup, bg=COLORS["primary"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  SYSTEM DASHBOARD",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["primary"], fg="white").pack(pady=18)

        body = tk.Frame(popup, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        stats = self.db.get_system_stats()

        if not stats:
            tk.Label(body, text="❌ Cannot load statistics",
                     font=("Segoe UI", 11),
                     bg=COLORS["bg"],
                     fg=COLORS["danger"]).pack(expand=True)
            return

        # Inventory section
        section1 = tk.LabelFrame(
            body, text="  📦  INVENTORY OVERVIEW  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["white"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        section1.pack(fill=tk.X, pady=(0, 10))

        s1 = tk.Frame(section1, bg=COLORS["white"])
        s1.pack(fill=tk.X, padx=14, pady=10)
        for i in range(3):
            s1.columnconfigure(i, weight=1)

        inventory_stats = [
            ("🏭", "Warehouses",  stats['total_warehouses'], COLORS["info"]),
            ("📦", "Containers",  stats['total_containers'], COLORS["secondary"]),
            ("🗃", "Boxes",       stats['total_boxes'],      COLORS["warning"]),
        ]

        for i, (icon, label, value, color) in enumerate(inventory_stats):
            box = tk.Frame(s1, bg="#F5F5F5")
            box.grid(row=0, column=i, sticky="ew", padx=6, pady=6)
            tk.Label(box, text=icon, font=("Segoe UI Emoji", 22),
                     bg="#F5F5F5").pack(pady=(10, 4))
            tk.Label(box, text=str(value),
                     font=("Segoe UI", 22, "bold"),
                     bg="#F5F5F5", fg=color).pack()
            tk.Label(box, text=label,
                     font=("Segoe UI", 9),
                     bg="#F5F5F5",
                     fg=COLORS["muted"]).pack(pady=(0, 10))

        # Requests section
        section2 = tk.LabelFrame(
            body, text="  🪖  SOLDIERS & REQUESTS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["white"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        section2.pack(fill=tk.X, pady=(0, 10))

        s2 = tk.Frame(section2, bg=COLORS["white"])
        s2.pack(fill=tk.X, padx=14, pady=10)
        for i in range(4):
            s2.columnconfigure(i, weight=1)

        request_stats = [
            ("🪖", "Soldiers",  stats['total_soldiers'],     COLORS["dark"]),
            ("⏳", "Pending",   stats['pending_requests'],   COLORS["warning"]),
            ("✅", "Assigned",  stats['assigned_requests'],  COLORS["info"]),
            ("✓", "Completed", stats['completed_requests'], COLORS["success"]),
        ]

        for i, (icon, label, value, color) in enumerate(request_stats):
            box = tk.Frame(s2, bg="#F5F5F5")
            box.grid(row=0, column=i, sticky="ew", padx=4, pady=6)
            tk.Label(box, text=icon, font=("Segoe UI Emoji", 18),
                     bg="#F5F5F5").pack(pady=(10, 2))
            tk.Label(box, text=str(value),
                     font=("Segoe UI", 18, "bold"),
                     bg="#F5F5F5", fg=color).pack()
            tk.Label(box, text=label,
                     font=("Segoe UI", 8),
                     bg="#F5F5F5",
                     fg=COLORS["muted"]).pack(pady=(0, 10))

        # Recent assignments
        section3 = tk.LabelFrame(
            body, text="  📋  RECENT ASSIGNMENTS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["white"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        section3.pack(fill=tk.BOTH, expand=True)

        s3 = tk.Frame(section3, bg=COLORS["white"])
        s3.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        history = self.db.get_all_assignments_history()
        recent = history[:10] if history else []

        history_text = tk.Text(s3, font=("Consolas", 9),
                                bg="white", fg=COLORS["text"],
                                relief=tk.FLAT, bd=0,
                                wrap=tk.NONE)
        history_text.pack(side=tk.LEFT, fill=tk.BOTH,
                           expand=True, padx=4, pady=4)

        sb = ttk.Scrollbar(s3, command=history_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        history_text.configure(yscrollcommand=sb.set)

        if recent:
            history_text.insert(tk.END,
                f"{'Soldier':<14} {'Item':<12} {'Qty':<8} "
                f"{'Status':<12} {'Date':<20}\n")
            history_text.insert(tk.END, "─" * 70 + "\n")
            for h in recent:
                date_str = (h['request_date'].strftime("%d/%m %H:%M")
                            if h.get('request_date') else '-')
                history_text.insert(tk.END,
                    f"{h['soldier_id']:<14} "
                    f"{h['item_name']:<12} "
                    f"{str(h['required_qty']):<8} "
                    f"{h['status']:<12} "
                    f"{date_str:<20}\n")
        else:
            history_text.insert(tk.END, "\n  No assignment history found")

        history_text.configure(state="disabled")

        tk.Button(body, text="✓  CLOSE",
                   command=popup.destroy,
                   font=("Segoe UI", 10, "bold"),
                   bg=COLORS["primary"], fg="white",
                   relief=tk.FLAT, pady=10,
                   cursor="hand2").pack(fill=tk.X, pady=(10, 0))


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT (Login → Launcher)
# ═══════════════════════════════════════════════════════════

def main():
    """Main entry point - shows login first, then launcher."""
    
    # ─── STEP 1: Show login window ───
    login_success = show_login()
    
    if not login_success:
        print("❌ Login cancelled or failed. Exiting.")
        return
    
    # ─── STEP 2: Show launcher (if logged in) ───
    if Session.is_logged_in():
        print(f"✅ Logged in as: {Session.get_full_name()} ({Session.get_role()})")
        
        root = tk.Tk()
        app = MainLauncher(root)
        root.mainloop()
    else:
        print("❌ Session not active. Exiting.")


if __name__ == "__main__":
    main()