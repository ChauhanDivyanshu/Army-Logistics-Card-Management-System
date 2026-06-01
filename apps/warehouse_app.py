# apps/warehouse_app.py
# 🏭 WAREHOUSE OPERATIONS - Optimized Layout

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

from theme import COLORS

API_BASE = "http://localhost:5000/api/v1"


class WarehouseApp:

    def __init__(self, root):
        self.root = root
        self.root.title("🏭 WAREHOUSE OPERATIONS - UHF Bulk Scanner")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.selected_req_id = None
        self.selected_item_name = None
        self.selected_required = 0
        self.selected_loaded = 0
        self.scan_count = 0
        self.fake_counter = 0
        self.polling_active = True
        self.all_pending_data = []
        self.scanning_in_progress = False

        self._setup_styles()
        self._build_ui()

        threading.Thread(target=self._poll_worker, daemon=True).start()
        self.root.after(500, self._fetch_pending)

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Pending.Treeview",
            background="white", foreground="black",
            rowheight=42, font=("Segoe UI", 9))
        s.configure("Pending.Treeview.Heading",
            background="#E65100", foreground="white",
            font=("Segoe UI", 9, "bold"), padding=6)
        s.map("Pending.Treeview",
              background=[("selected", "#FF9800")],
              foreground=[("selected", "white")])

    def _build_ui(self):
        # Footer first
        self._build_footer()
        
        # Header
        self._build_header()
        
        # Status bars
        self._build_status_bars()
        
        # Tip bar with reset
        self._build_tip_bar()

        # Main split container
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # LEFT: Pending Loads (takes most space)
        left = tk.Frame(main, bg=COLORS["bg"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._build_pending(left)

        # RIGHT: UHF Scanner Panel (FIXED width 420px)
        right = tk.Frame(main, bg=COLORS["bg"], width=420)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right.pack_propagate(False)  # Maintain fixed width
        
        self._build_scanner_panel(right)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg="#E65100", height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        
        tk.Label(hdr, text="🏭  WAREHOUSE OPERATIONS",
                 font=("Segoe UI", 16, "bold"),
                 bg="#E65100", fg="white").pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(hdr, text="UHF Bulk Scanner",
                 font=("Segoe UI", 10, "italic"),
                 bg="#E65100", fg="#FFE0B2").pack(side=tk.LEFT, pady=20)
        
        self.time_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.time_var,
                 font=("Segoe UI", 11, "bold"),
                 bg="#E65100", fg="#FFEB3B").pack(side=tk.RIGHT, padx=20)
        self._update_time()

    def _update_time(self):
        self.time_var.set(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(1000, self._update_time)

    def _build_status_bars(self):
        # Status bar
        status = tk.Frame(self.root, bg=COLORS["success"], height=26)
        status.pack(fill=tk.X)
        status.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="🌐 Connecting to API...")
        tk.Label(status, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)
        
        self.refresh_var = tk.StringVar(value="📡 UHF Reader: Ready")
        tk.Label(status, textvariable=self.refresh_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="#FFEB3B").pack(side=tk.RIGHT, padx=14)

    def _build_tip_bar(self):
        # Tip + Reset bar
        tip_bar = tk.Frame(self.root, bg=COLORS["dark"], height=36)
        tip_bar.pack(fill=tk.X)
        tip_bar.pack_propagate(False)
        
        tk.Label(tip_bar,
            text="💡 TIP: UHF Scanner detects ALL boxes in range at once (real behavior)",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["dark"], fg="#FFEB3B").pack(side=tk.LEFT, padx=15, pady=8)
        
        tk.Button(tip_bar, text="🔄 RESET DEMO",
            command=self._reset_demo,
            font=("Segoe UI", 9, "bold"),
            bg="#C62828", fg="white",
            relief=tk.FLAT, padx=15, pady=4,
            cursor="hand2").pack(side=tk.RIGHT, padx=15, pady=5)

    def _build_pending(self, parent):
        """Build pending loads panel (LEFT side)."""
        frame = tk.LabelFrame(parent, text="  📦  PENDING LOADS  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg="#E65100",
            bd=2, relief=tk.GROOVE)
        frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Stats bar
        stats = tk.Frame(inner, bg="#E65100", height=32)
        stats.pack(fill=tk.X, pady=(0, 6))
        stats.pack_propagate(False)
        
        self.stats_var = tk.StringVar(value="Loading...")
        tk.Label(stats, textvariable=self.stats_var,
                 font=("Segoe UI", 10, "bold"),
                 bg="#E65100", fg="white").pack(side=tk.LEFT, padx=14, pady=6)
        
        tk.Button(stats, text="🔄 Refresh",
                  command=self._fetch_pending,
                  font=("Segoe UI", 9, "bold"),
                  bg="white", fg="#E65100",
                  relief=tk.FLAT, padx=12, pady=2,
                  cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=4)

        # Treeview with optimized columns
        tf = tk.Frame(inner, bg=COLORS["white"])
        tf.pack(fill=tk.BOTH, expand=True)
        
        # COMPACT but readable columns
        cols = ("trip_id", "truck", "driver", "item", "req_qty", "loaded", "status")
        self.tree = ttk.Treeview(tf, columns=cols,
            show="headings", style="Pending.Treeview")
        
        # Headings - compact text
        self.tree.heading("trip_id", text="Trip ID")
        self.tree.heading("truck", text="🚛 Truck")
        self.tree.heading("driver", text="👤 Driver")
        self.tree.heading("item", text="📦 Item")
        self.tree.heading("req_qty", text="Req")
        self.tree.heading("loaded", text="Loaded")
        self.tree.heading("status", text="Status")
        
        # Column widths - optimized
        self.tree.column("trip_id", width=85, anchor="center", stretch=False)
        self.tree.column("truck", width=120, anchor="center", stretch=False)
        self.tree.column("driver", width=160, anchor="w", stretch=True)
        self.tree.column("item", width=110, anchor="w", stretch=False)
        self.tree.column("req_qty", width=65, anchor="center", stretch=False)
        self.tree.column("loaded", width=80, anchor="center", stretch=False)
        self.tree.column("status", width=120, anchor="center", stretch=False)
        
        # Only vertical scrollbar (no horizontal)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Tags
        self.tree.tag_configure("processing",
            background="#FFF3E0", foreground="#E65100")
        self.tree.tag_configure("loaded",
            background="#BBDEFB", foreground="#0D47A1")
        self.tree.tag_configure("complete",
            background="#A5D6A7", foreground="#1B5E20",
            font=("Segoe UI", 9, "bold"))

    def _build_scanner_panel(self, parent):
        """Build UHF Scanner panel with proper space management."""
        
        # Main container
        container = tk.LabelFrame(parent, text="  📡  UHF BULK SCANNER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["info"],
            bd=2, relief=tk.GROOVE)
        container.pack(fill=tk.BOTH, expand=True)

        # ═══════════════════════════════════════════════════════
        # TOP SECTION: Scanner Controls (fixed height)
        # ═══════════════════════════════════════════════════════
        
        top_section = tk.Frame(container, bg=COLORS["white"])
        top_section.pack(fill=tk.X, padx=8, pady=8)

        # ─── MODE 1: Scan Selected ───
        mode1 = tk.LabelFrame(top_section,
            text=" 📦 MODE 1: Scan Selected Item ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["white"], fg=COLORS["info"])
        mode1.pack(fill=tk.X, pady=(0, 6))
        
        # Selected display - COMPACT
        self.sel_var = tk.StringVar(value="⚠ Select item from left")
        self.sel_label = tk.Label(mode1, textvariable=self.sel_var,
            font=("Segoe UI", 9),
            bg="#FFF8E1", fg="#E65100",
            relief=tk.SOLID, bd=1,
            pady=6, padx=8,
            wraplength=370,
            justify="left",
            anchor="w")
        self.sel_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Scan button - compact
        self.scan_selected_btn = tk.Button(mode1,
            text="📡  SCAN ALL TAGS",
            command=self._scan_selected_bulk,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=8,
            cursor="hand2", state="disabled")
        self.scan_selected_btn.pack(fill=tk.X, padx=5, pady=(0, 5))

        # ─── MODE 2: Truck Bay ───
        mode2 = tk.LabelFrame(top_section,
            text=" 🚛 MODE 2: Truck/Bay Scan ",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS["white"], fg="#1B5E20")
        mode2.pack(fill=tk.X, pady=(0, 6))
        
        self.scan_all_btn = tk.Button(mode2,
            text="🚛  SCAN ENTIRE TRUCK",
            command=self._scan_all_bulk,
            font=("Segoe UI", 11, "bold"),
            bg="#1B5E20", fg="#FFEB3B",
            relief=tk.FLAT, pady=10,
            cursor="hand2")
        self.scan_all_btn.pack(fill=tk.X, padx=5, pady=5)

        # Scan status - small
        self.scan_status_var = tk.StringVar(value="🟢 Scanner Ready")
        self.scan_status_lbl = tk.Label(top_section, 
            textvariable=self.scan_status_var,
            font=("Segoe UI", 10, "bold"),
            bg="#E8F5E9", fg="#1B5E20",
            relief=tk.SOLID, bd=1, pady=6)
        self.scan_status_lbl.pack(fill=tk.X, pady=(2, 0))

        # ═══════════════════════════════════════════════════════
        # BOTTOM SECTION: Activity Log (EXPANDS!)
        # ═══════════════════════════════════════════════════════
        
        log_frame = tk.LabelFrame(container,
            text="  📋  SCAN ACTIVITY LOG  ",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg"], fg=COLORS["info"],
            bd=1, relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        log_inner = tk.Frame(log_frame, bg=COLORS["white"])
        log_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Log text widget - takes all remaining space
        self.log_text = tk.Text(log_inner,
            font=("Consolas", 8),
            bg="#0d1117", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD,
            height=10)  # Minimum 10 lines visible
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_sb = ttk.Scrollbar(log_inner, command=self.log_text.yview)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_sb.set)
        
        self._log("UHF Reader initialized", "ok")
        self._log("Ready to scan tags", "info")

    def _build_footer(self):
        ft = tk.Frame(self.root, bg=COLORS["dark"], height=24)
        ft.pack(fill=tk.X, side=tk.BOTTOM)
        ft.pack_propagate(False)
        tk.Label(ft, text="© 2025 Indian Army | Warehouse Station",
            font=("Segoe UI", 8), bg=COLORS["dark"],
            fg=COLORS["muted"]).pack(side=tk.LEFT, padx=14, pady=4)
        tk.Label(ft, text="UHF Bulk Scanner Mode",
            font=("Segoe UI", 8), bg=COLORS["dark"],
            fg=COLORS["muted"]).pack(side=tk.RIGHT, padx=14, pady=4)

    # ═══════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════

    def _log(self, msg, level="info"):
        icons = {"info": "ℹ", "ok": "✓", "err": "✗", "warn": "⚠", "scan": "📡"}
        ts = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert(tk.END, 
                f"[{ts}] {icons.get(level, '•')} {msg}\n")
            self.log_text.see(tk.END)
        except Exception:
            pass

    def _set_scan_status(self, text, color="#1B5E20", bg="#E8F5E9"):
        self.scan_status_var.set(text)
        try:
            self.scan_status_lbl.configure(fg=color, bg=bg)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # API CALLS
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
                    self.root.after(0, lambda: self.status_var.set(
                        "🗄 DB: ✓ | 🌐 API: ✓ Connected"))
            except Exception:
                self.root.after(0, lambda: self.status_var.set("🌐 API Offline"))
        
        threading.Thread(target=worker, daemon=True).start()

    def _update_pending(self, pending):
        """Update treeview with optimized field display."""
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
            self.stats_var.set("📊 No pending loads")
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
            req_qty = p.get('required_qty', 0)
            loaded_qty = p.get('boxes_loaded', 0)
            status = p.get('status', '?')
            
            if status == 'COMPLETE':
                tag = 'complete'
                disp = "✅ COMPLETE"
                complete += 1
            elif status == 'LOADED':
                tag = 'loaded'
                disp = "🔵 LOADED"
                loaded += 1
            else:
                tag = 'processing'
                disp = "🔴 PROCESSING"
                proc += 1
            
            iid = f"row-{req_id}"
            try:
                self.tree.insert("", "end", iid=iid,
                    values=(
                        trip_id,
                        truck,
                        driver,
                        item,
                        req_qty,
                        f"{loaded_qty}/{req_qty}",
                        disp
                    ),
                    tags=(tag,))
            except Exception:
                pass
        
        # Restore selection
        if prev_sel:
            for child in self.tree.get_children():
                if self.tree.item(child)['values'] == prev_sel:
                    self.tree.selection_set(child)
                    self._refresh_selected_info()
                    break
        
        self.stats_var.set(
            f"📊 Total: {len(pending)} | "
            f"🔴 {proc} Processing | 🔵 {loaded} Loaded | ✅ {complete} Done"
        )

    def _refresh_selected_info(self):
        if not self.tree.selection():
            return
        
        iid = self.tree.selection()[0]
        vals = self.tree.item(iid)['values']
        if len(vals) < 7:
            return
        
        try:
            loaded, required = str(vals[5]).split('/')
            self.selected_loaded = int(loaded)
            self.selected_required = int(required)
        except Exception:
            return
        
        status = str(vals[6])
        remaining = self.selected_required - self.selected_loaded
        
        # Find actual req_id from pending data
        item_name = vals[3]
        trip_id = vals[0]
        truck = vals[1]
        driver = vals[2]
        
        # Compact display for narrow panel
        self.sel_var.set(
            f"📦 {item_name}\n"
            f"🎫 Trip: {trip_id}\n"
            f"🚛 Truck: {truck}\n"
            f"👤 Driver: {driver}\n"
            f"📊 Loaded: {self.selected_loaded}/{self.selected_required}\n"
            f"⏳ Remaining: {remaining}"
        )
        
        if 'COMPLETE' in status or remaining <= 0:
            self.scan_selected_btn.configure(state="disabled",
                text="✅ COMPLETE")
        else:
            # Show count in button
            self.scan_selected_btn.configure(state="normal",
                text=f"📡  SCAN ALL TAGS\n({remaining} boxes)")

    def _on_select(self, event):
        if not self.tree.selection():
            return
        
        iid = self.tree.selection()[0]
        vals = self.tree.item(iid)['values']
        if len(vals) < 7:
            return
        
        # Get actual req_id from pending data
        item_name = vals[3]
        trip_id = vals[0]
        
        # Find matching pending item
        for p in self.all_pending_data:
            if (p.get('trip_id') == trip_id and 
                p.get('item_name') == item_name):
                self.selected_req_id = p.get('req_id')
                self.selected_item_name = item_name
                break
        
        self._refresh_selected_info()

    # ═══════════════════════════════════════════════════════
    # MODE 1: BULK SCAN SELECTED
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
        
        confirm = messagebox.askyesno(
            "📡 UHF Bulk Scan",
            f"📡 UHF READER ACTIVATING\n\n"
            f"Item: {self.selected_item_name}\n"
            f"Boxes to detect: {remaining}\n\n"
            f"⚡ Reader will detect ALL {remaining} boxes\n"
            f"in range simultaneously.\n\n"
            f"Start scan?"
        )
        
        if not confirm:
            return
        
        self.scanning_in_progress = True
        self.scan_selected_btn.configure(state="disabled",
            text="📡 SCANNING...")
        self._set_scan_status("📡 SCANNING IN PROGRESS...",
            color="#E65100", bg="#FFF3E0")
        
        self._log(f"📡 UHF Bulk scan: {self.selected_item_name}", "scan")
        self._log(f"   Detecting {remaining} tags...", "info")
        
        def worker():
            time.sleep(1.5)  # Simulate UHF read time
            
            detected_tags = []
            for i in range(remaining):
                self.fake_counter += 1
                epc = f"UHF-EPC-{self.fake_counter:08d}-{random.randint(1000, 9999)}"
                detected_tags.append(epc)
            
            self.root.after(0, self._log, 
                f"📡 Detected {len(detected_tags)} tags!", "ok")
            
            try:
                r = requests.post(
                    f"{API_BASE}/wh/load-box",
                    json={
                        'box_uid': f"BULK-{detected_tags[0]}",
                        'req_id': self.selected_req_id,
                        'item_name': self.selected_item_name,
                        'operator': 'UHF_BULK_SCAN',
                        'qty_in_box': remaining
                    },
                    timeout=5
                )
                
                if r.ok:
                    result = r.json()
                    p = result.get('progress', {})
                    self.root.after(0, self._on_bulk_scan_success,
                        len(detected_tags), p)
                else:
                    self.root.after(0, self._on_scan_fail, "API Error")
            except Exception as e:
                self.root.after(0, self._on_scan_fail, str(e))
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_bulk_scan_success(self, tag_count, progress):
        loaded = progress.get('loaded', 0)
        required = progress.get('required', 0)
        
        self.scanning_in_progress = False
        self.scan_selected_btn.configure(state="normal",
            text="📡  SCAN ALL TAGS")
        self._set_scan_status("🟢 Scanner Ready",
            color="#1B5E20", bg="#E8F5E9")
        
        self._log(f"✅ Loaded {tag_count} boxes! Total: {loaded}/{required}", "ok")
        
        self._fetch_pending()
        
        messagebox.showinfo("📡 Scan Complete",
            f"✅ UHF Bulk Scan Successful!\n\n"
            f"Tags Detected: {tag_count}\n"
            f"Total Loaded: {loaded}/{required}")

    def _on_scan_fail(self, error):
        self.scanning_in_progress = False
        self.scan_selected_btn.configure(state="normal",
            text="📡  SCAN ALL TAGS")
        self._set_scan_status("🟢 Scanner Ready",
            color="#1B5E20", bg="#E8F5E9")
        self._log(f"✗ Scan failed: {error}", "err")
        messagebox.showerror("Scan Failed", error)

    # ═══════════════════════════════════════════════════════
    # MODE 2: TRUCK BAY SCAN
    # ═══════════════════════════════════════════════════════

    def _scan_all_bulk(self):
        if self.scanning_in_progress:
            return
        
        incomplete = [
            p for p in self.all_pending_data 
            if p.get('status') != 'COMPLETE'
            and (p.get('required_qty', 0) - p.get('boxes_loaded', 0)) > 0
        ]
        
        if not incomplete:
            messagebox.showinfo("All Done!", 
                "🎉 All items complete!")
            return
        
        total_boxes = sum(
            p['required_qty'] - p.get('boxes_loaded', 0) 
            for p in incomplete
        )
        
        items_list = "\n".join([
            f"  • {p['item_name']}: {p['required_qty'] - p.get('boxes_loaded', 0)} boxes"
            for p in incomplete
        ])
        
        confirm = messagebox.askyesno(
            "🚛 TRUCK BAY SCAN",
            f"🚛 SCANNING ENTIRE LOADING BAY\n\n"
            f"Items:\n{items_list}\n\n"
            f"📊 Total tags: {total_boxes}\n\n"
            f"⚡ All boxes in 1 scan!\n\n"
            f"Activate UHF reader?"
        )
        
        if not confirm:
            return
        
        self.scanning_in_progress = True
        self.scan_all_btn.configure(state="disabled",
            text="🚛 SCANNING...")
        self._set_scan_status("📡 TRUCK BAY SCAN...",
            color="#E65100", bg="#FFF3E0")
        
        self._log("🚛 TRUCK BAY SCAN INITIATED", "scan")
        self._log(f"   Detecting {total_boxes} tags...", "info")
        
        def worker():
            scan_duration = min(3, 1 + (total_boxes / 100))
            time.sleep(scan_duration)
            
            self.root.after(0, self._log,
                f"📡 Detected {total_boxes} tags in {scan_duration:.1f}s!", "ok")
            
            success = 0
            failed = 0
            
            for p in incomplete:
                req_id = p['req_id']
                item_name = p['item_name']
                remaining = p['required_qty'] - p.get('boxes_loaded', 0)
                
                if remaining <= 0:
                    continue
                
                self.fake_counter += 1
                epc = f"TRUCK-EPC-{self.fake_counter:08d}"
                
                try:
                    r = requests.post(
                        f"{API_BASE}/wh/load-box",
                        json={
                            'box_uid': epc,
                            'req_id': req_id,
                            'item_name': item_name,
                            'operator': 'TRUCK_BAY_UHF',
                            'qty_in_box': remaining
                        },
                        timeout=5
                    )
                    
                    if r.ok:
                        success += 1
                        self.root.after(0, self._log,
                            f"   ✓ {item_name}: {remaining} boxes", "ok")
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
            
            self.root.after(0, self._on_truck_scan_complete, 
                success, failed, total_boxes)
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_truck_scan_complete(self, success, failed, total_boxes):
        self.scanning_in_progress = False
        self.scan_all_btn.configure(state="normal",
            text="🚛  SCAN ENTIRE TRUCK")
        self._set_scan_status("🟢 Scanner Ready",
            color="#1B5E20", bg="#E8F5E9")
        
        self._log(f"🎉 TRUCK SCAN COMPLETE!", "ok")
        self._log(f"   Items: {success} | Boxes: {total_boxes}", "ok")
        
        self._fetch_pending()
        
        messagebox.showinfo("🎉 SCAN COMPLETE",
            f"✅ Truck scanned successfully!\n\n"
            f"📊 Items: {success}\n"
            f"📦 Boxes: {total_boxes}\n"
            f"❌ Failed: {failed}")

    # ═══════════════════════════════════════════════════════
    # RESET
    # ═══════════════════════════════════════════════════════

    def _reset_demo(self):
        if not messagebox.askyesno("Reset Demo",
            "⚠ Clear all loading data?"):
            return
        
        def worker():
            try:
                # Clear in-memory trips
                requests.post(f"{API_BASE}/admin/clear-trips", timeout=5)
                self.root.after(0, self._log, "🔄 Demo reset!", "ok")
                self.root.after(0, self._fetch_pending)
                self.root.after(0, lambda: messagebox.showinfo(
                    "Reset Done", "✅ All data cleared!"))
            except Exception as e:
                self.root.after(0, self._log, f"Reset error: {e}", "err")
        
        threading.Thread(target=worker, daemon=True).start()

    # ═══════════════════════════════════════════════════════
    # POLLING
    # ═══════════════════════════════════════════════════════

    def _poll_worker(self):
        while self.polling_active:
            time.sleep(3)
            try:
                self.root.after(0, self._fetch_pending)
            except Exception:
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = WarehouseApp(root)
    root.mainloop()