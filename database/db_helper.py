# database/db_helper.py
# Army Logistics Database Helper
# All database operations - one place

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Import database config
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG


class DatabaseHelper:
    """
    All database operations for Army Logistics System.
    Handles connections, queries, and data manipulation.
    """

    def __init__(self):
        self.connection = None

    # ═══════════════════════════════════════════════════════
    # CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════

    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self):
        """Test if database is reachable."""
        try:
            if self.connect():
                cursor = self.connection.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                cursor.close()
                self.disconnect()
                return True, version[0]
            return False, "Could not connect"
        except Exception as e:
            return False, str(e)

    # ═══════════════════════════════════════════════════════
    # WAREHOUSE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def get_all_warehouses(self):
        """Get list of all warehouses."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM warehouses ORDER BY warehouse_id;")
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_warehouse_by_id(self, warehouse_id):
        """Get warehouse details by ID."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM warehouses WHERE warehouse_id = %s;
            """, (warehouse_id,))
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def add_warehouse(self, warehouse_id, name, location, capacity=0):
        """Add new warehouse."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO warehouses 
                (warehouse_id, warehouse_name, location, capacity)
                VALUES (%s, %s, %s, %s)
            """, (warehouse_id, name, location, capacity))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def update_warehouse(self, warehouse_id, name=None,
                          location=None, capacity=None):
        """Update existing warehouse."""
        try:
            self.connect()
            cursor = self.connection.cursor()

            updates = []
            values = []
            if name is not None:
                updates.append("warehouse_name = %s")
                values.append(name)
            if location is not None:
                updates.append("location = %s")
                values.append(location)
            if capacity is not None:
                updates.append("capacity = %s")
                values.append(capacity)

            if not updates:
                return False

            values.append(warehouse_id)
            query = f"""
                UPDATE warehouses 
                SET {', '.join(updates)}
                WHERE warehouse_id = %s
            """
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_warehouse(self, warehouse_id):
        """Delete a warehouse."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM warehouses WHERE warehouse_id = %s;
            """, (warehouse_id,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # CONTAINER OPERATIONS
    # ═══════════════════════════════════════════════════════

    def get_all_containers(self):
        """Get all containers with warehouse info."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT c.*, w.warehouse_name, w.location
                FROM containers c
                JOIN warehouses w ON c.warehouse_id = w.warehouse_id
                ORDER BY c.sku_id;
            """)
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_container_by_id(self, sku_id):
        """Get single container details."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT c.*, w.warehouse_name, w.location
                FROM containers c
                JOIN warehouses w ON c.warehouse_id = w.warehouse_id
                WHERE c.sku_id = %s;
            """, (sku_id,))
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_containers_by_item(self, item_name):
        """
        Find all containers that contain a specific item.
        Useful for gate operator to find where item is stored.
        """
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT c.*, w.warehouse_name, w.location
                FROM containers c
                JOIN warehouses w ON c.warehouse_id = w.warehouse_id
                WHERE LOWER(c.item_name) = LOWER(%s)
                AND c.status = 'ACTIVE'
                ORDER BY c.sku_id;
            """, (item_name,))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_containers_by_warehouse(self, warehouse_id):
        """Get all containers in a specific warehouse."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM containers 
                WHERE warehouse_id = %s
                ORDER BY sku_id;
            """, (warehouse_id,))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def add_container(self, sku_id, name, warehouse_id, item_name,
                       total_boxes=0, total_quantity=0):
        """Add new container."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO containers 
                (sku_id, container_name, warehouse_id, item_name,
                 total_boxes, total_quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (sku_id, name, warehouse_id, item_name,
                  total_boxes, total_quantity))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def update_container_quantity(self, sku_id, new_total_boxes,
                                    new_total_quantity):
        """Update container's box count and quantity."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE containers 
                SET total_boxes = %s,
                    total_quantity = %s
                WHERE sku_id = %s;
            """, (new_total_boxes, new_total_quantity, sku_id))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_container(self, sku_id):
        """Delete a container."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM containers WHERE sku_id = %s;
            """, (sku_id,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # BOX OPERATIONS
    # ═══════════════════════════════════════════════════════

    def get_all_boxes(self):
        """Get all boxes with container info."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT b.*, c.container_name, c.item_name,
                       c.warehouse_id
                FROM boxes b
                JOIN containers c ON b.container_id = c.sku_id
                ORDER BY b.box_uid;
            """)
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_box_by_uid(self, box_uid):
        """Get single box details."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT b.*, c.container_name, c.item_name,
                       c.warehouse_id, w.warehouse_name
                FROM boxes b
                JOIN containers c ON b.container_id = c.sku_id
                JOIN warehouses w ON c.warehouse_id = w.warehouse_id
                WHERE b.box_uid = %s;
            """, (box_uid,))
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_boxes_by_container(self, container_id):
        """Get all boxes inside a container."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM boxes 
                WHERE container_id = %s 
                ORDER BY box_uid;
            """, (container_id,))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def add_box(self, box_uid, container_id, quantity,
                 unit="PCS", batch_number=""):
        """Add new box to container."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO boxes 
                (box_uid, container_id, quantity, unit, batch_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (box_uid, container_id, quantity, unit, batch_number))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def update_box(self, box_uid, quantity=None, condition=None):
        """Update box details."""
        try:
            self.connect()
            cursor = self.connection.cursor()

            updates = []
            values = []
            if quantity is not None:
                updates.append("quantity = %s")
                values.append(quantity)
            if condition is not None:
                updates.append("condition = %s")
                values.append(condition)

            if not updates:
                return False

            values.append(box_uid)
            query = f"""
                UPDATE boxes 
                SET {', '.join(updates)}
                WHERE box_uid = %s
            """
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_box(self, box_uid):
        """Delete a box."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM boxes WHERE box_uid = %s;
            """, (box_uid,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # SOLDIER OPERATIONS
    # ═══════════════════════════════════════════════════════

    def get_all_soldiers(self):
        """Get all soldiers list."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM soldiers ORDER BY soldier_id;")
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_soldier_by_id(self, soldier_id):
        """Get soldier details by ID."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM soldiers WHERE soldier_id = %s;
            """, (soldier_id,))
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def add_soldier(self, soldier_id, soldier_name,
                     conductor_id="", conductor_name="",
                     unit_name=""):
        """Add new soldier."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO soldiers 
                (soldier_id, soldier_name, conductor_id,
                 conductor_name, unit_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (soldier_id, soldier_name, conductor_id,
                  conductor_name, unit_name))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def update_soldier(self, soldier_id, soldier_name=None,
                        conductor_id=None, conductor_name=None,
                        unit_name=None):
        """Update soldier details."""
        try:
            self.connect()
            cursor = self.connection.cursor()

            updates = []
            values = []
            if soldier_name is not None:
                updates.append("soldier_name = %s")
                values.append(soldier_name)
            if conductor_id is not None:
                updates.append("conductor_id = %s")
                values.append(conductor_id)
            if conductor_name is not None:
                updates.append("conductor_name = %s")
                values.append(conductor_name)
            if unit_name is not None:
                updates.append("unit_name = %s")
                values.append(unit_name)

            if not updates:
                return False

            values.append(soldier_id)
            query = f"""
                UPDATE soldiers 
                SET {', '.join(updates)}
                WHERE soldier_id = %s
            """
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_soldier(self, soldier_id):
        """Delete a soldier."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM soldiers WHERE soldier_id = %s;
            """, (soldier_id,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # CARGO REQUIREMENTS OPERATIONS
    # ═══════════════════════════════════════════════════════

    def get_cargo_requirements_by_soldier(self, soldier_id):
        """Get all cargo requirements for a soldier."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM cargo_requirements 
                WHERE soldier_id = %s
                ORDER BY req_id;
            """, (soldier_id,))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def add_cargo_requirement(self, soldier_id, item_name, required_qty):
        """Add new cargo requirement for soldier."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO cargo_requirements 
                (soldier_id, item_name, required_qty)
                VALUES (%s, %s, %s)
            """, (soldier_id, item_name, required_qty))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def assign_warehouse_to_requirement(self, req_id, warehouse_id,
                                          container_id):
        """
        Gate operator yahan se warehouse aur container assign karta hai.
        """
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE cargo_requirements 
                SET assigned_warehouse = %s,
                    assigned_container = %s,
                    status = 'ASSIGNED'
                WHERE req_id = %s;
            """, (warehouse_id, container_id, req_id))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def mark_requirement_completed(self, req_id):
        """Mark cargo requirement as completed (after loading)."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE cargo_requirements 
                SET status = 'COMPLETED',
                    completed_date = CURRENT_TIMESTAMP
                WHERE req_id = %s;
            """, (req_id,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_cargo_requirement(self, req_id):
        """Delete a cargo requirement."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                DELETE FROM cargo_requirements WHERE req_id = %s;
            """, (req_id,))
            self.connection.commit()
            cursor.close()
            self.disconnect()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # 🎯 GATE OPERATOR FUNCTIONS (Most Important!)
    # ═══════════════════════════════════════════════════════

    def get_soldier_full_assignment(self, soldier_id):
        """
        🎯 MAIN GATE QUERY
        Soldier ka complete assignment plan - kya saman, kahaa hai.
        Gate pe card scan karne ke baad ye function call hoga.
        """
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    s.soldier_id,
                    s.soldier_name,
                    s.conductor_id,
                    s.conductor_name,
                    s.unit_name,
                    cr.req_id,
                    cr.item_name        AS required_item,
                    cr.required_qty,
                    cr.status           AS req_status,
                    cr.assigned_warehouse,
                    cr.assigned_container,
                    c.sku_id            AS container_id,
                    c.container_name,
                    c.total_quantity    AS available_qty,
                    c.total_boxes       AS available_boxes,
                    w.warehouse_id,
                    w.warehouse_name,
                    w.location          AS warehouse_location
                FROM soldiers s
                JOIN cargo_requirements cr 
                    ON s.soldier_id = cr.soldier_id
                LEFT JOIN containers c 
                    ON LOWER(c.item_name) = LOWER(cr.item_name)
                    AND c.status = 'ACTIVE'
                LEFT JOIN warehouses w 
                    ON c.warehouse_id = w.warehouse_id
                WHERE s.soldier_id = %s
                ORDER BY cr.req_id;
            """, (soldier_id,))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def auto_assign_warehouses(self, soldier_id):
        """
        🎯 AUTO ASSIGNMENT
        Soldier ke saare requirements ko automatically warehouses
        assign kar deta hai based on item availability.
        """
        try:
            # Get all pending requirements
            requirements = self.get_cargo_requirements_by_soldier(soldier_id)

            assigned_list = []
            for req in requirements:
                # Skip if already assigned
                if req['status'] == 'ASSIGNED' or req['status'] == 'COMPLETED':
                    continue

                # Find containers having this item
                containers = self.get_containers_by_item(req['item_name'])

                if containers:
                    # Pick first available container
                    selected = containers[0]
                    self.assign_warehouse_to_requirement(
                        req['req_id'],
                        selected['warehouse_id'],
                        selected['sku_id']
                    )
                    assigned_list.append({
                        'item': req['item_name'],
                        'qty': req['required_qty'],
                        'container': selected['sku_id'],
                        'warehouse': selected['warehouse_id'],
                        'warehouse_name': selected['warehouse_name'],
                        'location': selected['location']
                    })
                else:
                    assigned_list.append({
                        'item': req['item_name'],
                        'qty': req['required_qty'],
                        'container': None,
                        'warehouse': None,
                        'warehouse_name': 'NOT AVAILABLE',
                        'location': '-'
                    })

            return assigned_list
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_warehouse_summary(self, warehouse_id):
        """
        Get complete warehouse summary - containers + items + qty.
        """
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    w.warehouse_id,
                    w.warehouse_name,
                    w.location,
                    COUNT(DISTINCT c.sku_id) AS total_containers,
                    COALESCE(SUM(c.total_boxes), 0) AS total_boxes,
                    COALESCE(SUM(c.total_quantity), 0) AS total_items
                FROM warehouses w
                LEFT JOIN containers c 
                    ON w.warehouse_id = c.warehouse_id
                WHERE w.warehouse_id = %s
                GROUP BY w.warehouse_id, w.warehouse_name, w.location;
            """, (warehouse_id,))
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def search_items(self, search_term):
        """
        Search items across all containers.
        Returns matching items with their containers and warehouses.
        """
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    c.item_name,
                    c.sku_id,
                    c.container_name,
                    c.total_quantity,
                    c.total_boxes,
                    w.warehouse_id,
                    w.warehouse_name,
                    w.location
                FROM containers c
                JOIN warehouses w ON c.warehouse_id = w.warehouse_id
                WHERE LOWER(c.item_name) LIKE LOWER(%s)
                AND c.status = 'ACTIVE'
                ORDER BY c.item_name, w.warehouse_id;
            """, (f"%{search_term}%",))
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    # ═══════════════════════════════════════════════════════
    # REPORTING & STATISTICS
    # ═══════════════════════════════════════════════════════

    def get_system_stats(self):
        """Get overall system statistics."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM warehouses)          AS total_warehouses,
                    (SELECT COUNT(*) FROM containers)          AS total_containers,
                    (SELECT COUNT(*) FROM boxes)               AS total_boxes,
                    (SELECT COUNT(*) FROM soldiers)            AS total_soldiers,
                    (SELECT COUNT(*) FROM cargo_requirements 
                     WHERE status = 'PENDING')                 AS pending_requests,
                    (SELECT COUNT(*) FROM cargo_requirements 
                     WHERE status = 'ASSIGNED')                AS assigned_requests,
                    (SELECT COUNT(*) FROM cargo_requirements 
                     WHERE status = 'COMPLETED')               AS completed_requests;
            """)
            result = cursor.fetchone()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_all_assignments_history(self):
        """Get complete assignment history (all soldiers)."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    s.soldier_id,
                    s.soldier_name,
                    s.conductor_name,
                    s.unit_name,
                    cr.item_name,
                    cr.required_qty,
                    cr.assigned_warehouse,
                    cr.assigned_container,
                    cr.status,
                    cr.request_date,
                    cr.completed_date
                FROM soldiers s
                JOIN cargo_requirements cr 
                    ON s.soldier_id = cr.soldier_id
                ORDER BY cr.request_date DESC;
            """)
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_pending_requests(self):
        """Get all pending cargo requests."""
        try:
            self.connect()
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    cr.req_id,
                    s.soldier_id,
                    s.soldier_name,
                    cr.item_name,
                    cr.required_qty,
                    cr.request_date
                FROM cargo_requirements cr
                JOIN soldiers s ON cr.soldier_id = s.soldier_id
                WHERE cr.status = 'PENDING'
                ORDER BY cr.request_date;
            """)
            result = cursor.fetchall()
            cursor.close()
            self.disconnect()
            return result
        except Exception as e:
            print(f"Error: {e}")
            return []


# ═══════════════════════════════════════════════════════════
#  STANDALONE TEST (Run this file directly to test)
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  ARMY LOGISTICS DATABASE HELPER - TEST MODE")
    print("=" * 60)

    db = DatabaseHelper()

    # Test 1: Connection
    print("\n📡 TEST 1: Database Connection")
    print("-" * 60)
    success, msg = db.test_connection()
    if success:
        print(f"✅ Connection OK")
        print(f"   PostgreSQL: {msg[:60]}...")
    else:
        print(f"❌ Connection FAILED: {msg}")
        exit(1)

    # Test 2: System Stats
    print("\n📊 TEST 2: System Statistics")
    print("-" * 60)
    stats = db.get_system_stats()
    if stats:
        print(f"   Warehouses:          {stats['total_warehouses']}")
        print(f"   Containers:          {stats['total_containers']}")
        print(f"   Boxes:               {stats['total_boxes']}")
        print(f"   Soldiers:            {stats['total_soldiers']}")
        print(f"   Pending Requests:    {stats['pending_requests']}")
        print(f"   Assigned Requests:   {stats['assigned_requests']}")
        print(f"   Completed Requests:  {stats['completed_requests']}")

    # Test 3: List Warehouses
    print("\n🏭 TEST 3: All Warehouses")
    print("-" * 60)
    warehouses = db.get_all_warehouses()
    for w in warehouses:
        print(f"   {w['warehouse_id']:8} | {w['warehouse_name']:25} "
              f"| {w['location']}")

    # Test 4: List Containers
    print("\n📦 TEST 4: All Containers")
    print("-" * 60)
    containers = db.get_all_containers()
    for c in containers:
        print(f"   {c['sku_id']:12} | {c['container_name']:15} "
              f"| Item: {c['item_name']:10} | WH: {c['warehouse_id']}")

    # Test 5: Soldier Full Assignment
    print("\n🎖  TEST 5: Soldier Full Assignment (SLD-1234)")
    print("-" * 60)
    assignment = db.get_soldier_full_assignment('SLD-1234')
    for a in assignment:
        print(f"   Item: {a['required_item']:10} × {a['required_qty']:4} "
              f"| Container: {a['container_id']:12} "
              f"| Warehouse: {a['warehouse_name']}")

    # Test 6: Search Items
    print("\n🔍 TEST 6: Search 'AK47'")
    print("-" * 60)
    items = db.search_items('AK47')
    for i in items:
        print(f"   {i['item_name']:10} | Qty: {i['total_quantity']:4} "
              f"| Container: {i['sku_id']} "
              f"| Warehouse: {i['warehouse_name']}")

    print("\n" + "=" * 60)
    print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)