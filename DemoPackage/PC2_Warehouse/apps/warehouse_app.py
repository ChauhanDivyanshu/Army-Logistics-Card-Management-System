# apps/warehouse_app.py
# 🏭 WAREHOUSE OPERATIONS - Indian Army Theme
# UHF Bulk Scanner + API Integration

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import threading
import random
from datetime import datetime
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'shared'))
sys.path.append(os.path.join(BASE, '..', 'database'))

from theme import COLORS

API_BASE = "http://localhost:5000/api/v1"


class WarehouseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("WAREHOUSE OPERATIONS — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x850")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.selected_req_id = None
        self.selected_item_name = None
        self.selected_container_id = None
        self.selected_required = 0
        self.selected_loaded = 0
        self.scan_count = 0
        self.fake_counter = 0
        self.polling_active = True
        self.all_pending_data = []
        self.scanning_in_progress = False

        # Try DB connection for real box data
        self.db = None
        try:
            from db_helper import DatabaseHelper
            self.db = DatabaseHelper()
            ok, _ = self.db.test_connection()
            if not ok:
                self.db = None
        except Exception:
            self.db = None

        self._setup_styles()
        self._build_ui()

        threading.Thread(target=self._poll_worker, daemon=True).start()
        self.root.after(500, self._fetch_pending)

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", foreground=COLORS["text"],
            rowheight=36, font=("Segoe UI", 9),
            fieldbackground="white",
            borderwidth=1)
        
        s.configure("Clean.Treeview.Heading",
            background=COLORS["primary"], foreground="white",
            font=("Segoe UI", 9, "bold"), padding=8, relief="flat",
            borderwidth=0)
        
        # ✅ Lock heading color (no white on hover)
        s.map("Clean.Treeview.Heading",
            background=[
                ("active", COLORS["primary"]),
                ("pressed", COLORS.get("primary_dark", "#0D3811")),
                ("!active", COLORS["primary"])
            ],
            foreground=[
                ("active", "white"),
                ("pressed", "white"),
                ("!active", "white")
            ],
            relief=[("active", "flat"), ("pressed", "flat")])
        
        # ✅ Selected row - gold (Army theme)
        s.map("Clean.Treeview",
              background=[("selected", "#FFE082")],
              foreground=[("selected", "#1B5E20")])

    def _build_ui(self):
        self._build_header()
        self._build_status_bar()
        self._build_tip_bar()

        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        left = tk.Frame(main, bg=COLORS["bg"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._build_pending(left)

        right = tk.Frame(main, bg=COLORS["bg"], width=420)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right.pack_propagate(False)
        self._build_scanner_panel(right)
        
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="🏭", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="WAREHOUSE OPERATIONS",
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
        self.time_var.set(datetime.now().strftime("%d %b %Y  |  %H:%M:%S"))
        self.root.after(1000, self._update_time)

    def _build_status_bar(self):
        status = tk.Frame(self.root, bg=COLORS["success"], height=26)
        status.pack(fill=tk.X)
        status.pack_propagate(False)
        self.status_var = tk.StringVar(value="Connecting to API...")
        tk.Label(status, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)
        self.refresh_var = tk.StringVar(value="UHF Reader: Ready")
        tk.Label(status, textvariable=self.refresh_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14)

    def _build_tip_bar(self):
        tip_bar = tk.Frame(self.root, bg=COLORS.get("primary_dark", "#0D3811"), height=32)
        tip_bar.pack(fill=tk.X)
        tip_bar.pack_propagate(False)
        tk.Label(tip_bar,
            text="📡 UHF Scanner detects ALL boxes in range simultaneously",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS.get("primary_dark", "#0D3811"), 
            fg=COLORS["accent"]).pack(side=tk.LEFT, padx=15, pady=7)
        tk.Button(tip_bar, text="RESET DEMO",
            command=self._reset_demo,
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["danger"], fg="white",
            relief=tk.FLAT, padx=15, pady=3,
            cursor="hand2").pack(side=tk.RIGHT, padx=15, pady=4)

    def _build_pending(self, parent):
        frame = tk.LabelFrame(parent, text="  PENDING LOADS  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        stats = tk.Frame(inner, bg=COLORS["primary"], height=32)
        stats.pack(fill=tk.X)
        stats.pack_propagate(False)
        self.stats_var = tk.StringVar(value="Loading...")
        tk.Label(stats, textvariable=self.stats_var,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=14, pady=6)
        tk.Button(stats, text="🔄 Refresh", command=self._fetch_pending,
                  font=("Segoe UI", 9, "bold"),
                  bg="white", fg=COLORS["primary"],
                  relief=tk.FLAT, padx=12, pady=2,
                  cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=4)

        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True)
        
        cols = ("trip_id", "truck", "driver", "item", "container", "req_qty", "loaded", "status")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="Clean.Treeview")
        
        # All center-aligned headers
        for col, label in [
            ("trip_id", "Trip ID"),
            ("truck", "Truck"),
            ("driver", "Driver"),
            ("item", "Item"),
            ("container", "From"),
            ("req_qty", "Req"),
            ("loaded", "Loaded"),
            ("status", "Status"),
        ]:
            self.tree.heading(col, text=label)
        
        # Compact widths
        self.tree.column("trip_id", width=90, anchor="center", stretch=False)
        self.tree.column("truck", width=110, anchor="center", stretch=False)
        self.tree.column("driver", width=140, anchor="center", stretch=False)
        self.tree.column("item", width=90, anchor="center", stretch=False)
        self.tree.column("container", width=80, anchor="center", stretch=False)
        self.tree.column("req_qty", width=55, anchor="center", stretch=False)
        self.tree.column("loaded", width=75, anchor="center", stretch=False)
        self.tree.column("status", width=120, anchor="center", stretch=True)
        
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        self.tree.tag_configure("processing", background="#FFE0B2", foreground="#F57C00")
        self.tree.tag_configure("loaded", background="#E3F2FD", foreground="#1565C0")
        self.tree.tag_configure("complete", background="#C8E6C9", foreground="#1B5E20")

    def _build_scanner_panel(self, parent):
        container = tk.LabelFrame(parent, text="  UHF BULK SCANNER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        container.pack(fill=tk.BOTH, expand=True)

        top_section = tk.Frame(container, bg=COLORS["bg_card"])
        top_section.pack(fill=tk.X, padx=2, pady=2)

        # MODE 1: Selected item scan
        mode1 = tk.LabelFrame(top_section,
            text=" MODE 1: Scan Selected Item ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["primary"])
        mode1.pack(fill=tk.X, padx=8, pady=8)
        
        self.sel_var = tk.StringVar(value="Select item from left to scan")
        self.sel_label = tk.Label(mode1, textvariable=self.sel_var,
            font=("Segoe UI", 9),
            bg=COLORS.get("primary_light", "#E8F5E9"), 
            fg=COLORS["primary"],
            relief=tk.SOLID, bd=1,
            pady=8, padx=8,
            wraplength=370, justify="left", anchor="w")
        self.sel_label.pack(fill=tk.X, padx=5, pady=5)
        
        self.scan_selected_btn = tk.Button(mode1,
            text="📡 SCAN ALL TAGS",
            command=self._scan_selected_bulk,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=8,
            cursor="hand2", state="disabled")
        self.scan_selected_btn.pack(fill=tk.X, padx=5, pady=(0, 5))

        # MODE 2: Truck bay scan
        mode2 = tk.LabelFrame(top_section,
            text=" MODE 2: Truck/Bay Scan (All Items) ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["primary"])
        mode2.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        self.scan_all_btn = tk.Button(mode2,
            text="🚛 SCAN ENTIRE TRUCK",
            command=self._scan_all_bulk,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["success"], fg="white",
            relief=tk.FLAT, pady=10,
            cursor="hand2")
        self.scan_all_btn.pack(fill=tk.X, padx=5, pady=5)

        # Status
        self.scan_status_var = tk.StringVar(value="✓ Scanner Ready")
        self.scan_status_lbl = tk.Label(top_section, 
            textvariable=self.scan_status_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS.get("primary_light", "#E8F5E9"), 
            fg=COLORS["primary"],
            relief=tk.SOLID, bd=1, pady=6)
        self.scan_status_lbl.pack(fill=tk.X, padx=8, pady=(2, 8))

        # Activity log
        log_frame = tk.LabelFrame(container,
            text="  ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        log_inner = tk.Frame(log_frame, bg="#212121")
        log_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.log_text = tk.Text(log_inner,
            font=("Consolas", 8),
            bg="#212121", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD, height=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        log_sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_sb.set)
        
        self._log("UHF Reader initialized", "ok")
        self._log("Ready to scan tags", "info")
        if self.db:
            self._log("DB connected - Using real box UIDs", "ok")
        else:
            self._log("DB offline - Using simulated UIDs", "warn")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Warehouse Operations",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="UHF Bulk Scanner Mode",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗", "warn": "⚠", "scan": "📡"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(tk.END, f"[{ts}] {icons.get(level, '•')} {msg}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _set_scan_status(self, text, color=None, bg=None):
        self.scan_status_var.set(text)
        try:
            if color: self.scan_status_lbl.configure(fg=color)
            if bg: self.scan_status_lbl.configure(bg=bg)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # API + DATA FETCH
    # ═══════════════════════════════════════════════════════

    def _fetch_pending(self):
        def worker():
            try:
                r = requests.get(f"{API_BASE}/wh/pending-loads", timeout=3)
                if r.ok:
                    data = r.json()
                    pending = data.get('pending', [])
                    self.all_pending_data = pending
                    self.root.after(0, self._update_pending, pending)
                    self.root.after(0, lambda: self.status_var.set("API: ✓ Connected"))
            except Exception:
                self.root.after(0, lambda: self.status_var.set("⚠ API Offline"))
        threading.Thread(target=worker, daemon=True).start()

    def _update_pending(self, pending):
        prev_sel = None
        if self.tree.selection():
            iid = self.tree.selection()[0]
            try:
                prev_sel = self.tree.item(iid)['values']
            except Exception:
                pass
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not pending:
            self.stats_var.set("✓ No pending loads")
            return
        
        proc = 0
        loaded = 0
        complete = 0
        
        for p in pending:
            req_id = p.get('req_id', '')
            trip_id = p.get('trip_id') or '—'
            truck = p.get('truck_number') or '—'
            driver = p.get('driver_name') or '—'
            item = p.get('item_name', '—')
            container = p.get('assigned_container') or '—'
            req_qty = p.get('required_qty', 0)
            loaded_qty = p.get('boxes_loaded', 0)
            status = p.get('status', '?')
            
            if status == 'COMPLETE':
                tag = 'complete'
                disp = "✓ COMPLETE"
                complete += 1
            elif status == 'LOADED':
                tag = 'loaded'
                disp = "📦 LOADED"
                loaded += 1
            else:
                tag = 'processing'
                disp = "⏳ PROCESSING"
                proc += 1
            
            iid = f"row-{req_id}"
            try:
                self.tree.insert("", "end", iid=iid,
                    values=(trip_id, truck, driver, item, container,
                           req_qty, f"{loaded_qty}/{req_qty}", disp),
                    tags=(tag,))
            except Exception:
                pass
        
        # Re-select previous if exists
        if prev_sel:
            for child in self.tree.get_children():
                if self.tree.item(child)['values'] == prev_sel:
                    self.tree.selection_set(child)
                    self._refresh_selected_info()
                    break
        
        self.stats_var.set(
            f"Total: {len(pending)}  |  ⏳ Processing: {proc}  |  📦 Loaded: {loaded}  |  ✓ Done: {complete}"
        )

    def _refresh_selected_info(self):
        if not self.tree.selection():
            return
        iid = self.tree.selection()[0]
        vals = self.tree.item(iid)['values']
        if len(vals) < 8:
            return
        try:
            loaded, required = str(vals[6]).split('/')
            self.selected_loaded = int(loaded)
            self.selected_required = int(required)
        except Exception:
            return
        
        status = str(vals[7])
        remaining = self.selected_required - self.selected_loaded
        item_name = vals[3]
        container = vals[4]
        trip_id = vals[0]
        truck = vals[1]
        driver = vals[2]
        
        self.sel_var.set(
            f"📦 Item: {item_name}\n"
            f"📋 From: {container}\n"
            f"🚛 Trip: {trip_id} | Truck: {truck}\n"
            f"👤 Driver: {driver}\n"
            f"📊 Loaded: {self.selected_loaded}/{self.selected_required}\n"
            f"⏳ Remaining: {remaining}"
        )
        
        if 'COMPLETE' in status or remaining <= 0:
            self.scan_selected_btn.configure(state="disabled", text="✓ COMPLETE")
        else:
            self.scan_selected_btn.configure(state="normal",
                text=f"📡 SCAN {remaining} TAGS")

    def _on_select(self, event):
        if not self.tree.selection():
            return
        iid = self.tree.selection()[0]
        vals = self.tree.item(iid)['values']
        if len(vals) < 8:
            return
        item_name = vals[3]
        trip_id = vals[0]
        container = vals[4]
        
        for p in self.all_pending_data:
            if (p.get('trip_id') == trip_id and 
                p.get('item_name') == item_name):
                self.selected_req_id = p.get('req_id')
                self.selected_item_name = item_name
                self.selected_container_id = p.get('assigned_container') or container
                break
        self._refresh_selected_info()

    # ═══════════════════════════════════════════════════════
    # GET REAL BOX UIDS FROM DATABASE
    # ═══════════════════════════════════════════════════════

    def _get_available_box_uids(self, container_id, max_count):
        """Get real box UIDs from database for this container."""
        if not self.db or not container_id:
            return []
        
        try:
            boxes = self.db.get_available_boxes_by_container(container_id)
            uids = [b['box_uid'] for b in boxes[:max_count]]
            return uids
        except Exception as e:
            self._log(f"DB query error: {e}", "err")
            return []

    # ═══════════════════════════════════════════════════════
    # MODE 1: SCAN SELECTED ITEM
    # ═══════════════════════════════════════════════════════

    def _scan_selected_bulk(self):
        if not self.selected_req_id:
            messagebox.showwarning("No Selection", "Select an item first!")
            return
        if self.scanning_in_progress:
            return
        remaining = self.selected_required - self.selected_loaded
        if remaining <= 0:
            messagebox.showinfo("Done", "Already complete!")
            return
        
        # Try to get real box UIDs
        real_uids = self._get_available_box_uids(self.selected_container_id, 1)
        scan_label = "REAL UHF tags" if real_uids else "SIMULATED tags"
        
        if not messagebox.askyesno("📡 UHF Bulk Scan",
            f"UHF READER ACTIVATING\n\n"
            f"Item: {self.selected_item_name}\n"
            f"From: {self.selected_container_id}\n"
            f"Quantity to load: {remaining}\n"
            f"Mode: {scan_label}\n\n"
            f"Start scan?"):
            return
        
        self.scanning_in_progress = True
        self.scan_selected_btn.configure(state="disabled", text="⏳ SCANNING...")
        self._set_scan_status("📡 SCANNING IN PROGRESS...", color=COLORS["warning"])
        
        self._log(f"UHF Bulk scan: {self.selected_item_name}", "scan")
        self._log(f"   Container: {self.selected_container_id}", "info")
        self._log(f"   Loading qty: {remaining}", "info")
        
        def worker():
            time.sleep(1.5)
            
            # Use real box UID if available, else simulate
            box_uid = real_uids[0] if real_uids else None
            if not box_uid:
                self.fake_counter += 1
                box_uid = f"SIM-{self.fake_counter:06d}"
            
            self.root.after(0, self._log, f"Detected box: {box_uid}", "ok")
            
            try:
                r = requests.post(f"{API_BASE}/wh/load-box",
                    json={
                        'box_uid': box_uid,
                        'req_id': self.selected_req_id,
                        'item_name': self.selected_item_name,
                        'operator': 'UHF_BULK_SCAN',
                        'qty_in_box': remaining
                    }, timeout=5)
                if r.ok:
                    result = r.json()
                    p = result.get('progress', {})
                    self.root.after(0, self._on_bulk_scan_success, box_uid, p)
                else:
                    self.root.after(0, self._on_scan_fail, f"HTTP {r.status_code}")
            except Exception as e:
                self.root.after(0, self._on_scan_fail, str(e))
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_bulk_scan_success(self, box_uid, progress):
        loaded = progress.get('loaded', 0)
        required = progress.get('required', 0)
        self.scanning_in_progress = False
        self.scan_selected_btn.configure(state="normal", text="📡 SCAN ALL TAGS")
        self._set_scan_status("✓ Scanner Ready", color=COLORS["primary"])
        self._log(f"Loaded! Total: {loaded}/{required}", "ok")
        self._fetch_pending()
        messagebox.showinfo("✓ Scan Complete",
            f"UHF Scan Successful!\n\n"
            f"Box: {box_uid}\n"
            f"Loaded: {loaded}/{required}")

    def _on_scan_fail(self, error):
        self.scanning_in_progress = False
        self.scan_selected_btn.configure(state="normal", text="📡 SCAN ALL TAGS")
        self._set_scan_status("✓ Scanner Ready", color=COLORS["primary"])
        self._log(f"Scan failed: {error}", "err")
        messagebox.showerror("Scan Failed", error)

    # ═══════════════════════════════════════════════════════
    # MODE 2: SCAN ENTIRE TRUCK
    # ═══════════════════════════════════════════════════════

    def _scan_all_bulk(self):
        if self.scanning_in_progress:
            return
        
        incomplete = [p for p in self.all_pending_data 
            if p.get('status') != 'COMPLETE'
            and (p.get('required_qty', 0) - p.get('boxes_loaded', 0)) > 0]
        
        if not incomplete:
            messagebox.showinfo("✓ All Done!", "All items complete!")
            return
        
        total_boxes = sum(p['required_qty'] - p.get('boxes_loaded', 0) for p in incomplete)
        items_list = "\n".join([
            f"  • {p['item_name']}: {p['required_qty'] - p.get('boxes_loaded', 0)} units"
            for p in incomplete
        ])
        
        if not messagebox.askyesno("🚛 TRUCK BAY SCAN",
            f"SCANNING ENTIRE LOADING BAY\n\n"
            f"Items to load:\n{items_list}\n\n"
            f"Total quantity: {total_boxes}\n\n"
            f"Activate UHF reader?"):
            return
        
        self.scanning_in_progress = True
        self.scan_all_btn.configure(state="disabled", text="⏳ SCANNING...")
        self._set_scan_status("🚛 TRUCK BAY SCAN...", color=COLORS["warning"])
        self._log("TRUCK BAY SCAN INITIATED", "scan")
        self._log(f"   Total qty: {total_boxes}", "info")
        
        def worker():
            scan_duration = min(3, 1 + (total_boxes / 100))
            time.sleep(scan_duration)
            self.root.after(0, self._log, 
                f"Detected all tags in {scan_duration:.1f}s!", "ok")
            
            success = 0
            failed = 0
            
            for p in incomplete:
                req_id = p['req_id']
                item_name = p['item_name']
                container = p.get('assigned_container')
                remaining = p['required_qty'] - p.get('boxes_loaded', 0)
                if remaining <= 0:
                    continue
                
                # Get real box UID
                real_uids = self._get_available_box_uids(container, 1)
                if real_uids:
                    box_uid = real_uids[0]
                else:
                    self.fake_counter += 1
                    box_uid = f"TRUCK-SIM-{self.fake_counter:06d}"
                
                try:
                    r = requests.post(f"{API_BASE}/wh/load-box",
                        json={
                            'box_uid': box_uid,
                            'req_id': req_id,
                            'item_name': item_name,
                            'operator': 'TRUCK_BAY_UHF',
                            'qty_in_box': remaining
                        }, timeout=5)
                    if r.ok:
                        success += 1
                        self.root.after(0, self._log, 
                            f"   ✓ {item_name}: {remaining} units", "ok")
                    else:
                        failed += 1
                        self.root.after(0, self._log, 
                            f"   ✗ {item_name} failed", "err")
                except Exception as e:
                    failed += 1
                    self.root.after(0, self._log, 
                        f"   ✗ {item_name}: {e}", "err")
            
            self.root.after(0, self._on_truck_scan_complete, success, failed, total_boxes)
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_truck_scan_complete(self, success, failed, total_boxes):
        self.scanning_in_progress = False
        self.scan_all_btn.configure(state="normal", text="🚛 SCAN ENTIRE TRUCK")
        self._set_scan_status("✓ Scanner Ready", color=COLORS["primary"])
        self._log(f"TRUCK SCAN COMPLETE!", "ok")
        self._log(f"   Items: {success} | Failed: {failed}", "ok")
        self._fetch_pending()
        messagebox.showinfo("✓ SCAN COMPLETE",
            f"Truck scanned successfully!\n\n"
            f"Items loaded: {success}\n"
            f"Total qty: {total_boxes}\n"
            f"Failed: {failed}")

    def _reset_demo(self):
        if not messagebox.askyesno("Reset Demo", 
            "Clear all loading data?\n\nThis will remove all active trips."):
            return
        
        def worker():
            try:
                requests.post(f"{API_BASE}/admin/clear-trips", timeout=5)
                self.root.after(0, self._log, "Demo reset complete!", "ok")
                self.root.after(0, self._fetch_pending)
                self.root.after(0, lambda: messagebox.showinfo("Reset Done", 
                    "All trip data cleared!\nDB inventory preserved."))
            except Exception as e:
                self.root.after(0, self._log, f"Reset error: {e}", "err")
        threading.Thread(target=worker, daemon=True).start()

    def _poll_worker(self):
        while self.polling_active:
            time.sleep(3)
            try:
                self.root.after(0, self._fetch_pending)
            except Exception:
                break


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
    app = WarehouseApp(root)  # ← Replace with your app class
    root.mainloop()