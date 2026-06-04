# database/db_helper.py
# 🗄️ Indian Army Logistics - Complete Database Helper
# Handles: Auth, Warehouse, Sheds, Containers, Boxes, Allocations, Gate Logs

import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from db_config import DB_CONFIG


class DatabaseHelper:
    """Complete database helper for Army Logistics system."""

    def __init__(self):
        self.config = DB_CONFIG

    # ═══════════════════════════════════════════════════════════
    #  CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def _get_connection(self):
        """Get a new database connection."""
        return psycopg2.connect(**self.config)

    def test_connection(self):
        """Test database connection."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.close()
            conn.close()
            return True, f"Connected: {version[:30]}..."
        except Exception as e:
            return False, str(e)

    def _execute(self, query, params=None, fetch=None):
        """
        Execute a query and optionally fetch results.
        
        Args:
            query: SQL query string
            params: Query parameters tuple/dict
            fetch: 'one' / 'all' / None
        
        Returns:
            Results based on fetch type, or True/False for non-fetch
        """
        conn = None
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            
            result = None
            if fetch == 'one':
                row = cur.fetchone()
                result = dict(row) if row else None
            elif fetch == 'all':
                rows = cur.fetchall()
                result = [dict(r) for r in rows]
            else:
                result = True
            
            conn.commit()
            cur.close()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"DB Error: {e}")
            return None if fetch else False
        finally:
            if conn:
                conn.close()

    # ═══════════════════════════════════════════════════════════
    #  AUTH - USER OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def get_user_by_username(self, username):
        """Get user details by username."""
        return self._execute(
            "SELECT * FROM users WHERE username = %s",
            (username,),
            fetch='one'
        )

    def authenticate_user(self, username, password_hash):
        """Verify user credentials."""
        return self._execute(
            """SELECT user_id, username, full_name, role, email, status
               FROM users 
               WHERE username = %s 
                 AND password_hash = %s 
                 AND status = 'ACTIVE'""",
            (username, password_hash),
            fetch='one'
        )

    def update_last_login(self, user_id):
        """Update user's last login time and reset failed attempts."""
        return self._execute(
            """UPDATE users 
               SET last_login = CURRENT_TIMESTAMP,
                   failed_attempts = 0
               WHERE user_id = %s""",
            (user_id,)
        )

    def increment_failed_attempts(self, username):
        """Increment failed login attempts; lock if >= 5."""
        return self._execute(
            """UPDATE users 
               SET failed_attempts = failed_attempts + 1,
                   status = CASE 
                       WHEN failed_attempts + 1 >= 5 THEN 'LOCKED'
                       ELSE status 
                   END
               WHERE username = %s""",
            (username,)
        )

    def log_login_attempt(self, user_id, username, success, reason=None):
        """Log a login attempt."""
        action = 'LOGIN' if success else 'FAILED'
        return self._execute(
            """INSERT INTO login_history 
               (user_id, username, action, success, failure_reason)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, username, action, success, reason)
        )

    def get_all_users(self):
        """Get all users."""
        return self._execute(
            "SELECT * FROM users ORDER BY user_id",
            fetch='all'
        )

    def create_user(self, username, password_hash, full_name, role, email=None, phone=None):
        """Create a new user."""
        return self._execute(
            """INSERT INTO users 
               (username, password_hash, full_name, role, email, phone)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (username, password_hash, full_name, role, email, phone)
        )

    def update_user_password(self, username, new_password_hash):
        """Update user password."""
        return self._execute(
            "UPDATE users SET password_hash = %s WHERE username = %s",
            (new_password_hash, username)
        )

    def unlock_user(self, username):
        """Unlock a user account."""
        return self._execute(
            """UPDATE users 
               SET status = 'ACTIVE', failed_attempts = 0
               WHERE username = %s""",
            (username,)
        )

    # ═══════════════════════════════════════════════════════════
    #  WAREHOUSE OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def get_warehouse(self):
        """Get the main warehouse (single warehouse system)."""
        return self._execute(
            "SELECT * FROM warehouse LIMIT 1",
            fetch='one'
        )

    def get_all_warehouses(self):
        """Get all warehouses (returns list - usually just 1)."""
        return self._execute(
            "SELECT * FROM warehouse ORDER BY warehouse_id",
            fetch='all'
        ) or []

    def get_warehouse_by_id(self, warehouse_id):
        """Get warehouse by ID."""
        return self._execute(
            "SELECT * FROM warehouse WHERE warehouse_id = %s",
            (warehouse_id,),
            fetch='one'
        )

    def add_warehouse(self, warehouse_id, name, location=None, gate_count=1):
        """Add a new warehouse."""
        return self._execute(
            """INSERT INTO warehouse 
               (warehouse_id, warehouse_name, location, gate_count)
               VALUES (%s, %s, %s, %s)""",
            (warehouse_id, name, location, gate_count)
        )

    # ═══════════════════════════════════════════════════════════
    #  SHED OPERATIONS (NEW)
    # ═══════════════════════════════════════════════════════════

    def get_all_sheds(self):
        """Get all sheds with warehouse info."""
        return self._execute(
            """SELECT s.*, w.warehouse_name 
               FROM sheds s
               LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
               ORDER BY s.shed_id""",
            fetch='all'
        ) or []

    def get_shed_by_id(self, shed_id):
        shed_id = str(shed_id)
        return self._execute(
            """SELECT s.*, w.warehouse_name 
            FROM sheds s
            LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
            WHERE s.shed_id = %s""",
            (str(shed_id),),  
            fetch='one'
        )

    def add_shed(self, shed_id, shed_name, warehouse_id, shed_type=None, description=None):
        """Add a new shed."""
        return self._execute(
            """INSERT INTO sheds 
               (shed_id, shed_name, warehouse_id, shed_type, description)
               VALUES (%s, %s, %s, %s, %s)""",
            (shed_id, shed_name, warehouse_id, shed_type, description)
        )

    def update_shed(self, shed_id, **kwargs):
        shed_id = str(shed_id)
        """Update shed fields."""
        allowed = ['shed_name', 'shed_type', 'description', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [shed_id]
        
        return self._execute(
            f"UPDATE sheds SET {set_clause} WHERE shed_id = %s",
            tuple(values)
        )

    def delete_shed(self, shed_id):
        shed_id = str(shed_id)
        """Delete a shed (cascade deletes containers and boxes)."""
        return self._execute(
            "DELETE FROM sheds WHERE shed_id = %s",
            (shed_id,)
        )

    def get_shed_stats(self, shed_id):
        shed_id = str(shed_id) 
        """Get statistics for a shed."""
        return self._execute(
            """SELECT 
                   COUNT(DISTINCT c.container_id) AS total_containers,
                   COALESCE(SUM(c.total_boxes), 0) AS total_boxes,
                   COALESCE(SUM(c.total_quantity), 0) AS total_quantity
               FROM containers c
               WHERE c.shed_id = %s""",
            (shed_id,),
            fetch='one'
        )

    # ═══════════════════════════════════════════════════════════
    #  CONTAINER OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def get_all_containers(self):
        """Get all containers with shed info."""
        return self._execute(
            """SELECT c.*, s.shed_name, s.warehouse_id, w.warehouse_name
               FROM containers c
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
               ORDER BY c.shed_id, c.container_id""",
            fetch='all'
        ) or []

    def get_container_by_id(self, container_id):
        """Get container by ID with shed/warehouse info."""
        return self._execute(
            """SELECT c.*, s.shed_name, s.warehouse_id, w.warehouse_name
               FROM containers c
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
               WHERE c.container_id = %s""",
            (container_id,),
            fetch='one'
        )

    def get_containers_by_shed(self, shed_id):
        shed_id = str(shed_id)
        """Get all containers in a specific shed."""
        return self._execute(
            "SELECT * FROM containers WHERE shed_id = %s ORDER BY container_id",
            (shed_id,),
            fetch='all'
        ) or []

    def get_containers_by_item(self, item_name):
        """Get all containers that have a specific item."""
        return self._execute(
            """SELECT c.*, s.shed_name 
               FROM containers c
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               WHERE c.item_name = %s 
                 AND c.total_quantity > 0
               ORDER BY c.total_quantity DESC""",
            (item_name,),
            fetch='all'
        ) or []

    def add_container(self, container_id, container_name, shed_id, item_name):
        """Add a new container (totals auto-calculated from boxes)."""
        return self._execute(
            """INSERT INTO containers 
               (container_id, container_name, shed_id, item_name)
               VALUES (%s, %s, %s, %s)""",
            (container_id, container_name, shed_id, item_name)
        )

    def update_container(self, container_id, **kwargs):
        """Update container fields."""
        allowed = ['container_name', 'shed_id', 'item_name', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [container_id]
        
        return self._execute(
            f"UPDATE containers SET {set_clause} WHERE container_id = %s",
            tuple(values)
        )

    def update_container_quantity(self, container_id, total_boxes, total_quantity):
        """Manually update container totals (usually auto via trigger)."""
        return self._execute(
            """UPDATE containers 
               SET total_boxes = %s, total_quantity = %s
               WHERE container_id = %s""",
            (total_boxes, total_quantity, container_id)
        )

    def delete_container(self, container_id):
        """Delete a container (cascade deletes boxes)."""
        return self._execute(
            "DELETE FROM containers WHERE container_id = %s",
            (container_id,)
        )

    # ═══════════════════════════════════════════════════════════
    #  BOX OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def get_all_boxes(self):
        """Get all boxes with container/shed info."""
        return self._execute(
            """SELECT b.*, c.shed_id, s.shed_name
               FROM boxes b
               LEFT JOIN containers c ON b.container_id = c.container_id
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               ORDER BY b.container_id, b.box_uid""",
            fetch='all'
        ) or []

    def get_box_by_uid(self, box_uid):
        """Get box by UID with full hierarchy info."""
        return self._execute(
            """SELECT b.*, 
                      c.shed_id, c.container_name,
                      s.shed_name,
                      w.warehouse_id, w.warehouse_name
               FROM boxes b
               LEFT JOIN containers c ON b.container_id = c.container_id
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
               WHERE b.box_uid = %s""",
            (box_uid,),
            fetch='one'
        )

    def get_box_by_uhf(self, uhf_tag_epc):
        """Get box by UHF tag EPC (for gate scanning)."""
        return self._execute(
            """SELECT b.*, 
                      c.shed_id, c.container_name,
                      s.shed_name,
                      w.warehouse_id, w.warehouse_name
               FROM boxes b
               LEFT JOIN containers c ON b.container_id = c.container_id
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
               WHERE b.uhf_tag_epc = %s""",
            (uhf_tag_epc,),
            fetch='one'
        )

    def get_boxes_by_container(self, container_id):
        """Get all boxes in a container."""
        return self._execute(
            "SELECT * FROM boxes WHERE container_id = %s ORDER BY box_uid",
            (container_id,),
            fetch='all'
        ) or []

    def get_available_boxes_by_container(self, container_id):
        """Get only IN_STOCK boxes in a container."""
        return self._execute(
            """SELECT * FROM boxes 
               WHERE container_id = %s AND status = 'IN_STOCK'
               ORDER BY quantity DESC, box_uid""",
            (container_id,),
            fetch='all'
        ) or []

    def add_box(self, box_uid, container_id, quantity, unit='PCS', 
                batch_number=None, uhf_tag_epc=None, item_name=None):
        """Add a new box. Item name auto-filled from container."""
        # Get item name from container if not provided
        if not item_name:
            container = self.get_container_by_id(container_id)
            if container:
                item_name = container['item_name']
        
        return self._execute(
            """INSERT INTO boxes 
               (box_uid, container_id, item_name, quantity, unit, 
                batch_number, uhf_tag_epc)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (box_uid, container_id, item_name, quantity, unit, 
             batch_number, uhf_tag_epc)
        )

    def update_box(self, box_uid, **kwargs):
        """Update box fields."""
        allowed = ['quantity', 'unit', 'condition', 'batch_number', 
                   'uhf_tag_epc', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [box_uid]
        
        return self._execute(
            f"UPDATE boxes SET {set_clause} WHERE box_uid = %s",
            tuple(values)
        )

    def delete_box(self, box_uid):
        """Delete a box."""
        return self._execute(
            "DELETE FROM boxes WHERE box_uid = %s",
            (box_uid,)
        )

    def mark_box_dispatched(self, box_uid, trip_id):
        """Mark box as dispatched (during gate exit)."""
        return self._execute(
            """UPDATE boxes 
               SET status = 'DISPATCHED',
                   allocated_to_trip = %s,
                   dispatched_at = CURRENT_TIMESTAMP
               WHERE box_uid = %s""",
            (trip_id, box_uid)
        )

    def mark_box_allocated(self, box_uid, trip_id):
        """Mark box as allocated to a trip (during gate entry)."""
        return self._execute(
            """UPDATE boxes 
               SET status = 'ALLOCATED',
                   allocated_to_trip = %s
               WHERE box_uid = %s""",
            (trip_id, box_uid)
        )

    def return_box(self, box_uid):
        """Return a box back to stock."""
        return self._execute(
            """UPDATE boxes 
               SET status = 'IN_STOCK',
                   allocated_to_trip = NULL,
                   dispatched_at = NULL
               WHERE box_uid = %s""",
            (box_uid,)
        )

    # ═══════════════════════════════════════════════════════════
    #  STOCK QUERIES (for Trip Card dropdown)
    # ═══════════════════════════════════════════════════════════

    def get_available_items(self):
        """Get all unique items with available stock (for dropdown)."""
        return self._execute(
            """SELECT 
                   item_name,
                   SUM(quantity) AS total_quantity,
                   COUNT(*) AS box_count
               FROM boxes
               WHERE status = 'IN_STOCK'
               GROUP BY item_name
               HAVING SUM(quantity) > 0
               ORDER BY item_name""",
            fetch='all'
        ) or []

    def get_item_stock(self, item_name):
        """Get total available stock for a specific item."""
        result = self._execute(
            """SELECT 
                   COALESCE(SUM(quantity), 0) AS total_quantity,
                   COUNT(*) AS box_count
               FROM boxes
               WHERE item_name = %s AND status = 'IN_STOCK'""",
            (item_name,),
            fetch='one'
        )
        return result if result else {'total_quantity': 0, 'box_count': 0}

    def get_item_availability_details(self, item_name):
        """Get detailed availability of an item across all containers."""
        return self._execute(
            """SELECT 
                   c.container_id,
                   c.container_name,
                   c.shed_id,
                   s.shed_name,
                   COUNT(b.box_uid) AS available_boxes,
                   COALESCE(SUM(b.quantity), 0) AS available_qty
               FROM containers c
               LEFT JOIN sheds s ON c.shed_id = s.shed_id
               LEFT JOIN boxes b ON c.container_id = b.container_id 
                                 AND b.status = 'IN_STOCK'
               WHERE c.item_name = %s
               GROUP BY c.container_id, c.container_name, c.shed_id, s.shed_name
               HAVING COALESCE(SUM(b.quantity), 0) > 0
               ORDER BY available_qty DESC""",
            (item_name,),
            fetch='all'
        ) or []

    def find_allocation_for_item(self, item_name, requested_qty):
        """
        Find which containers can fulfill the requested quantity.
        Returns list of allocations or None if insufficient stock.
        """
        available = self.get_item_availability_details(item_name)
        
        if not available:
            return None, f"No stock available for {item_name}"
        
        total_available = sum(c['available_qty'] for c in available)
        if total_available < requested_qty:
            return None, f"Insufficient stock: need {requested_qty}, have {total_available}"
        
        allocations = []
        remaining = requested_qty
        
        for container in available:
            if remaining <= 0:
                break
            
            qty_from_this = min(remaining, container['available_qty'])
            allocations.append({
                'shed_id': container['shed_id'],
                'shed_name': container['shed_name'],
                'container_id': container['container_id'],
                'container_name': container['container_name'],
                'allocated_qty': qty_from_this
            })
            remaining -= qty_from_this
        
        return allocations, "OK"

    # ═══════════════════════════════════════════════════════════
    #  TRIP ALLOCATION OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def create_allocation(self, trip_id, truck_number, driver_id, driver_name,
                          item_name, requested_qty, shed_id, container_id, 
                          allocated_qty):
        """Create a trip allocation entry."""
        return self._execute(
            """INSERT INTO trip_allocations
               (trip_id, truck_number, driver_id, driver_name,
                item_name, requested_qty, shed_id, container_id, allocated_qty,
                entry_time)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
            (trip_id, truck_number, driver_id, driver_name,
             item_name, requested_qty, shed_id, container_id, allocated_qty)
        )

    def get_allocation_by_trip(self, trip_id):
        """Get all allocations for a trip."""
        return self._execute(
            """SELECT * FROM trip_allocations 
               WHERE trip_id = %s 
               ORDER BY created_at""",
            (trip_id,),
            fetch='all'
        ) or []

    def get_active_allocation_by_truck(self, truck_number):
        """Get active (not completed) allocation for a truck."""
        return self._execute(
            """SELECT * FROM trip_allocations 
               WHERE truck_number = %s 
                 AND status IN ('PENDING', 'LOADED')
               ORDER BY created_at DESC""",
            (truck_number,),
            fetch='all'
        ) or []

    def update_allocation_status(self, allocation_id, status):
        """Update allocation status."""
        return self._execute(
            "UPDATE trip_allocations SET status = %s WHERE allocation_id = %s",
            (status, allocation_id)
        )

    def mark_allocation_dispatched(self, trip_id):
        """Mark all allocations for a trip as dispatched."""
        return self._execute(
            """UPDATE trip_allocations 
               SET status = 'DISPATCHED', 
                   exit_time = CURRENT_TIMESTAMP
               WHERE trip_id = %s""",
            (trip_id,)
        )

    # ═══════════════════════════════════════════════════════════
    #  GATE LOG OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def log_gate_entry(self, trip_id, truck_number, driver_name, 
                       gate_officer=None, notes=None):
        """Log a gate entry."""
        return self._execute(
            """INSERT INTO gate_logs
               (trip_id, truck_number, driver_name, action, 
                verification, notes, gate_officer)
               VALUES (%s, %s, %s, 'ENTRY', 'MATCH', %s, %s)""",
            (trip_id, truck_number, driver_name, notes, gate_officer)
        )

    def log_gate_exit(self, trip_id, truck_number, driver_name,
                      box_uid, item_name, quantity, container_id, shed_id,
                      verification='MATCH', notes=None, gate_officer=None):
        """Log a gate exit (per box scan)."""
        return self._execute(
            """INSERT INTO gate_logs
               (trip_id, truck_number, driver_name, action,
                box_uid, item_name, quantity, container_id, shed_id,
                verification, notes, gate_officer)
               VALUES (%s, %s, %s, 'EXIT', %s, %s, %s, %s, %s, %s, %s, %s)""",
            (trip_id, truck_number, driver_name,
             box_uid, item_name, quantity, container_id, shed_id,
             verification, notes, gate_officer)
        )

    def log_gate_rejection(self, trip_id, truck_number, driver_name, 
                            reason, gate_officer=None):
        """Log a gate rejection."""
        return self._execute(
            """INSERT INTO gate_logs
               (trip_id, truck_number, driver_name, action, 
                verification, notes, gate_officer)
               VALUES (%s, %s, %s, 'REJECTED', 'MISMATCH', %s, %s)""",
            (trip_id, truck_number, driver_name, reason, gate_officer)
        )

    def get_gate_logs(self, limit=100):
        """Get recent gate logs."""
        return self._execute(
            """SELECT * FROM gate_logs 
               ORDER BY scanned_at DESC 
               LIMIT %s""",
            (limit,),
            fetch='all'
        ) or []

    def get_gate_logs_by_trip(self, trip_id):
        """Get all gate logs for a specific trip."""
        return self._execute(
            """SELECT * FROM gate_logs 
               WHERE trip_id = %s 
               ORDER BY scanned_at""",
            (trip_id,),
            fetch='all'
        ) or []

    def get_gate_logs_by_truck(self, truck_number, limit=50):
        """Get gate logs for a specific truck."""
        return self._execute(
            """SELECT * FROM gate_logs 
               WHERE truck_number = %s 
               ORDER BY scanned_at DESC
               LIMIT %s""",
            (truck_number, limit),
            fetch='all'
        ) or []

    # ═══════════════════════════════════════════════════════════
    #  DASHBOARD / STATISTICS
    # ═══════════════════════════════════════════════════════════

    def get_dashboard_stats(self):
        """Get overall system statistics for dashboard."""
        stats = {}
        
        # Warehouse count
        result = self._execute(
            "SELECT COUNT(*) AS cnt FROM warehouse", fetch='one'
        )
        stats['warehouses'] = result['cnt'] if result else 0
        
        # Sheds count
        result = self._execute(
            "SELECT COUNT(*) AS cnt FROM sheds WHERE status = 'ACTIVE'", 
            fetch='one'
        )
        stats['sheds'] = result['cnt'] if result else 0
        
        # Containers count
        result = self._execute(
            "SELECT COUNT(*) AS cnt FROM containers WHERE status = 'ACTIVE'", 
            fetch='one'
        )
        stats['containers'] = result['cnt'] if result else 0
        
        # Boxes count
        result = self._execute(
            "SELECT COUNT(*) AS cnt FROM boxes WHERE status = 'IN_STOCK'", 
            fetch='one'
        )
        stats['boxes_in_stock'] = result['cnt'] if result else 0
        
        result = self._execute(
            "SELECT COUNT(*) AS cnt FROM boxes WHERE status = 'DISPATCHED'", 
            fetch='one'
        )
        stats['boxes_dispatched'] = result['cnt'] if result else 0
        
        # Total quantity in stock
        result = self._execute(
            "SELECT COALESCE(SUM(quantity), 0) AS total FROM boxes WHERE status = 'IN_STOCK'", 
            fetch='one'
        )
        stats['total_qty_in_stock'] = result['total'] if result else 0
        
        # Today's gate activity
        result = self._execute(
            """SELECT COUNT(*) AS cnt FROM gate_logs 
               WHERE DATE(scanned_at) = CURRENT_DATE 
                 AND action = 'EXIT'""",
            fetch='one'
        )
        stats['today_exits'] = result['cnt'] if result else 0
        
        return stats
    

    def get_item_summary(self):
        """Get summary of all items across warehouse."""
        return self._execute(
            """SELECT 
                   item_name,
                   SUM(quantity) AS total_qty,
                   COUNT(*) AS box_count,
                   COUNT(DISTINCT container_id) AS container_count
               FROM boxes
               WHERE status = 'IN_STOCK'
               GROUP BY item_name
               ORDER BY total_qty DESC""",
            fetch='all'
        ) or []
    
    def get_system_stats(self):
        """
        Get system-wide statistics for dashboard & main launcher.
        Returns dict with all keys expected by main.py.
        """
        stats = {
            # Inventory
            'total_warehouses': 0,
            'total_sheds': 0,
            'total_containers': 0,
            'total_boxes': 0,
            'boxes_in_stock': 0,
            'boxes_dispatched': 0,
            'total_quantity': 0,
            
            # Users (for backward compatibility - "soldiers")
            'total_soldiers': 0,
            'active_users': 0,
            
            # Requests / Trips
            'pending_requests': 0,
            'assigned_requests': 0,
            'completed_requests': 0,
            'today_exits': 0,
        }
        
        try:
            # ─── INVENTORY STATS ───
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM warehouse", 
                fetch='one'
            )
            stats['total_warehouses'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM sheds WHERE status = 'ACTIVE'", 
                fetch='one'
            )
            stats['total_sheds'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM containers WHERE status = 'ACTIVE'", 
                fetch='one'
            )
            stats['total_containers'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM boxes", 
                fetch='one'
            )
            stats['total_boxes'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM boxes WHERE status = 'IN_STOCK'", 
                fetch='one'
            )
            stats['boxes_in_stock'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM boxes WHERE status = 'DISPATCHED'", 
                fetch='one'
            )
            stats['boxes_dispatched'] = result['cnt'] if result else 0
            
            result = self._execute(
                "SELECT COALESCE(SUM(quantity), 0) AS total FROM boxes WHERE status = 'IN_STOCK'", 
                fetch='one'
            )
            stats['total_quantity'] = result['total'] if result else 0
            
            # ─── USERS (mapped to "soldiers" for legacy compatibility) ───
            result = self._execute(
                "SELECT COUNT(*) AS cnt FROM users WHERE status = 'ACTIVE'", 
                fetch='one'
            )
            stats['active_users'] = result['cnt'] if result else 0
            stats['total_soldiers'] = stats['active_users']  # Alias
            
            # ─── TRIPS / REQUESTS ───
            result = self._execute(
                """SELECT COUNT(DISTINCT trip_id) AS cnt FROM trip_allocations 
                   WHERE status = 'PENDING'""",
                fetch='one'
            )
            stats['pending_requests'] = result['cnt'] if result else 0
            
            result = self._execute(
                """SELECT COUNT(DISTINCT trip_id) AS cnt FROM trip_allocations 
                   WHERE status IN ('LOADED', 'DISPATCHED')""",
                fetch='one'
            )
            stats['assigned_requests'] = result['cnt'] if result else 0
            
            result = self._execute(
                """SELECT COUNT(DISTINCT trip_id) AS cnt FROM trip_allocations 
                   WHERE status = 'COMPLETED'""",
                fetch='one'
            )
            stats['completed_requests'] = result['cnt'] if result else 0
            
            # ─── TODAY'S EXITS ───
            result = self._execute(
                """SELECT COUNT(*) AS cnt FROM gate_logs 
                   WHERE DATE(scanned_at) = CURRENT_DATE 
                     AND action = 'EXIT'""",
                fetch='one'
            )
            stats['today_exits'] = result['cnt'] if result else 0
            
        except Exception as e:
            print(f"[get_system_stats] Error: {e}")
        
        return stats


