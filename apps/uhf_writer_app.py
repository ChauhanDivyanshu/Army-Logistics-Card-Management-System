# apps/uhf_writer_app.py
# 📡 UHF TAG WRITER - Write SKU info to UHF tags on boxes

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import threading
import random
import json
from datetime import datetime
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, '..'))
sys.path.append(os.path.join(BASE, '..', 'database'))
sys.path.append(os.path.join(BASE, '..', 'shared'))

from db_helper import DatabaseHelper
from theme import COLORS


API_BASE = "http://localhost:5000/api/v1"


class UHFWriterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("📡 UHF TAG WRITER — Box Tag Management")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("1300x800")
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
        s.configure("Container.Treeview",
            background="white", foreground="black",
            rowheight=38, font=("Segoe UI", 10))
        s.configure("Container.Treeview.Heading",
            background="#7B1FA2", foreground="white",
            font=("Segoe UI", 10, "bold"), padding=8)
        s.configure("Box.Treeview",
            background="white", foreground="black",
            rowheight=32, font=("Segoe UI", 9))
        s.configure("Box.Treeview.Heading",
            background="#1565C0", foreground="white",
            font=("Segoe UI", 9, "bold"), padding=6)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#7B1FA2", height=60)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        
        tk.Label(hdr, text="📡  UHF TAG WRITER",
                 font=("Segoe UI", 16, "bold"),
                 bg="#7B1FA2", fg="white").pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(hdr, text="Write SKU info to UHF tags on physical boxes",
                 font=("Segoe UI", 9, "italic"),
                 bg="#7B1FA2", fg="#E1BEE7").pack(side=tk.LEFT, pady=15)
        
        self.time_var = tk.StringVar()
        tk.Label(hdr, textvariable=self.time_var,
                 font=("Segoe UI", 10, "bold"),
                 bg="#7B1FA2", fg="#FFEB3B").pack(side=tk.RIGHT, padx=20)
        self._update_time()

        # Info bar
        info = tk.Frame(self.root, bg=COLORS["dark"], height=40)
        info.pack(fill=tk.X)
        info.pack_propagate(False)
        
        tk.Label(info,
            text="💡 Each box gets unique UHF tag containing SKU + item info | "
                 "Multiple boxes of same item share same SKU",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS["dark"], fg="#FFEB3B").pack(side=tk.LEFT, padx=15, pady=10)

        # Main split
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # LEFT: Containers list (40%)
        left = tk.Frame(main, bg=COLORS["bg"], width=480)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left.pack_propagate(False)
        self._build_containers_panel(left)

        # RIGHT: Boxes & Writer (60%)
        right = tk.Frame(main, bg=COLORS["bg"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._build_writer_panel(right)

        # Footer
        footer = tk.Frame(self.root, bg=COLORS["dark"], height=22)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Indian Army | UHF Tag Writer",
                 font=("Segoe UI", 8), bg=COLORS["dark"],
                 fg=COLORS["muted"]).pack(side=tk.LEFT, padx=14)

    def _update_time(self):
        self.time_var.set(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(1000, self._update_time)

    def _build_containers_panel(self, parent):
        frame = tk.LabelFrame(parent,
            text="  📦  CONTAINERS (Select to view boxes)  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg="#7B1FA2",
            bd=2, relief=tk.GROOVE)
        frame.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Refresh button
        top = tk.Frame(inner, bg="#7B1FA2", height=32)
        top.pack(fill=tk.X, pady=(0, 6))
        top.pack_propagate(False)
        
        self.cont_stats_var = tk.StringVar(value="Loading...")
        tk.Label(top, textvariable=self.cont_stats_var,
                 font=("Segoe UI", 10, "bold"),
                 bg="#7B1FA2", fg="white").pack(side=tk.LEFT, padx=14, pady=6)
        
        tk.Button(top, text="🔄 Refresh",
                  command=self._load_containers,
                  font=("Segoe UI", 9, "bold"),
                  bg="white", fg="#7B1FA2",
                  relief=tk.FLAT, padx=12, pady=2,
                  cursor="hand2").pack(side=tk.RIGHT, padx=10, pady=4)

        # Treeview
        tf = tk.Frame(inner, bg=COLORS["white"])
        tf.pack(fill=tk.BOTH, expand=True)
        
        cols = ("sku", "item", "qty", "boxes")
        self.cont_tree = ttk.Treeview(tf, columns=cols,
            show="headings", style="Container.Treeview")
        
        self.cont_tree.heading("sku", text="SKU ID")
        self.cont_tree.heading("item", text="Item")
        self.cont_tree.heading("qty", text="Total Qty")
        self.cont_tree.heading("boxes", text="Boxes")
        
        self.cont_tree.column("sku", width=110, anchor="center")
        self.cont_tree.column("item", width=130, anchor="w")
        self.cont_tree.column("qty", width=80, anchor="center")
        self.cont_tree.column("boxes", width=80, anchor="center")
        
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.cont_tree.yview)
        self.cont_tree.configure(yscrollcommand=sb.set)
        self.cont_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cont_tree.bind("<<TreeviewSelect>>", self._on_container_select)

    def _build_writer_panel(self, parent):
        # Top: Selected container info + Quick Actions
        top_frame = tk.LabelFrame(parent,
            text="  ✏  TAG WRITER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["info"],
            bd=2, relief=tk.GROOVE, height=240)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        top_frame.pack_propagate(False)

        inner = tk.Frame(top_frame, bg=COLORS["white"])
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Selected display
        self.sel_var = tk.StringVar(value="⚠ Select a container from left")
        tk.Label(inner, textvariable=self.sel_var,
            font=("Segoe UI", 11, "bold"),
            bg="#E3F2FD", fg="#0D47A1",
            relief=tk.SOLID, bd=1,
            pady=10, wraplength=700, justify="center"
        ).pack(fill=tk.X, pady=(0, 10))

        # Quantity selector
        qty_frame = tk.Frame(inner, bg=COLORS["white"])
        qty_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(qty_frame, text="How many boxes to create?",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["white"]).pack(side=tk.LEFT, padx=(0, 10))
        
        self.box_count_var = tk.StringVar(value="10")
        tk.Entry(qty_frame, textvariable=self.box_count_var,
                 font=("Segoe UI", 11, "bold"),
                 width=10, justify="center").pack(side=tk.LEFT, padx=5)
        
        for label, qty in [("5", 5), ("10", 10), ("20", 20), ("50", 50), ("100", 100)]:
            tk.Button(qty_frame, text=label,
                      command=lambda q=qty: self.box_count_var.set(str(q)),
                      font=("Segoe UI", 9, "bold"),
                      bg=COLORS["muted"], fg="white",
                      relief=tk.FLAT, padx=10, pady=3,
                      cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Buttons
        btn_frame = tk.Frame(inner, bg=COLORS["white"])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.write_single_btn = tk.Button(btn_frame,
            text="✏  WRITE 1 TAG (Manual)",
            command=lambda: self._write_tags(single=True),
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["info"], fg="white",
            relief=tk.FLAT, pady=12,
            cursor="hand2", state="disabled")
        self.write_single_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.write_bulk_btn = tk.Button(btn_frame,
            text="🚀  BULK WRITE TAGS",
            command=lambda: self._write_tags(single=False),
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["success"], fg="white",
            relief=tk.FLAT, pady=12,
            cursor="hand2", state="disabled")
        self.write_bulk_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Bottom: Boxes table
        bottom_frame = tk.LabelFrame(parent,
            text="  📦  BOXES IN CONTAINER  ",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg"], fg=COLORS["info"],
            bd=2, relief=tk.GROOVE)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        inner2 = tk.Frame(bottom_frame, bg=COLORS["white"])
        inner2.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Stats
        stats = tk.Frame(inner2, bg=COLORS["info"], height=28)
        stats.pack(fill=tk.X, pady=(0, 6))
        stats.pack_propagate(False)
        
        self.box_stats_var = tk.StringVar(value="Select container above")
        tk.Label(stats, textvariable=self.box_stats_var,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["info"], fg="white").pack(side=tk.LEFT, padx=14, pady=5)

        # Treeview
        tf2 = tk.Frame(inner2, bg=COLORS["white"])
        tf2.pack(fill=tk.BOTH, expand=True)
        
        cols2 = ("uid", "sku", "qty", "uhf_epc", "status", "written")
        self.box_tree = ttk.Treeview(tf2, columns=cols2,
            show="headings", style="Box.Treeview")
        
        self.box_tree.heading("uid", text="Box UID")
        self.box_tree.heading("sku", text="SKU")
        self.box_tree.heading("qty", text="Qty")
        self.box_tree.heading("uhf_epc", text="UHF Tag EPC")
        self.box_tree.heading("status", text="Status")
        self.box_tree.heading("written", text="Written At")
        
        self.box_tree.column("uid", width=120, anchor="center")
        self.box_tree.column("sku", width=110, anchor="center")
        self.box_tree.column("qty", width=60, anchor="center")
        self.box_tree.column("uhf_epc", width=240, anchor="w")
        self.box_tree.column("status", width=110, anchor="center")
        self.box_tree.column("written", width=130, anchor="center")
        
        sb2 = ttk.Scrollbar(tf2, orient="vertical", command=self.box_tree.yview)
        self.box_tree.configure(yscrollcommand=sb2.set)
        self.box_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tag colors
        self.box_tree.tag_configure("written",
            background="#C8E6C9", foreground="#1B5E20")
        self.box_tree.tag_configure("not_written",
            background="#FFCDD2", foreground="#B71C1C")

    # ═══════════════════════════════════════════════════════
    # DATA LOADING
    # ═══════════════════════════════════════════════════════

    def _load_containers(self):
        """Load all containers."""
        def worker():
            try:
                containers = self.db.get_all_containers()
                self.root.after(0, self._update_containers, containers or [])
            except Exception as e:
                print(f"Error: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def _update_containers(self, containers):
        """Update containers treeview."""
        for item in self.cont_tree.get_children():
            self.cont_tree.delete(item)
        
        if not containers:
            self.cont_stats_var.set("📊 No containers found")
            return
        
        for c in containers:
            sku = c.get('sku_id', '?')
            item = c.get('item_name', '-')
            qty = c.get('total_quantity', 0)
            boxes = c.get('total_boxes', 0)
            
            self.cont_tree.insert("", "end", iid=f"cnt-{sku}",
                values=(sku, item, qty, boxes))
        
        self.cont_stats_var.set(f"📊 {len(containers)} containers")

    def _on_container_select(self, event):
        """Container selected."""
        if not self.cont_tree.selection():
            return
        
        iid = self.cont_tree.selection()[0]
        vals = self.cont_tree.item(iid)['values']
        if len(vals) < 4:
            return
        
        sku = vals[0]
        item = vals[1]
        qty = vals[2]
        boxes = vals[3]
        
        self.selected_container = {
            'sku': sku,
            'item': item,
            'qty': qty,
            'boxes': boxes
        }
        
        self.sel_var.set(
            f"📦 Container: {sku}  |  Item: {item}  |  Total Qty: {qty}\n"
            f"Existing boxes: {boxes}  |  Ready to write UHF tags"
        )
        
        self.write_single_btn.configure(state="normal")
        self.write_bulk_btn.configure(state="normal")
        
        self._load_boxes(sku)

    def _load_boxes(self, sku):
        """Load boxes for selected container."""
        def worker():
            try:
                boxes = self.db.get_boxes_by_container(sku)
                self.root.after(0, self._update_boxes, boxes or [])
            except Exception as e:
                print(f"Error loading boxes: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def _update_boxes(self, boxes):
        """Update boxes treeview."""
        for item in self.box_tree.get_children():
            self.box_tree.delete(item)
        
        if not boxes:
            self.box_stats_var.set(
                f"📦 {self.selected_container['sku']}: 0 boxes (write tags to create)"
            )
            return
        
        written = 0
        not_written = 0
        
        for b in boxes:
            uid = b.get('box_uid', '?')
            sku = b.get('container_id', '?')
            qty = b.get('quantity', 1)
            epc = b.get('uhf_epc') or '— NOT WRITTEN —'
            tag_status = b.get('tag_status', 'NOT_WRITTEN')
            written_at = b.get('tag_written_at')
            
            if tag_status == 'WRITTEN' and b.get('uhf_epc'):
                tag = 'written'
                status_disp = "✅ WRITTEN"
                written += 1
                written_str = written_at.strftime("%d/%m %H:%M") if written_at else '-'
            else:
                tag = 'not_written'
                status_disp = "❌ EMPTY"
                not_written += 1
                written_str = '-'
            
            self.box_tree.insert("", "end",
                values=(uid, sku, qty, epc, status_disp, written_str),
                tags=(tag,))
        
        self.box_stats_var.set(
            f"📦 {self.selected_container['sku']}: {len(boxes)} boxes | "
            f"✅ Written: {written} | ❌ Empty: {not_written}"
        )

    # ═══════════════════════════════════════════════════════
    # UHF TAG WRITING
    # ═══════════════════════════════════════════════════════

    def _generate_uhf_epc(self, sku, sequence):
        """Generate unique UHF EPC code with embedded SKU info."""
        # Format: EPC-{SKU}-{SEQUENCE}-{RANDOM}
        # Real UHF EPC is 96-bit (24 hex chars), but for demo we use readable format
        timestamp = int(time.time())
        random_part = random.randint(1000, 9999)
        return f"EPC-{sku}-{sequence:04d}-{random_part}"

    def _create_tag_data(self, sku, item, qty, sequence):
        """Create JSON data to write to UHF tag."""
        return json.dumps({
            'sku': sku,
            'item': item,
            'qty': qty,
            'box_seq': sequence,
            'written': datetime.now().isoformat(),
            'app': 'Army_Logistics_v1'
        })

    def _write_tags(self, single=False):
        """Write UHF tags for boxes."""
        if not self.selected_container:
            return
        
        try:
            count = 1 if single else int(self.box_count_var.get())
            if count < 1:
                count = 1
        except:
            count = 1
        
        sku = self.selected_container['sku']
        item = self.selected_container['item']
        
        # Confirm
        confirm = messagebox.askyesno(
            "Write UHF Tags",
            f"📡 WRITE UHF TAGS\n\n"
            f"Container: {sku}\n"
            f"Item: {item}\n"
            f"Tags to write: {count}\n\n"
            f"Each tag will contain:\n"
            f"  • SKU: {sku}\n"
            f"  • Item: {item}\n"
            f"  • Box sequence number\n"
            f"  • Timestamp\n\n"
            f"Proceed?"
        )
        
        if not confirm:
            return
        
        # Disable buttons
        self.write_single_btn.configure(state="disabled", text="⏳ Writing...")
        self.write_bulk_btn.configure(state="disabled", text="⏳ Writing...")
        
        def worker():
            success = 0
            failed = 0
            
            # Get current box count to start sequence
            existing_boxes = self.db.get_boxes_by_container(sku) or []
            start_seq = len(existing_boxes) + 1
            
            for i in range(count):
                seq = start_seq + i
                
                # Generate UHF EPC
                epc = self._generate_uhf_epc(sku, seq)
                
                # Box UID (internal)
                box_uid = f"BOX-{sku}-{seq:04d}"
                
                # Tag data (what gets written to UHF tag memory)
                tag_data = self._create_tag_data(sku, item, 1, seq)
                
                try:
                    # Add box to database with UHF info
                    self.db.connect()
                    cur = self.db.connection.cursor()
                    
                    cur.execute("""
                        INSERT INTO boxes 
                        (box_uid, container_id, quantity, unit, batch_number,
                         uhf_epc, tag_data, tag_written_at, tag_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 'WRITTEN')
                        ON CONFLICT (box_uid) DO UPDATE SET
                            uhf_epc = EXCLUDED.uhf_epc,
                            tag_data = EXCLUDED.tag_data,
                            tag_written_at = NOW(),
                            tag_status = 'WRITTEN'
                    """, (
                        box_uid, sku, 1, 'PCS', f'BATCH-{datetime.now().strftime("%Y%m%d")}',
                        epc, tag_data
                    ))
                    
                    self.db.connection.commit()
                    cur.close()
                    self.db.disconnect()
                    
                    success += 1
                    self.write_count += 1
                    
                    # Small delay for visual effect (simulates real UHF write time)
                    time.sleep(0.1)
                    
                except Exception as e:
                    failed += 1
                    print(f"Write error: {e}")
                    try:
                        self.db.disconnect()
                    except:
                        pass
            
            self.root.after(0, self._on_write_complete, success, failed)
        
        threading.Thread(target=worker, daemon=True).start()

    def _on_write_complete(self, success, failed):
        """Tag writing complete."""
        self.write_single_btn.configure(state="normal", text="✏  WRITE 1 TAG (Manual)")
        self.write_bulk_btn.configure(state="normal", text="🚀  BULK WRITE TAGS")
        
        # Reload boxes
        if self.selected_container:
            self._load_boxes(self.selected_container['sku'])
            self._load_containers()  # Refresh container count too
        
        messagebox.showinfo("✅ Tags Written",
            f"📡 UHF TAG WRITING COMPLETE\n\n"
            f"✅ Successfully written: {success}\n"
            f"❌ Failed: {failed}\n\n"
            f"Each tag contains SKU + item info.\n"
            f"Boxes are now ready for warehouse loading!")


if __name__ == "__main__":
    root = tk.Tk()
    app = UHFWriterApp(root)
    root.mainloop()