# apps/container_app.py
# Container Tag Management App
# Database + MIFARE Card Integration
# Card pe sirf SKU-ID, baki sab database me

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time

# Add parent folders to path
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS, FONTS


# ═══════════════════════════════════════════════════════════
#  CONTAINER CARD - Simple data model
#  Card pe sirf SKU-ID write hota hai
# ═══════════════════════════════════════════════════════════

class ContainerCard:
    """
    Container card memory layout (Simple):
    ┌─────────┬──────────────────────────────────────────────┐
    │ Block 4 │ SKU-ID (16 bytes)                            │
    │ Block 5 │ Card Type Identifier "CONTAINER" (16 bytes)  │
    └─────────┴──────────────────────────────────────────────┘
    
    Baki sab info DATABASE se aati hai via SKU-ID lookup
    """

    def __init__(self):
        self.sku_id    = ""
        self.card_type = "CONTAINER"

    def write(self, core):
        """Write SKU-ID to card."""
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")

        # Block 4: SKU-ID
        core.write_block(4, core.encode(self.sku_id, 16))

        # Block 5: Card type identifier
        core.write_block(5, core.encode(self.card_type, 16))

        return True

    def read(self, core):
        """Read SKU-ID from card."""
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")

        # Read SKU-ID
        b4 = core.read_block(4)
        if b4:
            self.sku_id = core.decode(b4)

        # Read card type
        b5 = core.read_block(5)
        if b5:
            self.card_type = core.decode(b5)


# ═══════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════

class ContainerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Container Management — Army Logistics")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        # Initialize
        self.db = DatabaseHelper()
        self.selected_container = None
        self.warehouse_map = {}  # display_name -> warehouse_id

        # Test DB connection
        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror(
                "Database Error",
                f"Cannot connect to database!\n\n{msg}"
            )
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_warehouses_dropdown()
        self._load_containers()

    
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(
            "Custom.Treeview",
            background=COLORS["white"],
            foreground=COLORS["text"],
            rowheight=30,
            fieldbackground=COLORS["white"],
            font=FONTS["body"],
            borderwidth=0
        )
        s.configure(
            "Custom.Treeview.Heading",
            background=COLORS["primary"],
            foreground="white",
            font=FONTS["title"]
        )
        s.map("Custom.Treeview",
              background=[("selected", COLORS["secondary"])],
              foreground=[("selected", "white")])

    # ═══════════════════════════════════════════════════════
    # UI BUILD
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_status_bars()

        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Left: Container list
        self._build_container_list(main)

        # Middle: Form
        self._build_form_panel(main)

        # Right: Card operations + log
        self._build_card_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=16, pady=8)

        tk.Label(left, text="📦",
                 font=("Segoe UI Emoji", 24),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 10))

        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="CONTAINER TAG MANAGEMENT",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")
        tk.Label(tb,
                 text="Database + MIFARE Card  •  1 Container = 1 Item Type",
                 font=("Segoe UI", 8),
                 bg=COLORS["primary"], fg="#C8E6C9").pack(anchor="w")

        tk.Label(hdr, text="v1.0",
                 font=("Segoe UI", 8, "bold"),
                 bg=COLORS["primary"],
                 fg="#C8E6C9").pack(side=tk.RIGHT, padx=18)

    def _build_status_bars(self):
        # DB Status
        self.db_status = tk.Frame(
            self.root, bg=COLORS["success"], height=26
        )
        self.db_status.pack(fill=tk.X)
        self.db_status.pack_propagate(False)

        tk.Label(self.db_status, text="🗄  Database: Connected",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(
                     side=tk.LEFT, padx=14)

        self.count_var = tk.StringVar(value="Total: 0 containers")
        tk.Label(self.db_status, textvariable=self.count_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(
                     side=tk.RIGHT, padx=14)

        # Card Status
        self.card_status = tk.Frame(
            self.root, bg=COLORS["danger"], height=26
        )
        self.card_status.pack(fill=tk.X)
        self.card_status.pack_propagate(False)

        self.card_dot = tk.Label(
            self.card_status, text="●",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["danger"], fg="white"
        )
        self.card_dot.pack(side=tk.LEFT, padx=(14, 6))

        self.card_var = tk.StringVar(
            value="No Card Detected — Place card on reader"
        )
        self.card_lbl = tk.Label(
            self.card_status, textvariable=self.card_var,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="white"
        )
        self.card_lbl.pack(side=tk.LEFT)

        self.atr_var = tk.StringVar(value="ATR: --")
        self.atr_lbl = tk.Label(
            self.card_status, textvariable=self.atr_var,
            font=("Consolas", 8),
            bg=COLORS["danger"], fg="white"
        )
        self.atr_lbl.pack(side=tk.RIGHT, padx=14)

    # ── Left Panel: Container List ────────────────────────

    def _build_container_list(self, parent):
        left_frame = tk.LabelFrame(
            parent,
            text="  📋  ALL CONTAINERS (Database)  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=(0, 5))

        # Search
        search_frame = tk.Frame(left_frame, bg=COLORS["bg"])
        search_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(search_frame, text="🔍",
                 font=("Segoe UI", 11),
                 bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_containers())
        tk.Entry(search_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), relief=tk.SOLID,
                 bd=1, highlightbackground=COLORS["border"],
                 highlightthickness=1).pack(
                     side=tk.LEFT, fill=tk.X, expand=True)

        # Table
        tree_frame = tk.Frame(left_frame, bg=COLORS["white"])
        tree_frame.pack(fill=tk.BOTH, expand=True,
                        padx=8, pady=(0, 8))

        cols = ("sku", "name", "item", "boxes", "qty", "warehouse")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols,
            show="headings", style="Custom.Treeview"
        )

        self.tree.heading("sku",       text="SKU-ID")
        self.tree.heading("name",      text="Name")
        self.tree.heading("item",      text="Item")
        self.tree.heading("boxes",     text="Boxes")
        self.tree.heading("qty",       text="Total Qty")
        self.tree.heading("warehouse", text="Warehouse")

        self.tree.column("sku",       width=100, anchor="w")
        self.tree.column("name",      width=120, anchor="w")
        self.tree.column("item",      width=90,  anchor="w")
        self.tree.column("boxes",     width=60,  anchor="center")
        self.tree.column("warehouse", width=90,  anchor="center")

        sb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.tree.tag_configure("odd", background=COLORS["white"])
        self.tree.tag_configure("even", background=COLORS["row_alt"])

    # ── Middle Panel: Form ────────────────────────────────

    def _build_form_panel(self, parent):
        mid_frame = tk.Frame(parent, bg=COLORS["bg"], width=380)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        mid_frame.pack_propagate(False)

        # Form box
                # ═══ UHF TAG OPERATIONS (replaces MIFARE) ═══
        uhf_box = tk.LabelFrame(
            mid_frame,  # or wherever your card section is
            text="  📡  UHF TAG OPERATIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg="#7B1FA2",
            bd=1, relief=tk.GROOVE
        )
        uhf_box.pack(fill=tk.X, pady=(0, 6))

        uhf_inner = tk.Frame(uhf_box, bg=COLORS["white"])
        uhf_inner.pack(fill=tk.X, padx=6, pady=6)

        tk.Label(uhf_inner,
            text="💡 Containers don't have UHF tags themselves.\n"
                 "   Their boxes have UHF tags with SKU info.\n"
                 "   Use UHF Writer to manage box tags.",
            font=("Segoe UI", 8, "italic"),
            bg=COLORS["white"], fg=COLORS["muted"],
            justify="left").pack(anchor="w", padx=8, pady=(4, 8))

        tk.Button(uhf_inner, text="📡  WRITE UHF TAGS (Open UHF Writer)",
                   command=self._launch_uhf_writer,
                   font=("Segoe UI", 10, "bold"),
                   bg="#7B1FA2", fg="white",
                   relief=tk.FLAT, bd=0,
                   pady=10, cursor="hand2",
                   activebackground=COLORS["dark"],
                   activeforeground="white").pack(fill=tk.X, pady=2)

        self.warehouse_combo = ttk.Combobox(
            form_inner, state="readonly",
            font=("Segoe UI", 9)
        )
        self.warehouse_combo.grid(row=2, column=1, sticky="ew",
                                    padx=10, pady=5)
        self.fields["warehouse_id"] = self.warehouse_combo

        # Row 3: Item Name
        self._add_field(form_inner, 3, "Item Name:", "item_name")

        # Row 4: Total Boxes
        self._add_field(form_inner, 4, "Total Boxes:", "total_boxes")

        # Row 5: Total Quantity
        self._add_field(form_inner, 5,
                         "Total Quantity:", "total_quantity")

        # Row 6: Status
        tk.Label(form_inner, text="Status:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=6, column=0,
                                   sticky="w", padx=10, pady=5)

        self.status_combo = ttk.Combobox(
            form_inner,
            values=["ACTIVE", "SEALED", "DISPATCHED", "EMPTY"],
            state="readonly", font=("Segoe UI", 9)
        )
        self.status_combo.set("ACTIVE")
        self.status_combo.grid(row=6, column=1, sticky="ew",
                                padx=10, pady=5)
        self.fields["status"] = self.status_combo

        # Help text
        tk.Label(form_inner,
                 text="💡 Note: 1 container = 1 item type only\n"
                      "   (e.g., Container A = only AK47)",
                 font=("Segoe UI", 8, "italic"),
                 bg=COLORS["white"],
                 fg=COLORS["muted"],
                 justify="left").grid(
                     row=7, column=0, columnspan=2,
                     sticky="w", padx=10, pady=(8, 6))

        # Database Actions
        db_box = tk.LabelFrame(
            mid_frame,
            text="  🗄  DATABASE ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        db_box.pack(fill=tk.X, pady=(0, 6))

        db_inner = tk.Frame(db_box, bg=COLORS["white"])
        db_inner.pack(fill=tk.X, padx=6, pady=6)

        db_actions = [
            ("➕  ADD TO DATABASE",
             COLORS["success"], self._add_container),
            ("✏  UPDATE SELECTED",
             COLORS["info"], self._update_container),
            ("🗑  DELETE SELECTED",
             COLORS["danger"], self._delete_container),
            ("🔄  REFRESH",
             COLORS["warning"], self._load_containers),
            ("🧹  CLEAR FORM",
             COLORS["muted"], self._clear_form),
        ]

        for text, color, cmd in db_actions:
            tk.Button(db_inner, text=text, command=cmd,
                       font=("Segoe UI", 9, "bold"),
                       bg=color, fg="white",
                       relief=tk.FLAT, bd=0,
                       pady=8, cursor="hand2",
                       activebackground=COLORS["dark"],
                       activeforeground="white").pack(
                           fill=tk.X, pady=2)

    def _add_field(self, parent, row, label, key):
        """Helper to create label + entry row."""
        tk.Label(parent, text=label,
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=row, column=0,
                                   sticky="w", padx=10, pady=5)

        entry = tk.Entry(parent, font=("Segoe UI", 10),
                          relief=tk.SOLID, bd=1,
                          highlightbackground=COLORS["border"],
                          highlightthickness=1)
        entry.grid(row=row, column=1, sticky="ew",
                   padx=10, pady=5)
        self.fields[key] = entry

    # ── Right Panel: Card Operations + Log ────────────────

    def _build_card_panel(self, parent):
        right_frame = tk.Frame(parent, bg=COLORS["bg"], width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)

        # Card Operations
        card_box = tk.LabelFrame(
            right_frame,
            text="  💳  MIFARE CARD OPERATIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        card_box.pack(fill=tk.X, pady=(0, 6))

        card_inner = tk.Frame(card_box, bg=COLORS["white"])
        card_inner.pack(fill=tk.X, padx=6, pady=6)

        # Info text
        tk.Label(
            card_inner,
            text="💡 Card pe sirf SKU-ID write hota hai.\n"
                 "   Baki info database me rahegi.\n"
                 "   Scan karte hi DB se details load hongi.",
            font=("Segoe UI", 8),
            bg=COLORS["white"], fg=COLORS["muted"],
            justify="left"
        ).pack(anchor="w", padx=8, pady=(4, 8))

        card_actions = [
            ("💾  WRITE SKU TO CARD",
             COLORS["success"], self._write_to_card),
            ("📖  READ FROM CARD",
             COLORS["info"], self._read_from_card),
            ("🔍  VERIFY CARD ↔ DB",
             COLORS["warning"], self._verify_card_db),
        ]

        for text, color, cmd in card_actions:
            tk.Button(card_inner, text=text, command=cmd,
                       font=("Segoe UI", 10, "bold"),
                       bg=color, fg="white",
                       relief=tk.FLAT, bd=0,
                       pady=10, cursor="hand2",
                       activebackground=COLORS["dark"],
                       activeforeground="white").pack(
                           fill=tk.X, pady=3)

        # Activity Log
        log_box = tk.LabelFrame(
            right_frame,
            text="  📋  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        log_box.pack(fill=tk.BOTH, expand=True)

        log_inner = tk.Frame(log_box, bg=COLORS["white"])
        log_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.log_text = tk.Text(
            log_inner, font=("Consolas", 9),
            bg="#0d1117", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD,
            insertbackground="white"
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=24)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer,
                 text="© 2025 Indian Army  |  "
                      "Container Management Module",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.LEFT, padx=12, pady=4)
        tk.Label(footer,
                 text="DB: PostgreSQL  |  Card: MIFARE 1K",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.RIGHT, padx=12, pady=4)

    # ═══════════════════════════════════════════════════════
    # LOGGING
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

    # ═══════════════════════════════════════════════════════
    # CARD POLLING
    # ═══════════════════════════════════════════════════════

    def _poll_card(self):
        present = self.mifare.connect()
        if present and not self.card_present:
            atr = self.mifare.get_atr()
            self.atr_var.set(f"ATR: {atr}")
            self._set_card_status(
                "Card Detected — Ready", COLORS["success"])
            self._log("Card detected on reader", "ok")
            self.card_present = True
        elif not present and self.card_present:
            self.atr_var.set("ATR: --")
            self._set_card_status(
                "No Card Detected — Place card on reader",
                COLORS["danger"])
            self._log("Card removed", "warn")
            self.card_present = False
        self.mifare.disconnect()
        self.root.after(1500, self._poll_card)

    def _set_card_status(self, text, color):
        self.card_var.set(text)
        for w in [self.card_status, self.card_dot,
                  self.card_lbl, self.atr_lbl]:
            try:
                w.configure(bg=color)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _load_warehouses_dropdown(self):
        """Populate warehouse dropdown from DB."""
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

    def _load_containers(self):
        """Load all containers from database into table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        containers = self.db.get_all_containers()
        self.all_containers = containers

        for i, c in enumerate(containers):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    c['sku_id'],
                    c['container_name'],
                    c['item_name'],
                    c['total_boxes'],
                    c['total_quantity'],
                    c['warehouse_id']
                ),
                tags=(tag,)
            )

        self.count_var.set(f"Total: {len(containers)} containers")
        self._log(f"Loaded {len(containers)} containers from DB",
                   "ok")

    def _filter_containers(self):
        """Filter table based on search."""
        search = self.search_var.get().lower().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered = [
            c for c in self.all_containers
            if search in c['sku_id'].lower()
            or search in c['container_name'].lower()
            or search in c['item_name'].lower()
        ]

        for i, c in enumerate(filtered):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    c['sku_id'], c['container_name'],
                    c['item_name'], c['total_boxes'],
                    c['total_quantity'], c['warehouse_id']
                ),
                tags=(tag,)
            )

    def _on_select(self, event):
        """When user clicks a row, fill form."""
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])['values']

        self._clear_form(refresh=False)

        self.fields['sku_id'].insert(0, values[0])
        self.fields['container_name'].insert(0, values[1])
        self.fields['item_name'].insert(0, values[2])
        self.fields['total_boxes'].insert(0, values[3])
        self.fields['total_quantity'].insert(0, values[4])

        # Set warehouse dropdown
        warehouse_id = values[5]
        for display, wid in self.warehouse_map.items():
            if wid == warehouse_id:
                self.warehouse_combo.set(display)
                break

        # Get full container details for status
        container = self.db.get_container_by_id(values[0])
        if container:
            self.status_combo.set(container['status'])

        self.selected_container = values[0]

        # Make SKU readonly when editing
        self.fields['sku_id'].configure(state="readonly")

        self._log(f"Selected: {values[0]} ({values[2]})", "info")

    def _get_warehouse_id(self):
        """Get warehouse_id from dropdown selection."""
        selected = self.warehouse_combo.get()
        return self.warehouse_map.get(selected, "")

    def _add_container(self):
        """Add new container to database."""
        sku    = self.fields['sku_id'].get().strip()
        name   = self.fields['container_name'].get().strip()
        wid    = self._get_warehouse_id()
        item   = self.fields['item_name'].get().strip()
        boxes  = self.fields['total_boxes'].get().strip()
        qty    = self.fields['total_quantity'].get().strip()

        # Validation
        if not sku:
            messagebox.showwarning("Required", "SKU-ID is required!")
            self.fields['sku_id'].focus()
            return

        if not name:
            messagebox.showwarning("Required",
                                    "Container Name is required!")
            return

        if not wid:
            messagebox.showwarning("Required",
                                    "Please select a Warehouse!")
            return

        if not item:
            messagebox.showwarning("Required", "Item Name is required!")
            return

        # Parse numbers
        try:
            boxes = int(boxes) if boxes else 0
            qty   = int(qty) if qty else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Boxes and Quantity must be numbers!"
            )
            return

        # Check duplicate
        existing = self.db.get_container_by_id(sku)
        if existing:
            messagebox.showerror(
                "Duplicate",
                f"Container SKU '{sku}' already exists!\n\n"
                f"Use Update button to modify existing container."
            )
            return

        # Insert into database
        if self.db.add_container(sku, name, wid, item, boxes, qty):
            self._log(f"Container {sku} added to database", "ok")
            messagebox.showinfo(
                "Success",
                f"✅ Container added to database!\n\n"
                f"SKU-ID: {sku}\n"
                f"Name: {name}\n"
                f"Item: {item}\n"
                f"Warehouse: {wid}\n\n"
                f"💡 Now click 'WRITE SKU TO CARD' to\n"
                f"   program a MIFARE card for this container."
            )
            self._clear_form()
            self._load_containers()
        else:
            messagebox.showerror(
                "Error", "Failed to add container to database!"
            )
            self._log(f"Failed to add container {sku}", "err")

    def _update_container(self):
        """Update selected container."""
        if not self.selected_container:
            messagebox.showwarning(
                "No Selection",
                "Please select a container from the list first!"
            )
            return

        boxes = self.fields['total_boxes'].get().strip()
        qty   = self.fields['total_quantity'].get().strip()

        try:
            boxes = int(boxes) if boxes else 0
            qty   = int(qty) if qty else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Boxes and Quantity must be numbers!"
            )
            return

        if not messagebox.askyesno(
            "Confirm Update",
            f"Update container '{self.selected_container}'?"
        ):
            return

        # Update quantities (extend db_helper for full update)
        if self.db.update_container_quantity(
            self.selected_container, boxes, qty
        ):
            self._log(f"Container {self.selected_container} updated",
                       "ok")
            messagebox.showinfo(
                "Success", "✅ Container updated successfully!"
            )
            self._clear_form()
            self._load_containers()
        else:
            messagebox.showerror(
                "Error", "Failed to update container!"
            )

    def _delete_container(self):
        """Delete selected container."""
        if not self.selected_container:
            messagebox.showwarning(
                "No Selection",
                "Please select a container from the list first!"
            )
            return

        # Check if boxes exist
        boxes = self.db.get_boxes_by_container(self.selected_container)
        if boxes:
            messagebox.showerror(
                "Cannot Delete",
                f"❌ Container '{self.selected_container}' has "
                f"{len(boxes)} box(es)!\n\n"
                f"Delete or move all boxes first."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"⚠️  Delete container '{self.selected_container}'?\n\n"
            f"This action cannot be undone!"
        ):
            return

        if self.db.delete_container(self.selected_container):
            self._log(
                f"Container {self.selected_container} deleted", "warn"
            )
            messagebox.showinfo(
                "Success", "✅ Container deleted successfully!"
            )
            self._clear_form()
            self._load_containers()
        else:
            messagebox.showerror(
                "Error", "Failed to delete container!"
            )

    def _clear_form(self, refresh=True):
        """Clear all form fields."""
        for key, widget in self.fields.items():
            if key in ["status", "warehouse_id"]:
                continue
            try:
                widget.configure(state="normal")
                widget.delete(0, tk.END)
            except Exception:
                pass

        self.status_combo.set("ACTIVE")
        if self.warehouse_combo['values']:
            self.warehouse_combo.set(
                self.warehouse_combo['values'][0]
            )

        self.selected_container = None

        # Clear tree selection
        for item in self.tree.selection():
            self.tree.selection_remove(item)

        if refresh:
            self._log("Form cleared", "info")

    # ═══════════════════════════════════════════════════════
    # MIFARE CARD OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _write_to_card(self):
        """Write SKU-ID to MIFARE card."""
        sku = self.fields['sku_id'].get().strip()

        if not sku:
            messagebox.showwarning(
                "Required",
                "Please enter or select a SKU-ID first!"
            )
            return

        # Verify container exists in DB
        container = self.db.get_container_by_id(sku)
        if not container:
            if not messagebox.askyesno(
                "Not in Database",
                f"Container '{sku}' is not in database!\n\n"
                f"Do you still want to write it to card?"
            ):
                return

        # Check card present
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card",
                "Place MIFARE card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log(f"WRITING SKU-ID to card: {sku}", "info")

            card = ContainerCard()
            card.sku_id = sku
            card.write(self.mifare)

            self._log(f"✅ Card programmed with SKU: {sku}", "ok")

            # Show success with details
            info = f"✅ Card programmed successfully!\n\n"
            info += f"SKU-ID: {sku}\n"
            info += f"Card Type: CONTAINER\n\n"

            if container:
                info += f"📦 Container Details (from DB):\n"
                info += f"  Name: {container['container_name']}\n"
                info += f"  Item: {container['item_name']}\n"
                info += f"  Warehouse: {container['warehouse_name']}\n"
                info += f"  Boxes: {container['total_boxes']}\n"
                info += f"  Qty: {container['total_quantity']}"

            messagebox.showinfo("Success", info)

        except Exception as e:
            self._log(f"Write error: {e}", "err")
            messagebox.showerror("Write Error", str(e))
        finally:
            self.mifare.disconnect()

    def _read_from_card(self):
        """Read SKU-ID from card and load DB info."""
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card",
                "Place MIFARE card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log("READING container card...", "info")

            card = ContainerCard()
            card.read(self.mifare)

            if not card.sku_id:
                messagebox.showwarning(
                    "Empty Card",
                    "This card has no SKU-ID written on it!"
                )
                return

            self._log(f"Card SKU-ID: {card.sku_id}", "ok")
            self._log(f"Card Type: {card.card_type}", "ok")

            # Lookup in database
            container = self.db.get_container_by_id(card.sku_id)

            if container:
                self._log("✅ Container found in database", "ok")

                # Auto-fill form
                self._clear_form(refresh=False)
                self.fields['sku_id'].insert(0, container['sku_id'])
                self.fields['container_name'].insert(
                    0, container['container_name'])
                self.fields['item_name'].insert(
                    0, container['item_name'])
                self.fields['total_boxes'].insert(
                    0, str(container['total_boxes']))
                self.fields['total_quantity'].insert(
                    0, str(container['total_quantity']))

                # Set warehouse
                for display, wid in self.warehouse_map.items():
                    if wid == container['warehouse_id']:
                        self.warehouse_combo.set(display)
                        break

                self.status_combo.set(container['status'])
                self.selected_container = container['sku_id']
                self.fields['sku_id'].configure(state="readonly")

                # Show success popup
                self._show_container_details(container)

            else:
                self._log(
                    f"⚠ SKU '{card.sku_id}' not found in DB", "warn"
                )
                messagebox.showwarning(
                    "Not Found",
                    f"Card SKU-ID: {card.sku_id}\n\n"
                    f"❌ Not found in database!\n\n"
                    f"This card may be orphaned or from\n"
                    f"another system."
                )

        except Exception as e:
            self._log(f"Read error: {e}", "err")
            messagebox.showerror("Read Error", str(e))
        finally:
            self.mifare.disconnect()

    def _verify_card_db(self):
        """Verify card SKU matches database entry."""
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card", "Place card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log("VERIFYING card with database...", "info")

            card = ContainerCard()
            card.read(self.mifare)

            if not card.sku_id:
                messagebox.showwarning(
                    "Empty Card", "Card has no SKU-ID!"
                )
                return

            container = self.db.get_container_by_id(card.sku_id)

            if container:
                # Get boxes count from DB
                boxes = self.db.get_boxes_by_container(card.sku_id)

                msg = f"✅ VERIFICATION SUCCESSFUL\n\n"
                msg += f"{'─'*30}\n"
                msg += f"Card SKU-ID:  {card.sku_id}\n"
                msg += f"Card Type:    {card.card_type}\n"
                msg += f"{'─'*30}\n\n"
                msg += f"📦 Database Match:\n"
                msg += f"  Container:  {container['container_name']}\n"
                msg += f"  Item:       {container['item_name']}\n"
                msg += f"  Warehouse:  {container['warehouse_name']}\n"
                msg += f"  Location:   {container['location']}\n"
                msg += f"  Boxes:      {len(boxes)} actual / "
                msg += f"{container['total_boxes']} expected\n"
                msg += f"  Total Qty:  {container['total_quantity']}\n"
                msg += f"  Status:     {container['status']}"

                self._log("Card verified successfully", "ok")
                messagebox.showinfo("Verification OK", msg)
            else:
                self._log(
                    f"Card SKU not in DB: {card.sku_id}", "err"
                )
                messagebox.showerror(
                    "Verification Failed",
                    f"❌ Card SKU '{card.sku_id}' "
                    f"NOT found in database!\n\n"
                    f"This card may be invalid or removed."
                )

        except Exception as e:
            self._log(f"Verify error: {e}", "err")
            messagebox.showerror("Error", str(e))
        finally:
            self.mifare.disconnect()

    def _show_container_details(self, container):
        """Show detailed popup of container info from DB."""
        popup = tk.Toplevel(self.root)
        popup.title("Container Details (from Database)")
        popup.configure(bg=COLORS["bg"])
        popup.geometry("500x600")
        popup.grab_set()

        # Header
        hdr = tk.Frame(popup, bg=COLORS["primary"], height=54)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📦  CONTAINER VERIFIED",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["primary"],
                 fg="white").pack(pady=13)

        # Status banner
        stat = tk.Frame(popup, bg=COLORS["success"], height=34)
        stat.pack(fill=tk.X)
        stat.pack_propagate(False)
        tk.Label(stat,
                 text=f"✓  Card SKU matches Database Entry",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["success"],
                 fg="white").pack(pady=7)

        # Body
        body = tk.Frame(popup, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        def info_block(title, rows):
            frm = tk.LabelFrame(
                body, text=f"  {title}",
                font=("Segoe UI", 9, "bold"),
                bg=COLORS["white"],
                fg=COLORS["primary"],
                bd=1, relief=tk.GROOVE
            )
            frm.pack(fill=tk.X, pady=(0, 6))
            inner = tk.Frame(frm, bg=COLORS["white"])
            inner.pack(fill=tk.X, padx=8, pady=6)
            for lbl, val in rows:
                row = tk.Frame(inner, bg=COLORS["white"])
                row.pack(fill=tk.X, pady=2)
                tk.Label(row, text=f"{lbl}:",
                         font=("Segoe UI", 9),
                         bg=COLORS["white"],
                         fg=COLORS["muted"],
                         width=15,
                         anchor="w").pack(side=tk.LEFT)
                tk.Label(row, text=str(val) if val else "—",
                         font=("Segoe UI", 9, "bold"),
                         bg=COLORS["white"],
                         fg=COLORS["text"]).pack(side=tk.LEFT)

        # Container info
        info_block("📦  CONTAINER INFORMATION", [
            ("SKU-ID",         container['sku_id']),
            ("Container Name", container['container_name']),
            ("Item Name",      container['item_name']),
            ("Status",         container['status']),
        ])

        # Warehouse info
        info_block("🏭  WAREHOUSE LOCATION", [
            ("Warehouse ID",   container['warehouse_id']),
            ("Warehouse Name", container['warehouse_name']),
            ("Location",       container['location']),
        ])

        # Inventory info
        info_block("📊  INVENTORY", [
            ("Total Boxes",    container['total_boxes']),
            ("Total Quantity", container['total_quantity']),
        ])

        # Get boxes inside
        boxes = self.db.get_boxes_by_container(container['sku_id'])

        boxes_box = tk.LabelFrame(
            body,
            text=f"  🗃  BOXES INSIDE ({len(boxes)} total)  ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["white"],
            fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        boxes_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        boxes_inner = tk.Frame(boxes_box, bg=COLORS["white"])
        boxes_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        if boxes:
            box_text = tk.Text(
                boxes_inner, font=("Consolas", 9),
                bg="#F8FFF8", fg=COLORS["text"],
                relief=tk.FLAT, height=6
            )
            box_text.pack(fill=tk.BOTH, expand=True)

            for b in boxes:
                box_text.insert(
                    tk.END,
                    f"  {b['box_uid']:<12} | "
                    f"Qty: {b['quantity']:<5} {b['unit']} | "
                    f"Batch: {b['batch_number']}\n"
                )
            box_text.configure(state="disabled")
        else:
            tk.Label(boxes_inner,
                     text="No boxes added yet",
                     font=("Segoe UI", 9, "italic"),
                     bg=COLORS["white"],
                     fg=COLORS["muted"]).pack(pady=14)

        # Close button
        tk.Button(body, text="✓  CLOSE",
                   font=("Segoe UI", 10, "bold"),
                   bg=COLORS["primary"], fg="white",
                   relief=tk.FLAT, pady=10,
                   cursor="hand2",
                   command=popup.destroy).pack(fill=tk.X, pady=(4, 0))
        
        
    def _launch_uhf_writer(self):
        """Launch UHF Writer App for selected box's container."""
        # Get selected container from selected box
        if not self.selected_box:
            messagebox.showwarning("Select Box",
                "Please select a box first!")
            return
        
        # Get the SKU/container for this box
        sku = self.selected_box.get('container_id', 'Unknown')
        
        if not messagebox.askyesno("Launch UHF Writer",
            f"Open UHF Writer App?\n\n"
            f"Container: {sku}\n"
            f"Box: {self.selected_box.get('box_uid')}\n\n"
            f"You can write UHF tags there."):
            return
        
        import subprocess
        import sys
        
        BASE = os.path.dirname(os.path.abspath(__file__))
        uhf_app = os.path.join(BASE, 'uhf_writer_app.py')
        
        if os.path.exists(uhf_app):
            try:
                subprocess.Popen([sys.executable, uhf_app])
                self._log(f"✓ Launched UHF Writer", "ok")
                messagebox.showinfo("Launched",
                    f"UHF Writer App opened!\n\n"
                    f"Select container '{sku}'\n"
                    f"and write tags for boxes.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch: {e}")
        else:
            messagebox.showerror("Not Found",
                f"UHF Writer app not found!")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = ContainerApp(root)
    root.mainloop()