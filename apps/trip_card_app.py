# apps/trip_card_app.py
# 🎖 TRIP CARD MANAGER - Simple Demand Card (No Warehouse Integration)
# Unit Manager just creates demand - Gate verifies stock

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from theme import COLORS, FONTS
from mifare_core import MifareCore
from trip_card import TripCard


# ═══════════════════════════════════════════════════════════
# PREDEFINED ITEMS LIST (Standard military items)
# ═══════════════════════════════════════════════════════════
# Unit can request these items - actual availability checked at gate

ITEMS_CATALOG = [
    "AK47",
    "Pistol",
    "Rifle",
    "Ammo",
    "Grenade",
    "Helmet",
    "Boots",
    "Uniform",
    "Bullet-proof Vest",
    "Night Vision Goggles",
    "Medical Kit",
    "Ration Pack",
    "Water Bottle",
    "Tent",
    "Sleeping Bag",
    "Radio",
    "Binoculars",
    "Knife",
    "Flashlight",
    "Battery"
]


class TripCardApp:

    def __init__(self, root):
        self.root = root
        self.root.title("TRIP CARD MANAGER — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.mifare = MifareCore(self._log)
        self.card_present = False
        self.items = []

        self._setup_styles()
        self._build_ui()
        self._load_items_catalog()

        self.mifare.find_reader()
        self._poll_card()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", 
            foreground=COLORS["text"],
            rowheight=36,
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
            font=("Segoe UI", 11),
            padding=6,
            fieldbackground="white",
            background="white",
            arrowsize=18)
        s.map("TCombobox",
            fieldbackground=[("readonly", "white")],
            foreground=[("readonly", COLORS["text"])],
            selectbackground=[("readonly", "white")],
            selectforeground=[("readonly", COLORS["text"])])
        
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))
        self.root.option_add("*TCombobox*Listbox.background", "white")
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["primary"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "white")

    # ═══════════════════════════════════════════════════════
    # MAIN UI BUILD
    # ═══════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        self._build_card_status_bar()
        
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        
        left = tk.Frame(main, bg=COLORS["bg"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        self._build_form(left)
        
        right = tk.Frame(main, bg=COLORS["bg"], width=400)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right.pack_propagate(False)
        self._build_actions(right)
        
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        
        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="🎖",
                 font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"],
                 fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        
        tk.Label(tb, text="INDIAN ARMY",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"],
                 fg=COLORS["accent"]).pack(anchor="w")
        
        tk.Label(tb, text="TRIP CARD MANAGER",
                 font=("Segoe UI", 18, "bold"),
                 bg=COLORS["primary"],
                 fg="white").pack(anchor="w")
        
        right = tk.Frame(hdr, bg=COLORS["primary"])
        right.pack(side=tk.RIGHT, padx=20)
        
        self.time_var = tk.StringVar()
        tk.Label(right, textvariable=self.time_var,
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["primary"],
                 fg="white").pack(anchor="e", pady=(15, 0))
        
        tk.Label(right, text="● ONLINE",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["primary"],
                 fg="#4ade80").pack(anchor="e")
        
        self._update_time()

    def _update_time(self):
        self.time_var.set(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))
        self.root.after(1000, self._update_time)

    def _build_card_status_bar(self):
        self.card_bar = tk.Frame(self.root, bg=COLORS["danger"], height=28)
        self.card_bar.pack(fill=tk.X)
        self.card_bar.pack_propagate(False)
        
        self.card_dot = tk.Label(self.card_bar, text="●",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["danger"], fg="white")
        self.card_dot.pack(side=tk.LEFT, padx=(16, 8))
        
        self.card_var = tk.StringVar(value="No card detected - Place MIFARE card on reader")
        self.card_lbl = tk.Label(self.card_bar, textvariable=self.card_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["danger"], fg="white")
        self.card_lbl.pack(side=tk.LEFT)
        
        self.atr_var = tk.StringVar(value="ATR: --")
        self.atr_lbl = tk.Label(self.card_bar, textvariable=self.atr_var,
            font=("Consolas", 9),
            bg=COLORS["danger"], fg="white")
        self.atr_lbl.pack(side=tk.RIGHT, padx=16)

    def _build_form(self, parent):
        # ─── TRIP INFO ───
        trip_frame = tk.LabelFrame(parent,
            text="  TRIP INFORMATION  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        trip_frame.pack(fill=tk.X, pady=(0, 8))
        
        trip_inner = tk.Frame(trip_frame, bg=COLORS["bg_card"])
        trip_inner.pack(fill=tk.X, padx=2, pady=2)
        trip_inner.columnconfigure(1, weight=1)
        trip_inner.columnconfigure(3, weight=1)
        
        self.fields = {}
        self._add_field(trip_inner, 0, 0, "Trip ID:", "trip_id")
        self._add_field(trip_inner, 0, 2, "Truck Number:", "truck_number")
        
        # ─── DRIVER INFO ───
        driver_frame = tk.LabelFrame(parent,
            text="  DRIVER INFORMATION  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        driver_frame.pack(fill=tk.X, pady=(0, 8))
        
        driver_inner = tk.Frame(driver_frame, bg=COLORS["bg_card"])
        driver_inner.pack(fill=tk.X, padx=2, pady=2)
        driver_inner.columnconfigure(1, weight=1)
        driver_inner.columnconfigure(3, weight=1)
        
        self._add_field(driver_inner, 0, 0, "Driver ID:", "driver_id")
        self._add_field(driver_inner, 0, 2, "Driver Name:", "driver_name")
        
        # ─── SUB-DRIVER INFO ───
        sub_frame = tk.LabelFrame(parent,
            text="  SUB-DRIVER INFORMATION  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        sub_frame.pack(fill=tk.X, pady=(0, 8))
        
        sub_inner = tk.Frame(sub_frame, bg=COLORS["bg_card"])
        sub_inner.pack(fill=tk.X, padx=2, pady=2)
        sub_inner.columnconfigure(1, weight=1)
        sub_inner.columnconfigure(3, weight=1)
        
        self._add_field(sub_inner, 0, 0, "Sub-driver ID:", "subdriver_id")
        self._add_field(sub_inner, 0, 2, "Sub-driver Name:", "subdriver_name")
        
        # ─── ITEMS REQUESTED ───
        items_frame = tk.LabelFrame(parent,
            text="  ITEMS TO TRANSPORT  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        items_inner = tk.Frame(items_frame, bg=COLORS["bg_card"])
        items_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add item row
        add_row = tk.Frame(items_inner, bg=COLORS["bg_card"])
        add_row.pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(add_row, text="Item:",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text"]).pack(side=tk.LEFT, padx=(0, 5))
        
        # Simple dropdown from catalog
        self.item_name_entry = ttk.Combobox(add_row,
            font=("Segoe UI", 11),
            width=30,
            state="readonly",
            values=["-- Select Item --"])
        self.item_name_entry.set("-- Select Item --")
        self.item_name_entry.pack(side=tk.LEFT, padx=(0, 12), pady=4)
        
        tk.Label(add_row, text="Qty:",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text"]).pack(side=tk.LEFT, padx=(0, 5))
        
        self.item_qty_entry = tk.Entry(add_row,
            font=("Segoe UI", 11),
            relief=tk.SOLID, bd=1, width=10,
            highlightthickness=1,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["primary"])
        self.item_qty_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=5)
        
        tk.Button(add_row, text="+ ADD ITEM",
            command=self._add_item,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["primary"], fg="white",
            relief=tk.FLAT, padx=15, pady=7,
            cursor="hand2",
            activebackground=COLORS["primary_dark"],
            activeforeground="white").pack(side=tk.LEFT)
        
        tk.Button(add_row, text="REMOVE",
            command=self._remove_item,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["danger"], fg="white",
            relief=tk.FLAT, padx=15, pady=7,
            cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))
        
        tk.Button(add_row, text="CLEAR ALL",
            command=self._clear_items,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["text_muted"], fg="white",
            relief=tk.FLAT, padx=12, pady=7,
            cursor="hand2").pack(side=tk.RIGHT)
        
        # Bindings
        self.item_name_entry.bind("<<ComboboxSelected>>", 
                                    lambda e: self.item_qty_entry.focus())
        self.item_qty_entry.bind("<Return>", lambda e: self._add_item())
        
        # Items table (directly after add row - no info hint)
        tree_frame = tk.Frame(items_inner, bg=COLORS["bg_card"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        cols = ("num", "item", "qty")
        self.items_tree = ttk.Treeview(tree_frame, columns=cols,
            show="headings", style="Clean.Treeview")
        
        self.items_tree.heading("num", text="S.No.", anchor="center")
        self.items_tree.heading("item", text="Item Name", anchor="center")
        self.items_tree.heading("qty", text="Quantity", anchor="center")
        
        self.items_tree.column("num", width=80, anchor="center", stretch=False)
        self.items_tree.column("item", width=400, anchor="center", stretch=True)
        self.items_tree.column("qty", width=150, anchor="center", stretch=False)
        
        sb = ttk.Scrollbar(tree_frame, orient="vertical",
            command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=sb.set)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Count
        self.count_var = tk.StringVar(value="0 items added")
        tk.Label(items_inner, textvariable=self.count_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["primary"]
        ).pack(anchor="w", padx=8, pady=(0, 8))

    def _add_field(self, parent, row, col, label, key):
        tk.Label(parent, text=label,
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["text"],
            anchor="w").grid(row=row, column=col, sticky="w",
                              padx=(12, 5), pady=10)
        
        entry = tk.Entry(parent,
            font=("Segoe UI", 11),
            relief=tk.SOLID, bd=1,
            highlightthickness=1,
            highlightbackground=COLORS["input_border"],
            highlightcolor=COLORS["primary"])
        entry.grid(row=row, column=col+1, sticky="ew",
                    padx=(0, 12), pady=10, ipady=5)
        self.fields[key] = entry

    def _build_actions(self, parent):
        # ─── CARD OPERATIONS ───
        card_frame = tk.LabelFrame(parent,
            text="  CARD OPERATIONS  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        card_frame.pack(fill=tk.X, pady=(0, 8))
        
        inner = tk.Frame(card_frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.X, padx=2, pady=2)
        
        tk.Label(inner,
            text="Fill all fields, then write to card.\n"
                "Or read existing card to view data.",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            justify="left").pack(anchor="w", padx=12, pady=(10, 12))
        
        self.write_btn = tk.Button(inner,
            text="WRITE TO CARD",
            command=self._write_card,
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["primary"], fg="white",
            relief=tk.FLAT, pady=14,
            cursor="hand2",
            activebackground=COLORS["primary_dark"],
            activeforeground="white")
        self.write_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        self.read_btn = tk.Button(inner,
            text="READ FROM CARD",
            command=self._read_card,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=12,
            cursor="hand2")
        self.read_btn.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        tk.Button(inner,
            text="CLEAR FORM",
            command=self._clear_form,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["text_muted"], fg="white",
            relief=tk.FLAT, pady=10,
            cursor="hand2").pack(fill=tk.X, padx=12, pady=(0, 12))
        
        # ─── ACTIVITY LOG ───
        log_frame = tk.LabelFrame(parent,
            text="  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_inner = tk.Frame(log_frame, bg="#212121")
        log_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.log_text = tk.Text(log_inner,
            font=("Consolas", 9),
            bg="#212121", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD,
            insertbackground="white")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)
        
        self._log("Trip Card Manager started", "ok")
        self._log("Place card on reader to begin", "info")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        tk.Label(footer, 
            text="© 2025 Indian Army | Trip Card Module",
            font=("Segoe UI", 8), 
            bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        
        tk.Label(footer, 
            text="MIFARE Classic 1K  |  ACR122U Reader",
            font=("Segoe UI", 8), 
            bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗", "warn": "⚠"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(tk.END,
                f"[{ts}] {icons.get(level, '•')} {msg}\n")
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

    def _poll_card(self):
        present = self.mifare.connect()
        if present and not self.card_present:
            atr = self.mifare.get_atr()
            self.atr_var.set(f"ATR: {atr}")
            self._set_card_status(
                "Card detected - Ready for operations",
                COLORS["success"])
            self._log("Card detected on reader", "ok")
            self.card_present = True
        elif not present and self.card_present:
            self.atr_var.set("ATR: --")
            self._set_card_status(
                "No card detected - Place MIFARE card on reader",
                COLORS["danger"])
            self._log("Card removed", "warn")
            self.card_present = False
        self.mifare.disconnect()
        self.root.after(1500, self._poll_card)

    # ═══════════════════════════════════════════════════════
    # ITEMS CATALOG (static list)
    # ═══════════════════════════════════════════════════════

    def _load_items_catalog(self):
        """Load predefined items catalog (no database)."""
        values = ["-- Select Item --"] + sorted(ITEMS_CATALOG)
        self.item_name_entry['values'] = values
        self.item_name_entry.set("-- Select Item --")
        self._log(f"Loaded {len(ITEMS_CATALOG)} items in catalog", "ok")

    # ═══════════════════════════════════════════════════════
    # ITEM MANAGEMENT
    # ═══════════════════════════════════════════════════════

    def _add_item(self):
        name = self.item_name_entry.get().strip()
        qty_str = self.item_qty_entry.get().strip()

        if not name or name.startswith("--"):
            messagebox.showwarning("Required", "Select an item from dropdown!")
            self.item_name_entry.focus()
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Invalid", "Enter valid quantity (>0)!")
            self.item_qty_entry.focus()
            return

        if len(self.items) >= 36:
            messagebox.showwarning("Max Items", "Maximum 36 items per card!")
            return

        # Check if already added
        for idx, item in enumerate(self.items):
            if item['name'].lower() == name.lower():
                if messagebox.askyesno("Duplicate",
                    f"'{name}' already added with qty {item['qty']}.\n\n"
                    f"Add {qty} more? (Total will be {item['qty'] + qty})"):
                    self.items[idx]['qty'] += qty
                    self._refresh_items()
                    self._log(f"Updated: {name} → {self.items[idx]['qty']}", "ok")
                    self._reset_item_input()
                return

        self.items.append({'name': name, 'qty': qty})
        self._refresh_items()
        self._log(f"Added: {name} × {qty}", "ok")
        self._reset_item_input()

    def _reset_item_input(self):
        self.item_name_entry.set("-- Select Item --")
        self.item_qty_entry.delete(0, tk.END)
        self.item_name_entry.focus()

    def _remove_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Select", "Select an item to remove!")
            return

        iid = selection[0]
        idx = int(iid.replace("item-", ""))
        
        if 0 <= idx < len(self.items):
            removed = self.items.pop(idx)
            self._refresh_items()
            self._log(f"Removed: {removed['name']}", "warn")

    def _clear_items(self):
        if not self.items:
            return
        if messagebox.askyesno("Clear All", "Remove all items?"):
            self.items = []
            self._refresh_items()
            self._log("All items cleared", "warn")

    def _refresh_items(self):
        for c in self.items_tree.get_children():
            self.items_tree.delete(c)
        
        for i, item in enumerate(self.items):
            self.items_tree.insert("", "end",
                iid=f"item-{i}",
                values=(str(i+1), item['name'], item['qty']))
        
        self.count_var.set(f"{len(self.items)} items added")

    # ═══════════════════════════════════════════════════════
    # CARD OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _write_card(self):
        trip_id = self.fields['trip_id'].get().strip()
        truck = self.fields['truck_number'].get().strip()
        driver_id = self.fields['driver_id'].get().strip()
        driver_name = self.fields['driver_name'].get().strip()
        subdriver_id = self.fields['subdriver_id'].get().strip()
        subdriver_name = self.fields['subdriver_name'].get().strip()

        if not truck:
            messagebox.showwarning("Required", "Truck Number is required!")
            self.fields['truck_number'].focus()
            return

        if not driver_id or not driver_name:
            messagebox.showwarning("Required",
                "Driver ID and Name are required!")
            return

        if not self.items:
            if not messagebox.askyesno("No Items",
                "No items added!\n\nWrite card with empty items list?"):
                return

        if not self.mifare.connect():
            messagebox.showerror("No Card",
                "Place MIFARE card on reader and try again!")
            return

        try:
            self._log("=" * 40)
            self._log("Writing trip card...", "info")

            card = TripCard()
            card.trip_id = trip_id or f"TRIP-{int(time.time())}"
            card.truck_number = truck
            card.driver_id = driver_id
            card.driver_name = driver_name
            card.subdriver_id = subdriver_id
            card.subdriver_name = subdriver_name
            
            for item in self.items:
                card.add_item(item['name'], item['qty'])

            card.write(self.mifare)

            self._log(f"Truck: {truck}", "ok")
            self._log(f"Driver: {driver_name} ({driver_id})", "ok")
            self._log(f"Items: {len(self.items)}", "ok")
            self._log("CARD WRITTEN SUCCESSFULLY!", "ok")

            info = f"TRIP CARD WRITTEN SUCCESSFULLY!\n\n"
            info += f"Trip ID:       {card.trip_id}\n"
            info += f"Truck Number:  {truck}\n"
            info += f"Driver:        {driver_name}\n"
            info += f"Driver ID:     {driver_id}\n"
            info += f"Sub-driver:    {subdriver_name or '(empty)'}\n\n"
            info += f"📦 Items Requested: {len(self.items)}\n"
            for item in self.items:
                info += f"  • {item['name']} × {item['qty']}\n"
            info += f"\n➡️ Driver can now take card to warehouse gate."

            messagebox.showinfo("Success", info)

        except Exception as e:
            self._log(f"Write error: {e}", "err")
            messagebox.showerror("Write Error", str(e))
        finally:
            self.mifare.disconnect()

    def _read_card(self):
        if not self.mifare.connect():
            messagebox.showerror("No Card",
                "Place MIFARE card on reader and try again!")
            return

        try:
            self._log("=" * 40)
            self._log("Reading trip card...", "info")

            card = TripCard()
            card.read(self.mifare)

            if not card.is_valid():
                messagebox.showwarning("Empty Card",
                    "This card has no trip data!")
                return

            self._clear_form()
            
            self.fields['trip_id'].insert(0, card.trip_id)
            self.fields['truck_number'].insert(0, card.truck_number)
            self.fields['driver_id'].insert(0, card.driver_id)
            self.fields['driver_name'].insert(0, card.driver_name)
            self.fields['subdriver_id'].insert(0, card.subdriver_id)
            self.fields['subdriver_name'].insert(0, card.subdriver_name)

            self.items = list(card.items)
            self._refresh_items()

            self._log(f"Truck: {card.truck_number}", "ok")
            self._log(f"Driver: {card.driver_name}", "ok")
            self._log(f"Items: {len(card.items)}", "ok")
            self._log("CARD READ SUCCESSFULLY!", "ok")

            info = f"TRIP CARD DATA\n\n"
            info += f"Trip ID:       {card.trip_id}\n"
            info += f"Truck Number:  {card.truck_number}\n"
            info += f"Driver:        {card.driver_name}\n"
            info += f"Driver ID:     {card.driver_id}\n"
            info += f"Sub-driver:    {card.subdriver_name or '(empty)'}\n"
            info += f"Items: {len(card.items)}\n"
            for item in card.items:
                info += f"  • {item['name']} × {item['qty']}\n"

            messagebox.showinfo("Card Data", info)

        except Exception as e:
            self._log(f"Read error: {e}", "err")
            messagebox.showerror("Read Error", str(e))
        finally:
            self.mifare.disconnect()

    def _clear_form(self):
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        
        self.item_name_entry.set("-- Select Item --")
        self.item_qty_entry.delete(0, tk.END)
        
        self.items = []
        self._refresh_items()
        
        self._log("Form cleared", "info")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = TripCardApp(root)
    root.mainloop()