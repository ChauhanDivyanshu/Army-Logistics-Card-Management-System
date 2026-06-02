# apps/dashboard_app.py
# 📊 ADMIN DASHBOARD - Clean Army Theme

import tkinter as tk
from tkinter import ttk
import sys
import os
import time
import threading
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS


class DashboardApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ADMIN DASHBOARD — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x850")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.polling_active = True
        self.last_scan_id = 0

        self._build_ui()
        self._start_polling()

    def _build_ui(self):
        # Header
        self._build_header()
        
        # Live status
        self._build_status_bar()
        
        # Main content
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Top: Stat cards
        self._build_stat_cards(main)

        # Middle: Active operations (40% height)
        self._build_active_panel(main)

        # Bottom: Recent activity (40% height - BIGGER!)
        self._build_activity_panel(main)
        
        # Footer
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="🎖", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="ADMIN DASHBOARD",
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
        
        self.status_var = tk.StringVar(value="LIVE - Refreshing every 3 seconds")
        tk.Label(status, textvariable=self.status_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["success"], fg="white").pack(side=tk.LEFT, padx=14)
        
        self.last_refresh_var = tk.StringVar(value="Last update: —")
        tk.Label(status, textvariable=self.last_refresh_var,
                 font=("Segoe UI", 9),
                 bg=COLORS["success"], fg="white").pack(side=tk.RIGHT, padx=14)

    def _build_stat_cards(self, parent):
        """Top section - stat cards."""
        cards_frame = tk.Frame(parent, bg=COLORS["bg"])
        cards_frame.pack(fill=tk.X, pady=(0, 10))
        
        for i in range(5):
            cards_frame.columnconfigure(i, weight=1, uniform="col")
        
        self.stat_vars = {}
        
        cards_data = [
            ("👥", "Total Trips", "soldiers"),
            ("📦", "Active Loads", "active"),
            ("✅", "Completed", "complete"),
            ("📡", "Total Scans", "scans"),
            ("⏳", "Pending", "pending"),
        ]
        
        for i, (icon, label, key) in enumerate(cards_data):
            card = tk.Frame(cards_frame, bg=COLORS["bg_card"],
                            relief=tk.SOLID, bd=1,
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=5)
            
            # Top stripe (army green)
            tk.Frame(card, bg=COLORS["primary"], height=4).pack(fill=tk.X)
            
            # Icon
            tk.Label(card, text=icon,
                     font=("Segoe UI Emoji", 26),
                     bg=COLORS["bg_card"]).pack(pady=(15, 5))
            
            # Value
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var,
                     font=("Segoe UI", 24, "bold"),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["primary"]).pack()
            
            # Label
            tk.Label(card, text=label,
                     font=("Segoe UI", 9),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text_muted"]).pack(pady=(0, 12))

    def _build_active_panel(self, parent):
        """Middle section - active operations (smaller)."""
        frame = tk.LabelFrame(
            parent, text="  ACTIVE LOADING OPERATIONS  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        inner = tk.Frame(frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollable canvas
        canvas = tk.Canvas(inner, bg=COLORS["bg_card"], 
                          highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.active_container = tk.Frame(canvas, bg=COLORS["bg_card"])
        canvas.create_window((0, 0), window=self.active_container, anchor="nw")
        
        self.active_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

    def _build_activity_panel(self, parent):
        """Bottom section - BIGGER recent activity panel."""
        frame = tk.LabelFrame(
            parent, text="  RECENT ACTIVITY  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, height=280  # BIGGER!
        )
        frame.pack(fill=tk.BOTH, expand=True)
        frame.pack_propagate(False)  # Maintain height
        
        inner = tk.Frame(frame, bg="#212121")
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.activity_text = tk.Text(
            inner, font=("Consolas", 10),
            bg="#212121", fg="#4ade80",
            relief=tk.FLAT, bd=0, wrap=tk.WORD
        )
        self.activity_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        sb = ttk.Scrollbar(inner, command=self.activity_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.activity_text.config(yscrollcommand=sb.set)
        
        self._log_activity("Dashboard started - monitoring all operations")
        self._log_activity("Waiting for activity...")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | Admin Dashboard",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="Real-time Monitoring System",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    def _log_activity(self, msg):
        ts = time.strftime("%H:%M:%S")
        try:
            self.activity_text.insert(tk.END, f"[{ts}] {msg}\n")
            self.activity_text.see(tk.END)
        except Exception:
            pass

    def _update_active_operations(self, soldiers_data):
        """Update active operations cards."""
        for widget in self.active_container.winfo_children():
            widget.destroy()
        
        if not soldiers_data:
            tk.Label(self.active_container,
                     text="No active loading operations\n\n"
                          "Truck assignments will appear here.",
                     font=("Segoe UI", 11, "italic"),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text_muted"],
                     justify="center").pack(pady=40)
            return
        
        for sdata in soldiers_data:
            self._create_operation_card(sdata)

    def _create_operation_card(self, sdata):
        """Create a clean card for one active operation."""
        soldier_id = sdata.get('soldier_id', '?')
        soldier_name = sdata.get('soldier_name', 'Unknown')
        items = sdata.get('items', [])
        
        total_required = sum(i.get('required_qty', 0) for i in items)
        total_loaded = sum(i.get('boxes_loaded', 0) for i in items)
        pct = (total_loaded / total_required * 100) if total_required > 0 else 0
        
        all_complete = all(i.get('status') == 'COMPLETE' for i in items)
        any_loading = any(i.get('status') in ('LOADED', 'PROCESSING') for i in items)
        
        if all_complete:
            status_text = "COMPLETE"
            status_color = COLORS["success"]
        elif pct >= 50:
            status_text = "LOADING"
            status_color = COLORS["info"]
        elif any_loading:
            status_text = "PROCESSING"
            status_color = COLORS["warning"]
        else:
            status_text = "WAITING"
            status_color = COLORS["text_muted"]
        
        # Card
        card = tk.Frame(self.active_container, bg=COLORS["bg_card"],
                        relief=tk.SOLID, bd=1)
        card.pack(fill=tk.X, pady=4, padx=4)
        
        # Top stripe with status color
        tk.Frame(card, bg=status_color, height=3).pack(fill=tk.X)
        
        # Header
        hdr = tk.Frame(card, bg=COLORS["bg_card"])
        hdr.pack(fill=tk.X, padx=12, pady=6)
        
        tk.Label(hdr, text=f"🚛 {soldier_name}",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["bg_card"], 
                 fg=COLORS["primary"]).pack(side=tk.LEFT)
        
        tk.Label(hdr, text=f"ID: {soldier_id}",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg_card"], 
                 fg=COLORS["text_muted"]).pack(side=tk.LEFT, padx=10)
        
        tk.Label(hdr, text=status_text,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], 
                 fg=status_color).pack(side=tk.RIGHT)
        
        # Progress
        prog_frame = tk.Frame(card, bg=COLORS["bg_card"])
        prog_frame.pack(fill=tk.X, padx=12, pady=(0, 6))
        
        tk.Label(prog_frame, 
                 text=f"Progress: {total_loaded}/{total_required} ({pct:.0f}%)",
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["bg_card"]).pack(anchor="w", pady=(0, 3))
        
        # Progress bar
        bar_bg = tk.Frame(prog_frame, bg=COLORS["border"], height=8)
        bar_bg.pack(fill=tk.X)
        
        if pct > 0:
            bar_fill = tk.Frame(bar_bg, bg=status_color, height=8)
            bar_fill.place(relwidth=min(pct/100, 1.0), relheight=1)
        
        # Items detail (compact)
        items_frame = tk.Frame(card, bg=COLORS["primary_light"])
        items_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        for item in items:
            item_name = item.get('item_name', '?')
            req = item.get('required_qty', 0)
            loaded = item.get('boxes_loaded', 0)
            item_status = item.get('status', '?')
            
            if item_status == 'COMPLETE':
                item_color = COLORS["success"]
            elif item_status == 'LOADED':
                item_color = COLORS["info"]
            elif item_status == 'PROCESSING':
                item_color = COLORS["warning"]
            else:
                item_color = COLORS["text_muted"]
            
            row = tk.Frame(items_frame, bg=COLORS["primary_light"])
            row.pack(fill=tk.X, padx=8, pady=2)
            
            tk.Label(row, text=f"• {item_name}",
                     font=("Segoe UI", 9, "bold"),
                     bg=COLORS["primary_light"], 
                     fg=item_color,
                     width=15, anchor="w").pack(side=tk.LEFT)
            
            tk.Label(row, text=f"{loaded}/{req}",
                     font=("Consolas", 9),
                     bg=COLORS["primary_light"], 
                     fg=item_color).pack(side=tk.LEFT, padx=10)

    def _start_polling(self):
        thread = threading.Thread(target=self._poll_worker, daemon=True)
        thread.start()

    def _poll_worker(self):
        while self.polling_active:
            try:
                data = self._fetch_data()
                self.root.after(0, self._apply_data, data)
            except Exception as e:
                print(f"Poll error: {e}")
            time.sleep(3)

    def _fetch_data(self):
        result = {'stats': {}, 'soldiers': [], 'recent_scans': []}
        
        try:
            self.db.connect()
            cur = self.db.connection.cursor()
            
            cur.execute("SELECT COUNT(*) FROM soldiers")
            result['stats']['soldiers'] = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(DISTINCT soldier_id) FROM cargo_requirements
                WHERE status IN ('PROCESSING', 'LOADED')
            """)
            result['stats']['active'] = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM cargo_requirements
                WHERE status = 'COMPLETE'
            """)
            result['stats']['complete'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM box_loading_log")
            result['stats']['scans'] = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM cargo_requirements
                WHERE status IN ('PENDING', 'ASSIGNED', 'AVAILABLE')
            """)
            result['stats']['pending'] = cur.fetchone()[0]
            
            cur.execute("""
                SELECT DISTINCT s.soldier_id, s.soldier_name
                FROM soldiers s
                JOIN cargo_requirements cr ON s.soldier_id = cr.soldier_id
                WHERE cr.status IN ('PROCESSING', 'LOADED', 'COMPLETE')
                ORDER BY s.soldier_id
                LIMIT 15
            """)
            
            for sid, sname in cur.fetchall():
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
                        'req_id': r[0], 'item_name': r[1],
                        'required_qty': r[2], 'boxes_loaded': r[3],
                        'status': r[4]
                    })
                cur2.close()
                
                result['soldiers'].append({
                    'soldier_id': sid, 'soldier_name': sname,
                    'items': items
                })
            
            cur.execute("""
                SELECT log_id, item_name, quantity_in_box, 
                       operator_id, load_time, box_uid
                FROM box_loading_log
                ORDER BY log_id DESC
                LIMIT 5
            """)
            
            for r in cur.fetchall():
                result['recent_scans'].append({
                    'log_id': r[0], 'item': r[1], 'qty': r[2],
                    'operator': r[3], 'time': r[4], 'box_uid': r[5]
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
        try:
            stats = data.get('stats', {})
            self.stat_vars['soldiers'].set(str(stats.get('soldiers', 0)))
            self.stat_vars['active'].set(str(stats.get('active', 0)))
            self.stat_vars['complete'].set(str(stats.get('complete', 0)))
            self.stat_vars['scans'].set(str(stats.get('scans', 0)))
            self.stat_vars['pending'].set(str(stats.get('pending', 0)))
            
            self._update_active_operations(data.get('soldiers', []))
            
            recent = data.get('recent_scans', [])
            for scan in reversed(recent):
                log_id = scan.get('log_id', 0)
                if log_id > self.last_scan_id:
                    self.last_scan_id = log_id
                    self._log_activity(
                        f"📦 {scan.get('item', '?')} × {scan.get('qty', 1)} "
                        f"loaded by {scan.get('operator', '?')}"
                    )
            
            self.last_refresh_var.set(
                f"Last update: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            print(f"Apply data error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()