# ═══════════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  🗄️  DATABASE HELPER - TEST MODE")
    print("=" * 70)
    
    db = DatabaseHelper()
    
    # Test connection
    print("\n[1] Testing connection...")
    ok, msg = db.test_connection()
    print(f"   {'✅' if ok else '❌'} {msg}")
    
    if not ok:
        sys.exit(1)
    
    # Test warehouse
    print("\n[2] Warehouse:")
    wh = db.get_warehouse()
    if wh:
        print(f"   ✅ {wh['warehouse_id']} - {wh['warehouse_name']}")
    
    # Test sheds
    print("\n[3] Sheds:")
    sheds = db.get_all_sheds()
    print(f"   ✅ Total: {len(sheds)} sheds")
    for s in sheds:
        print(f"      • {s['shed_id']} - {s['shed_name']}")
    
    # Test containers
    print("\n[4] Containers:")
    containers = db.get_all_containers()
    print(f"   ✅ Total: {len(containers)} containers")
    for c in containers:
        print(f"      • {c['container_id']:5s} | {c['item_name']:10s} | "
              f"{c['total_boxes']} boxes, {c['total_quantity']} qty")
    
    # Test boxes
    print("\n[5] Boxes:")
    boxes = db.get_all_boxes()
    print(f"   ✅ Total: {len(boxes)} boxes")
    
    # Test stock query
    print("\n[6] Available items (for trip card dropdown):")
    items = db.get_available_items()
    for item in items:
        print(f"      • {item['item_name']:10s} | "
              f"Qty: {item['total_quantity']:5d} | "
              f"Boxes: {item['box_count']}")
    
    # Test allocation finder
    print("\n[7] Allocation test (Find 50 AK47):")
    allocs, msg = db.find_allocation_for_item('AK47', 50)
    print(f"   Status: {msg}")
    if allocs:
        for a in allocs:
            print(f"      • {a['shed_name']} → {a['container_name']}: "
                  f"{a['allocated_qty']} units")
    
    # Test users
    print("\n[8] Users:")
    users = db.get_all_users()
    for u in users:
        print(f"      • {u['username']:12s} | {u['role']:10s} | {u['status']}")
    
    # Dashboard stats
    print("\n[9] Dashboard Stats:")
    stats = db.get_dashboard_stats()
    for k, v in stats.items():
        print(f"      • {k:25s}: {v}")
    
    print("\n" + "=" * 70)
    print("  ✅ ALL TESTS COMPLETED")
    print("=" * 70)