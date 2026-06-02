# apps/container_app.py
# 📦 CONTAINER MANAGEMENT - With Shed Assignment + UHF Integration
# Hierarchy: Warehouse → Shed → Container → Box

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


class ContainerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("CONTAINER MANAGEMENT — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.selected_container = None
        self.shed_map = {}        # display → shed_id
        self.shed_filter_map = {} # for filter dropdown
        self.fields = {}
        self.all_containers = []

        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror("Database Error", f"Cannot connect!\n\n{msg}")
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_sheds_dropdown()
        self._load_containers()

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
        
        # Combobox styling
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

    # ═══════════════════════════════════════════════════════
    # UI BUILD
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_status_bar()

        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self._build_container_list(main)
        self._build_form_panel(main)
        self._build_actions_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="📦", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="CONTAINER MANAGEMENT",
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
        self.count_var = tk.StringVar(value="Total: 0 containers")
        tk.Label(status, textvariable=self.count_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

    # ═══════════════════════════════════════════════════════
    # PANEL 1: ALL CONTAINERS (LEFT)
    # ═══════════════════════════════════════════════════════

    def _build_container_list(self, parent):
        # Fixed width container
        list_container = tk.Frame(parent, bg=COLORS["bg"], width=650)
        list_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        list_container.pack_propagate(False)

        frame = tk.LabelFrame(list_container, text="  ALL CONTAINERS  ",
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
        self.search_var.trace("w", lambda *a: self._filter_containers())
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), relief=tk.SOLID, bd=1,
                 highlightthickness=1,
                 highlightbackground=COLORS["input_border"],
                 highlightcolor=COLORS["primary"]
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        # ✅ NEW: Filter by Shed
        filter_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        filter_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(filter_frame, text="Shed:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(0, 6))
        self.shed_filter_combo = ttk.Combobox(filter_frame, state="readonly",
                                                font=("Segoe UI", 9))
        self.shed_filter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.shed_filter_combo.bind("<<ComboboxSelected>>",
                                      lambda e: self._filter_containers())

        # Table
        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        cols = ("sku", "name", "shed", "item", "boxes", "qty")
        self.tree = ttk.Treeview(tf, columns=cols,
            show="headings", style="Clean.Treeview")

        self.tree.heading("sku", text="Container ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("shed", text="Shed")
        self.tree.heading("item", text="Item")
        self.tree.heading("boxes", text="Boxes")
        self.tree.heading("qty", text="Qty")

        # All center-aligned for proper alignment
        self.tree.column("sku", width=95, anchor="center", stretch=False)
        self.tree.column("name", width=140, anchor="center", stretch=False)
        self.tree.column("shed", width=70, anchor="center", stretch=False)
        self.tree.column("item", width=110, anchor="center", stretch=False)
        self.tree.column("boxes", width=70, anchor="center", stretch=False)
        self.tree.column("qty", width=85, anchor="center", stretch=False)

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ═══════════════════════════════════════════════════════
    # PANEL 2: CONTAINER DETAILS FORM (MIDDLE)
    # ═══════════════════════════════════════════════════════

    def _build_form_panel(self, parent):
        mid_frame = tk.Frame(parent, bg=COLORS["bg"], width=380)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        mid_frame.pack_propagate(False)

        # FORM
        form_box = tk.LabelFrame(mid_frame,
            text="  CONTAINER DETAILS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        form_box.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        form_inner = tk.Frame(form_box, bg=COLORS["bg_card"])
        form_inner.pack(fill=tk.X, padx=2, pady=2)
        form_inner.columnconfigure(1, weight=1)

        # Container ID
        self._add_field(form_inner, 0, "Container ID:", "container_id")
        # Container Name
        self._add_field(form_inner, 1, "Name:", "container_name")
        
        # ✅ NEW: Shed dropdown (container belongs to shed)
        tk.Label(form_inner, text="Shed:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=2, column=0, sticky="w", padx=8, pady=5)
        self.shed_combo = ttk.Combobox(form_inner, state="readonly",
            font=("Segoe UI", 10))
        self.shed_combo.grid(row=2, column=1, sticky="ew", padx=8, pady=5)
        self.fields["shed_id"] = self.shed_combo

        # Item Name
        self._add_field(form_inner, 3, "Item Name:", "item_name")
        
        # Auto-calculated info
        tk.Label(form_inner, text="Boxes:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=4, column=0, sticky="w", padx=8, pady=5)
        self.boxes_label = tk.Label(form_inner, text="0 (auto)",
                                     font=("Segoe UI", 10, "bold"),
                                     bg=COLORS["bg_card"],
                                     fg=COLORS["primary"], anchor="w")
        self.boxes_label.grid(row=4, column=1, sticky="ew", padx=8, pady=5)
        
        tk.Label(form_inner, text="Quantity:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=5, column=0, sticky="w", padx=8, pady=5)
        self.qty_label = tk.Label(form_inner, text="0 (auto)",
                                   font=("Segoe UI", 10, "bold"),
                                   bg=COLORS["bg_card"],
                                   fg=COLORS["primary"], anchor="w")
        self.qty_label.grid(row=5, column=1, sticky="ew", padx=8, pady=5)

        # Status
        tk.Label(form_inner, text="Status:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=6, column=0, sticky="w", padx=8, pady=5)
        self.status_combo = ttk.Combobox(form_inner,
            values=["ACTIVE", "SEALED", "DISPATCHED", "EMPTY"],
            state="readonly", font=("Segoe UI", 10))
        self.status_combo.set("ACTIVE")
        self.status_combo.grid(row=6, column=1, sticky="ew", padx=8, pady=5)
        self.fields["status"] = self.status_combo

        # Help
        tk.Label(form_inner,
            text="Note: 1 container = 1 item type\nTotals auto-calculated from boxes",
            font=("Segoe UI", 8, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left").grid(row=7, column=0, columnspan=2,
                sticky="w", padx=8, pady=(5, 8))

        # ACTIONS
        db_box = tk.LabelFrame(mid_frame, text="  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        db_box.pack(side=tk.TOP, fill=tk.X)

        db_inner = tk.Frame(db_box, bg=COLORS["bg_card"])
        db_inner.pack(fill=tk.X, padx=2, pady=2)

        actions = [
            ("ADD CONTAINER", COLORS["success"], self._add_container),
            ("UPDATE / MOVE SHED", COLORS["info"], self._update_container),
            ("DELETE SELECTED", COLORS["danger"], self._delete_container),
            ("REFRESH", COLORS["warning"], self._load_containers),
            ("CLEAR FORM", COLORS["text_muted"], self._clear_form),
        ]

        for text, color, cmd in actions:
            tk.Button(db_inner, text=text, command=cmd,
                font=("Segoe UI", 10, "bold"),
                bg=color, fg="white",
                relief=tk.FLAT, bd=0,
                pady=5, cursor="hand2",
                activebackground=COLORS["primary_dark"],
                activeforeground="white").pack(fill=tk.X, padx=8, pady=1)

    def _add_field(self, parent, row, label, key):
        tk.Label(parent, text=label,
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["text"],
            anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        entry = tk.Entry(parent, font=("Segoe UI", 10),
            relief=tk.SOLID, bd=1,
            highlightthickness=1,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["primary"])
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=5, ipady=3)
        self.fields[key] = entry

    # ═══════════════════════════════════════════════════════
    # PANEL 3: UHF + ACTIVITY LOG (RIGHT)
    # ═══════════════════════════════════════════════════════

    def _build_actions_panel(self, parent):
        right_frame = tk.Frame(parent, bg=COLORS["bg"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

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
            text="Containers don't have UHF tags themselves.\n"
                 "Their boxes have UHF tags with SKU info.\n"
                 "Use UHF Writer to manage box tags.",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left").pack(anchor="w", padx=10, pady=(10, 10))

        tk.Button(uhf_inner,
            text="OPEN UHF WRITER",
            command=self._launch_uhf_writer,
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"], fg="white",
            relief=tk.FLAT, bd=0,
            pady=12, cursor="hand2",
            activebackground=COLORS["primary_dark"],
            activeforeground="white").pack(fill=tk.X, padx=10, pady=(0, 10))

        # SHED INFO (for selected container)
        info_box = tk.LabelFrame(right_frame,
            text="  SHED INFO  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        info_box.pack(fill=tk.X, pady=(0, 6))

        info_inner = tk.Frame(info_box, bg=COLORS["bg_card"])
        info_inner.pack(fill=tk.X, padx=2, pady=2)

        self.shed_info_var = tk.StringVar(value="Select a container to view shed info")
        tk.Label(info_inner, textvariable=self.shed_info_var,
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

        self._log("Container Management started", "ok")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Container Management",
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
        
        confirm_msg = "Open UHF Writer App?"
        if self.selected_container:
            confirm_msg += f"\n\nSelected: {self.selected_container}"
        
        if not messagebox.askyesno("Launch UHF Writer", confirm_msg):
            return
        
        try:
            subprocess.Popen([sys.executable, uhf_app])
            self._log("Launched UHF Writer", "ok")
            messagebox.showinfo("Launched",
                "UHF Writer App opened!\n\n"
                "Select container and write tags for boxes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch: {e}")

    # ═══════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _load_sheds_dropdown(self):
        """Load sheds for both form dropdown and filter dropdown."""
        sheds = self.db.get_all_sheds()
        
        # Form dropdown (no "all" option)
        self.shed_map = {}
        form_values = []
        for s in sheds:
            display = f"{s['shed_id']} - {s['shed_name']}"
            form_values.append(display)
            self.shed_map[display] = s['shed_id']
        
        self.shed_combo['values'] = form_values
        if form_values:
            self.shed_combo.set(form_values[0])
        
        # Filter dropdown (with "All Sheds")
        self.shed_filter_map = {}
        filter_values = ["All Sheds"]
        for s in sheds:
            display = f"{s['shed_id']} - {s['shed_name']}"
            filter_values.append(display)
            self.shed_filter_map[display] = s['shed_id']
        
        self.shed_filter_combo['values'] = filter_values
        self.shed_filter_combo.set("All Sheds")

    def _load_containers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        containers = self.db.get_all_containers()
        self.all_containers = containers
        
        for c in containers:
            self.tree.insert("", tk.END, values=(
                c['container_id'],
                c['container_name'],
                c.get('shed_id', '-') or '-',
                c['item_name'],
                c['total_boxes'],
                c['total_quantity']
            ))
        
        self.count_var.set(f"Total: {len(containers)} containers")
        self._log(f"Loaded {len(containers)} containers", "ok")

    def _filter_containers(self):
        search = self.search_var.get().lower().strip()
        shed_filter = self.shed_filter_combo.get()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered = self.all_containers
        
        # Filter by shed
        if shed_filter and shed_filter != "All Sheds":
            shed_id = self.shed_filter_map.get(shed_filter)
            if shed_id:
                filtered = [c for c in filtered if c.get('shed_id') == shed_id]
        
        # Filter by search
        if search:
            filtered = [c for c in filtered
                if search in c['container_id'].lower()
                or search in c['container_name'].lower()
                or search in c['item_name'].lower()]
        
        for c in filtered:
            self.tree.insert("", tk.END, values=(
                c['container_id'],
                c['container_name'],
                c.get('shed_id', '-') or '-',
                c['item_name'],
                c['total_boxes'],
                c['total_quantity']
            ))
        
        self.count_var.set(f"Showing: {len(filtered)} of {len(self.all_containers)}")

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0])['values']
        self._clear_form(refresh=False)
        
        self.fields['container_id'].insert(0, values[0])
        self.fields['container_name'].insert(0, values[1])
        self.fields['item_name'].insert(0, values[3])
        
        # Show auto-calculated values
        self.boxes_label.configure(text=f"{values[4]} (auto)")
        self.qty_label.configure(text=f"{values[5]} (auto)")
        
        # Set shed dropdown
        shed_id = values[2]
        for display, sid in self.shed_map.items():
            if sid == shed_id:
                self.shed_combo.set(display)
                break
        
        # Get full container details
        container = self.db.get_container_by_id(values[0])
        if container:
            self.status_combo.set(container.get('status', 'ACTIVE'))
            
            # Show shed info
            shed_name = container.get('shed_name', 'Unknown')
            warehouse_name = container.get('warehouse_name', 'Unknown')
            info_text = (
                f"📦 Container: {values[0]}\n"
                f"🏚️ Shed: {shed_id} ({shed_name})\n"
                f"🏛️ Warehouse: {warehouse_name}\n"
                f"📊 Stock: {values[4]} boxes, {values[5]} qty"
            )
            self.shed_info_var.set(info_text)
        
        self.selected_container = values[0]
        self.fields['container_id'].configure(state="readonly")
        self._log(f"Selected: {values[0]}", "info")

    def _get_shed_id(self):
        return self.shed_map.get(self.shed_combo.get(), "")

    def _add_container(self):
        container_id = self.fields['container_id'].get().strip().upper()
        name = self.fields['container_name'].get().strip()
        shed_id = self._get_shed_id()
        item = self.fields['item_name'].get().strip()

        if not container_id or not name or not shed_id or not item:
            messagebox.showwarning("Required",
                "Container ID, Name, Shed, and Item Name are required!")
            return

        if self.db.get_container_by_id(container_id):
            messagebox.showerror("Duplicate", f"Container '{container_id}' already exists!")
            return

        if self.db.add_container(container_id, name, shed_id, item):
            self._log(f"Container {container_id} added in shed {shed_id}", "ok")
            messagebox.showinfo("Success",
                f"Container added!\n\n"
                f"ID: {container_id}\n"
                f"Shed: {shed_id}\n"
                f"Item: {item}\n\n"
                f"Now add boxes in Box Management.")
            self._clear_form()
            self._load_containers()
        else:
            messagebox.showerror("Error", "Failed to add container!")

    def _update_container(self):
        """Update container - including MOVE between sheds."""
        if not self.selected_container:
            messagebox.showwarning("No Selection", "Select a container first!")
            return
        
        name = self.fields['container_name'].get().strip()
        new_shed_id = self._get_shed_id()
        item = self.fields['item_name'].get().strip()
        status = self.status_combo.get()
        
        if not name or not new_shed_id or not item:
            messagebox.showwarning("Required",
                "Name, Shed, and Item Name are required!")
            return
        
        # Check if shed is being changed
        current = self.db.get_container_by_id(self.selected_container)
        current_shed = current.get('shed_id', '') if current else ''
        is_moving = current_shed != new_shed_id
        
        if is_moving:
            confirm_msg = (f"MOVE container '{self.selected_container}'?\n\n"
                          f"From Shed: {current_shed}\n"
                          f"To Shed:   {new_shed_id}\n\n"
                          f"All boxes will move with the container.")
        else:
            confirm_msg = f"Update '{self.selected_container}'?"
        
        if not messagebox.askyesno("Confirm", confirm_msg):
            return
        
        if self.db.update_container(self.selected_container,
                                     container_name=name,
                                     shed_id=new_shed_id,
                                     item_name=item,
                                     status=status):
            if is_moving:
                self._log(f"Moved {self.selected_container}: {current_shed} → {new_shed_id}", "ok")
                messagebox.showinfo("Moved", 
                    f"Container moved successfully!\n\n"
                    f"{self.selected_container}\n"
                    f"{current_shed} → {new_shed_id}")
            else:
                self._log(f"Updated {self.selected_container}", "ok")
                messagebox.showinfo("Success", "Container updated!")
            self._clear_form()
            self._load_containers()
        else:
            messagebox.showerror("Error", "Failed to update container!")

    def _delete_container(self):
        if not self.selected_container:
            messagebox.showwarning("No Selection", "Select a container first!")
            return
        
        boxes = self.db.get_boxes_by_container(self.selected_container)
        if boxes:
            messagebox.showerror("Cannot Delete",
                f"Container has {len(boxes)} box(es)!\n"
                f"Delete boxes first from Box Management.")
            return
        
        if not messagebox.askyesno("Confirm Delete",
            f"Delete '{self.selected_container}'?\nThis cannot be undone!"):
            return
        
        if self.db.delete_container(self.selected_container):
            self._log(f"Deleted {self.selected_container}", "warn")
            messagebox.showinfo("Success", "Container deleted!")
            self._clear_form()
            self._load_containers()

    def _clear_form(self, refresh=True):
        for key, widget in self.fields.items():
            if key in ["status", "shed_id"]:
                continue
            try:
                widget.configure(state="normal")
                widget.delete(0, tk.END)
            except Exception:
                pass
        
        self.status_combo.set("ACTIVE")
        if self.shed_combo['values']:
            self.shed_combo.set(self.shed_combo['values'][0])
        
        self.boxes_label.configure(text="0 (auto)")
        self.qty_label.configure(text="0 (auto)")
        self.shed_info_var.set("Select a container to view shed info")
        
        self.selected_container = None
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        
        if refresh:
            self._log("Form cleared", "info")


if __name__ == "__main__":
    root = tk.Tk()
    app = ContainerApp(root)
    root.mainloop()