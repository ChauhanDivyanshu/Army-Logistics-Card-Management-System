# apps/gate_app.py
# 🎖 GATE VERIFICATION - Clean Army Theme

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import threading
from datetime import datetime
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from theme import COLORS, FONTS
from mifare_core import MifareCore
from trip_card import TripCard

API_BASE = "http://localhost:5000/api/v1"
CARD_REMOVAL_RESET_DELAY = 2000


class GateApp:

    def __init__(self, root):
        self.root = root
        self.root.title("GATE VERIFICATION — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x850")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.mifare = MifareCore(self._log)
        self.card_present = False
        self.last_trip_id = None
        self.current_trip = None
        self.current_results = []
        self.assignment_session_id = None
        self.counter_scans = 0
        self.counter_approved = 0
        self.counter_denied = 0
        self.api_connected = False
        self.polling_active = False

        self._setup_styles()
        self._build_ui()

        self._connect_api()
        threading.Thread(target=self._retry_api_loop, daemon=True).start()

        self.mifare.find_reader()
        self._poll_card()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", foreground=COLORS["text"],
            rowheight=38, font=("Segoe UI", 10),
            fieldbackground="white")
        
        s.configure("Clean.Treeview.Heading",
            background=COLORS["primary"], foreground="white",
            font=("Segoe UI", 10, "bold"), padding=8, relief="flat",
            borderwidth=0)
        
        # ✅ Lock heading color - prevent white-on-hover bug
        s.map("Clean.Treeview.Heading",
            background=[
                ("active", COLORS["primary"]),
                ("pressed", COLORS["primary_dark"]),
                ("!active", COLORS["primary"])
            ],
            foreground=[
                ("active", "white"),
                ("pressed", "white"),
                ("!active", "white")
            ],
            relief=[("active", "flat"), ("pressed", "flat")])
        
        # ✅ Selected row - gold highlight (Army theme)
        s.map("Clean.Treeview",
            background=[("selected", "#FFE082")],
            foreground=[("selected", "#1B5E20")])

    def _connect_api(self):
        """Try to connect to API once."""
        try:
            r = requests.get(f"{API_BASE}/health", timeout=3)
            if r.ok:
                self.api_connected = True
                try:
                    self.root.after(0, lambda: self.api_lbl.configure(
                        text="API: Online", bg=COLORS["success"]))
                    self._log("API connected", "ok")
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"[API] Connection failed: {e}")
            try:
                self.root.after(0, lambda: self.api_lbl.configure(
                    text="API: Offline", bg=COLORS["danger"]))
            except Exception:
                pass
        return False

    def _retry_api_loop(self):
        """Keep retrying API connection every 5 seconds if offline."""
        while True:
            if not self.api_connected:
                self._connect_api()
            time.sleep(5)

    # ═══════════════════════════════════════════════════════
    # UI BUILD
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_status_bars()
        
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        top = tk.Frame(main, bg=COLORS["bg"])
        top.pack(fill=tk.X, pady=(0, 8))
        self._build_scan_panel(top)
        self._build_trip_panel(top)

        self._build_items_panel(main)

        bot = tk.Frame(main, bg=COLORS["bg"], height=170)
        bot.pack(fill=tk.X, pady=(8, 0))
        bot.pack_propagate(False)
        self._build_actions_panel(bot)
        self._build_log_panel(bot)
        
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="🎖", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="GATE VERIFICATION STATION",
                 font=("Segoe UI", 18, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")

        right = tk.Frame(hdr, bg=COLORS["primary"])
        right.pack(side=tk.RIGHT, padx=20)
        
        self.time_var = tk.StringVar()
        tk.Label(right, textvariable=self.time_var,
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="e", pady=(15, 0))
        tk.Label(right, text="● ONLINE", font=("Segoe UI", 9, "bold"),
                 bg=COLORS["primary"], fg="#4ade80").pack(anchor="e")
        self._tick()

    def _tick(self):
        self.time_var.set(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))
        self.root.after(1000, self._tick)

    def _build_status_bars(self):
        bar1 = tk.Frame(self.root, bg=COLORS["info"], height=26)
        bar1.pack(fill=tk.X)
        bar1.pack_propagate(False)
        self.api_lbl = tk.Label(bar1, text="API: Connecting...",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["info"], fg="white")
        self.api_lbl.pack(side=tk.LEFT, padx=14)
        tk.Label(bar1, text="Card-based verification system",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["info"], fg="white").pack(side=tk.RIGHT, padx=14)

        bar2 = tk.Frame(self.root, bg=COLORS["danger"], height=28)
        bar2.pack(fill=tk.X)
        bar2.pack_propagate(False)
        self.card_bar = bar2
        self.card_dot = tk.Label(bar2, text="●", font=("Segoe UI", 12, "bold"),
                                  bg=COLORS["danger"], fg="white")
        self.card_dot.pack(side=tk.LEFT, padx=(14, 6))
        self.card_var = tk.StringVar(value="Waiting for trip card...")
        self.card_lbl = tk.Label(bar2, textvariable=self.card_var,
                                  font=("Segoe UI", 10, "bold"),
                                  bg=COLORS["danger"], fg="white")
        self.card_lbl.pack(side=tk.LEFT)
        self.atr_var = tk.StringVar(value="ATR: --")
        self.atr_lbl = tk.Label(bar2, textvariable=self.atr_var,
                                 font=("Consolas", 9),
                                 bg=COLORS["danger"], fg="white")
        self.atr_lbl.pack(side=tk.RIGHT, padx=14)

    def _build_scan_panel(self, parent):
        f = tk.LabelFrame(parent, text="  CARD SCAN  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, width=480, height=180)
        f.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        f.pack_propagate(False)

        inner = tk.Frame(f, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        top = tk.Frame(inner, bg=COLORS["bg_card"])
        top.pack(fill=tk.X, pady=(15, 8), padx=15)
        
        self.scan_icon = tk.Label(top, text="🚛",
            font=("Segoe UI Emoji", 48),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.scan_icon.pack(side=tk.LEFT, padx=(0, 20))

        msg_box = tk.Frame(top, bg=COLORS["bg_card"])
        msg_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scan_msg = tk.Label(msg_box, text="Place Trip Card",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"], anchor="w")
        self.scan_msg.pack(anchor="w")
        self.scan_sub = tk.Label(msg_box, text="Truck • Driver • Items",
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"], anchor="w")
        self.scan_sub.pack(anchor="w")

        tk.Label(inner,
            text="Card-based verification - Auto-resets when removed",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left").pack(anchor="w", padx=15, pady=(5, 10))

    def _build_trip_panel(self, parent):
        f = tk.LabelFrame(parent, text="  TRIP DETAILS (from card)  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, height=180)
        f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        f.pack_propagate(False)

        inner = tk.Frame(f, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.auth_banner = tk.Frame(inner, bg=COLORS["text_muted"], height=34)
        self.auth_banner.pack(fill=tk.X)
        self.auth_banner.pack_propagate(False)
        self.auth_label = tk.Label(self.auth_banner,
            text="WAITING FOR CARD",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["text_muted"], fg="white")
        self.auth_label.pack(expand=True)

        grid = tk.Frame(inner, bg=COLORS["bg_card"])
        grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        self.info_vars = {}
        fields = [
            ("Trip ID:",        "trip_id",       0, 0),
            ("Truck #:",         "truck",         0, 2),
            ("Driver:",          "driver_name",   1, 0),
            ("Driver ID:",       "driver_id",     1, 2),
            ("Sub-driver:",      "subdriver_name", 2, 0),
            ("Items:",           "item_count",    2, 2),
        ]

        for label, key, row, col in fields:
            tk.Label(grid, text=label, font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                anchor="w").grid(row=row, column=col, sticky="w",
                                  padx=(8, 5), pady=4)
            var = tk.StringVar(value="—")
            tk.Label(grid, textvariable=var,
                font=("Segoe UI", 11, "bold"),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=row, column=col+1, sticky="ew",
                                  padx=(0, 10), pady=4)
            self.info_vars[key] = var

    def _build_items_panel(self, parent):
        f = tk.LabelFrame(parent,
            text="  ITEMS REQUIRED → WAREHOUSE LOCATION  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        f.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(f, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.summary_bar = tk.Frame(inner, bg=COLORS["info"], height=40)
        self.summary_bar.pack(fill=tk.X)
        self.summary_bar.pack_propagate(False)

        self.summary_var = tk.StringVar(value="No trip loaded")
        tk.Label(self.summary_bar, textvariable=self.summary_var,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["info"], fg="white").pack(side=tk.LEFT, padx=14, pady=8)

        self.live_var = tk.StringVar(value="")
        tk.Label(self.summary_bar, textvariable=self.live_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["info"], fg=COLORS["accent"]).pack(side=tk.LEFT, padx=10)

        self.btn_assign = tk.Button(self.summary_bar,
            text="ASSIGN ALL FOR LOADING",
            command=self._assign_all,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["success"], fg="white",
            relief=tk.FLAT, padx=20, pady=5,
            cursor="hand2", state="disabled")
        self.btn_assign.pack(side=tk.RIGHT, padx=14, pady=4)

        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True)

        cols = ("num", "item", "qty", "loaded", "sku", "shed", "warehouse", "status")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="Clean.Treeview")

        # ✅ Status column stretches to fill remaining space
        columns_config = [
            ("num", "S.No.", 70, "center", False),
            ("item", "Item Required", 160, "center", False),
            ("qty", "Qty Needed", 110, "center", False),
            ("loaded", "Loaded", 100, "center", False),
            ("sku", "Container", 110, "center", False),
            ("shed", "Shed", 90, "center", False),
            ("warehouse", "Warehouse", 200, "center", False),
            ("status", "Status", 160, "center", True),  # ✅ stretch=True
        ]

        for c, t, w, anchor, stretch in columns_config:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=anchor, stretch=stretch)
            

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for tag, bg, fg in [
            ("available", "#E8F5E9", "#1B5E20"),
            ("unavailable", "#FFEBEE", "#C62828"),
            ("partial", "#FFF3E0", "#F57C00"),
            ("processing", "#FFE0B2", "#F57C00"),
            ("loaded", "#E3F2FD", "#1565C0"),
            ("complete", "#C8E6C9", "#1B5E20"),
            ("searching", "#F5F5F5", "#757575"),
        ]:
            self.tree.tag_configure(tag, background=bg, foreground=fg)

    def _build_actions_panel(self, parent):
        f = tk.LabelFrame(parent, text="  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, width=400)
        f.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        f.pack_propagate(False)

        inner = tk.Frame(f, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        btns = tk.Frame(inner, bg=COLORS["bg_card"])
        btns.pack(fill=tk.X, padx=10, pady=10)

        self.print_btn = tk.Button(btns, text="PRINT TRIP SLIP",
            command=self._print_slip,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=10, state="disabled",
            cursor="hand2")
        self.print_btn.pack(fill=tk.X, pady=3)

        tk.Button(btns, text="RESET / NEW TRUCK",
            command=self._reset,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["warning"], fg="white",
            relief=tk.FLAT, pady=10, cursor="hand2").pack(fill=tk.X, pady=3)

        tk.Button(btns, text="FORCE CLEAR",
            command=self._force_clear,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="white",
            relief=tk.FLAT, pady=8, cursor="hand2").pack(fill=tk.X, pady=3)

        tk.Frame(inner, bg=COLORS["border"], height=1).pack(fill=tk.X, pady=8, padx=10)

        sf = tk.Frame(inner, bg=COLORS["bg_card"])
        sf.pack(fill=tk.X, padx=10, pady=5)
        sf.columnconfigure(0, weight=1)
        sf.columnconfigure(1, weight=1)
        sf.columnconfigure(2, weight=1)

        self.stat_scans = tk.StringVar(value="0")
        self.stat_ok = tk.StringVar(value="0")
        self.stat_fail = tk.StringVar(value="0")

        for i, (lbl, var, clr) in enumerate([
            ("Scans", self.stat_scans, COLORS["info"]),
            ("Assigned", self.stat_ok, COLORS["success"]),
            ("Failed", self.stat_fail, COLORS["danger"]),
        ]):
            bx = tk.Frame(sf, bg=COLORS["bg_card"])
            bx.grid(row=0, column=i, sticky="ew", padx=2)
            tk.Label(bx, textvariable=var, font=("Segoe UI", 18, "bold"),
                bg=COLORS["bg_card"], fg=clr).pack()
            tk.Label(bx, text=lbl, font=("Segoe UI", 8),
                bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack()

    def _build_log_panel(self, parent):
        f = tk.LabelFrame(parent, text="  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        inner = tk.Frame(f, bg="#212121")
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.log_text = tk.Text(inner, font=("Consolas", 9),
            bg="#212121", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb = ttk.Scrollbar(inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

        self._log("Gate started - Card-based mode", "ok")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Gate Verification",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="MIFARE 1K | Card-based",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗", "warn": "⚠"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(tk.END, f"[{ts}] {icons.get(level, '•')} {msg}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _set_card_status(self, text, color):
        self.card_var.set(text)
        for w in [self.card_bar, self.card_dot, self.card_lbl, self.atr_lbl]:
            try:
                w.configure(bg=color)
            except Exception:
                pass

    def _set_summary(self, text, color):
        self.summary_var.set(text)
        self.summary_bar.configure(bg=color)
        for w in self.summary_bar.winfo_children():
            try:
                w.configure(bg=color)
            except Exception:
                pass

    def _poll_card(self):
        present = self.mifare.connect()
        if present and not self.card_present:
            self.atr_var.set(f"ATR: {self.mifare.get_atr()}")
            self._set_card_status("Card detected - Reading...", COLORS["warning"])
            self.card_present = True
            self.root.after(500, self._read_card)
        elif not present and self.card_present:
            self.atr_var.set("ATR: --")
            self._set_card_status("Card removed - Auto-resetting...", COLORS["warning"])
            self.card_present = False
            self.root.after(CARD_REMOVAL_RESET_DELAY, self._auto_reset_if_no_card)
        self.mifare.disconnect()
        self.root.after(1500, self._poll_card)

    def _auto_reset_if_no_card(self):
        if not self.card_present and self.current_trip:
            self._reset()

    def _read_card(self):
        if not self.mifare.connect():
            return
        try:
            card = TripCard()
            card.read(self.mifare)
            if not card.is_valid():
                self._log("Card empty/invalid", "warn")
                return
            trip_key = card.trip_id or card.truck_number
            if trip_key == self.last_trip_id:
                return
            self.last_trip_id = trip_key
            self._log("=" * 40)
            self._log("CARD READ SUCCESSFULLY", "ok")
            self._log(f"  Trip: {card.trip_id}", "ok")
            self._log(f"  Truck: {card.truck_number}", "ok")
            self._log(f"  Driver: {card.driver_name}", "ok")
            self._log(f"  Items: {len(card.items)}", "ok")
            self._set_card_status(f"Truck: {card.truck_number} | {len(card.items)} items", COLORS["success"])
            self._process_trip(card)
        except Exception as e:
            self._log(f"Read error: {e}", "err")
        finally:
            self.mifare.disconnect()

    def _process_trip(self, card):
        self.counter_scans += 1
        self.stat_scans.set(str(self.counter_scans))
        self.polling_active = False
        trip = card.to_dict()
        self.current_trip = trip

        self.info_vars['trip_id'].set(trip['trip_id'] or '—')
        self.info_vars['truck'].set(trip['truck_number'] or '—')
        self.info_vars['driver_name'].set(trip['driver_name'] or '—')
        self.info_vars['driver_id'].set(trip['driver_id'] or '—')
        self.info_vars['subdriver_name'].set(trip['subdriver_name'] or '—')
        self.info_vars['item_count'].set(f"{len(trip['items'])} items")

        self.scan_icon.configure(text="🚛", fg=COLORS["success"])
        self.scan_msg.configure(text=f"Truck: {trip['truck_number']}", fg=COLORS["success"])
        self.scan_sub.configure(text=f"Driver: {trip['driver_name']}")
        self.auth_label.configure(text="CARD VERIFIED - Searching warehouses...", bg=COLORS["success"])
        self.auth_banner.configure(bg=COLORS["success"])

        self._show_items_loading(trip['items'])
        self._find_items_via_api(trip)

    def _show_items_loading(self, items):
        for c in self.tree.get_children():
            self.tree.delete(c)
        for i, item in enumerate(items, 1):
            self.tree.insert("", "end", iid=f"row-{i}",
                values=(str(i), item['name'], str(item['qty']),
                        "—", "...", "...", "Searching...", "LOOKING UP"),
                tags=("searching",))
        self._set_summary(f"Searching {len(items)} items in warehouses...", COLORS["info"])

    def _find_items_via_api(self, trip):
        # ✅ Re-check API in case it was offline before
        if not self.api_connected:
            self._log("Re-checking API connection...", "info")
            self._connect_api()
        
        if not self.api_connected:
            self._show_api_offline_in_table()
            return
        
        payload = {'trip_id': trip['trip_id'] or trip['truck_number'], 'items': trip['items']}
        
        def worker():
            try:
                r = requests.post(f"{API_BASE}/gate/find-items", json=payload, timeout=10)
                if r.ok:
                    self.root.after(0, self._on_items_found, r.json())
                else:
                    self.root.after(0, self._on_api_error, f"HTTP {r.status_code}: {r.text[:100]}")
            except requests.exceptions.ConnectionError:
                self.api_connected = False  # Mark as offline
                self.root.after(0, lambda: self.api_lbl.configure(
                    text="API: Offline", bg=COLORS["danger"]))
                self.root.after(0, self._on_api_error, "Connection refused")
            except Exception as e:
                self.root.after(0, self._on_api_error, str(e))
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_api_error(self, error_msg):
        self._log(f"API error: {error_msg}", "err")
        for child in self.tree.get_children():
            vals = list(self.tree.item(child)['values'])
            vals[4] = "—"   # sku
            vals[5] = "—"   # shed (NEW)
            vals[6] = "API Error"  # warehouse
            vals[7] = "API FAILED"  # status
            self.tree.item(child, values=tuple(vals), tags=("unavailable",))
        self._set_summary(f"API Error: {error_msg}", COLORS["danger"])

    def _show_api_offline_in_table(self):
        for child in self.tree.get_children():
            vals = list(self.tree.item(child)['values'])
            vals[4] = "—"
            vals[5] = "—"
            vals[6] = "Start API server"
            vals[7] = "API OFFLINE"
            self.tree.item(child, values=tuple(vals), tags=("unavailable",))
        self._set_summary("API offline - Run: python api_server.py", COLORS["warning"])

    def _on_items_found(self, data):
        if not data or not data.get('success'):
            self._on_api_error("Invalid response")
            return
        results = data.get('results', [])
        self.current_results = results

        for c in self.tree.get_children():
            self.tree.delete(c)

        avail = 0
        unavail = 0
        partial = 0

        for i, r in enumerate(results, 1):
            name = r['item_name']
            qty = r['required_qty']
            best = r.get('best_location') or {}
            loc_count = r.get('location_count', 0)
            total_avail = r.get('total_available_qty', 0)

            if r['is_available']:
                sku = best.get('sku_id', '—')
                shed = best.get('shed_id', '—')
                wh_name = best.get('warehouse_name', '—')
                # ✅ Short warehouse name only (e.g., "Main Armory")
                wh = wh_name.replace('Depot', '').strip() if wh_name else '—'
                st = f"AVAILABLE" if loc_count == 1 else f"AVAILABLE ({loc_count} locs)"
                tag = "available"
                avail += 1
            elif loc_count > 0:
                sku = best.get('sku_id', '—')
                shed = best.get('shed_id', '—')
                wh_name = best.get('warehouse_name', '—')
                wh = wh_name.replace('Depot', '').strip() if wh_name else '—'
                st = f"PARTIAL {total_avail}/{qty}"
                tag = "partial"
                partial += 1
            else:
                sku = "—"
                shed = "—"
                wh = "NOT FOUND"
                st = "NOT AVAILABLE"
                tag = "unavailable"
                unavail += 1

            self.tree.insert("", "end", iid=f"row-{i}",
                values=(str(i), name, str(qty), "—", sku, shed, wh, st),
                tags=(tag,))

        total = len(results)
        if avail == total and total > 0:
            self._set_summary(f"All {total} items available - Ready", COLORS["success"])
            self.auth_label.configure(text="ALL ITEMS AVAILABLE", bg=COLORS["success"])
        elif avail > 0:
            self._set_summary(f"{avail} available, {partial} partial, {unavail} missing", COLORS["warning"])
            self.auth_label.configure(text="PARTIAL AVAILABILITY", bg=COLORS["warning"])
        else:
            self._set_summary("No items available!", COLORS["danger"])
            self.auth_label.configure(text="ITEMS NOT IN STOCK", bg=COLORS["danger"])

        self.auth_banner.configure(bg=self.summary_bar.cget("bg"))
        if avail > 0 or partial > 0:
            self.btn_assign.configure(state="normal")
            self.print_btn.configure(state="normal")

    def _assign_all(self):
        if not self.current_trip or not self.current_results:
            return
        trip = self.current_trip
        items = []
        for r in self.current_results:
            if r.get('is_available') or r.get('location_count', 0) > 0:
                best = r.get('best_location') or {}
                items.append({
                    'name': r['item_name'], 'qty': r['required_qty'],
                    'sku': best.get('sku_id'),
                    'warehouse_id': best.get('warehouse_id'),
                })
        if not items:
            messagebox.showinfo("Nothing", "No items to assign!")
            return
        if not messagebox.askyesno("Confirm",
            f"Assign {len(items)} items for loading?\n\n"
            f"Truck: {trip.get('truck_number')}\n"
            f"Driver: {trip.get('driver_name')}"):
            return

        self.btn_assign.configure(state="disabled", text="Assigning...")
        payload = {
            'trip_id': trip.get('trip_id') or trip.get('truck_number'),
            'truck_number': trip.get('truck_number'),
            'driver_id': trip.get('driver_id'),
            'driver_name': trip.get('driver_name'),
            'subdriver_name': trip.get('subdriver_name'),
            'items': items,
        }
        def worker():
            try:
                r = requests.post(f"{API_BASE}/gate/assign-trip", json=payload, timeout=5)
                if r.ok:
                    self.root.after(0, self._on_assigned, r.json())
                else:
                    self.root.after(0, self._on_assign_fail, str(r.status_code))
            except Exception as e:
                self.root.after(0, self._on_assign_fail, str(e))
        threading.Thread(target=worker, daemon=True).start()

    def _on_assigned(self, data):
        count = data.get('items_assigned', 0)
        self.assignment_session_id = data.get('soldier_id') or data.get('trip_id')
        self.counter_approved += 1
        self.stat_ok.set(str(self.counter_approved))
        self._log(f"ASSIGNED {count} items!", "ok")
        self.btn_assign.configure(text="ASSIGNED - Monitoring...", bg=COLORS["text_muted"])
        self._set_summary(f"{count} items assigned - Loading in progress", COLORS["warning"])

        for child in self.tree.get_children():
            vals = list(self.tree.item(child)['values'])
            if 'AVAILABLE' in str(vals[7]) or 'PARTIAL' in str(vals[7]):
                vals[7] = "PROCESSING"
                self.tree.item(child, values=tuple(vals), tags=("processing",))

        self.polling_active = True
        self.live_var.set("LIVE - Monitoring")
        threading.Thread(target=self._poll_status, daemon=True).start()

        messagebox.showinfo("Assigned",
            f"Assigned {count} items!\nWarehouse will load.")

    def _on_assign_fail(self, error):
        self.btn_assign.configure(state="normal", text="ASSIGN ALL FOR LOADING")
        self.counter_denied += 1
        self.stat_fail.set(str(self.counter_denied))
        self._log(f"Assignment failed: {error}", "err")
        messagebox.showerror("Failed", f"Assignment failed!\n\n{error}")

    def _poll_status(self):
        sid = (self.current_trip or {}).get('trip_id') or (self.current_trip or {}).get('truck_number')
        if not sid:
            return
        while self.polling_active:
            try:
                r = requests.get(f"{API_BASE}/gate/soldier/{sid}/live-status", timeout=2)
                if r.ok:
                    self.root.after(0, self._apply_live, r.json())
            except Exception:
                pass
            time.sleep(2)
        self.root.after(0, lambda: self.live_var.set(""))

    def _apply_live(self, data):
        if not data:
            return
        try:
            items = data.get('items', [])
            changes = False
            for item in items:
                item_name = str(item.get('item_name', '')).lower()
                for child in self.tree.get_children():
                    vals = self.tree.item(child)['values']
                    if str(vals[1]).lower() == item_name:
                        new_loaded = item.get('boxes_loaded', 0)
                        required = item.get('required_qty', 0)
                        status = item.get('status', '')
                        if status == 'COMPLETE':
                            disp, tag = "COMPLETE", "complete"
                        elif status == 'LOADED':
                            disp, tag = "LOADED", "loaded"
                        elif status == 'PROCESSING':
                            disp, tag = "PROCESSING", "processing"
                        else:
                            continue
                        new_vals = list(vals)
                        loaded_str = f"{new_loaded}/{required}" if new_loaded > 0 else "—"
                        if new_vals[3] != loaded_str or new_vals[7] != disp:
                            new_vals[3] = loaded_str
                            new_vals[7] = disp  
                            self.tree.item(child, values=tuple(new_vals), tags=(tag,))
                            changes = True
                            self._log(f"{item.get('item_name')}: {new_loaded}/{required}", "ok")
                        break
            if changes:
                self.live_var.set("UPDATED!")
                self.root.after(700, lambda: self.live_var.set("LIVE"))
            if data.get('all_complete'):
                self.polling_active = False
                self.live_var.set("COMPLETE!")
                self._log("ALL LOADED!", "ok")
                self._set_summary("ALL COMPLETE!", COLORS["success"])
                self.root.after(500, lambda: messagebox.showinfo("Complete!", "All items loaded!"))
        except Exception:
            pass

    def _print_slip(self):
        if not self.current_trip:
            return
        t = self.current_trip
        info = f"TRIP SLIP\n\nTruck: {t.get('truck_number')}\n"
        info += f"Driver: {t.get('driver_name')}\nItems: {t.get('item_count')}"
        messagebox.showinfo("Print", info)

    def _force_clear(self):
        if messagebox.askyesno("Force Clear", "Force clear everything?"):
            self.card_present = False
            self.last_trip_id = None
            self._reset()

    def _reset(self):
        self.polling_active = False
        self.live_var.set("")
        self.last_trip_id = None
        self.current_trip = None
        self.current_results = []
        self.assignment_session_id = None
        self.scan_icon.configure(text="🚛", fg=COLORS["text_muted"])
        self.scan_msg.configure(text="Place Trip Card", fg=COLORS["text_muted"])
        self.scan_sub.configure(text="Truck • Driver • Items")
        self.auth_label.configure(text="WAITING FOR CARD", bg=COLORS["text_muted"])
        self.auth_banner.configure(bg=COLORS["text_muted"])
        for k in self.info_vars:
            self.info_vars[k].set("—")
        for c in self.tree.get_children():
            self.tree.delete(c)
        self._set_summary("No trip loaded - Place card to begin", COLORS["info"])
        self.btn_assign.configure(text="ASSIGN ALL FOR LOADING",
            state="disabled", bg=COLORS["success"])
        self.print_btn.configure(state="disabled")
        self._log("Ready for next truck", "info")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-launcher', action='store_true',
                        help='Skip login if from launcher')
    parser.add_argument('--user', type=str, default='gate1')
    parser.add_argument('--role', type=str, default='GATE')
    parser.add_argument('--name', type=str, default='Gate Officer')
    args, _ = parser.parse_known_args()
    
    if not args.from_launcher:
        # Standalone mode - show login
        try:
            sys.path.insert(0, os.path.join(BASE, '..'))
            from auth.login_window import show_login
            from auth.session import Session
            
            if not show_login():
                sys.exit(0)
        except Exception as e:
            print(f" {e}")
    else:
        print(f" From main: {args.name} ({args.role})")
    
    root = tk.Tk()
    app = GateApp(root)
    root.mainloop()