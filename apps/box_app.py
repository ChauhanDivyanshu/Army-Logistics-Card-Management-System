# apps/box_app.py
# Box Tag Management App
# Database + MIFARE Card Integration

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
from mifare_core import MifareCore


# ═══════════════════════════════════════════════════════════
#  BOX CARD - Simple data model
# ═══════════════════════════════════════════════════════════

class BoxCard:
    """
    Box card memory layout (Simple):
    ┌─────────┬──────────────────────────────────────────────┐
    │ Block 4 │ Box UID (16 bytes)                           │
    │ Block 5 │ Card Type "BOX" (16 bytes)                   │
    └─────────┴──────────────────────────────────────────────┘
    
    Baki sab info DATABASE se aati hai via Box UID lookup
    """

    def __init__(self):
        self.box_uid   = ""
        self.card_type = "BOX"

    def write(self, core):
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")
        core.write_block(4, core.encode(self.box_uid, 16))
        core.write_block(5, core.encode(self.card_type, 16))
        return True

    def read(self, core):
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")
        b4 = core.read_block(4)
        if b4:
            self.box_uid = core.decode(b4)
        b5 = core.read_block(5)
        if b5:
            self.card_type = core.decode(b5)


# ═══════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════

class BoxApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Box Tag Management — Army Logistics")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        # Initialize
        self.db = DatabaseHelper()
        self.mifare = MifareCore(self._log)
        self.selected_box = None
        self.card_present = False
        self.container_map = {}  # display_name -> sku_id

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
        self._load_containers_dropdown()
        self._load_boxes()

        # Start card polling
        self.mifare.find_reader()
        self._poll_card()

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

        self._build_box_list(main)
        self._build_form_panel(main)
        self._build_card_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=16, pady=8)

        tk.Label(left, text="🗃",
                 font=("Segoe UI Emoji", 24),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 10))

        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="BOX TAG MANAGEMENT",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")
        tk.Label(tb,
                 text="Database + MIFARE Card  •  Individual Box Tracking",
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

        self.count_var = tk.StringVar(value="Total: 0 boxes")
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

    # ── Left Panel: Box List ──────────────────────────────

    def _build_box_list(self, parent):
        left_frame = tk.LabelFrame(
            parent,
            text="  📋  ALL BOXES (Database)  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=(0, 5))

        # Filter bar
        filter_frame = tk.Frame(left_frame, bg=COLORS["bg"])
        filter_frame.pack(fill=tk.X, padx=8, pady=8)

        # Search
        tk.Label(filter_frame, text="🔍",
                 font=("Segoe UI", 11),
                 bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_boxes())
        tk.Entry(filter_frame, textvariable=self.search_var,
                 font=("Segoe UI", 10), relief=tk.SOLID,
                 bd=1, highlightbackground=COLORS["border"],
                 highlightthickness=1).pack(
                     side=tk.LEFT, fill=tk.X, expand=True)

        # Container filter
        filter_frame2 = tk.Frame(left_frame, bg=COLORS["bg"])
        filter_frame2.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Label(filter_frame2, text="Filter by Container:",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side=tk.LEFT, padx=(0, 6))

        self.filter_combo = ttk.Combobox(
            filter_frame2, state="readonly",
            font=("Segoe UI", 9), width=18
        )
        self.filter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.filter_combo.bind("<<ComboboxSelected>>",
                                lambda e: self._filter_boxes())

        # Table
        tree_frame = tk.Frame(left_frame, bg=COLORS["white"])
        tree_frame.pack(fill=tk.BOTH, expand=True,
                        padx=8, pady=(0, 8))

        cols = ("uid", "container", "item", "qty", "unit",
                "condition", "batch")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols,
            show="headings", style="Custom.Treeview"
        )

        self.tree.heading("uid",       text="Box UID")
        self.tree.heading("container", text="Container")
        self.tree.heading("item",      text="Item")
        self.tree.heading("qty",       text="Qty")
        self.tree.heading("unit",      text="Unit")
        self.tree.heading("condition", text="Condition")
        self.tree.heading("batch",     text="Batch")

        self.tree.column("uid",       width=90,  anchor="w")
        self.tree.column("container", width=100, anchor="w")
        self.tree.column("item",      width=80,  anchor="w")
        self.tree.column("qty",       width=50,  anchor="center")
        self.tree.column("unit",      width=50,  anchor="center")
        self.tree.column("condition", width=70,  anchor="center")
        self.tree.column("batch",     width=110, anchor="w")

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
        form_box = tk.LabelFrame(
            mid_frame,
            text="  ➕  BOX DETAILS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        form_box.pack(fill=tk.X, pady=(0, 6))

        form_inner = tk.Frame(form_box, bg=COLORS["white"])
        form_inner.pack(fill=tk.X, padx=4, pady=4)
        form_inner.columnconfigure(1, weight=1)

        self.fields = {}

        # Row 0: Box UID
        self._add_field(form_inner, 0, "Box UID:", "box_uid")

        # Row 1: Container dropdown
        tk.Label(form_inner, text="Container:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=1, column=0,
                                   sticky="w", padx=10, pady=5)

        self.container_combo = ttk.Combobox(
            form_inner, state="readonly",
            font=("Segoe UI", 9)
        )
        self.container_combo.grid(row=1, column=1, sticky="ew",
                                    padx=10, pady=5)
        self.container_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._on_container_select()
        )
        self.fields["container_id"] = self.container_combo

        # Row 2: Item Name (auto-filled from container)
        tk.Label(form_inner, text="Item Name:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=2, column=0,
                                   sticky="w", padx=10, pady=5)

        self.item_label = tk.Label(
            form_inner, text="(select container)",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["white"],
            fg=COLORS["info"],
            anchor="w"
        )
        self.item_label.grid(row=2, column=1, sticky="ew",
                              padx=10, pady=5)

        # Row 3: Quantity
        self._add_field(form_inner, 3, "Quantity:", "quantity")

        # Row 4: Unit
        tk.Label(form_inner, text="Unit:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=4, column=0,
                                   sticky="w", padx=10, pady=5)

        self.unit_combo = ttk.Combobox(
            form_inner,
            values=["PCS", "KG", "LTR", "MTR", "BOX", "SET"],
            state="readonly", font=("Segoe UI", 9)
        )
        self.unit_combo.set("PCS")
        self.unit_combo.grid(row=4, column=1, sticky="ew",
                              padx=10, pady=5)
        self.fields["unit"] = self.unit_combo

        # Row 5: Condition
        tk.Label(form_inner, text="Condition:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["text"],
                 anchor="w").grid(row=5, column=0,
                                   sticky="w", padx=10, pady=5)

        self.condition_combo = ttk.Combobox(
            form_inner,
            values=["GOOD", "DAMAGED", "EXPIRED", "SEALED"],
            state="readonly", font=("Segoe UI", 9)
        )
        self.condition_combo.set("GOOD")
        self.condition_combo.grid(row=5, column=1, sticky="ew",
                                    padx=10, pady=5)
        self.fields["condition"] = self.condition_combo

        # Row 6: Batch Number
        self._add_field(form_inner, 6, "Batch Number:", "batch_number")

        # Help text
        tk.Label(form_inner,
                 text="💡 Note: Box item is determined by\n"
                      "   the selected container's item type.",
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
            ("➕  ADD BOX TO DATABASE",
             COLORS["success"], self._add_box),
            ("✏  UPDATE SELECTED",
             COLORS["info"], self._update_box),
            ("🗑  DELETE SELECTED",
             COLORS["danger"], self._delete_box),
            ("🔄  REFRESH",
             COLORS["warning"], self._load_boxes),
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

    # ── Right Panel: Card + Log ───────────────────────────

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

        tk.Label(
            card_inner,
            text="💡 Card pe sirf Box UID write hota hai.\n"
                 "   Item, qty, container info DB se aati hai.",
            font=("Segoe UI", 8),
            bg=COLORS["white"], fg=COLORS["muted"],
            justify="left"
        ).pack(anchor="w", padx=8, pady=(4, 8))

        card_actions = [
            ("💾  WRITE UID TO CARD",
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
                 text="© 2025 Indian Army  |  Box Tag Module",
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

    def _load_containers_dropdown(self):
        """Load containers into dropdowns."""
        containers = self.db.get_all_containers()
        self.container_map = {}
        self.container_info = {}  # sku_id -> full container data

        values = ["-- Select Container --"]
        filter_values = ["All Containers"]

        for c in containers:
            display = f"{c['sku_id']} ({c['item_name']})"
            values.append(display)
            filter_values.append(display)
            self.container_map[display] = c['sku_id']
            self.container_info[c['sku_id']] = c

        self.container_combo['values'] = values
        if values:
            self.container_combo.set(values[0])

        self.filter_combo['values'] = filter_values
        self.filter_combo.set(filter_values[0])

    def _on_container_select(self):
        """Update item label when container selected."""
        selected = self.container_combo.get()
        sku_id = self.container_map.get(selected)

        if sku_id and sku_id in self.container_info:
            container = self.container_info[sku_id]
            self.item_label.configure(
                text=f"{container['item_name']} "
                     f"(from {container['container_name']})",
                fg=COLORS["info"]
            )
        else:
            self.item_label.configure(
                text="(select container)",
                fg=COLORS["muted"]
            )

    def _load_boxes(self):
        """Load all boxes from database."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        boxes = self.db.get_all_boxes()
        self.all_boxes = boxes

        for i, b in enumerate(boxes):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    b['box_uid'],
                    b['container_id'],
                    b.get('item_name', '-'),
                    b['quantity'],
                    b['unit'],
                    b['condition'],
                    b.get('batch_number', '-')
                ),
                tags=(tag,)
            )

        self.count_var.set(f"Total: {len(boxes)} boxes")
        self._log(f"Loaded {len(boxes)} boxes from DB", "ok")

    def _filter_boxes(self):
        """Filter boxes by search and container."""
        search = self.search_var.get().lower().strip()
        container_filter = self.filter_combo.get()

        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter
        filtered = self.all_boxes

        # Container filter
        if container_filter and container_filter != "All Containers":
            sku = self.container_map.get(container_filter)
            if sku:
                filtered = [b for b in filtered
                            if b['container_id'] == sku]

        # Search filter
        if search:
            filtered = [
                b for b in filtered
                if search in b['box_uid'].lower()
                or search in b['container_id'].lower()
                or search in b.get('item_name', '').lower()
                or search in b.get('batch_number', '').lower()
            ]

        # Re-insert
        for i, b in enumerate(filtered):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    b['box_uid'], b['container_id'],
                    b.get('item_name', '-'), b['quantity'],
                    b['unit'], b['condition'],
                    b.get('batch_number', '-')
                ),
                tags=(tag,)
            )

        self.count_var.set(
            f"Showing: {len(filtered)} of "
            f"{len(self.all_boxes)} boxes"
        )

    def _on_select(self, event):
        """Fill form when row clicked."""
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])['values']

        self._clear_form(refresh=False)

        self.fields['box_uid'].insert(0, values[0])

        # Set container
        container_id = values[1]
        for display, sku in self.container_map.items():
            if sku == container_id:
                self.container_combo.set(display)
                self._on_container_select()
                break

        self.fields['quantity'].insert(0, values[3])
        self.unit_combo.set(values[4])
        self.condition_combo.set(values[5])

        if values[6] and values[6] != '-':
            self.fields['batch_number'].insert(0, values[6])

        self.selected_box = values[0]
        self.fields['box_uid'].configure(state="readonly")

        self._log(f"Selected box: {values[0]}", "info")

    def _get_container_id(self):
        """Get container_id from dropdown."""
        selected = self.container_combo.get()
        return self.container_map.get(selected, "")

    def _update_container_totals(self, container_id):
        """Recalculate container's total_boxes and total_quantity."""
        boxes = self.db.get_boxes_by_container(container_id)
        total_boxes = len(boxes)
        total_qty = sum(b['quantity'] for b in boxes)

        self.db.update_container_quantity(
            container_id, total_boxes, total_qty
        )
        self._log(
            f"Container {container_id}: {total_boxes} boxes, "
            f"{total_qty} units", "ok"
        )

    def _add_box(self):
        """Add new box to database."""
        uid          = self.fields['box_uid'].get().strip()
        container_id = self._get_container_id()
        qty          = self.fields['quantity'].get().strip()
        unit         = self.unit_combo.get()
        condition    = self.condition_combo.get()
        batch        = self.fields['batch_number'].get().strip()

        # Validation
        if not uid:
            messagebox.showwarning("Required", "Box UID is required!")
            self.fields['box_uid'].focus()
            return

        if not container_id:
            messagebox.showwarning("Required",
                                    "Please select a Container!")
            return

        try:
            qty = int(qty) if qty else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Quantity must be a number!"
            )
            return

        if qty <= 0:
            messagebox.showwarning("Invalid",
                                    "Quantity must be greater than 0!")
            return

        # Check duplicate
        existing = self.db.get_box_by_uid(uid)
        if existing:
            messagebox.showerror(
                "Duplicate",
                f"Box UID '{uid}' already exists!\n\n"
                f"Use Update button to modify."
            )
            return

        # Insert
        if self.db.add_box(uid, container_id, qty, unit, batch):
            # Update condition if not GOOD
            if condition != "GOOD":
                self.db.update_box(uid, condition=condition)

            # Update container totals
            self._update_container_totals(container_id)

            self._log(f"Box {uid} added to {container_id}", "ok")

            container = self.container_info.get(container_id, {})
            messagebox.showinfo(
                "Success",
                f"✅ Box added to database!\n\n"
                f"Box UID: {uid}\n"
                f"Container: {container_id}\n"
                f"Item: {container.get('item_name', '-')}\n"
                f"Quantity: {qty} {unit}\n\n"
                f"💡 Now click 'WRITE UID TO CARD' to\n"
                f"   program a MIFARE card."
            )
            self._clear_form()
            self._load_boxes()
            self._load_containers_dropdown()
        else:
            messagebox.showerror(
                "Error", "Failed to add box to database!"
            )

    def _update_box(self):
        """Update selected box."""
        if not self.selected_box:
            messagebox.showwarning(
                "No Selection",
                "Please select a box from the list first!"
            )
            return

        qty       = self.fields['quantity'].get().strip()
        condition = self.condition_combo.get()

        try:
            qty = int(qty) if qty else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Quantity must be a number!"
            )
            return

        if not messagebox.askyesno(
            "Confirm Update",
            f"Update box '{self.selected_box}'?"
        ):
            return

        if self.db.update_box(
            self.selected_box, quantity=qty, condition=condition
        ):
            # Get container to update totals
            box = self.db.get_box_by_uid(self.selected_box)
            if box:
                self._update_container_totals(box['container_id'])

            self._log(f"Box {self.selected_box} updated", "ok")
            messagebox.showinfo(
                "Success", "✅ Box updated successfully!"
            )
            self._clear_form()
            self._load_boxes()
            self._load_containers_dropdown()
        else:
            messagebox.showerror(
                "Error", "Failed to update box!"
            )

    def _delete_box(self):
        """Delete selected box."""
        if not self.selected_box:
            messagebox.showwarning(
                "No Selection",
                "Please select a box from the list first!"
            )
            return

        # Get container before deletion
        box = self.db.get_box_by_uid(self.selected_box)
        container_id = box['container_id'] if box else None

        if not messagebox.askyesno(
            "Confirm Delete",
            f"⚠️  Delete box '{self.selected_box}'?\n\n"
            f"This action cannot be undone!\n\n"
            f"Container totals will auto-update."
        ):
            return

        if self.db.delete_box(self.selected_box):
            # Update container totals after deletion
            if container_id:
                self._update_container_totals(container_id)

            self._log(f"Box {self.selected_box} deleted", "warn")
            messagebox.showinfo(
                "Success", "✅ Box deleted successfully!"
            )
            self._clear_form()
            self._load_boxes()
            self._load_containers_dropdown()
        else:
            messagebox.showerror(
                "Error", "Failed to delete box!"
            )

    def _clear_form(self, refresh=True):
        """Clear all form fields."""
        for key, widget in self.fields.items():
            if key in ["unit", "condition", "container_id"]:
                continue
            try:
                widget.configure(state="normal")
                widget.delete(0, tk.END)
            except Exception:
                pass

        self.unit_combo.set("PCS")
        self.condition_combo.set("GOOD")

        if self.container_combo['values']:
            self.container_combo.set(
                self.container_combo['values'][0]
            )

        self.item_label.configure(
            text="(select container)",
            fg=COLORS["muted"]
        )

        self.selected_box = None

        # Clear tree selection
        for item in self.tree.selection():
            self.tree.selection_remove(item)

        if refresh:
            self._log("Form cleared", "info")

    # ═══════════════════════════════════════════════════════
    # MIFARE CARD OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _write_to_card(self):
        """Write Box UID to MIFARE card."""
        uid = self.fields['box_uid'].get().strip()

        if not uid:
            messagebox.showwarning(
                "Required",
                "Please enter or select a Box UID first!"
            )
            return

        # Verify box exists in DB
        box = self.db.get_box_by_uid(uid)
        if not box:
            if not messagebox.askyesno(
                "Not in Database",
                f"Box '{uid}' is not in database!\n\n"
                f"Do you still want to write it to card?"
            ):
                return

        # Check card
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card", "Place MIFARE card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log(f"WRITING Box UID to card: {uid}", "info")

            card = BoxCard()
            card.box_uid = uid
            card.write(self.mifare)

            self._log(f"✅ Card programmed with UID: {uid}", "ok")

            # Show success with details
            info = f"✅ Card programmed successfully!\n\n"
            info += f"Box UID: {uid}\n"
            info += f"Card Type: BOX\n\n"

            if box:
                info += f"🗃 Box Details (from DB):\n"
                info += f"  Container: {box['container_id']}\n"
                info += f"  Item:      {box.get('item_name', '-')}\n"
                info += f"  Quantity:  {box['quantity']} {box['unit']}\n"
                info += f"  Condition: {box['condition']}\n"
                info += f"  Batch:     {box.get('batch_number', '-')}"

            messagebox.showinfo("Success", info)

        except Exception as e:
            self._log(f"Write error: {e}", "err")
            messagebox.showerror("Write Error", str(e))
        finally:
            self.mifare.disconnect()

    def _read_from_card(self):
        """Read Box UID from card and load DB info."""
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card", "Place MIFARE card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log("READING box card...", "info")

            card = BoxCard()
            card.read(self.mifare)

            if not card.box_uid:
                messagebox.showwarning(
                    "Empty Card",
                    "This card has no Box UID written on it!"
                )
                return

            self._log(f"Card Box UID: {card.box_uid}", "ok")
            self._log(f"Card Type: {card.card_type}", "ok")

            # Lookup in database
            box = self.db.get_box_by_uid(card.box_uid)

            if box:
                self._log("✅ Box found in database", "ok")

                # Auto-fill form
                self._clear_form(refresh=False)
                self.fields['box_uid'].insert(0, box['box_uid'])

                # Set container
                for display, sku in self.container_map.items():
                    if sku == box['container_id']:
                        self.container_combo.set(display)
                        self._on_container_select()
                        break

                self.fields['quantity'].insert(0, str(box['quantity']))
                self.unit_combo.set(box['unit'])
                self.condition_combo.set(box['condition'])

                if box.get('batch_number'):
                    self.fields['batch_number'].insert(
                        0, box['batch_number']
                    )

                self.selected_box = box['box_uid']
                self.fields['box_uid'].configure(state="readonly")

                # Show success popup
                self._show_box_details(box)

            else:
                self._log(
                    f"⚠ Box UID '{card.box_uid}' not in DB", "warn"
                )
                messagebox.showwarning(
                    "Not Found",
                    f"Card Box UID: {card.box_uid}\n\n"
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
        """Verify card matches database entry."""
        if not self.mifare.connect():
            messagebox.showerror(
                "No Card", "Place card on reader!"
            )
            return

        try:
            self._log("═" * 36)
            self._log("VERIFYING box card with database...", "info")

            card = BoxCard()
            card.read(self.mifare)

            if not card.box_uid:
                messagebox.showwarning(
                    "Empty Card", "Card has no Box UID!"
                )
                return

            box = self.db.get_box_by_uid(card.box_uid)

            if box:
                msg = f"✅ VERIFICATION SUCCESSFUL\n\n"
                msg += f"{'─'*30}\n"
                msg += f"Card Box UID:  {card.box_uid}\n"
                msg += f"Card Type:     {card.card_type}\n"
                msg += f"{'─'*30}\n\n"
                msg += f"🗃 Database Match:\n"
                msg += f"  Container:    {box['container_id']}\n"
                msg += f"  Item:         {box.get('item_name', '-')}\n"
                msg += f"  Quantity:     {box['quantity']} {box['unit']}\n"
                msg += f"  Condition:    {box['condition']}\n"
                msg += f"  Batch:        {box.get('batch_number', '-')}\n"
                msg += f"  Warehouse:    {box.get('warehouse_name', '-')}"

                self._log("Card verified successfully", "ok")
                messagebox.showinfo("Verification OK", msg)
            else:
                self._log(
                    f"Card UID not in DB: {card.box_uid}", "err"
                )
                messagebox.showerror(
                    "Verification Failed",
                    f"❌ Card UID '{card.box_uid}' "
                    f"NOT found in database!\n\n"
                    f"This card may be invalid or removed."
                )

        except Exception as e:
            self._log(f"Verify error: {e}", "err")
            messagebox.showerror("Error", str(e))
        finally:
            self.mifare.disconnect()

    def _show_box_details(self, box):
        """Show detailed popup of box info from DB."""
        popup = tk.Toplevel(self.root)
        popup.title("Box Details (from Database)")
        popup.configure(bg=COLORS["bg"])
        popup.geometry("500x550")
        popup.grab_set()

        # Header
        hdr = tk.Frame(popup, bg=COLORS["primary"], height=54)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🗃  BOX VERIFIED",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["primary"],
                 fg="white").pack(pady=13)

        # Status banner
        stat = tk.Frame(popup, bg=COLORS["success"], height=34)
        stat.pack(fill=tk.X)
        stat.pack_propagate(False)
        tk.Label(stat,
                 text=f"✓  Box UID matches Database Entry",
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

        # Box info
        info_block("🗃  BOX INFORMATION", [
            ("Box UID",       box['box_uid']),
            ("Item Name",     box.get('item_name', '-')),
            ("Quantity",      f"{box['quantity']} {box['unit']}"),
            ("Condition",     box['condition']),
            ("Batch Number",  box.get('batch_number', '-')),
        ])

        # Container info
        info_block("📦  PARENT CONTAINER", [
            ("Container ID",  box['container_id']),
            ("Container Name", box.get('container_name', '-')),
        ])

        # Warehouse info (if available)
        if box.get('warehouse_name'):
            info_block("🏭  WAREHOUSE LOCATION", [
                ("Warehouse ID",   box.get('warehouse_id', '-')),
                ("Warehouse Name", box.get('warehouse_name', '-')),
            ])

        # Close button
        tk.Button(body, text="✓  CLOSE",
                   font=("Segoe UI", 10, "bold"),
                   bg=COLORS["primary"], fg="white",
                   relief=tk.FLAT, pady=10,
                   cursor="hand2",
                   command=popup.destroy).pack(fill=tk.X, pady=(4, 0))


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = BoxApp(root)
    root.mainloop()