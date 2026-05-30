# apps/warehouse_app.py
# Warehouse Management App
# Add, view, update, delete warehouses

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent folders to path
sys.path.append(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'database'))
sys.path.append(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS, FONTS


class WarehouseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Warehouse Management — Army Logistics")
        self.root.configure(bg=COLORS["bg"])

        # Full screen
        self.root.geometry("1280x780")
        self.root.minsize(1100, 650)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.selected_warehouse = None

        # Test DB connection first
        success, msg = self.db.test_connection()
        if not success:
            messagebox.showerror(
                "Database Error",
                f"Cannot connect to database!\n\n{msg}\n\n"
                f"Check database/db_config.py"
            )
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_warehouses()

    # ═══════════════════════════════════════════════════════
    # STYLES
    # ═══════════════════════════════════════════════════════

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Treeview style
        s.configure(
            "Custom.Treeview",
            background=COLORS["white"],
            foreground=COLORS["text"],
            rowheight=32,
            fieldbackground=COLORS["white"],
            font=FONTS["body"],
            borderwidth=0
        )
        s.configure(
            "Custom.Treeview.Heading",
            background=COLORS["primary"],
            foreground="white",
            font=FONTS["title"],
            borderwidth=0,
            relief="flat"
        )
        s.map(
            "Custom.Treeview",
            background=[("selected", COLORS["secondary"])],
            foreground=[("selected", "white")]
        )
        s.map(
            "Custom.Treeview.Heading",
            background=[("active", COLORS["secondary"])]
        )

    # ═══════════════════════════════════════════════════════
    # UI BUILD
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_status_bar()

        # Main content
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Left: Warehouses list
        self._build_warehouse_list(main)

        # Right: Form + actions
        self._build_form_panel(main)

        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=64)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=18, pady=8)

        tk.Label(left, text="🏭",
                 font=("Segoe UI Emoji", 26),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(side=tk.LEFT, padx=(0, 12))

        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="WAREHOUSE MANAGEMENT",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["primary"], fg="white").pack(anchor="w")
        tk.Label(tb,
                 text="Army Logistics  •  Warehouse Database Module",
                 font=("Segoe UI", 9),
                 bg=COLORS["primary"], fg="#C8E6C9").pack(anchor="w")

        tk.Label(hdr, text="v1.0",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["primary"],
                 fg="#C8E6C9").pack(side=tk.RIGHT, padx=18)

    def _build_status_bar(self):
        self.status_frame = tk.Frame(
            self.root, bg=COLORS["success"], height=30
        )
        self.status_frame.pack(fill=tk.X)
        self.status_frame.pack_propagate(False)

        tk.Label(self.status_frame, text="●",
                 font=("Segoe UI", 12, "bold"),
                 bg=COLORS["success"], fg="white").pack(
                     side=tk.LEFT, padx=(16, 6))

        self.status_var = tk.StringVar(
            value="Database Connected — Ready"
        )
        tk.Label(self.status_frame, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT)

        self.count_var = tk.StringVar(value="Total: 0 warehouses")
        tk.Label(self.status_frame, textvariable=self.count_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(
                     side=tk.RIGHT, padx=16)

    # ── Left Panel: Warehouse List ────────────────────────

    def _build_warehouse_list(self, parent):
        left_frame = tk.LabelFrame(
            parent,
            text="  📋  WAREHOUSE LIST  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=(0, 6))

        # Search bar
        search_frame = tk.Frame(left_frame, bg=COLORS["bg"])
        search_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(search_frame, text="🔍",
                 font=("Segoe UI", 11),
                 bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._filter_warehouses())
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            relief=tk.SOLID, bd=1,
            highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Treeview (table)
        tree_frame = tk.Frame(left_frame, bg=COLORS["white"])
        tree_frame.pack(fill=tk.BOTH, expand=True,
                        padx=8, pady=(0, 8))

        columns = ("id", "name", "location", "capacity", "status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview"
        )

        # Column headings
        self.tree.heading("id",       text="Warehouse ID")
        self.tree.heading("name",     text="Name")
        self.tree.heading("location", text="Location")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("status",   text="Status")

        # Column widths
                # Column widths
        self.tree.column("id",       width=110, anchor="w")
        self.tree.column("name",     width=200, anchor="w")
        self.tree.column("location", width=180, anchor="w")
        self.tree.column("capacity", width=90,  anchor="center")
        self.tree.column("status",   width=90,  anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Alternate row colors
        self.tree.tag_configure(
            "odd", background=COLORS["white"]
        )
        self.tree.tag_configure(
            "even", background=COLORS["row_alt"]
        )

    # ── Right Panel: Form ─────────────────────────────────

    def _build_form_panel(self, parent):
        right_frame = tk.Frame(parent, bg=COLORS["bg"], width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right_frame.pack_propagate(False)

        # ── Form Section ──
        form_box = tk.LabelFrame(
            right_frame,
            text="  ➕  ADD / EDIT WAREHOUSE  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        form_box.pack(fill=tk.X, pady=(0, 8))

        form_inner = tk.Frame(form_box, bg=COLORS["white"])
        form_inner.pack(fill=tk.X, padx=4, pady=4)
        form_inner.columnconfigure(1, weight=1)

        # Fields
        self.fields = {}

        fields_list = [
            ("Warehouse ID",   "warehouse_id",   20),
            ("Warehouse Name", "warehouse_name", 100),
            ("Location",       "location",       200),
            ("Capacity",       "capacity",       10),
        ]

        for i, (label, key, maxlen) in enumerate(fields_list):
            tk.Label(form_inner, text=f"{label}:",
                     font=("Segoe UI", 9),
                     bg=COLORS["white"],
                     fg=COLORS["text"],
                     anchor="w").grid(
                         row=i, column=0,
                         sticky="w", padx=10, pady=6
                     )

            entry = tk.Entry(
                form_inner,
                font=("Segoe UI", 10),
                relief=tk.SOLID, bd=1,
                highlightbackground=COLORS["border"],
                highlightthickness=1
            )
            entry.grid(row=i, column=1, sticky="ew",
                       padx=10, pady=6)
            self.fields[key] = entry

        # Status dropdown
        tk.Label(form_inner, text="Status:",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"],
                 fg=COLORS["text"],
                 anchor="w").grid(
                     row=4, column=0,
                     sticky="w", padx=10, pady=6
                 )

        self.status_combo = ttk.Combobox(
            form_inner,
            values=["ACTIVE", "INACTIVE", "MAINTENANCE"],
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.status_combo.set("ACTIVE")
        self.status_combo.grid(row=4, column=1,
                                sticky="ew", padx=10, pady=6)
        self.fields["status"] = self.status_combo

        # Help text
        help_text = tk.Label(
            form_inner,
            text="💡 Tip: Click a row above to edit it",
            font=("Segoe UI", 8, "italic"),
            bg=COLORS["white"],
            fg=COLORS["muted"]
        )
        help_text.grid(row=5, column=0, columnspan=2,
                       sticky="w", padx=10, pady=(8, 6))

        # ── Action Buttons ──
        actions_box = tk.LabelFrame(
            right_frame,
            text="  ⚡  ACTIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        actions_box.pack(fill=tk.X, pady=(0, 8))

        btn_inner = tk.Frame(actions_box, bg=COLORS["white"])
        btn_inner.pack(fill=tk.X, padx=6, pady=6)

        actions = [
            ("➕  ADD WAREHOUSE",    COLORS["success"], self._add_warehouse),
            ("✏  UPDATE SELECTED",   COLORS["info"],    self._update_warehouse),
            ("🗑  DELETE SELECTED",  COLORS["danger"],  self._delete_warehouse),
            ("🔄  REFRESH LIST",     COLORS["warning"], self._load_warehouses),
            ("🧹  CLEAR FORM",       COLORS["muted"],   self._clear_form),
        ]

        for text, color, cmd in actions:
            btn = tk.Button(
                btn_inner, text=text, command=cmd,
                font=("Segoe UI", 10, "bold"),
                bg=color, fg="white",
                relief=tk.FLAT, bd=0,
                pady=10, cursor="hand2",
                activebackground=COLORS["dark"],
                activeforeground="white"
            )
            btn.pack(fill=tk.X, pady=3)

        # ── Statistics Panel ──
        stats_box = tk.LabelFrame(
            right_frame,
            text="  📊  WAREHOUSE STATISTICS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.GROOVE
        )
        stats_box.pack(fill=tk.BOTH, expand=True)

        self.stats_frame = tk.Frame(stats_box, bg=COLORS["white"])
        self.stats_frame.pack(fill=tk.BOTH, expand=True,
                               padx=6, pady=6)

        self._show_default_stats()

    def _show_default_stats(self):
        """Show default message when no warehouse selected."""
        for w in self.stats_frame.winfo_children():
            w.destroy()

        tk.Label(
            self.stats_frame,
            text="📋\n\nSelect a warehouse to view\nits statistics",
            font=("Segoe UI", 10),
            bg=COLORS["white"],
            fg=COLORS["muted"],
            justify="center"
        ).pack(expand=True)

    def _show_warehouse_stats(self, warehouse_id):
        """Show statistics for selected warehouse."""
        for w in self.stats_frame.winfo_children():
            w.destroy()

        summary = self.db.get_warehouse_summary(warehouse_id)
        if not summary:
            tk.Label(
                self.stats_frame,
                text="No data available",
                font=("Segoe UI", 10),
                bg=COLORS["white"],
                fg=COLORS["muted"]
            ).pack(expand=True)
            return

        # Warehouse name
        tk.Label(
            self.stats_frame,
            text=summary['warehouse_name'],
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["white"],
            fg=COLORS["primary"]
        ).pack(pady=(8, 2))

        tk.Label(
            self.stats_frame,
            text=f"📍 {summary['location']}",
            font=("Segoe UI", 9),
            bg=COLORS["white"],
            fg=COLORS["muted"]
        ).pack(pady=(0, 12))

        # Stats cards
        stats_data = [
            ("📦", "Containers", summary['total_containers'],
             COLORS["info"]),
            ("🗃", "Total Boxes", summary['total_boxes'],
             COLORS["success"]),
            ("📊", "Total Items", summary['total_items'],
             COLORS["warning"]),
        ]

        for icon, label, value, color in stats_data:
            row = tk.Frame(self.stats_frame, bg=COLORS["white"])
            row.pack(fill=tk.X, padx=10, pady=4)

            tk.Label(row, text=icon,
                     font=("Segoe UI Emoji", 18),
                     bg=COLORS["white"]).pack(side=tk.LEFT, padx=(0, 8))

            text_frame = tk.Frame(row, bg=COLORS["white"])
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(text_frame, text=label,
                     font=("Segoe UI", 8),
                     bg=COLORS["white"],
                     fg=COLORS["muted"],
                     anchor="w").pack(anchor="w")

            tk.Label(text_frame, text=str(value),
                     font=("Segoe UI", 14, "bold"),
                     bg=COLORS["white"],
                     fg=color,
                     anchor="w").pack(anchor="w")

    # ── Footer ────────────────────────────────────────────

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(footer,
                 text="© 2025 Indian Army  |  "
                      "Warehouse Management Module",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.LEFT, padx=14, pady=4)

        tk.Label(footer,
                 text="Database: PostgreSQL  |  v1.0",
                 font=("Segoe UI", 8),
                 bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.RIGHT, padx=14, pady=4)

    # ═══════════════════════════════════════════════════════
    # DATA OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _load_warehouses(self):
        """Load all warehouses from database into table."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Fetch from database
        warehouses = self.db.get_all_warehouses()
        self.all_warehouses = warehouses  # Cache for filtering

        # Insert into tree
        for i, w in enumerate(warehouses):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    w['warehouse_id'],
                    w['warehouse_name'],
                    w['location'] or "-",
                    w['capacity'],
                    w['status']
                ),
                tags=(tag,)
            )

        # Update count
        self.count_var.set(f"Total: {len(warehouses)} warehouses")
        self._set_status(
            f"Loaded {len(warehouses)} warehouses",
            COLORS["success"]
        )

    def _filter_warehouses(self):
        """Filter table based on search."""
        search = self.search_var.get().lower().strip()

        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter
        filtered = [
            w for w in self.all_warehouses
            if search in w['warehouse_id'].lower()
            or search in w['warehouse_name'].lower()
            or search in (w['location'] or "").lower()
        ]

        # Re-insert
        for i, w in enumerate(filtered):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", tk.END,
                values=(
                    w['warehouse_id'],
                    w['warehouse_name'],
                    w['location'] or "-",
                    w['capacity'],
                    w['status']
                ),
                tags=(tag,)
            )

        self.count_var.set(
            f"Showing: {len(filtered)} of "
            f"{len(self.all_warehouses)} warehouses"
        )

    def _on_select(self, event):
        """When user clicks a row, fill form with data."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item['values']

        # Fill form
        self._clear_form(refresh_status=False)
        self.fields['warehouse_id'].insert(0, values[0])
        self.fields['warehouse_name'].insert(0, values[1])
        self.fields['location'].insert(
            0, values[2] if values[2] != "-" else ""
        )
        self.fields['capacity'].insert(0, values[3])
        self.status_combo.set(values[4])

        self.selected_warehouse = values[0]

        # Make ID field readonly when editing
        self.fields['warehouse_id'].configure(state="readonly")

        # Show stats
        self._show_warehouse_stats(values[0])

        self._set_status(
            f"Selected: {values[0]} — {values[1]}",
            COLORS["info"]
        )

    def _add_warehouse(self):
        """Add new warehouse."""
        # Get values
        wid    = self.fields['warehouse_id'].get().strip()
        name   = self.fields['warehouse_name'].get().strip()
        loc    = self.fields['location'].get().strip()
        cap    = self.fields['capacity'].get().strip()

        # Validate
        if not wid:
            messagebox.showwarning(
                "Required", "Warehouse ID is required!"
            )
            self.fields['warehouse_id'].focus()
            return

        if not name:
            messagebox.showwarning(
                "Required", "Warehouse Name is required!"
            )
            self.fields['warehouse_name'].focus()
            return

        # Parse capacity
        try:
            cap = int(cap) if cap else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Capacity must be a number!"
            )
            return

        # Check duplicate
        existing = self.db.get_warehouse_by_id(wid)
        if existing:
            messagebox.showerror(
                "Duplicate",
                f"Warehouse ID '{wid}' already exists!\n\n"
                f"Use Update button to modify existing warehouse."
            )
            return

        # Insert
        if self.db.add_warehouse(wid, name, loc, cap):
            messagebox.showinfo(
                "Success",
                f"✅ Warehouse added successfully!\n\n"
                f"ID: {wid}\n"
                f"Name: {name}\n"
                f"Location: {loc}"
            )
            self._clear_form()
            self._load_warehouses()
        else:
            messagebox.showerror(
                "Error", "Failed to add warehouse!"
            )

    def _update_warehouse(self):
        """Update selected warehouse."""
        if not self.selected_warehouse:
            messagebox.showwarning(
                "No Selection",
                "Please select a warehouse from the list first!"
            )
            return

        # Get values
        name = self.fields['warehouse_name'].get().strip()
        loc  = self.fields['location'].get().strip()
        cap  = self.fields['capacity'].get().strip()

        if not name:
            messagebox.showwarning(
                "Required", "Warehouse Name is required!"
            )
            return

        try:
            cap = int(cap) if cap else 0
        except ValueError:
            messagebox.showwarning(
                "Invalid", "Capacity must be a number!"
            )
            return

        # Confirm
        if not messagebox.askyesno(
            "Confirm Update",
            f"Update warehouse '{self.selected_warehouse}'?"
        ):
            return

        # Update
        if self.db.update_warehouse(
            self.selected_warehouse,
            name=name,
            location=loc,
            capacity=cap
        ):
            messagebox.showinfo(
                "Success",
                f"✅ Warehouse updated successfully!"
            )
            self._clear_form()
            self._load_warehouses()
        else:
            messagebox.showerror(
                "Error", "Failed to update warehouse!"
            )

    def _delete_warehouse(self):
        """Delete selected warehouse."""
        if not self.selected_warehouse:
            messagebox.showwarning(
                "No Selection",
                "Please select a warehouse from the list first!"
            )
            return

        # Check if containers exist
        containers = self.db.get_containers_by_warehouse(
            self.selected_warehouse
        )

        if containers:
            messagebox.showerror(
                "Cannot Delete",
                f"❌ Warehouse '{self.selected_warehouse}' has "
                f"{len(containers)} container(s)!\n\n"
                f"Delete or move all containers first."
            )
            return

        # Confirm
        if not messagebox.askyesno(
            "Confirm Delete",
            f"⚠️  Delete warehouse '{self.selected_warehouse}'?\n\n"
            f"This action cannot be undone!"
        ):
            return

        # Delete
        if self.db.delete_warehouse(self.selected_warehouse):
            messagebox.showinfo(
                "Success",
                f"✅ Warehouse deleted successfully!"
            )
            self._clear_form()
            self._load_warehouses()
        else:
            messagebox.showerror(
                "Error", "Failed to delete warehouse!"
            )

    def _clear_form(self, refresh_status=True):
        """Clear all form fields."""
        for key, widget in self.fields.items():
            if key == "status":
                widget.set("ACTIVE")
            else:
                widget.configure(state="normal")
                widget.delete(0, tk.END)

        self.selected_warehouse = None
        self._show_default_stats()

        # Clear tree selection
        for item in self.tree.selection():
            self.tree.selection_remove(item)

        if refresh_status:
            self._set_status(
                "Form cleared — Ready for new entry",
                COLORS["success"]
            )

    def _set_status(self, text, color):
        """Update status bar."""
        self.status_var.set(text)
        try:
            self.status_frame.configure(bg=color)
            for w in self.status_frame.winfo_children():
                w.configure(bg=color)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = WarehouseApp(root)
    root.mainloop()