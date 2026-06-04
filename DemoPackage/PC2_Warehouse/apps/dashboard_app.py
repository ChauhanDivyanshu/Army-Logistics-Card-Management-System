# apps/dashboard_app.py
# 📊 ADMIN DASHBOARD - Updated for new schema
# Warehouse → Sheds → Containers → Boxes

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
        self.last_log_id = 0

        self._build_ui()
        self._start_polling()

    def _build_ui(self):
        self._build_header()
        self._build_status_bar()
        
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Top: Stat cards
        self._build_stat_cards(main)

        # Middle: Active trips
        self._build_active_panel(main)

        # Bottom: Recent activity
        self._build_activity_panel(main)
        
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        
        tk.Label(left, text="📊", font=("Segoe UI Emoji", 32),
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
        cards_frame = tk.Frame(parent, bg=COLORS["bg"])
        cards_frame.pack(fill=tk.X, pady=(0, 10))
        
        for i in range(6):
            cards_frame.columnconfigure(i, weight=1, uniform="col")
        
        self.stat_vars = {}
        
        cards_data = [
            ("🏛️", "Warehouses", "warehouses", COLORS["primary"]),
            ("🏚️", "Sheds", "sheds", COLORS["info"]),
            ("📦", "Containers", "containers", COLORS["success"]),
            ("🗃", "Boxes", "boxes", COLORS["warning"]),
            ("🚛", "Active Trips", "active_trips", "#7B1FA2"),
            ("✅", "Today's Exits", "today_exits", COLORS["danger"]),
        ]
        
        for i, (icon, label, key, color) in enumerate(cards_data):
            card = tk.Frame(cards_frame, bg=COLORS["bg_card"],
                            relief=tk.SOLID, bd=1,
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            
            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
            
            tk.Label(card, text=icon,
                     font=("Segoe UI Emoji", 24),
                     bg=COLORS["bg_card"]).pack(pady=(12, 4))
            
            var = tk.StringVar(value="0")
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var,
                     font=("Segoe UI", 22, "bold"),
                     bg=COLORS["bg_card"], 
                     fg=color).pack()
            
            tk.Label(card, text=label,
                     font=("Segoe UI", 9),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text_muted"]).pack(pady=(0, 10))

    def _build_active_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text="  ACTIVE TRIPS & ALLOCATIONS  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        inner = tk.Frame(frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
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
        frame = tk.LabelFrame(
            parent, text="  RECENT GATE ACTIVITY  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, height=250
        )
        frame.pack(fill=tk.BOTH, expand=True)
        frame.pack_propagate(False)
        
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
        self._log_activity("Waiting for gate activity...")

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

    def _update_active_operations(self, trips_data):
        """Update active trips display."""
        for widget in self.active_container.winfo_children():
            widget.destroy()
        
        if not trips_data:
            tk.Label(self.active_container,
                     text="No active trips\n\n"
                          "Trip allocations will appear here when gate assigns trucks.",
                     font=("Segoe UI", 11, "italic"),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text_muted"],
                     justify="center").pack(pady=40)
            return
        
        for trip in trips_data:
            self._create_trip_card(trip)

    def _create_trip_card(self, trip):
        """Create card for one trip."""
        trip_id = trip.get('trip_id', '?')
        truck = trip.get('truck_number', 'Unknown')
        driver = trip.get('driver_name', '-')
        items = trip.get('items', [])
        
        total_required = sum(i.get('requested_qty', 0) for i in items)
        total_allocated = sum(i.get('allocated_qty', 0) for i in items)
        
        # Status from any item
        statuses = [i.get('status', 'PENDING') for i in items]
        if all(s == 'COMPLETED' for s in statuses):
            status_text = "✅ COMPLETED"
            status_color = COLORS["success"]
        elif any(s == 'DISPATCHED' for s in statuses):
            status_text = "🚛 DISPATCHED"
            status_color = COLORS["info"]
        elif any(s == 'LOADED' for s in statuses):
            status_text = "📦 LOADED"
            status_color = COLORS["warning"]
        else:
            status_text = "⏳ PENDING"
            status_color = COLORS["text_muted"]
        
        card = tk.Frame(self.active_container, bg=COLORS["bg_card"],
                        relief=tk.SOLID, bd=1)
        card.pack(fill=tk.X, pady=4, padx=4)
        
        tk.Frame(card, bg=status_color, height=3).pack(fill=tk.X)
        
        # Header
        hdr = tk.Frame(card, bg=COLORS["bg_card"])
        hdr.pack(fill=tk.X, padx=12, pady=6)
        
        tk.Label(hdr, text=f"🚛 {truck}",
                 font=("Segoe UI", 11, "bold"),
                 bg=COLORS["bg_card"], 
                 fg=COLORS["primary"]).pack(side=tk.LEFT)
        
        tk.Label(hdr, text=f"Trip: {trip_id}",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg_card"], 
                 fg=COLORS["text_muted"]).pack(side=tk.LEFT, padx=10)
        
        tk.Label(hdr, text=f"Driver: {driver}",
                 font=("Segoe UI", 9),
                 bg=COLORS["bg_card"], 
                 fg=COLORS["text_muted"]).pack(side=tk.LEFT, padx=10)
        
        tk.Label(hdr, text=status_text,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"], 
                 fg=status_color).pack(side=tk.RIGHT)
        
        # Items
        items_frame = tk.Frame(card, bg=COLORS["bg_card"])
        items_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        for item in items:
            item_name = item.get('item_name', '?')
            req = item.get('requested_qty', 0)
            alloc = item.get('allocated_qty', 0)
            container = item.get('container_id', '-')
            shed = item.get('shed_id', '-')
            
            row = tk.Frame(items_frame, bg=COLORS["bg_card"])
            row.pack(fill=tk.X, pady=1)
            
            tk.Label(row, text=f"  • {item_name}",
                     font=("Segoe UI", 9, "bold"),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text"],
                     width=12, anchor="w").pack(side=tk.LEFT)
            
            tk.Label(row, text=f"Qty: {alloc}/{req}",
                     font=("Consolas", 9),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["primary"]).pack(side=tk.LEFT, padx=10)
            
            tk.Label(row, text=f"From: {shed}/{container}",
                     font=("Consolas", 8),
                     bg=COLORS["bg_card"], 
                     fg=COLORS["text_muted"]).pack(side=tk.LEFT, padx=10)

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
        """Fetch all dashboard data from new schema."""
        result = {
            'stats': {},
            'trips': [],
            'recent_logs': []
        }
        
        try:
            stats = self.db.get_system_stats() or {}
            result['stats']['warehouses'] = stats.get('total_warehouses', 0)
            result['stats']['sheds'] = stats.get('total_sheds', 0)
            result['stats']['containers'] = stats.get('total_containers', 0)
            result['stats']['boxes'] = stats.get('total_boxes', 0)
            result['stats']['active_trips'] = stats.get('pending_requests', 0) + stats.get('assigned_requests', 0)
            result['stats']['today_exits'] = stats.get('today_exits', 0)
            
            # Get active trips from trip_allocations
            trips_raw = self.db._execute("""
                SELECT trip_id, truck_number, driver_name
                FROM trip_allocations
                WHERE status IN ('PENDING', 'LOADED', 'DISPATCHED')
                GROUP BY trip_id, truck_number, driver_name
                ORDER BY MAX(created_at) DESC
                LIMIT 10
            """, fetch='all') or []
            
            for trip in trips_raw:
                trip_id = trip['trip_id']
                
                items = self.db._execute("""
                    SELECT item_name, requested_qty, allocated_qty,
                           container_id, shed_id, status
                    FROM trip_allocations
                    WHERE trip_id = %s
                    ORDER BY item_name
                """, (trip_id,), fetch='all') or []
                
                result['trips'].append({
                    'trip_id': trip_id,
                    'truck_number': trip['truck_number'],
                    'driver_name': trip['driver_name'],
                    'items': items
                })
            
            # Recent gate logs
            logs = self.db.get_gate_logs(limit=10) or []
            result['recent_logs'] = logs
            
        except Exception as e:
            print(f"Fetch error: {e}")
        
        return result

    def _apply_data(self, data):
        try:
            stats = data.get('stats', {})
            self.stat_vars['warehouses'].set(str(stats.get('warehouses', 0)))
            self.stat_vars['sheds'].set(str(stats.get('sheds', 0)))
            self.stat_vars['containers'].set(str(stats.get('containers', 0)))
            self.stat_vars['boxes'].set(str(stats.get('boxes', 0)))
            self.stat_vars['active_trips'].set(str(stats.get('active_trips', 0)))
            self.stat_vars['today_exits'].set(str(stats.get('today_exits', 0)))
            
            self._update_active_operations(data.get('trips', []))
            
            # Log new activity
            logs = data.get('recent_logs', [])
            for log in reversed(logs):
                log_id = log.get('log_id', 0)
                if log_id > self.last_log_id:
                    self.last_log_id = log_id
                    action = log.get('action', '?')
                    truck = log.get('truck_number', '?')
                    item = log.get('item_name', '')
                    qty = log.get('quantity', '')
                    
                    if action == 'ENTRY':
                        msg = f"🚪 ENTRY: Truck {truck} - {log.get('notes', '')}"
                    elif action == 'EXIT':
                        msg = f"📤 EXIT: {item} × {qty} | Truck {truck}"
                    elif action == 'REJECTED':
                        msg = f"❌ REJECTED: Truck {truck}"
                    else:
                        msg = f"📋 {action}: Truck {truck}"
                    
                    self._log_activity(msg)
            
            self.last_refresh_var.set(
                f"Last update: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            print(f"Apply error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-launcher', action='store_true')
    parser.add_argument('--user', type=str, default='standalone')
    parser.add_argument('--role', type=str, default='ADMIN')
    parser.add_argument('--name', type=str, default='Standalone User')
    args, _ = parser.parse_known_args()
    
    if not args.from_launcher:
        try:
            sys.path.insert(0, os.path.join(BASE, '..'))
            from auth.login_window import show_login
            from auth.session import Session
            
            if not show_login():
                sys.exit(0)
        except Exception as e:
            print(f"⚠️ {e}")
    else:
        print(f"✅ Launched from main as: {args.name} ({args.role})")
    
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()