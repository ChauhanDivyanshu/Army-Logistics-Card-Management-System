# apps/shed_app.py
# 🏚️ SHED MANAGEMENT - Final Working Version

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS, FONTS


class ShedApp:

    def __init__(self, root):
        self.root = root
        self.root.title("SHED MANAGEMENT — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.selected_shed = None
        self.warehouse_map = {}
        self.fields = {}
        self.all_sheds = []

        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror("Database Error", f"Cannot connect!\n\n{msg}")
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_warehouses_dropdown()
        self._load_sheds()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", 
            foreground=COLORS["text"],
            rowheight=32,
            font=("Segoe UI", 10),
            fieldbackground="white",
            borderwidth=1)
        
        s.configure("Clean.Treeview.Heading",
            background=COLORS["primary"], 
            foreground="white",
            font=("Segoe UI", 10, "bold"), 
            padding=10,
            relief="flat",
            borderwidth=0)
        
        s.map("Clean.Treeview.Heading",
            background=[("active", COLORS["primary"]),
                        ("pressed", COLORS["primary_dark"]),
                        ("!active", COLORS["primary"])],
            foreground=[("active", "white"),
                        ("pressed", "white"),
                        ("!active", "white")],
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

        self._build_shed_list(main)
        self._build_form_panel(main)
        self._build_info_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="🏚",
                 font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="SHED MANAGEMENT",
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
        self.count_var = tk.StringVar(value="Total: 0 sheds")
        tk.Label(status, textvariable=self.count_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

    # ═══════════════════════════════════════════════════════
    # PANEL 1: ALL SHEDS (LEFT) - 600px
    # ═══════════════════════════════════════════════════════

    def _build_shed_list(self, parent):
        shed_container = tk.Frame(parent, bg=COLORS["bg"], width=560)
        shed_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        shed_container.pack_propagate(False)

        frame = tk.LabelFrame(shed_container, text="  ALL SHEDS  ",
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
        self.search_var.trace("w", lambda *a: self._filter_sheds())
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), relief=tk.SOLID, bd=1,
                 highlightthickness=1,
                 highlightbackground=COLORS["input_border"],
                 highlightcolor=COLORS["primary"]
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        # Table
        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        cols = ("shed_id", "name", "type", "containers", "boxes", "qty", "warehouse")
        self.tree = ttk.Treeview(tf, columns=cols,
            show="headings", style="Clean.Treeview")

        # Headers - all center aligned
        self.tree.heading("shed_id", text="Shed ID")
        self.tree.heading("name", text="Shed Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("containers", text="Cont.")
        self.tree.heading("boxes", text="Boxes")
        self.tree.heading("qty", text="Qty")
        self.tree.heading("warehouse", text="WH")

        # ✅ ALL columns center-aligned - headers match data perfectly
        self.tree.column("shed_id", width=68, anchor="center", stretch=False)
        self.tree.column("name", width=170, anchor="center", stretch=False)
        self.tree.column("type", width=70, anchor="center", stretch=False)
        self.tree.column("containers", width=57, anchor="center", stretch=False)
        self.tree.column("boxes", width=56, anchor="center", stretch=False)
        self.tree.column("qty", width=75, anchor="center", stretch=False)
        self.tree.column("warehouse", width=55, anchor="center", stretch=False)

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ═══════════════════════════════════════════════════════
    # PANEL 2: SHED DETAILS FORM (MIDDLE) - 340px
    # ═══════════════════════════════════════════════════════

    def _build_form_panel(self, parent):
        mid_frame = tk.Frame(parent, bg=COLORS["bg"], width=340)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        mid_frame.pack_propagate(False)

        form_box = tk.LabelFrame(mid_frame,
            text="  SHED DETAILS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        form_box.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        form_inner = tk.Frame(form_box, bg=COLORS["bg_card"])
        form_inner.pack(fill=tk.X, padx=2, pady=2)
        form_inner.columnconfigure(1, weight=1)

        self._add_field(form_inner, 0, "Shed ID:", "shed_id")
        self._add_field(form_inner, 1, "Shed Name:", "shed_name")
        
        tk.Label(form_inner, text="Warehouse:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=2, column=0, sticky="w", padx=8, pady=5)
        self.warehouse_combo = ttk.Combobox(form_inner, state="readonly",
            font=("Segoe UI", 10))
        self.warehouse_combo.grid(row=2, column=1, sticky="ew", padx=8, pady=5)
        self.fields["warehouse_id"] = self.warehouse_combo

        tk.Label(form_inner, text="Shed Type:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=3, column=0, sticky="w", padx=8, pady=5)
        self.type_combo = ttk.Combobox(form_inner,
            values=["Weapons", "Ammo", "Gear", "Vehicles", "Medical", "General"],
            font=("Segoe UI", 10))
        self.type_combo.set("General")
        self.type_combo.grid(row=3, column=1, sticky="ew", padx=8, pady=5)
        self.fields["shed_type"] = self.type_combo

        tk.Label(form_inner, text="Desc:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="nw").grid(row=4, column=0, sticky="nw", padx=8, pady=5)
        self.desc_text = tk.Text(form_inner, font=("Segoe UI", 10),
            relief=tk.SOLID, bd=1, height=2,
            highlightthickness=1,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["primary"])
        self.desc_text.grid(row=4, column=1, sticky="ew", padx=8, pady=5)

        tk.Label(form_inner, text="Status:",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg_card"], fg=COLORS["text"],
                 anchor="w").grid(row=5, column=0, sticky="w", padx=8, pady=5)
        self.status_combo = ttk.Combobox(form_inner,
            values=["ACTIVE", "INACTIVE", "MAINTENANCE"],
            state="readonly", font=("Segoe UI", 10))
        self.status_combo.set("ACTIVE")
        self.status_combo.grid(row=5, column=1, sticky="ew", padx=8, pady=5)
        self.fields["status"] = self.status_combo

        tk.Label(form_inner,
            text="Note: Sheds contain containers",
            font=("Segoe UI", 8, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"]
        ).grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(3, 5))

        # ACTIONS
        db_box = tk.LabelFrame(mid_frame, text="  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        db_box.pack(side=tk.TOP, fill=tk.X)

        db_inner = tk.Frame(db_box, bg=COLORS["bg_card"])
        db_inner.pack(fill=tk.X, padx=2, pady=2)

        actions = [
            ("ADD SHED", COLORS["success"], self._add_shed),
            ("UPDATE SELECTED", COLORS["info"], self._update_shed),
            ("DELETE SELECTED", COLORS["danger"], self._delete_shed),
            ("REFRESH", COLORS["warning"], self._load_sheds),
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
    # PANEL 3: CONTAINERS + ACTIVITY LOG (RIGHT) - EXPAND
    # ═══════════════════════════════════════════════════════

    def _build_info_panel(self, parent):
        # ✅ Expand to fill remaining space - NO blank area!
        right_frame = tk.Frame(parent, bg=COLORS["bg"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # CONTAINERS IN SHED
        cont_box = tk.LabelFrame(right_frame,
            text="  CONTAINERS IN SHED  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        cont_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        cont_inner = tk.Frame(cont_box, bg=COLORS["bg_card"])
        cont_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.cont_info_var = tk.StringVar(value="Select a shed to view")
        tk.Label(cont_inner, textvariable=self.cont_info_var,
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            wraplength=400, justify="left"
        ).pack(anchor="w", padx=8, pady=(8, 4))

        ctf = tk.Frame(cont_inner, bg=COLORS["bg_card"])
        ctf.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))

        ccols = ("cid", "item", "boxes", "qty")
        self.cont_tree = ttk.Treeview(ctf, columns=ccols,
            show="headings", style="Clean.Treeview", height=6)

        self.cont_tree.heading("cid", text="Container")
        self.cont_tree.heading("item", text="Item")
        self.cont_tree.heading("boxes", text="Boxes")
        self.cont_tree.heading("qty", text="Qty")

        # ✅ All center-aligned for proper alignment
        # ✅ Compact widths - tight spacing
        self.cont_tree.column("cid", width=90, anchor="center", stretch=False)
        self.cont_tree.column("item", width=90, anchor="center", stretch=False)
        self.cont_tree.column("boxes", width=55, anchor="center", stretch=False)
        self.cont_tree.column("qty", width=70, anchor="center", stretch=False)

        csb = ttk.Scrollbar(ctf, orient="vertical", command=self.cont_tree.yview)
        self.cont_tree.configure(yscrollcommand=csb.set)
        self.cont_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        csb.pack(side=tk.RIGHT, fill=tk.Y)

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
            relief=tk.FLAT, bd=0, wrap=tk.WORD,
            height=6)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

        self._log("Shed Management started", "ok")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Shed Management",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="Database: PostgreSQL",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗", "warn": "⚠"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(tk.END, f"[{ts}] {icons.get(level, '•')} {msg}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _load_warehouses_dropdown(self):
        warehouses = self.db.get_all_warehouses()
        self.warehouse_map = {}
        values = []
        for w in warehouses:
            display = f"{w['warehouse_id']} - {w['warehouse_name']}"
            values.append(display)
            self.warehouse_map[display] = w['warehouse_id']
        self.warehouse_combo['values'] = values
        if values:
            self.warehouse_combo.set(values[0])

    def _load_sheds(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        sheds = self.db.get_all_sheds()
        self.all_sheds = sheds
        
        for s in sheds:
            # ✅ Ensure string type
            shed_id = str(s['shed_id'])
            stats = self.db.get_shed_stats(shed_id) or {
                'total_containers': 0,
                'total_boxes': 0,
                'total_quantity': 0
            }
            
            self.tree.insert("", tk.END, values=(
                shed_id,  # ✅ string
                s['shed_name'],
                s.get('shed_type', '-') or '-',
                stats['total_containers'],
                stats['total_boxes'],
                stats['total_quantity'],
                s.get('warehouse_id', '-')
            ))
        
        self.count_var.set(f"Total: {len(sheds)} sheds")
        self._log(f"Loaded {len(sheds)} sheds", "ok") 
            

    def _filter_sheds(self):
        search = self.search_var.get().lower().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered = [s for s in self.all_sheds
            if search in str(s['shed_id']).lower()
            or search in s['shed_name'].lower()
            or (s.get('shed_type', '') or '').lower().find(search) >= 0]
        
        for s in filtered:
            # ✅ Ensure string
            shed_id = str(s['shed_id'])
            stats = self.db.get_shed_stats(shed_id) or {
                'total_containers': 0, 'total_boxes': 0, 'total_quantity': 0
            }
            self.tree.insert("", tk.END, values=(
                shed_id, s['shed_name'],
                s.get('shed_type', '-') or '-',
                stats['total_containers'],
                stats['total_boxes'],
                stats['total_quantity'],
                s.get('warehouse_id', '-')
            ))

    def _load_containers_for_shed(self, shed_id):
        for item in self.cont_tree.get_children():
            self.cont_tree.delete(item)
        
        # ✅ Ensure string type
        shed_id = str(shed_id)
        
        containers = self.db.get_containers_by_shed(shed_id)
        
        for c in containers:
            self.cont_tree.insert("", tk.END, values=(
                c['container_id'],
                c['item_name'],
                c['total_boxes'],
                c['total_quantity']
            ))
        
        self.cont_info_var.set(
            f"Shed {shed_id}: {len(containers)} container(s)")

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0])['values']
        self._clear_form(refresh=False)
        
        # ✅ Convert to string (Treeview auto-converts numeric IDs)
        shed_id = str(values[0])
        
        self.fields['shed_id'].insert(0, shed_id)
        self.fields['shed_name'].insert(0, values[1])
        
        shed = self.db.get_shed_by_id(shed_id)
        if shed:
            self.type_combo.set(shed.get('shed_type') or 'General')
            self.status_combo.set(shed.get('status', 'ACTIVE'))
            
            if shed.get('description'):
                self.desc_text.delete('1.0', tk.END)
                self.desc_text.insert('1.0', shed['description'])
            
            warehouse_id = shed.get('warehouse_id', '')
            for display, wid in self.warehouse_map.items():
                if wid == warehouse_id:
                    self.warehouse_combo.set(display)
                    break
        
        self.selected_shed = shed_id  # already string
        self.fields['shed_id'].configure(state="readonly")
        
        self._load_containers_for_shed(shed_id)
        self._log(f"Selected: {shed_id}", "info")

    def _get_warehouse_id(self):
        return self.warehouse_map.get(self.warehouse_combo.get(), "")

    def _add_shed(self):
        shed_id = self.fields['shed_id'].get().strip().upper()
        name = self.fields['shed_name'].get().strip()
        wid = self._get_warehouse_id()
        shed_type = self.type_combo.get().strip()
        description = self.desc_text.get('1.0', tk.END).strip()

        if not shed_id or not name or not wid:
            messagebox.showwarning("Required", "Shed ID, Name, and Warehouse are required!")
            return

        if self.db.get_shed_by_id(shed_id):
            messagebox.showerror("Duplicate", f"Shed ID '{shed_id}' already exists!")
            return

        if self.db.add_shed(shed_id, name, wid, shed_type, description):
            self._log(f"Shed {shed_id} added", "ok")
            messagebox.showinfo("Success", f"Shed added!\n\nID: {shed_id}\nName: {name}")
            self._clear_form()
            self._load_sheds()
        else:
            messagebox.showerror("Error", "Failed to add shed!")

    def _update_shed(self):
        if not self.selected_shed:
            messagebox.showwarning("No Selection", "Select a shed first!")
            return
        
        # ✅ Ensure string
        shed_id = str(self.selected_shed)
        
        name = self.fields['shed_name'].get().strip()
        shed_type = self.type_combo.get().strip()
        description = self.desc_text.get('1.0', tk.END).strip()
        status = self.status_combo.get()
        
        if not name:
            messagebox.showwarning("Required", "Shed Name is required!")
            return
        
        if not messagebox.askyesno("Confirm", f"Update shed '{shed_id}'?"):
            return
        
        if self.db.update_shed(shed_id,
                            shed_name=name, shed_type=shed_type,
                            description=description, status=status):
            self._log(f"Updated {shed_id}", "ok")
            messagebox.showinfo("Success", "Shed updated!")
            self._clear_form()
            self._load_sheds()
        else:
            messagebox.showerror("Error", "Failed to update shed!")

    def _delete_shed(self):
        if not self.selected_shed:
            messagebox.showwarning("No Selection", "Select a shed first!")
            return
        
        # ✅ Ensure string type
        shed_id = str(self.selected_shed)
        
        containers = self.db.get_containers_by_shed(shed_id)
        if containers:
            messagebox.showerror("Cannot Delete",
                f"Shed has {len(containers)} container(s)!\n"
                f"Delete or move containers first.")
            return
        
        if not messagebox.askyesno("Confirm Delete",
            f"Delete shed '{shed_id}'?\n\nThis cannot be undone!"):
            return
        
        if self.db.delete_shed(shed_id):
            self._log(f"Deleted {shed_id}", "warn")
            messagebox.showinfo("Success", "Shed deleted!")
            self._clear_form()
            self._load_sheds()
        else:
            messagebox.showerror("Error", "Failed to delete shed!")

    def _clear_form(self, refresh=True):
        for key, widget in self.fields.items():
            if key in ["status", "warehouse_id", "shed_type"]:
                continue
            try:
                widget.configure(state="normal")
                widget.delete(0, tk.END)
            except Exception:
                pass
        
        self.type_combo.set("General")
        self.status_combo.set("ACTIVE")
        self.desc_text.delete('1.0', tk.END)
        
        if self.warehouse_combo['values']:
            self.warehouse_combo.set(self.warehouse_combo['values'][0])
        
        self.selected_shed = None
        
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        
        for item in self.cont_tree.get_children():
            self.cont_tree.delete(item)
        self.cont_info_var.set("Select a shed to view")
        
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
    app = ShedApp(root)  # ← Replace with your app class
    root.mainloop()