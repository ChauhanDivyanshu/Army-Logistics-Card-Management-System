# apps/dashboard_app.py
# 📊 ADMIN DASHBOARD - Fixed Version

import tkinter as tk
from tkinter import ttk
import sys
import os
import time
import threading
from datetime import datetime
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS

API_BASE = "http://localhost:5000/api/v1"


class DashboardApp:

    def __init__(self, root):
        self.root = root
        self.root.title("📊 ADMIN DASHBOARD — Army Logistics")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x900")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.polling_active = True
        self.last_scan_id = 0  # Track latest scan for activity log

        self._build_ui()
        self._start_polling()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#6A1B9A", height=70)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="📊  ADMIN DASHBOARD",
                 font=("Segoe UI", 18, "bold"),
                 bg="#6A1B9A", fg="white").pack(side=tk.LEFT, padx=20, pady=15)
        
        self.time_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.time_var,
                 font=("Segoe UI", 11, "bold"),
                 bg="#6A1B9A", fg="#FFEB3B").pack(side=tk.RIGHT, padx=20)
        self._update_time()

        # Status bar
        status = tk.Frame(self.root, bg=COLORS["success"], height=24)
        status.pack(fill=tk.X)
        status.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="🟢 LIVE - Refreshing every 3 seconds")
        tk.Label(status, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)
        
        self.last_refresh_var = tk.StringVar(value="Last update: —")
        tk.Label(status, textvariable=self.last_refresh_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

        # Main container
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Top: Stat cards
        self._build_stat_cards(main)

        # Middle: Active operations
        self._build_active_panel(main)

        # Bottom: Activity feed
        self._build_activity_panel(main)

    def _update_time(self):
        self.time_var.set(f"🕐 {datetime.now().strftime('%d %b %Y | %H:%M:%S')}")
        self.root.after(1000, self._update_time)

    def _build_stat_cards(self, parent):
        cards_frame = tk.Frame(parent, bg=COLORS["bg"])
        cards_frame.pack(fill=tk.X, pady=(0, 12))
        
        for i in range(5):
            cards_frame.columnconfigure(i, weight=1, uniform="col")
        
        self.stat_vars = {}
        
        cards_data = [
            ("👥", "Total Soldiers", "soldiers", "#1565C0"),
            ("📦", "Active Loads", "active", "#E65100"),
            ("✅", "Completed", "complete", "#2E7D32"),
            ("📡", "Total Box Scans", "scans", "#7B1FA2"),
            ("⏳", "Pending", "pending", "#C62828"),
        ]
        
        for i, (icon, label, key, color) in enumerate(cards_data):
            card = tk.Frame(cards_frame, bg=COLORS["white"],
                            relief=tk.SOLID, bd=1)
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            
            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
            
            tk.Label(card, text=icon,
                     font=("Segoe UI Emoji", 28),
                     bg=COLORS["white"]).pack(pady=(15, 5))
            
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var,
                     font=("Segoe UI", 24, "bold"),
                     bg=COLORS["white"], fg=color).pack()
            
            tk.Label(card, text=label,
                     font=("Segoe UI", 9),
                     bg=COLORS["white"], fg=COLORS["muted"]).pack(pady=(0, 15))

    def _build_active_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text="  🚀  ACTIVE LOADING OPERATIONS  ",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg"], fg="#6A1B9A",
            bd=2, relief=tk.GROOVE
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        inner = tk.Frame(frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Scrollable canvas
        canvas = tk.Canvas(inner, bg=COLORS["white"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.active_container = tk.Frame(canvas, bg=COLORS["white"])
        canvas.create_window((0, 0), window=self.active_container, anchor="nw")
        
        self.active_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

    def _build_activity_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text="  📋  RECENT ACTIVITY  ",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["bg"], fg="#6A1B9A",
            bd=2, relief=tk.GROOVE, height=200
        )
        frame.pack(fill=tk.X)
        frame.pack_propagate(False)
        
        inner = tk.Frame(frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.activity_text = tk.Text(
            inner, font=("Consolas", 9),
            bg="#0d1117", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD
        )
        self.activity_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = ttk.Scrollbar(inner, command=self.activity_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.activity_text.config(yscrollcommand=sb.set)
        
        self._log_activity("📊 Dashboard started - monitoring all operations")

    def _log_activity(self, msg):
        ts = time.strftime("%H:%M:%S")
        try:
            self.activity_text.insert(tk.END, f"[{ts}] {msg}\n")
            self.activity_text.see(tk.END)
        except Exception:
            pass

    def _update_active_operations(self, soldiers_data):
        """Update active operations cards."""
        # Clear existing
        for widget in self.active_container.winfo_children():
            widget.destroy()
        
        if not soldiers_data:
            tk.Label(self.active_container,
                     text="💤 No active loading operations\n\n"
                          "Soldiers ke ASSIGN ALL click karne pe yaha dikhega.",
                     font=("Segoe UI", 11, "italic"),
                     bg=COLORS["white"], fg=COLORS["muted"],
                     justify="center").pack(pady=60)
            return
        
        for sdata in soldiers_data:
            self._create_operation_card(sdata)

    def _create_operation_card(self, sdata):
        """Create a card for one active operation."""
        soldier_id = sdata.get('soldier_id', '?')
        soldier_name = sdata.get('soldier_name', 'Unknown')
        items = sdata.get('items', [])
        
        # Calculate progress
        total_required = sum(i.get('required_qty', 0) for i in items)
        total_loaded = sum(i.get('boxes_loaded', 0) for i in items)
        pct = (total_loaded / total_required * 100) if total_required > 0 else 0
        
        # All complete check
        all_complete = all(i.get('status') == 'COMPLETE' for i in items)
        any_loading = any(i.get('status') in ('LOADED', 'PROCESSING') for i in items)
        
        if all_complete:
            color = "#2E7D32"
            status = "✅ COMPLETE"
        elif pct >= 50:
            color = "#1565C0"
            status = "🔵 LOADING"
        elif any_loading:
            color = "#E65100"
            status = "🔴 PROCESSING"
        else:
            color = "#9E9E9E"
            status = "⏳ WAITING"
        
        # Card
        card = tk.Frame(self.active_container, bg=COLORS["white"],
                        relief=tk.SOLID, bd=1)
        card.pack(fill=tk.X, pady=5, padx=4)
        
        tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
        
        # Header
        hdr = tk.Frame(card, bg=COLORS["white"])
        hdr.pack(fill=tk.X, padx=12, pady=8)
        
        tk.Label(hdr, text=f"🪖 {soldier_name}",
                 font=("Segoe UI", 12, "bold"),
                 bg=COLORS["white"], fg=color).pack(side=tk.LEFT)
        
        tk.Label(hdr, text=f"ID: {soldier_id}",
                 font=("Segoe UI", 9),
                 bg=COLORS["white"], fg=COLORS["muted"]).pack(side=tk.LEFT, padx=10)
        
        tk.Label(hdr, text=status,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["white"], fg=color).pack(side=tk.RIGHT)
        
        # Overall progress bar
        prog_frame = tk.Frame(card, bg=COLORS["white"])
        prog_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        tk.Label(prog_frame, 
                 text=f"Overall Progress: {total_loaded}/{total_required} units ({pct:.0f}%)",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["white"]).pack(anchor="w", pady=(0, 3))
        
        # Progress bar visual
        bar_bg = tk.Frame(prog_frame, bg="#E0E0E0", height=10)
        bar_bg.pack(fill=tk.X)
        
        if pct > 0:
            bar_fill = tk.Frame(bar_bg, bg=color, height=10)
            bar_fill.place(relwidth=min(pct/100, 1.0), relheight=1)
        
        # Items detail
        items_frame = tk.Frame(card, bg="#F5F5F5")
        items_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        
        for item in items:
            item_name = item.get('item_name', '?')
            req = item.get('required_qty', 0)
            loaded = item.get('boxes_loaded', 0)
            item_status = item.get('status', '?')
            
            if item_status == 'COMPLETE':
                icon = "✅"
                item_color = "#2E7D32"
            elif item_status == 'LOADED':
                icon = "🔵"
                item_color = "#1565C0"
            elif item_status == 'PROCESSING':
                icon = "🔴"
                item_color = "#E65100"
            else:
                icon = "⏳"
                item_color = "#9E9E9E"
            
            item_pct = (loaded / req * 100) if req > 0 else 0
            
            row = tk.Frame(items_frame, bg="#F5F5F5")
            row.pack(fill=tk.X, padx=8, pady=3)
            
            tk.Label(row, text=f"{icon} {item_name}",
                     font=("Segoe UI", 9, "bold"),
                     bg="#F5F5F5", fg=item_color,
                     width=15, anchor="w").pack(side=tk.LEFT)
            
            tk.Label(row, text=f"{loaded}/{req}",
                     font=("Consolas", 9),
                     bg="#F5F5F5", fg=item_color,
                     width=10).pack(side=tk.LEFT, padx=10)
            
            tk.Label(row, text=f"{item_pct:.0f}%",
                     font=("Segoe UI", 9, "bold"),
                     bg="#F5F5F5", fg=item_color).pack(side=tk.LEFT)

    # ═══════════════════════════════════════════════════════
    # POLLING (Background Thread)
    # ═══════════════════════════════════════════════════════

    def _start_polling(self):
        thread = threading.Thread(target=self._poll_worker, daemon=True)
        thread.start()

    def _poll_worker(self):
        """Background polling for live updates."""
        while self.polling_active:
            try:
                # Fetch data in background, then schedule UI update
                data = self._fetch_data()
                self.root.after(0, self._apply_data, data)
            except Exception as e:
                print(f"Poll error: {e}")
            time.sleep(3)

    def _fetch_data(self):
        """Fetch all data from DB - runs in background thread."""
        result = {
            'stats': {},
            'soldiers': [],
            'recent_scans': []
        }
        
        try:
            self.db.connect()
            cur = self.db.connection.cursor()
            
            # Total soldiers
            cur.execute("SELECT COUNT(*) FROM soldiers")
            result['stats']['soldiers'] = cur.fetchone()[0]
            
            # Active loads (PROCESSING or LOADED)
            cur.execute("""
                SELECT COUNT(DISTINCT soldier_id) FROM cargo_requirements
                WHERE status IN ('PROCESSING', 'LOADED')
            """)
            result['stats']['active'] = cur.fetchone()[0]
            
            # Total completed
            cur.execute("""
                SELECT COUNT(*) FROM cargo_requirements
                WHERE status = 'COMPLETE'
            """)
            result['stats']['complete'] = cur.fetchone()[0]
            
            # Total scans
            cur.execute("SELECT COUNT(*) FROM box_loading_log")
            result['stats']['scans'] = cur.fetchone()[0]
            
            # Pending (ASSIGNED, AVAILABLE)
            cur.execute("""
                SELECT COUNT(*) FROM cargo_requirements
                WHERE status IN ('PENDING', 'ASSIGNED', 'AVAILABLE')
            """)
            result['stats']['pending'] = cur.fetchone()[0]
            
            # Active soldiers detail (includes complete ones too)
            cur.execute("""
                SELECT DISTINCT s.soldier_id, s.soldier_name
                FROM soldiers s
                JOIN cargo_requirements cr ON s.soldier_id = cr.soldier_id
                WHERE cr.status IN ('PROCESSING', 'LOADED', 'COMPLETE')
                ORDER BY s.soldier_id
                LIMIT 15
            """)
            
            soldier_rows = cur.fetchall()
            
            for sid, sname in soldier_rows:
                cur2 = self.db.connection.cursor()
                cur2.execute("""
                    SELECT req_id, item_name, required_qty, 
                           COALESCE(boxes_loaded, 0), status
                    FROM cargo_requirements
                    WHERE soldier_id = %s
                    ORDER BY req_id
                """, (sid,))
                
                items = []
                for r in cur2.fetchall():
                    items.append({
                        'req_id': r[0],
                        'item_name': r[1],
                        'required_qty': r[2],
                        'boxes_loaded': r[3],
                        'status': r[4]
                    })
                cur2.close()
                
                result['soldiers'].append({
                    'soldier_id': sid,
                    'soldier_name': sname,
                    'items': items
                })
            
            # Recent scans (last 5)
            cur.execute("""
                SELECT log_id, item_name, quantity_in_box, 
                       operator_id, load_time, box_uid
                FROM box_loading_log
                ORDER BY log_id DESC
                LIMIT 5
            """)
            
            for r in cur.fetchall():
                result['recent_scans'].append({
                    'log_id': r[0],
                    'item': r[1],
                    'qty': r[2],
                    'operator': r[3],
                    'time': r[4],
                    'box_uid': r[5]
                })
            
            cur.close()
            self.db.disconnect()
            
        except Exception as e:
            print(f"Fetch error: {e}")
            try:
                self.db.disconnect()
            except Exception:
                pass
        
        return result

    def _apply_data(self, data):
        """Apply fetched data to UI - runs on main thread."""
        try:
            # Update stats
            stats = data.get('stats', {})
            self.stat_vars['soldiers'].set(str(stats.get('soldiers', 0)))
            self.stat_vars['active'].set(str(stats.get('active', 0)))
            self.stat_vars['complete'].set(str(stats.get('complete', 0)))
            self.stat_vars['scans'].set(str(stats.get('scans', 0)))
            self.stat_vars['pending'].set(str(stats.get('pending', 0)))
            
            # Update active operations
            self._update_active_operations(data.get('soldiers', []))
            
            # Log new scans
            recent = data.get('recent_scans', [])
            for scan in reversed(recent):
                log_id = scan.get('log_id', 0)
                if log_id > self.last_scan_id:
                    self.last_scan_id = log_id
                    self._log_activity(
                        f"📦 {scan.get('item', '?')} x{scan.get('qty', 1)} "
                        f"loaded by {scan.get('operator', '?')} "
                        f"[Box: {scan.get('box_uid', '?')[:20]}...]"
                    )
            
            # Update last refresh
            self.last_refresh_var.set(
                f"Last update: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            print(f"Apply data error: {e}")


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()