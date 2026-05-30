# apps/gate_app.py
# 🎯 GATE VERIFICATION APP - Optimized Layout

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS, FONTS
from mifare_core import MifareCore


class SoldierCard:
    def __init__(self):
        self.soldier_id = ""
        self.card_type  = ""

    def read(self, core):
        if not core.authenticate(1):
            raise Exception("Auth failed")
        b4 = core.read_block(4)
        if b4:
            self.soldier_id = core.decode(b4)
        b5 = core.read_block(5)
        if b5:
            self.card_type = core.decode(b5)


class GateApp:

    def __init__(self, root):
        self.root = root
        self.root.title("GATE VERIFICATION STATION — Army Logistics")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x900")
        self.root.minsize(1200, 750)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.mifare = MifareCore(self._log)
        self.card_present = False
        self.last_soldier_id = None
        self.current_soldier = None
        self.current_assignments = []

        self.counter_scans = 0
        self.counter_approved = 0
        self.counter_denied = 0

        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror("Database Error",
                                  f"Cannot connect to database!\n\n{msg}")
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self.mifare.find_reader()
        self._poll_card()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(
            "Assignment.Treeview",
            background="white",
            foreground="black",
            rowheight=38,
            fieldbackground="white",
            font=("Segoe UI", 10),
            borderwidth=1
        )
        s.configure(
            "Assignment.Treeview.Heading",
            background="#1B5E20",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=8
        )
        s.map("Assignment.Treeview",
              background=[("selected", "#2E7D32")],
              foreground=[("selected", "white")])

    # ═══════════════════════════════════════════════════════
    # UI BUILD - Optimized Compact Layout
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        # Footer first (reserves bottom space)
        self._build_footer()

        # Header
        self._build_header()
        self._build_status_bars()

        # Main content area
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # TOP ROW: Scan + Soldier info (fixed height)
        top = tk.Frame(main, bg=COLORS["bg"])
        top.pack(fill=tk.X, pady=(0, 8))

        self._build_scan_panel(top)
        self._build_soldier_panel(top)

        # MIDDLE: Cargo Assignment Table (EXPANDS)
        self._build_assignment_panel(main)

        # BOTTOM ROW: Actions + Log (fixed height)
        bottom = tk.Frame(main, bg=COLORS["bg"], height=200)
        bottom.pack(fill=tk.X, pady=(8, 0))
        bottom.pack_propagate(False)

        self._build_actions_panel(bottom)
        self._build_log_panel(bottom)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=18, pady=8)

        tk.Label(left, text="🎖", font=("Segoe UI Emoji", 26),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 12))

        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="GATE VERIFICATION STATION",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")
        tk.Label(tb,
                 text="Scan Soldier Card  •  Auto Warehouse Assignment",
                 font=("Segoe UI", 8),
                 bg=COLORS["primary"], fg="#C8E6C9").pack(anchor="w")

        self.time_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.time_var,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=18)
        self._update_time()

    def _update_time(self):
        now = datetime.now().strftime("%d %b %Y  |  %H:%M:%S")
        self.time_var.set(f"🕐  {now}")
        self.root.after(1000, self._update_time)

    def _build_status_bars(self):
        self.db_status = tk.Frame(self.root, bg=COLORS["success"], height=24)
        self.db_status.pack(fill=tk.X)
        self.db_status.pack_propagate(False)

        tk.Label(self.db_status, text="🗄 Database: Connected",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)

        self.stats_var = tk.StringVar(value="Ready to scan")
        tk.Label(self.db_status, textvariable=self.stats_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

        self.card_status = tk.Frame(self.root, bg=COLORS["danger"], height=24)
        self.card_status.pack(fill=tk.X)
        self.card_status.pack_propagate(False)

        self.card_dot = tk.Label(self.card_status, text="●",
                                  font=("Segoe UI", 11, "bold"),
                                  bg=COLORS["danger"], fg="white")
        self.card_dot.pack(side=tk.LEFT, padx=(14, 6))

        self.card_var = tk.StringVar(value="📡 Waiting for soldier card...")
        self.card_lbl = tk.Label(self.card_status, textvariable=self.card_var,
                                  font=("Segoe UI", 9, "bold"),
                                  bg=COLORS["danger"], fg="white")
        self.card_lbl.pack(side=tk.LEFT)

        self.atr_var = tk.StringVar(value="ATR: --")
        self.atr_lbl = tk.Label(self.card_status, textvariable=self.atr_var,
                                 font=("Consolas", 8),
                                 bg=COLORS["danger"], fg="white")
        self.atr_lbl.pack(side=tk.RIGHT, padx=14)

    def _build_scan_panel(self, parent):
        scan_frame = tk.LabelFrame(parent, text="  📡  CARD SCAN  ",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=COLORS["bg"], fg=COLORS["primary"],
                                    bd=2, relief=tk.GROOVE,
                                    width=450, height=200)
        scan_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        scan_frame.pack_propagate(False)

        inner = tk.Frame(scan_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        top_row = tk.Frame(inner, bg=COLORS["white"])
        top_row.pack(fill=tk.X, pady=(8, 4))

        self.scan_icon = tk.Label(top_row, text="💳",
                                   font=("Segoe UI Emoji", 36),
                                   bg=COLORS["white"], fg=COLORS["muted"])
        self.scan_icon.pack(side=tk.LEFT, padx=12)

        msg_box = tk.Frame(top_row, bg=COLORS["white"])
        msg_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.scan_msg = tk.Label(msg_box, text="Place Soldier Card",
                                  font=("Segoe UI", 12, "bold"),
                                  bg=COLORS["white"], fg=COLORS["muted"],
                                  anchor="w")
        self.scan_msg.pack(anchor="w")

        self.scan_sub = tk.Label(msg_box, text="Auto-detect & verify",
                                  font=("Segoe UI", 8, "italic"),
                                  bg=COLORS["white"], fg=COLORS["muted"],
                                  anchor="w")
        self.scan_sub.pack(anchor="w")

        # Manual search
        manual_frame = tk.Frame(inner, bg=COLORS["white"])
        manual_frame.pack(fill=tk.X, padx=12, pady=(10, 8))

        tk.Label(manual_frame, text="🔍 Manual Search (Soldier ID):",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["white"]).pack(anchor="w", pady=(0, 4))

        entry_row = tk.Frame(manual_frame, bg=COLORS["white"])
        entry_row.pack(fill=tk.X)

        self.manual_entry = tk.Entry(entry_row, font=("Segoe UI", 10),
                                       relief=tk.SOLID, bd=1)
        self.manual_entry.pack(side=tk.LEFT, fill=tk.X,
                                expand=True, ipady=4)
        self.manual_entry.bind("<Return>",
                                 lambda e: self._manual_search())

        tk.Button(entry_row, text="GO", command=self._manual_search,
                   font=("Segoe UI", 10, "bold"),
                   bg=COLORS["info"], fg="white",
                   relief=tk.FLAT, padx=16,
                   cursor="hand2").pack(side=tk.RIGHT, padx=(6, 0))

    def _build_soldier_panel(self, parent):
        info_frame = tk.LabelFrame(parent,
                                    text="  👤  SOLDIER INFORMATION  ",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=COLORS["bg"], fg=COLORS["primary"],
                                    bd=2, relief=tk.GROOVE,
                                    height=200)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                         expand=True, padx=(5, 0))
        info_frame.pack_propagate(False)

        inner = tk.Frame(info_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Auth banner
        self.auth_banner = tk.Frame(inner, bg=COLORS["muted"], height=32)
        self.auth_banner.pack(fill=tk.X, pady=(0, 8))
        self.auth_banner.pack_propagate(False)

        self.auth_label = tk.Label(self.auth_banner,
                                    text="⏳  WAITING FOR CARD",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=COLORS["muted"], fg="white")
        self.auth_label.pack(expand=True)

        # Info grid - 2 columns
        grid = tk.Frame(inner, bg=COLORS["white"])
        grid.pack(fill=tk.BOTH, expand=True)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        self.info_vars = {}
        info_fields = [
            ("Soldier ID:",    "soldier_id",    0, 0),
            ("Conductor ID:",  "conductor_id",  0, 2),
            ("Soldier Name:",  "soldier_name",  1, 0),
            ("Conductor:",     "conductor_name", 1, 2),
            ("Unit:",          "unit_name",     2, 0),
            ("Scan Time:",     "scan_time",     2, 2),
        ]

        for label, key, row, col in info_fields:
            tk.Label(grid, text=label,
                     font=("Segoe UI", 9),
                     bg=COLORS["white"],
                     fg=COLORS["muted"],
                     anchor="w").grid(row=row, column=col,
                                       sticky="w", padx=(8, 4),
                                       pady=3)

            var = tk.StringVar(value="—")
            tk.Label(grid, textvariable=var,
                     font=("Segoe UI", 10, "bold"),
                     bg=COLORS["white"],
                     fg=COLORS["text"],
                     anchor="w").grid(row=row, column=col+1,
                                       sticky="ew", padx=(0, 8),
                                       pady=3)
            self.info_vars[key] = var

    def _build_assignment_panel(self, parent):
        assign_frame = tk.LabelFrame(
            parent,
            text="  📋  CARGO ASSIGNMENT PLAN  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=2, relief=tk.GROOVE
        )
        assign_frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(assign_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Summary bar
        self.summary_bar = tk.Frame(inner, bg=COLORS["info"], height=34)
        self.summary_bar.pack(fill=tk.X, pady=(0, 6))
        self.summary_bar.pack_propagate(False)

        self.summary_var = tk.StringVar(value="📊 No assignment loaded")
        tk.Label(self.summary_bar, textvariable=self.summary_var,
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["info"], fg="white").pack(
                     side=tk.LEFT, padx=14, pady=6)

        # Table with scrollbar
        tree_frame = tk.Frame(inner, bg=COLORS["white"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("num", "item", "qty", "container",
                "warehouse", "location", "status")
        self.assign_tree = ttk.Treeview(
            tree_frame, columns=cols,
            show="headings",
            style="Assignment.Treeview"
        )

        self.assign_tree.heading("num",       text="#")
        self.assign_tree.heading("item",      text="Item Required")
        self.assign_tree.heading("qty",       text="Quantity")
        self.assign_tree.heading("container", text="Container")
        self.assign_tree.heading("warehouse", text="Warehouse")
        self.assign_tree.heading("location",  text="Location")
        self.assign_tree.heading("status",    text="Status")

        self.assign_tree.column("num",       width=50,  anchor="center")
        self.assign_tree.column("item",      width=160, anchor="w")
        self.assign_tree.column("qty",       width=100, anchor="center")
        self.assign_tree.column("container", width=140, anchor="center")
        self.assign_tree.column("warehouse", width=220, anchor="w")
        self.assign_tree.column("location",  width=180, anchor="w")
        self.assign_tree.column("status",    width=130, anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.assign_tree.yview)
        self.assign_tree.configure(yscrollcommand=sb.set)

        self.assign_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Status tags with GUARANTEED visible colors
        self.assign_tree.tag_configure(
            "available",
            background="#C8E6C9",
            foreground="#1B5E20"
        )
        self.assign_tree.tag_configure(
            "unavailable",
            background="#FFCDD2",
            foreground="#B71C1C"
        )
        self.assign_tree.tag_configure(
            "assigned",
            background="#BBDEFB",
            foreground="#0D47A1"
        )

    def _build_actions_panel(self, parent):
        action_frame = tk.LabelFrame(
            parent, text="  ⚡  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=2, relief=tk.GROOVE, width=480
        )
        action_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        action_frame.pack_propagate(False)

        inner = tk.Frame(action_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Action buttons
        btn_frame = tk.Frame(inner, bg=COLORS["white"])
        btn_frame.pack(fill=tk.X)

        self.approve_btn = tk.Button(
            btn_frame, text="✅ APPROVE & ASSIGN",
            command=self._approve_assignment,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["success"], fg="white",
            relief=tk.FLAT, pady=10,
            cursor="hand2", state="disabled"
        )
        self.approve_btn.pack(fill=tk.X, pady=2)

        self.print_btn = tk.Button(
            btn_frame, text="🖨 PRINT SLIP",
            command=self._print_slip,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=10,
            cursor="hand2", state="disabled"
        )
        self.print_btn.pack(fill=tk.X, pady=2)

        self.reset_btn = tk.Button(
            btn_frame, text="🔄 RESET / NEW SCAN",
            command=self._reset_screen,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["warning"], fg="white",
            relief=tk.FLAT, pady=10,
            cursor="hand2"
        )
        self.reset_btn.pack(fill=tk.X, pady=2)

        # Stats
        tk.Frame(inner, bg=COLORS["border"], height=1).pack(
            fill=tk.X, pady=6)

        stats_frame = tk.Frame(inner, bg=COLORS["white"])
        stats_frame.pack(fill=tk.X)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)

        self.stat_scans = tk.StringVar(value="0")
        self.stat_approved = tk.StringVar(value="0")
        self.stat_denied = tk.StringVar(value="0")

        for i, (label, var, color) in enumerate([
            ("Scans",    self.stat_scans,    COLORS["info"]),
            ("Approved", self.stat_approved, COLORS["success"]),
            ("Denied",   self.stat_denied,   COLORS["danger"]),
        ]):
            box = tk.Frame(stats_frame, bg=COLORS["white"])
            box.grid(row=0, column=i, sticky="ew", padx=2)

            tk.Label(box, textvariable=var,
                     font=("Segoe UI", 16, "bold"),
                     bg=COLORS["white"],
                     fg=color).pack()
            tk.Label(box, text=label,
                     font=("Segoe UI", 8),
                     bg=COLORS["white"],
                     fg=COLORS["muted"]).pack()

    def _build_log_panel(self, parent):
        log_frame = tk.LabelFrame(
            parent, text="  📋  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=2, relief=tk.GROOVE
        )
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        inner = tk.Frame(log_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.log_text = tk.Text(
            inner, font=("Consolas", 8),
            bg="#0d1117", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

        self._log("Gate System Started", "ok")
        self._log("Waiting for soldier card...", "info")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=24)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer,
                 text="© 2025 Indian Army  |  Gate Verification Station",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.LEFT, padx=14, pady=4)
        tk.Label(footer,
                 text="DB: PostgreSQL  |  Card: MIFARE 1K",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.RIGHT, padx=14, pady=4)

    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗",
                  "warn": "⚠", "lock": "🔐"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(
                tk.END, f"[{ts}] {icons.get(level, '•')} {msg}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _set_card_status(self, text, color):
        self.card_var.set(text)
        for w in [self.card_status, self.card_dot,
                  self.card_lbl, self.atr_lbl]:
            try:
                w.configure(bg=color)
            except Exception:
                pass

    def _set_auth_status(self, text, color):
        self.auth_label.configure(text=text, bg=color)
        self.auth_banner.configure(bg=color)

    def _poll_card(self):
        present = self.mifare.connect()
        if present and not self.card_present:
            atr = self.mifare.get_atr()
            self.atr_var.set(f"ATR: {atr}")
            self._set_card_status("📡 Card Detected — Reading...",
                                    COLORS["warning"])
            self._log("Card detected", "ok")
            self.card_present = True
            self.root.after(500, self._auto_scan_card)
        elif not present and self.card_present:
            self.atr_var.set("ATR: --")
            self._set_card_status("📡 Waiting for soldier card...",
                                    COLORS["danger"])
            self._log("Card removed", "warn")
            self.card_present = False
        self.mifare.disconnect()
        self.root.after(1500, self._poll_card)

    def _auto_scan_card(self):
        if not self.mifare.connect():
            return
        try:
            card = SoldierCard()
            card.read(self.mifare)
            if not card.soldier_id:
                self._show_error_state("EMPTY CARD",
                                         "Card has no Soldier ID")
                return
            if card.soldier_id == self.last_soldier_id:
                return
            self.last_soldier_id = card.soldier_id
            self._log(f"Card ID: {card.soldier_id}", "ok")
            self._set_card_status(f"✓ Card Read: {card.soldier_id}",
                                    COLORS["success"])
            self._process_soldier(card.soldier_id)
        except Exception as e:
            self._log(f"Read error: {e}", "err")
        finally:
            self.mifare.disconnect()

    def _manual_search(self):
        soldier_id = self.manual_entry.get().strip()
        if not soldier_id:
            messagebox.showwarning("Required", "Enter Soldier ID!")
            return
        self._log(f"Manual search: {soldier_id}", "info")
        self.last_soldier_id = soldier_id
        self._process_soldier(soldier_id)
        self.manual_entry.delete(0, tk.END)

    def _process_soldier(self, soldier_id):
        self.counter_scans += 1
        self.stat_scans.set(str(self.counter_scans))

        soldier = self.db.get_soldier_by_id(soldier_id)

        if not soldier:
            self._log(f"❌ Soldier '{soldier_id}' NOT found", "err")
            self.counter_denied += 1
            self.stat_denied.set(str(self.counter_denied))
            self._show_error_state("❌ UNAUTHORIZED",
                                     f"ID '{soldier_id}' not registered")
            return

        self.current_soldier = soldier
        self._log(f"✓ Verified: {soldier['soldier_name']}", "ok")

        # Update info
        self.info_vars['soldier_id'].set(soldier['soldier_id'])
        self.info_vars['soldier_name'].set(soldier['soldier_name'])
        self.info_vars['conductor_id'].set(
            soldier.get('conductor_id') or '—')
        self.info_vars['conductor_name'].set(
            soldier.get('conductor_name') or '—')
        self.info_vars['unit_name'].set(
            soldier.get('unit_name') or '—')
        self.info_vars['scan_time'].set(
            datetime.now().strftime("%H:%M:%S"))

        self.scan_icon.configure(text="✅", fg=COLORS["success"])
        self.scan_msg.configure(text="Card Verified!",
                                  fg=COLORS["success"])
        self.scan_sub.configure(
            text=f"Welcome, {soldier['soldier_name']}")

        self._set_auth_status("✅ AUTHORIZED — Access Granted",
                                COLORS["success"])

        assignments = self.db.get_soldier_full_assignment(soldier_id)
        if not assignments:
            self._log("⚠ No cargo found", "warn")
            self.summary_var.set("⚠ No cargo requirements")
            return

        self.current_assignments = assignments
        self._update_assignment_table(assignments)

        self.approve_btn.configure(state="normal")
        self.print_btn.configure(state="normal")

    def _update_assignment_table(self, assignments):
        # Clear
        for item in self.assign_tree.get_children():
            self.assign_tree.delete(item)

        self._log(f"Received {len(assignments)} records", "info")

        if not assignments:
            self.summary_var.set("No items")
            return

        # Group unique items
        unique_items = {}
        for a in assignments:
            key = a.get('required_item')
            if key and key not in unique_items:
                unique_items[key] = a

        available_count = 0
        unavailable_count = 0

        for i, (item_key, a) in enumerate(unique_items.items(), 1):
            item       = str(a.get('required_item', '—'))
            qty        = a.get('required_qty', 0)
            container  = str(a.get('container_id') or '—')
            warehouse  = str(a.get('warehouse_name') or 'NOT AVAILABLE')
            location   = str(a.get('warehouse_location') or '—')
            req_status = a.get('req_status', 'PENDING')

            if not a.get('container_id'):
                status = "UNAVAILABLE"
                tag = "unavailable"
                unavailable_count += 1
            elif req_status == 'ASSIGNED':
                status = "ASSIGNED"
                tag = "assigned"
                available_count += 1
            else:
                status = "AVAILABLE"
                tag = "available"
                available_count += 1

            try:
                self.assign_tree.insert(
                    parent="", index="end",
                    values=(str(i), item, f"{qty} units",
                            container, warehouse, location, status),
                    tags=(tag,)
                )
                self._log(f"  #{i} {item}×{qty} → {container}", "ok")
            except Exception as e:
                self._log(f"Insert error: {e}", "err")

        self.assign_tree.update_idletasks()

        total = len(unique_items)
        if unavailable_count == 0:
            self.summary_var.set(
                f"✓ All {total} items available — Ready to assign")
            self.summary_bar.configure(bg=COLORS["success"])
            for w in self.summary_bar.winfo_children():
                w.configure(bg=COLORS["success"])
        else:
            self.summary_var.set(
                f"⚠ {available_count} available, "
                f"{unavailable_count} unavailable")
            self.summary_bar.configure(bg=COLORS["warning"])
            for w in self.summary_bar.winfo_children():
                w.configure(bg=COLORS["warning"])

    def _show_error_state(self, title, message):
        self.scan_icon.configure(text="❌", fg=COLORS["danger"])
        self.scan_msg.configure(text=title, fg=COLORS["danger"])
        self.scan_sub.configure(text=message)
        self._set_auth_status(f"❌ {title}", COLORS["danger"])

        for key in self.info_vars:
            self.info_vars[key].set("—")

        for item in self.assign_tree.get_children():
            self.assign_tree.delete(item)

        self.summary_var.set("❌ No data")
        self.summary_bar.configure(bg=COLORS["danger"])
        for w in self.summary_bar.winfo_children():
            w.configure(bg=COLORS["danger"])

        self.approve_btn.configure(state="disabled")
        self.print_btn.configure(state="disabled")

    def _approve_assignment(self):
        if not self.current_soldier or not self.current_assignments:
            return

        if not messagebox.askyesno(
            "Confirm",
            f"Approve assignment for:\n\n"
            f"Soldier: {self.current_soldier['soldier_name']}\n"
            f"ID: {self.current_soldier['soldier_id']}\n\n"
            f"This will mark all items as ASSIGNED."
        ):
            return

        soldier_id = self.current_soldier['soldier_id']
        assigned = self.db.auto_assign_warehouses(soldier_id)

        if assigned:
            self.counter_approved += 1
            self.stat_approved.set(str(self.counter_approved))
            self._log(f"✅ Approved {len(assigned)} items", "ok")

            # Reload
            new_assignments = self.db.get_soldier_full_assignment(
                soldier_id)
            self._update_assignment_table(new_assignments)
            self.current_assignments = new_assignments

            messagebox.showinfo(
                "Approved",
                f"✅ Assignment Approved!\n\n"
                f"Soldier: {self.current_soldier['soldier_name']}\n"
                f"Items: {len(assigned)}\n\n"
                f"Soldier may proceed to warehouses."
            )
        else:
            messagebox.showwarning(
                "Already Assigned",
                "All items are already assigned!"
            )

    def _print_slip(self):
        if not self.current_soldier or not self.current_assignments:
            return
        self._show_assignment_slip()

    def _show_assignment_slip(self):
        popup = tk.Toplevel(self.root)
        popup.title("Assignment Slip")
        popup.configure(bg=COLORS["white"])
        popup.geometry("600x700")
        popup.grab_set()

        # Header
        hdr = tk.Frame(popup, bg=COLORS["primary"], height=80)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🎖  INDIAN ARMY",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["primary"], fg="white").pack(pady=(12, 0))
        tk.Label(hdr, text="CARGO ASSIGNMENT SLIP",
                 font=("Segoe UI", 11),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack()

        body = tk.Frame(popup, bg=COLORS["white"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Slip number + date
        info_row = tk.Frame(body, bg=COLORS["white"])
        info_row.pack(fill=tk.X, pady=(0, 12))

        slip_no = f"GS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        tk.Label(info_row, text=f"Slip No: {slip_no}",
                 font=("Consolas", 10),
                 bg=COLORS["white"]).pack(side=tk.LEFT)
        tk.Label(info_row,
                 text=datetime.now().strftime("%d %b %Y  %H:%M:%S"),
                 font=("Consolas", 10),
                 bg=COLORS["white"]).pack(side=tk.RIGHT)

        tk.Frame(body, bg=COLORS["primary"], height=2).pack(
            fill=tk.X, pady=(0, 12))

        # Soldier details
        soldier = self.current_soldier
        details = [
            ("Soldier ID:",     soldier['soldier_id']),
            ("Soldier Name:",   soldier['soldier_name']),
            ("Conductor ID:",   soldier.get('conductor_id') or '—'),
            ("Conductor Name:", soldier.get('conductor_name') or '—'),
            ("Unit:",           soldier.get('unit_name') or '—'),
        ]

        for label, value in details:
            row = tk.Frame(body, bg=COLORS["white"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label,
                     font=("Segoe UI", 10),
                     bg=COLORS["white"],
                     fg=COLORS["muted"],
                     width=16, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=value,
                     font=("Segoe UI", 10, "bold"),
                     bg=COLORS["white"],
                     fg=COLORS["text"]).pack(side=tk.LEFT)

        tk.Frame(body, bg=COLORS["primary"], height=2).pack(
            fill=tk.X, pady=12)

        # Cargo list
        tk.Label(body, text="📦  CARGO ASSIGNMENT:",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["white"],
                 fg=COLORS["primary"]).pack(anchor="w", pady=(0, 8))

        cargo_box = tk.Frame(body, bg=COLORS["white"],
                              relief=tk.SOLID, bd=1)
        cargo_box.pack(fill=tk.BOTH, expand=True)

        cargo_text = tk.Text(cargo_box, font=("Consolas", 10),
                              bg=COLORS["white"],
                              fg=COLORS["text"],
                              relief=tk.FLAT, bd=0)
        cargo_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        cargo_text.insert(tk.END,
            f"{'#':<3} {'ITEM':<14} {'QTY':<10} "
            f"{'CONTAINER':<14} {'WAREHOUSE':<20}\n")
        cargo_text.insert(tk.END, "─" * 62 + "\n")

        unique_items = {}
        for a in self.current_assignments:
            key = a.get('required_item')
            if key and key not in unique_items:
                unique_items[key] = a

        for i, (k, a) in enumerate(unique_items.items(), 1):
            item = (a.get('required_item') or '-')[:14]
            qty  = f"{a.get('required_qty', 0)} units"
            cnt  = (a.get('container_id') or '-')[:14]
            wh   = (a.get('warehouse_name') or 'N/A')[:20]
            cargo_text.insert(tk.END,
                f"{i:<3} {item:<14} {qty:<10} {cnt:<14} {wh:<20}\n")

        cargo_text.insert(tk.END, "\n" + "─" * 62 + "\n")
        cargo_text.insert(tk.END,
            f"\n✓ AUTHORIZED BY: Gate Operator\n"
            f"✓ Soldier may proceed to listed warehouses\n")

        cargo_text.configure(state="disabled")

        # Close button
        btn_frame = tk.Frame(popup, bg=COLORS["white"])
        btn_frame.pack(fill=tk.X, padx=24, pady=(0, 16))

        tk.Button(btn_frame, text="✓  CLOSE",
                   command=popup.destroy,
                   font=("Segoe UI", 11, "bold"),
                   bg=COLORS["primary"], fg="white",
                   relief=tk.FLAT, pady=10,
                   cursor="hand2").pack(fill=tk.X)

    def _reset_screen(self):
        """Reset gate screen for new scan."""
        self.last_soldier_id = None
        self.current_soldier = None
        self.current_assignments = []

        self.scan_icon.configure(text="💳", fg=COLORS["muted"])
        self.scan_msg.configure(text="Place Soldier Card",
                                  fg=COLORS["muted"])
        self.scan_sub.configure(text="Auto-detect & verify")

        self._set_auth_status("⏳  WAITING FOR CARD", COLORS["muted"])

        for key in self.info_vars:
            self.info_vars[key].set("—")

        for item in self.assign_tree.get_children():
            self.assign_tree.delete(item)

        self.summary_var.set("📊 No assignment loaded")
        self.summary_bar.configure(bg=COLORS["info"])
        for w in self.summary_bar.winfo_children():
            w.configure(bg=COLORS["info"])

        self.approve_btn.configure(state="disabled")
        self.print_btn.configure(state="disabled")

        self.manual_entry.delete(0, tk.END)
        self._log("Screen reset — Ready for new scan", "info")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = GateApp(root)
    root.mainloop()