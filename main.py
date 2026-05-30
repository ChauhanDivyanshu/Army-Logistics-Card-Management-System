# main.py
# 🎖  ARMY LOGISTICS - MAIN LAUNCHER (Compact Version)

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from database.db_helper import DatabaseHelper
from shared.theme import COLORS, FONTS


class MainLauncher:

    def __init__(self, root):
        self.root = root
        self.root.title("🎖 Army Logistics System — Main Launcher")
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

    def _build_ui(self):
        # IMPORTANT: Footer first to reserve bottom space
        self._build_footer()
        self._build_header()
        self._build_status_bar()
        self._build_main_content()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=80)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        center = tk.Frame(hdr, bg=COLORS["primary"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        logo_row = tk.Frame(center, bg=COLORS["primary"])
        logo_row.pack()

        tk.Label(logo_row, text="🎖",
                 font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 14))

        title_box = tk.Frame(logo_row, bg=COLORS["primary"])
        title_box.pack(side=tk.LEFT)

        tk.Label(title_box, text="ARMY LOGISTICS SYSTEM",
                 font=("Segoe UI", 18, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")

        tk.Label(title_box,
                 text="MIFARE Classic 1K • PostgreSQL • "
                      "Cargo Management",
                 font=("Segoe UI", 9),
                 bg=COLORS["primary"], fg="#C8E6C9").pack(anchor="w")

        self.time_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.time_var,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).place(
                     relx=0.98, rely=0.2, anchor="ne")

    def _update_time(self):
        now = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        self.time_var.set(f"🕐  {now}")
        self.root.after(1000, self._update_time)

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

    def _build_main_content(self):
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Title row
        title_row = tk.Frame(main, bg=COLORS["bg"])
        title_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(title_row, text="📋  SELECT MODULE TO LAUNCH",
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

        cards_wrap.columnconfigure(0, weight=1, uniform="col")
        cards_wrap.columnconfigure(1, weight=1, uniform="col")
        cards_wrap.columnconfigure(2, weight=1, uniform="col")
        cards_wrap.rowconfigure(0, weight=1, uniform="row")
        cards_wrap.rowconfigure(1, weight=1, uniform="row")

        modules = [
            {
                "icon": "🏭", "title": "WAREHOUSE",
                "subtitle": "Management",
                "stat_key": "total_warehouses",
                "stat_label": "Warehouses",
                "script": "apps/warehouse_app.py",
                "color": COLORS["info"],
                "row": 0, "col": 0
            },
            {
                "icon": "📦", "title": "CONTAINER",
                "subtitle": "Tag Management",
                "stat_key": "total_containers",
                "stat_label": "Containers",
                "script": "apps/container_app.py",
                "color": COLORS["secondary"],
                "row": 0, "col": 1
            },
            {
                "icon": "🗃", "title": "BOX / ITEM",
                "subtitle": "Tag Management",
                "stat_key": "total_boxes",
                "stat_label": "Boxes",
                "script": "apps/box_app.py",
                "color": COLORS["warning"],
                "row": 0, "col": 2
            },
            {
                "icon": "🪖", "title": "SOLDIER",
                "subtitle": "Card Management",
                "stat_key": "total_soldiers",
                "stat_label": "Soldiers",
                "script": "apps/soldier_app.py",
                "color": COLORS["dark"],
                "row": 1, "col": 0
            },
            {
                "icon": "🎯", "title": "GATE",
                "subtitle": "VERIFICATION",
                "stat_key": "pending_requests",
                "stat_label": "Pending",
                "script": "apps/gate_app.py",
                "color": COLORS["primary"],
                                "row": 1, "col": 1,
                "featured": True
            },
            {
                "icon": "📊", "title": "SYSTEM",
                "subtitle": "Dashboard",
                "stat_key": "completed_requests",
                "stat_label": "Completed",
                "script": None,
                "color": COLORS["muted"],
                "row": 1, "col": 2,
                "builtin": True
            }
        ]

        self.stat_vars = {}

        for mod in modules:
            self._build_module_card(cards_wrap, mod)

    def _build_module_card(self, parent, mod):
        """Build a compact module card - guaranteed visible button."""
        is_featured = mod.get("featured", False)
        border_color = COLORS["accent"] if is_featured else COLORS["border"]
        border_width = 3 if is_featured else 1

        # Card frame
        card = tk.Frame(parent, bg=COLORS["white"],
                        relief=tk.SOLID, bd=border_width,
                        highlightbackground=border_color,
                        highlightthickness=border_width)
        card.grid(row=mod["row"], column=mod["col"],
                  sticky="nsew", padx=8, pady=8)

        # Top color strip
        tk.Frame(card, bg=mod["color"], height=4).pack(fill=tk.X)

        # Featured badge (small)
        if is_featured:
            badge = tk.Frame(card, bg=COLORS["accent"], height=20)
            badge.pack(fill=tk.X)
            badge.pack_propagate(False)
            tk.Label(badge, text="⭐ RECOMMENDED",
                     font=("Segoe UI", 7, "bold"),
                     bg=COLORS["accent"],
                     fg=COLORS["dark"]).pack(pady=2)

        # ─── BOTTOM: Launch Button (pack FIRST so it always visible) ───
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

        # Hover effects
        def on_enter(_, b=btn):
            b.configure(bg=COLORS["dark"])

        def on_leave(_, b=btn, c=mod["color"]):
            b.configure(bg=c)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        # ─── TOP: Content (fills remaining space) ───
        inner = tk.Frame(card, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # Icon
        tk.Label(inner, text=mod["icon"],
                 font=("Segoe UI Emoji", 30),
                 bg=COLORS["white"]).pack(pady=(4, 6))

        # Title
        tk.Label(inner, text=mod["title"],
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["white"],
                 fg=mod["color"]).pack()

        tk.Label(inner, text=mod["subtitle"],
                 font=("Segoe UI", 8),
                 bg=COLORS["white"],
                 fg=COLORS["muted"]).pack(pady=(0, 6))

        # Underline
        tk.Frame(inner, bg=mod["color"], height=2,
                 width=40).pack(pady=(0, 8))

        # Stats display
        stat_box = tk.Frame(inner, bg="#F5F5F5",
                             relief=tk.FLAT, bd=0)
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

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(footer,
                 text="© 2025 Indian Army  |  "
                      "Army Logistics Card Management System",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg="#B0BEC5").pack(side=tk.LEFT, padx=16, pady=6)

        tk.Label(footer,
                 text="Hardware: ACR122U  |  DB: PostgreSQL  |  "
                      "Card: MIFARE 1K",
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
                messagebox.showerror(
                    "File Not Found",
                    f"Cannot find:\n{script_path}"
                )
                return

            subprocess.Popen([sys.executable, script_path])
            self.root.after(2000, self._load_stats)

        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch:\n{script}\n\nError: {e}"
            )

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
            ("🏭", "Warehouses",  stats['total_warehouses'],
             COLORS["info"]),
            ("📦", "Containers",  stats['total_containers'],
             COLORS["secondary"]),
            ("🗃", "Boxes",       stats['total_boxes'],
             COLORS["warning"]),
        ]

        for i, (icon, label, value, color) in enumerate(inventory_stats):
            box = tk.Frame(s1, bg="#F5F5F5")
            box.grid(row=0, column=i, sticky="ew", padx=6, pady=6)
            tk.Label(box, text=icon,
                     font=("Segoe UI Emoji", 22),
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
            ("🪖", "Soldiers",  stats['total_soldiers'],
             COLORS["dark"]),
            ("⏳", "Pending",   stats['pending_requests'],
             COLORS["warning"]),
            ("✅", "Assigned",  stats['assigned_requests'],
             COLORS["info"]),
            ("✓", "Completed", stats['completed_requests'],
             COLORS["success"]),
        ]

        for i, (icon, label, value, color) in enumerate(request_stats):
            box = tk.Frame(s2, bg="#F5F5F5")
            box.grid(row=0, column=i, sticky="ew", padx=4, pady=6)
            tk.Label(box, text=icon,
                     font=("Segoe UI Emoji", 18),
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
            history_text.insert(tk.END,
                                 "\n  No assignment history found")

        history_text.configure(state="disabled")

        # Close button
        tk.Button(body, text="✓  CLOSE",
                   command=popup.destroy,
                   font=("Segoe UI", 10, "bold"),
                   bg=COLORS["primary"], fg="white",
                   relief=tk.FLAT, pady=10,
                   cursor="hand2").pack(fill=tk.X, pady=(10, 0))


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()