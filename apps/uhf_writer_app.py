# apps/uhf_writer_app.py
# 📡 UHF TAG WRITER - Updated for new schema (Warehouse → Sheds → Containers → Boxes)
# Each box gets unique UHF tag (uhf_tag_epc) for tracking

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import threading
import random
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS


class UHFWriterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("UHF TAG WRITER — Indian Army")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1400x800")
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.db = DatabaseHelper()
        self.selected_container = None
        self.write_count = 0

        ok, msg = self.db.test_connection()
        if not ok:
            messagebox.showerror("DB Error", msg)
            self.root.destroy()
            return

        self._setup_styles()
        self._build_ui()
        self._load_containers()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        
        s.configure("Clean.Treeview",
            background="white", foreground=COLORS["text"],
            rowheight=36, font=("Segoe UI", 10),
            fieldbackground="white",
            borderwidth=1)
        
        s.configure("Clean.Treeview.Heading",
            background=COLORS["primary"], foreground="white",
            font=("Segoe UI", 10, "bold"), padding=8, relief="flat",
            borderwidth=0)
        
        # ✅ Lock heading color (no white hover)
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
        self._build_info_bar()
        
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        
        left = tk.Frame(main, bg=COLORS["bg"], width=520)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left.pack_propagate(False)
        self._build_containers_panel(left)
        
        right = tk.Frame(main, bg=COLORS["bg"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._build_writer_panel(right)
        
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["primary"], height=75)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        left = tk.Frame(hdr, bg=COLORS["primary"])
        left.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(left, text="📡", font=("Segoe UI Emoji", 32),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=(0, 15))
        tb = tk.Frame(left, bg=COLORS["primary"])
        tb.pack(side=tk.LEFT)
        tk.Label(tb, text="INDIAN ARMY", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg=COLORS["accent"]).pack(anchor="w")
        tk.Label(tb, text="UHF TAG WRITER",
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

    def _build_info_bar(self):
        info = tk.Frame(self.root, bg=COLORS.get("primary_dark", "#0D3811"), height=32)
        info.pack(fill=tk.X)
        info.pack_propagate(False)
        tk.Label(info,
            text="📡 Each box gets unique UHF tag with SKU info  |  Multiple boxes share same container",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS.get("primary_dark", "#0D3811"), 
            fg=COLORS["accent"]).pack(side=tk.LEFT, padx=15, pady=7)

    # ═══════════════════════════════════════════════════════
    # PANEL 1: CONTAINERS (LEFT)
    # ═══════════════════════════════════════════════════════

    def _build_containers_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  CONTAINERS  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        frame.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        top = tk.Frame(inner, bg=COLORS["primary"], height=32)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        self.cont_stats_var = tk.StringVar(value="Loading...")
        tk.Label(top, textvariable=self.cont_stats_var,
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["primary"], fg="white").pack(side=tk.LEFT, padx=14, pady=6)
        tk.Button(top, text="🔄 Refresh", command=self._load_containers,
                  font=("Segoe UI", 9, "bold"),
                  bg="white", fg=COLORS["primary"],
                  relief=tk.FLAT, padx=12, pady=2,
                  cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=4)

        tf = tk.Frame(inner, bg=COLORS["bg_card"])
        tf.pack(fill=tk.BOTH, expand=True)
        
        cols = ("container", "shed", "item", "qty", "boxes")
        self.cont_tree = ttk.Treeview(tf, columns=cols, show="headings", 
                                       style="Clean.Treeview")
        
        for col, label in [
            ("container", "Container"),
            ("shed", "Shed"),
            ("item", "Item"),
            ("qty", "Total Qty"),
            ("boxes", "Boxes"),
        ]:
            self.cont_tree.heading(col, text=label)
        
        self.cont_tree.column("container", width=85, anchor="center", stretch=False)
        self.cont_tree.column("shed", width=70, anchor="center", stretch=False)
        self.cont_tree.column("item", width=120, anchor="center", stretch=False)
        self.cont_tree.column("qty", width=90, anchor="center", stretch=False)
        self.cont_tree.column("boxes", width=70, anchor="center", stretch=True)
        
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.cont_tree.yview)
        self.cont_tree.configure(yscrollcommand=sb.set)
        self.cont_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.cont_tree.bind("<<TreeviewSelect>>", self._on_container_select)

    # ═══════════════════════════════════════════════════════
    # PANEL 2: WRITER + BOXES (RIGHT)
    # ═══════════════════════════════════════════════════════

    def _build_writer_panel(self, parent):
        # Top section - Tag Writer
        top_frame = tk.LabelFrame(parent, text="  TAG WRITER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID, height=280)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        top_frame.pack_propagate(False)
        
        inner = tk.Frame(top_frame, bg=COLORS["bg_card"])
        inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Container info display
        self.sel_var = tk.StringVar(value="Select a container from left panel to write tags")
        sel_frame = tk.Frame(inner, 
            bg=COLORS.get("primary_light", "#E8F5E9"),
            relief=tk.SOLID, bd=1)
        sel_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(sel_frame, textvariable=self.sel_var,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS.get("primary_light", "#E8F5E9"), 
            fg=COLORS["primary"],
            wraplength=700, justify="center", pady=12
        ).pack(fill=tk.X, padx=8)

        # Quantity controls
        qty_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        qty_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        tk.Label(qty_frame, text="📦 Boxes to create:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.box_count_var = tk.StringVar(value="10")
        tk.Entry(qty_frame, textvariable=self.box_count_var,
                 font=("Segoe UI", 11, "bold"),
                 width=8, justify="center",
                 relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=5)
        
        # Box quantity per box
        tk.Label(qty_frame, text="  Qty per box:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg_card"]).pack(side=tk.LEFT, padx=(15, 5))
        
        self.qty_per_box_var = tk.StringVar(value="10")
        tk.Entry(qty_frame, textvariable=self.qty_per_box_var,
                 font=("Segoe UI", 11, "bold"),
                 width=8, justify="center",
                 relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=5)
        
        # Quick quantity buttons
        for label, qty in [("5", 5), ("10", 10), ("20", 20), ("50", 50), ("100", 100)]:
            tk.Button(qty_frame, text=label,
                      command=lambda q=qty: self.box_count_var.set(str(q)),
                      font=("Segoe UI", 9, "bold"),
                      bg=COLORS["text_muted"], fg="white",
                      relief=tk.FLAT, padx=10, pady=3,
                      cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Action buttons
        btn_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(15, 10))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        self.write_single_btn = tk.Button(btn_frame,
            text="📡 WRITE 1 TAG",
            command=lambda: self._write_tags(single=True),
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=12,
            cursor="hand2", state="disabled")
        self.write_single_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.write_bulk_btn = tk.Button(btn_frame,
            text="📡 BULK WRITE",
            command=lambda: self._write_tags(single=False),
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["success"], fg="white",
            relief=tk.FLAT, pady=12,
            cursor="hand2", state="disabled")
        self.write_bulk_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Bottom section - Boxes in Container
        bottom_frame = tk.LabelFrame(parent, text="  BOXES IN CONTAINER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["primary"],
            bd=1, relief=tk.SOLID)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        inner2 = tk.Frame(bottom_frame, bg=COLORS["bg_card"])
        inner2.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Stats bar
        stats = tk.Frame(inner2, bg=COLORS["primary"], height=28)
        stats.pack(fill=tk.X)
        stats.pack_propagate(False)
        self.box_stats_var = tk.StringVar(value="Select container above")
        tk.Label(stats, textvariable=self.box_stats_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["primary"], fg="white"
        ).pack(side=tk.LEFT, padx=14, pady=5)

        # Boxes table
        tf2 = tk.Frame(inner2, bg=COLORS["bg_card"])
        tf2.pack(fill=tk.BOTH, expand=True)
        
        cols2 = ("uid", "container", "qty", "uhf_epc", "status")
        self.box_tree = ttk.Treeview(tf2, columns=cols2,
            show="headings", style="Clean.Treeview")
        
        for col, label in [
            ("uid", "Box UID"),
            ("container", "Container"),
            ("qty", "Qty"),
            ("uhf_epc", "UHF Tag EPC"),
            ("status", "Status"),
        ]:
            self.box_tree.heading(col, text=label)
        
        self.box_tree.column("uid", width=170, anchor="center", stretch=False)
        self.box_tree.column("container", width=90, anchor="center", stretch=False)
        self.box_tree.column("qty", width=60, anchor="center", stretch=False)
        self.box_tree.column("uhf_epc", width=220, anchor="center", stretch=True)
        self.box_tree.column("status", width=120, anchor="center", stretch=False)
        
        sb2 = ttk.Scrollbar(tf2, orient="vertical", command=self.box_tree.yview)
        self.box_tree.configure(yscrollcommand=sb2.set)
        self.box_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.box_tree.tag_configure("written", 
            background="#C8E6C9", foreground="#1B5E20")
        self.box_tree.tag_configure("not_written", 
            background="#FFEBEE", foreground="#C62828")
        self.box_tree.tag_configure("dispatched", 
            background="#E1F5FE", foreground="#0277BD")

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLORS["primary"], height=26)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | UHF Tag Writer",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg="white").pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="EPC Generator | Bulk Write Mode",
            font=("Segoe UI", 8), bg=COLORS["primary"],
            fg=COLORS["accent"]).pack(side=tk.RIGHT, padx=14, pady=5)

    # ═══════════════════════════════════════════════════════
    # DATA OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _load_containers(self):
        def worker():
            try:
                containers = self.db.get_all_containers()
                self.root.after(0, self._update_containers, containers or [])
            except Exception as e:
                print(f"[ERROR] {e}")
                self.root.after(0, messagebox.showerror, "Error", str(e))
        threading.Thread(target=worker, daemon=True).start()

    def _update_containers(self, containers):
        for item in self.cont_tree.get_children():
            self.cont_tree.delete(item)
        
        if not containers:
            self.cont_stats_var.set("No containers found")
            return
        
        for c in containers:
            container_id = c.get('container_id', '?')
            shed_id = c.get('shed_id', '-') or '-'
            item = c.get('item_name', '-')
            qty = c.get('total_quantity', 0)
            boxes = c.get('total_boxes', 0)
            
            self.cont_tree.insert("", "end", iid=f"cnt-{container_id}",
                values=(container_id, shed_id, item, qty, boxes))
        
        self.cont_stats_var.set(f"{len(containers)} containers")

    def _on_container_select(self, event):
        if not self.cont_tree.selection():
            return
        iid = self.cont_tree.selection()[0]
        vals = self.cont_tree.item(iid)['values']
        if len(vals) < 5:
            return
        
        self.selected_container = {
            'container_id': vals[0],
            'shed_id': vals[1],
            'item': vals[2],
            'qty': vals[3],
            'boxes': vals[4]
        }
        
        self.sel_var.set(
            f"📦 Container: {vals[0]}  |  🏚 Shed: {vals[1]}  |  🎯 Item: {vals[2]}\n"
            f"📊 Current Qty: {vals[3]}  |  Existing Boxes: {vals[4]}\n"
            f"✅ Ready to write UHF tags"
        )
        
        self.write_single_btn.configure(state="normal")
        self.write_bulk_btn.configure(state="normal")
        self._load_boxes(vals[0])

    def _load_boxes(self, container_id):
        def worker():
            try:
                boxes = self.db.get_boxes_by_container(container_id)
                self.root.after(0, self._update_boxes, boxes or [])
            except Exception as e:
                print(f"[ERROR] {e}")
        threading.Thread(target=worker, daemon=True).start()

    def _update_boxes(self, boxes):
        for item in self.box_tree.get_children():
            self.box_tree.delete(item)
        
        if not boxes:
            if self.selected_container:
                self.box_stats_var.set(
                    f"{self.selected_container['container_id']}: 0 boxes - Click WRITE to create"
                )
            return
        
        written = 0
        not_written = 0
        dispatched = 0
        
        for b in boxes:
            uid = b.get('box_uid', '?')
            container = b.get('container_id', '?')
            qty = b.get('quantity', 1)
            epc = b.get('uhf_tag_epc') or '— NOT WRITTEN —'
            status = b.get('status', 'IN_STOCK')
            
            # Determine tag
            if status == 'DISPATCHED':
                tag = 'dispatched'
                status_disp = "📤 DISPATCHED"
                dispatched += 1
            elif b.get('uhf_tag_epc'):
                tag = 'written'
                status_disp = "✓ WRITTEN"
                written += 1
            else:
                tag = 'not_written'
                status_disp = "✗ EMPTY"
                not_written += 1
            
            self.box_tree.insert("", "end",
                values=(uid, container, qty, epc, status_disp),
                tags=(tag,))
        
        self.box_stats_var.set(
            f"{self.selected_container['container_id']}: {len(boxes)} boxes  |  "
            f"✓ Written: {written}  |  ✗ Empty: {not_written}  |  📤 Dispatched: {dispatched}"
        )

    # ═══════════════════════════════════════════════════════
    # UHF TAG GENERATION
    # ═══════════════════════════════════════════════════════

    def _generate_box_uid(self, container_id, shed_id, sequence):
        """Generate Box UID like: BOX-SHA-CA1-001"""
        return f"BOX-{shed_id}-{container_id}-{sequence:03d}"

    def _generate_uhf_epc(self, container_id, sequence):
        """Generate UHF EPC like: EPC-CA1-001-1234"""
        random_part = random.randint(1000, 9999)
        return f"EPC-{container_id}-{sequence:03d}-{random_part}"

    # ═══════════════════════════════════════════════════════
    # WRITE TAGS
    # ═══════════════════════════════════════════════════════

    def _write_tags(self, single=False):
        if not self.selected_container:
            return
        
        try:
            count = 1 if single else int(self.box_count_var.get())
            if count < 1:
                count = 1
            if count > 1000:
                if not messagebox.askyesno("Large Batch", 
                    f"Write {count} tags? This may take a while."):
                    return
        except:
            count = 1
        
        try:
            qty_per_box = int(self.qty_per_box_var.get())
            if qty_per_box < 1:
                qty_per_box = 1
        except:
            qty_per_box = 1
        
        container_id = self.selected_container['container_id']
        shed_id = self.selected_container['shed_id']
        item = self.selected_container['item']
        
        if not messagebox.askyesno("📡 Write UHF Tags",
            f"WRITE UHF TAGS\n\n"
            f"Container: {container_id}\n"
            f"Shed: {shed_id}\n"
            f"Item: {item}\n\n"
            f"Tags to write: {count}\n"
            f"Qty per box: {qty_per_box}\n"
            f"Total units: {count * qty_per_box}\n\n"
            f"Each box gets unique EPC.\n\n"
            f"Proceed?"):
            return
        
        self.write_single_btn.configure(state="disabled", text="⏳ Writing...")
        self.write_bulk_btn.configure(state="disabled", text="⏳ Writing...")
        
        def worker():
            success = 0
            failed = 0
            
            # Get existing boxes to determine sequence
            try:
                existing_boxes = self.db.get_boxes_by_container(container_id) or []
                start_seq = len(existing_boxes) + 1
            except Exception:
                start_seq = 1
            
            batch_num = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M')}"
            
            for i in range(count):
                seq = start_seq + i
                box_uid = self._generate_box_uid(container_id, shed_id, seq)
                epc = self._generate_uhf_epc(container_id, seq)
                
                try:
                    # Use db_helper's add_box method
                    result = self.db.add_box(
                        box_uid=box_uid,
                        container_id=container_id,
                        quantity=qty_per_box,
                        unit='PCS',
                        batch_number=batch_num,
                        uhf_tag_epc=epc,
                        item_name=item
                    )
                    
                    if result:
                        success += 1
                        self.write_count += 1
                    else:
                        failed += 1
                    
                    time.sleep(0.05)  # Small delay between writes
                    
                except Exception as e:
                    print(f"[WRITE ERROR] {e}")
                    failed += 1
            
            self.root.after(0, self._on_write_complete, success, failed)
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_write_complete(self, success, failed):
        self.write_single_btn.configure(state="normal", text="📡 WRITE 1 TAG")
        self.write_bulk_btn.configure(state="normal", text="📡 BULK WRITE")
        
        # Reload data
        if self.selected_container:
            self._load_boxes(self.selected_container['container_id'])
            self._load_containers()
        
        if failed == 0:
            messagebox.showinfo("✓ Tags Written",
                f"UHF TAG WRITING COMPLETE!\n\n"
                f"✓ Successfully written: {success}\n"
                f"Total written this session: {self.write_count}")
        else:
            messagebox.showwarning("Partial Success",
                f"UHF TAG WRITING COMPLETE\n\n"
                f"✓ Success: {success}\n"
                f"✗ Failed: {failed}\n\n"
                f"Check terminal for errors.")


if __name__ == "__main__":
    root = tk.Tk()
    app = UHFWriterApp(root)
    root.mainloop()