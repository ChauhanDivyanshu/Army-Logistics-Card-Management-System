# apps/box_app.py
# 🗃 BOX MANAGEMENT - Updated for new schema (Shed → Container → Box)
# Each box has variable quantity + UHF tag EPC

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS, FONTS


class BoxApp:

    def __init__(self, root):
        self.root = root
        self.root.title("BOX MANAGEMENT — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.selected_box = None
        self.container_map = {}
        self.container_info = {}
        self.shed_filter_map = {}
        self.fields = {}
        self.all_boxes = []

        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror("Database Error", f"Cannot connect!\n\n{msg}")
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_sheds_filter()
        self._load_containers_dropdown()
        self._load_boxes()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", foreground=COLORS["text"],
            rowheight=32, font=("Segoe UI", 10),
            fieldbackground="white")
        
        s.configure("Clean.Treeview.Heading",
            background=COLORS["primary"], foreground="white",
            font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        
        s.map("Clean.Treeview.Heading",
            background=[("active", COLORS["primary"]),
                        ("pressed", COLORS["primary_dark"])],
            foreground=[("active", "white"),
                        ("pressed", "white")],
            relief=[("active", "flat"), ("pressed", "flat")])
        
        s.map("Clean.Treeview",
              background=[("selected", "#FFE082")],
              foreground=[("selected", "#1B5E20")])
        
        s.configure("TCombobox",
            font=("Segoe UI", 10),
            padding=5,
            fieldbackground="white",
            background="white",
            arrowsize=18)
        s.map("TCombobox",
            fieldbackground=[("readonly", "white")],
            foreground=[("readonly", COLORS["text"])])
        
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))
        self.root.option_add("*TCombobox*Listbox.background", "white")
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["primary"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "white")

    def _build_ui(self):
        self._build_header()
        self._build_status_bar()

        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self._build_box_list(main)
        self._build_form_panel(main)
        self._build_actions_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(left, text="🗃", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="BOX MANAGEMENT",
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
        self._update_time()

    def _update_time(self):
        from datetime import datetime
        self.time_var.set(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))
        self.root.after(1000, self._update_time)

    def _build_status_bar(self):
        status = tk.Frame(self.root, bg=COLORS["success"], height=26)
        status.pack(fill=tk.X)
        status.pack_propagate(False)
        tk.Label(status, text="Database: Connected",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)
        self.count_var = tk.StringVar(value="Total: 0 boxes")
        tk.Label(status, textvariable=self.count_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

    # ═══════════════════════════════════════════════════════
    # PANEL 1: ALL BOXES (LEFT)
    # ═══════════════════════════════════════════════════════

    def _build_box_list(self, parent):
        list_container = tk.Frame(parent, bg=COLORS["bg"], width=620)
        list_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        list_container.pack_propagate(False)

        frame = tk.LabelFrame(list_container, text="  ALL BOXES  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Search
        search_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        search_frame.pack(fill=tk.X, padx=8, pady=8)
        tk.Label(search_frame, text="Search:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_boxes())
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), relief=tk.SOLID, bd=1,
                 highlightthickness=1,
                 highlightbackground=COLORS["input_border"],
                 highlightcolor=COLORS["primary"]
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        # Shed Filter
        shed_filter_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        shed_filter_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        tk.Label(shed_filter_frame, text="Shed:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(0, 6))
        self.shed_filter_combo = ttk.Combobox(shed_filter_frame, state="readonly",
                                                font=("Segoe UI", 9))
        self.shed_filter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.shed_filter_combo.bind("<<ComboboxSelected>>",
                                      lambda e: self._filter_boxes())

        # Container Filter
        cont_filter_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        cont_filter_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(cont_filter_frame, text="Container:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(0, 6))
        self.filter_combo = ttk.Combobox(cont_filter_frame, state="readonly",
                                          font=("Segoe UI", 9))
        self.filter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.filter_combo.bind("<<ComboboxSelected>>",
                                lambda e: self._filter_boxes())

        # Table
        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        cols = ("uid", "shed", "container", "item", "qty", "unit", "status")
        self.tree = ttk.Treeview(tf, columns=cols,
            show="headings", style="Clean.Treeview")

        self.tree.heading("uid", text="Box UID")
        self.tree.heading("shed", text="Shed")
        self.tree.heading("container", text="Container")
        self.tree.heading("item", text="Item")
        self.tree.heading("qty", text="Qty")
        self.tree.heading("unit", text="Unit")
        self.tree.heading("status", text="Status")

        self.tree.column("uid", width=155, anchor="center", stretch=False)
        self.tree.column("shed", width=55, anchor="center", stretch=False)
        self.tree.column("container", width=75, anchor="center", stretch=False)
        self.tree.column("item", width=80, anchor="center", stretch=False)
        self.tree.column("qty", width=60, anchor="center", stretch=False)
        self.tree.column("unit", width=50, anchor="center", stretch=False)
        self.tree.column("status", width=95, anchor="center", stretch=True)

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ═══════════════════════════════════════════════════════
    # PANEL 2: BOX DETAILS FORM (MIDDLE)
    # ═══════════════════════════════════════════════════════

    def _build_form_panel(self, parent):
        mid_frame = tk.Frame(parent, bg=COLORS["bg"], width=360)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        mid_frame.pack_propagate(False)

        # FORM
        form_box = tk.LabelFrame(mid_frame,
            text="  BOX DETAILS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        form_box.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        form_inner = tk.Frame(form_box, bg=COLORS["bg_card"])
        form_inner.pack(fill=tk.X, padx=2, pady=2)
        form_inner.columnconfigure(1, weight=1)

        # Box UID
        self._add_field(form_inner, 0, "Box UID:", "box_uid")

        # Container
        tk.Label(form_inner, text="Container:",
                font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=1, column=0, sticky="w", padx=8, pady=3)
        self.container_combo = ttk.Combobox(form_inner, state="readonly",
                                            font=("Segoe UI", 10))
        self.container_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=3)
        self.container_combo.bind("<<ComboboxSelected>>",
                                    lambda e: self._on_container_select())
        self.fields["container_id"] = self.container_combo

        # Item (auto)
        tk.Label(form_inner, text="Item:",
                font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=2, column=0, sticky="w", padx=8, pady=3)
        self.item_label = tk.Label(form_inner, text="(select container)",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=COLORS["bg_card"],
                                    fg=COLORS["text_muted"],
                                    anchor="w")
        self.item_label.grid(row=2, column=1, sticky="ew", padx=8, pady=3)

        # Quantity
        self._add_field(form_inner, 3, "Quantity:", "quantity")

        # Unit
        tk.Label(form_inner, text="Unit:",
                font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=4, column=0, sticky="w", padx=8, pady=3)
        self.unit_combo = ttk.Combobox(form_inner,
            values=["PCS", "KG", "LTR", "MTR", "PAIR", "BOX", "SET"],
            state="readonly", font=("Segoe UI", 10))
        self.unit_combo.set("PCS")
        self.unit_combo.grid(row=4, column=1, sticky="ew", padx=8, pady=3)
        self.fields["unit"] = self.unit_combo

        # Condition
        tk.Label(form_inner, text="Condition:",
                font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=5, column=0, sticky="w", padx=8, pady=3)
        self.condition_combo = ttk.Combobox(form_inner,
            values=["GOOD", "DAMAGED", "EXPIRED", "SEALED"],
            state="readonly", font=("Segoe UI", 10))
        self.condition_combo.set("GOOD")
        self.condition_combo.grid(row=5, column=1, sticky="ew", padx=8, pady=3)
        self.fields["condition"] = self.condition_combo

        # Status
        tk.Label(form_inner, text="Status:",
                font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text"],
                anchor="w").grid(row=6, column=0, sticky="w", padx=8, pady=3)
        self.status_combo = ttk.Combobox(form_inner,
            values=["IN_STOCK", "ALLOCATED", "DISPATCHED", "RETURNED"],
            state="readonly", font=("Segoe UI", 10))
        self.status_combo.set("IN_STOCK")
        self.status_combo.grid(row=6, column=1, sticky="ew", padx=8, pady=3)
        self.fields["status"] = self.status_combo

        # Batch
        self._add_field(form_inner, 7, "Batch No:", "batch_number")
        
        # UHF Tag EPC
        self._add_field(form_inner, 8, "UHF Tag:", "uhf_tag_epc")

        # ACTIONS
        db_box = tk.LabelFrame(mid_frame, text="  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        db_box.pack(side=tk.TOP, fill=tk.X)

        db_inner = tk.Frame(db_box, bg=COLORS["bg_card"])
        db_inner.pack(fill=tk.X, padx=2, pady=2)

        actions = [
            ("ADD BOX", COLORS["success"], self._add_box),
            ("UPDATE SELECTED", COLORS["info"], self._update_box),
            ("DELETE SELECTED", COLORS["danger"], self._delete_box),
            ("REFRESH", COLORS["warning"], self._load_boxes),
            ("CLEAR FORM", COLORS["text_muted"], self._clear_form),
        ]

        for text, color, cmd in actions:
            tk.Button(db_inner, text=text, command=cmd,
                font=("Segoe UI", 10, "bold"),
                bg=color, fg="white",
                relief=tk.FLAT, bd=0,
                pady=4, cursor="hand2",
                activebackground=COLORS["primary_dark"],
                activeforeground="white").pack(fill=tk.X, padx=6, pady=1)

    def _add_field(self, parent, row, label, key):
        tk.Label(parent, text=label,
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["text"],
            anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=3)
        entry = tk.Entry(parent, font=("Segoe UI", 10),
            relief=tk.SOLID, bd=1,
            highlightthickness=1,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["primary"])
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=3, ipady=3)
        self.fields[key] = entry

    # ═══════════════════════════════════════════════════════
    # PANEL 3: UHF + INFO + LOG (RIGHT)
    # ═══════════════════════════════════════════════════════

    def _build_actions_panel(self, parent):
        right_frame = tk.Frame(parent, bg=COLORS["bg"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        right_frame.pack_propagate(False)

        # UHF OPERATIONS
        uhf_box = tk.LabelFrame(right_frame,
            text="  UHF TAG OPERATIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        uhf_box.pack(fill=tk.X, pady=(0, 6))

        uhf_inner = tk.Frame(uhf_box, bg=COLORS["bg_card"])
        uhf_inner.pack(fill=tk.X, padx=2, pady=2)

        tk.Label(uhf_inner,
            text="Each box has a UHF tag with SKU info.\n"
                 "Tags contain: SKU, Item, Sequence #",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left", wraplength=380
        ).pack(anchor="w", padx=10, pady=(10, 10))

        tk.Button(uhf_inner,
            text="OPEN UHF WRITER",
            command=self._launch_uhf_writer,
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"], fg="white",
            relief=tk.FLAT, bd=0,
            pady=12, cursor="hand2",
            activebackground=COLORS["primary_dark"],
            activeforeground="white").pack(fill=tk.X, padx=10, pady=(0, 10))

        # BOX INFO
        info_box = tk.LabelFrame(right_frame,
            text="  BOX INFO  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        info_box.pack(fill=tk.X, pady=(0, 6))

        info_inner = tk.Frame(info_box, bg=COLORS["bg_card"])
        info_inner.pack(fill=tk.X, padx=2, pady=2)

        self.box_info_var = tk.StringVar(value="Select a box to view info")
        tk.Label(info_inner, textvariable=self.box_info_var,
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left", wraplength=380
        ).pack(anchor="w", padx=10, pady=10)

        # ACTIVITY LOG
        log_box = tk.LabelFrame(right_frame,
            text="  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        log_box.pack(fill=tk.BOTH, expand=True)

        log_inner = tk.Frame(log_box, bg="#212121")
        log_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.log_text = tk.Text(log_inner, font=("Consolas", 9),
            bg="#212121", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

        self._log("Box Management started", "ok")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Box Management",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="Database: PostgreSQL",
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

    # ═══════════════════════════════════════════════════════
    # UHF WRITER LAUNCHER
    # ═══════════════════════════════════════════════════════

    def _launch_uhf_writer(self):
        uhf_app = os.path.join(BASE, 'uhf_writer_app.py')
        
        if not os.path.exists(uhf_app):
            messagebox.showerror("Not Found",
                f"UHF Writer app not found at:\n{uhf_app}")
            return
        
        try:
            subprocess.Popen([sys.executable, uhf_app])
            self._log("Launched UHF Writer", "ok")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch: {e}")

    # ═══════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _load_sheds_filter(self):
        """Load sheds for filter dropdown."""
        sheds = self.db.get_all_sheds()
        self.shed_filter_map = {}
        values = ["All Sheds"]
        for s in sheds:
            display = f"{s['shed_id']} - {s['shed_name']}"
            values.append(display)
            self.shed_filter_map[display] = s['shed_id']
        self.shed_filter_combo['values'] = values
        self.shed_filter_combo.set("All Sheds")

    def _load_containers_dropdown(self):
        containers = self.db.get_all_containers()
        self.container_map = {}
        self.container_info = {}
        values = ["-- Select Container --"]
        filter_values = ["All Containers"]
        
        for c in containers:
            display = f"{c['container_id']} ({c['item_name']})"
            values.append(display)
            filter_values.append(display)
            self.container_map[display] = c['container_id']
            self.container_info[c['container_id']] = c
        
        self.container_combo['values'] = values
        if values:
            self.container_combo.set(values[0])
        self.filter_combo['values'] = filter_values
        self.filter_combo.set(filter_values[0])

    def _on_container_select(self):
        selected = self.container_combo.get()
        container_id = self.container_map.get(selected)
        if container_id and container_id in self.container_info:
            container = self.container_info[container_id]
            shed_id = container.get('shed_id', '?')
            self.item_label.configure(
                text=f"{container['item_name']} (Shed: {shed_id})",
                fg=COLORS["primary"])
        else:
            self.item_label.configure(text="(select container)",
                                       fg=COLORS["text_muted"])

    def _load_boxes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        boxes = self.db.get_all_boxes()
        self.all_boxes = boxes
        
        for b in boxes:
            self.tree.insert("", tk.END, values=(
                b['box_uid'],
                b.get('shed_id', '-') or '-',
                b['container_id'],
                b.get('item_name', '-'),
                b['quantity'],
                b['unit'],
                b.get('status', 'IN_STOCK')
            ))
        
        self.count_var.set(f"Total: {len(boxes)} boxes")
        self._log(f"Loaded {len(boxes)} boxes", "ok")

    def _filter_boxes(self):
        search = self.search_var.get().lower().strip()
        shed_filter = self.shed_filter_combo.get()
        container_filter = self.filter_combo.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered = self.all_boxes
        
        # Filter by shed
        if shed_filter and shed_filter != "All Sheds":
            shed_id = self.shed_filter_map.get(shed_filter)
            if shed_id:
                filtered = [b for b in filtered if b.get('shed_id') == shed_id]
        
        # Filter by container
        if container_filter and container_filter != "All Containers":
            container_id = self.container_map.get(container_filter)
            if container_id:
                filtered = [b for b in filtered if b['container_id'] == container_id]
        
        # Filter by search
        if search:
            filtered = [b for b in filtered
                if search in b['box_uid'].lower()
                or search in b['container_id'].lower()
                or search in (b.get('item_name', '') or '').lower()
                or search in (b.get('uhf_tag_epc', '') or '').lower()]
        
        for b in filtered:
            self.tree.insert("", tk.END, values=(
                b['box_uid'],
                b.get('shed_id', '-') or '-',
                b['container_id'],
                b.get('item_name', '-'),
                b['quantity'],
                b['unit'],
                b.get('status', 'IN_STOCK')
            ))
        
        self.count_var.set(f"Showing: {len(filtered)} of {len(self.all_boxes)}")

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0])['values']
        self._clear_form(refresh=False)
        
        box_uid = str(values[0])
        self.fields['box_uid'].insert(0, box_uid)
        
        container_id = str(values[2])
        for display, cid in self.container_map.items():
            if cid == container_id:
                self.container_combo.set(display)
                self._on_container_select()
                break
        
        self.fields['quantity'].insert(0, values[4])
        self.unit_combo.set(values[5])
        self.status_combo.set(values[6])
        
        # Get full box details
        box = self.db.get_box_by_uid(box_uid)
        if box:
            self.condition_combo.set(box.get('condition', 'GOOD'))
            
            if box.get('batch_number'):
                self.fields['batch_number'].insert(0, box['batch_number'])
            
            if box.get('uhf_tag_epc'):
                self.fields['uhf_tag_epc'].insert(0, box['uhf_tag_epc'])
            
            # Show box info
            info_text = (
                f"📦 Box: {box_uid}\n"
                f"🏚️ Shed: {box.get('shed_id', '?')}\n"
                f"📋 Container: {box.get('container_id', '?')}\n"
                f"🎯 Item: {box.get('item_name', '?')} × {box['quantity']} {box.get('unit', 'PCS')}\n"
                f"📡 UHF: {box.get('uhf_tag_epc', '(none)')}\n"
                f"🔵 Status: {box.get('status', 'IN_STOCK')}"
            )
            self.box_info_var.set(info_text)
        
        self.selected_box = box_uid
        self.fields['box_uid'].configure(state="readonly")
        self._log(f"Selected: {box_uid}", "info")

    def _get_container_id(self):
        return self.container_map.get(self.container_combo.get(), "")

    def _add_box(self):
        uid = self.fields['box_uid'].get().strip()
        container_id = self._get_container_id()
        qty = self.fields['quantity'].get().strip()
        unit = self.unit_combo.get()
        condition = self.condition_combo.get()
        batch = self.fields['batch_number'].get().strip()
        uhf_epc = self.fields['uhf_tag_epc'].get().strip()

        if not uid or not container_id:
            messagebox.showwarning("Required", "Box UID and Container are required!")
            return
        
        try:
            qty = int(qty) if qty else 0
        except ValueError:
            messagebox.showwarning("Invalid", "Quantity must be a number!")
            return
        
        if qty <= 0:
            messagebox.showwarning("Invalid", "Quantity must be > 0!")
            return
        
        if self.db.get_box_by_uid(uid):
            messagebox.showerror("Duplicate", f"Box UID '{uid}' exists!")
            return

        if self.db.add_box(uid, container_id, qty, unit, batch, uhf_epc or None):
            # Update extra fields
            if condition != "GOOD":
                self.db.update_box(uid, condition=condition)
            
            self._log(f"Box {uid} added", "ok")
            messagebox.showinfo("Success",
                f"Box added!\n\nUID: {uid}\nContainer: {container_id}\n"
                f"Qty: {qty} {unit}")
            self._clear_form()
            self._load_boxes()
        else:
            messagebox.showerror("Error", "Failed to add box! Check if UHF tag is unique.")

    def _update_box(self):
        if not self.selected_box:
            messagebox.showwarning("No Selection", "Select a box first!")
            return
        
        try:
            qty = int(self.fields['quantity'].get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid", "Quantity must be a number!")
            return
        
        if qty <= 0:
            messagebox.showwarning("Invalid", "Quantity must be > 0!")
            return
        
        unit = self.unit_combo.get()
        condition = self.condition_combo.get()
        status = self.status_combo.get()
        batch = self.fields['batch_number'].get().strip()
        uhf_epc = self.fields['uhf_tag_epc'].get().strip()
        
        if not messagebox.askyesno("Confirm", f"Update '{self.selected_box}'?"):
            return
        
        if self.db.update_box(self.selected_box,
                              quantity=qty,
                              unit=unit,
                              condition=condition,
                              status=status,
                              batch_number=batch,
                              uhf_tag_epc=uhf_epc or None):
            self._log(f"Box {self.selected_box} updated", "ok")
            messagebox.showinfo("Success", "Box updated!")
            self._clear_form()
            self._load_boxes()

    def _delete_box(self):
        if not self.selected_box:
            messagebox.showwarning("No Selection", "Select a box first!")
            return
        
        if not messagebox.askyesno("Confirm Delete",
            f"Delete box '{self.selected_box}'?\nThis cannot be undone!"):
            return
        
        if self.db.delete_box(self.selected_box):
            self._log(f"Box {self.selected_box} deleted", "warn")
            messagebox.showinfo("Success", "Box deleted!")
            self._clear_form()
            self._load_boxes()

    def _clear_form(self, refresh=True):
        for key, widget in self.fields.items():
            if key in ["unit", "condition", "container_id", "status"]:
                continue
            try:
                widget.configure(state="normal")
                widget.delete(0, tk.END)
            except Exception:
                pass
        
        self.unit_combo.set("PCS")
        self.condition_combo.set("GOOD")
        self.status_combo.set("IN_STOCK")
        
        if self.container_combo['values']:
            self.container_combo.set(self.container_combo['values'][0])
        
        self.item_label.configure(text="(select container)", fg=COLORS["text_muted"])
        self.box_info_var.set("Select a box to view info")
        
        self.selected_box = None
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        
        if refresh:
            self._log("Form cleared", "info")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-launcher', action='store_true')
    parser.add_argument('--user', type=str, default='standalone')
    parser.add_argument('--role', type=str, default='ADMIN')
    parser.add_argument('--name', type=str, default='Standalone User')
    args, _ = parser.parse_known_args()
    
    # Show login only if standalone
    if not args.from_launcher:
        try:
            sys.path.insert(0, os.path.join(BASE, '..'))
            from auth.login_window import show_login
            from auth.session import Session
            
            if not show_login():
                print("❌ Login cancelled")
                sys.exit(0)
        except Exception as e:
            print(f"⚠️ Running standalone: {e}")
    else:
        print(f"✅ Launched from main as: {args.name} ({args.role})")
    
    root = tk.Tk()
    app = BoxApp(root)  # ← Replace with your app class
    root.mainloop()