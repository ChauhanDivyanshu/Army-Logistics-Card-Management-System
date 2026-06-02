# #!/usr/bin/env python3
# """
# ARMY LOGISTICS - API SERVER v2.0
# Pure In-Memory Trip Management + DB for Inventory Only

# Trip data: Card → Gate → API Memory → Warehouse
# NO database for trip/driver/truck info!
# DB only for: containers, warehouses, boxes (inventory)

# Run: python api_server.py
# """

# import os
# import sys
# import json
# import time
# import random
# from datetime import datetime
# import threading

# try:
#     from flask import Flask, request, jsonify
#     from flask_cors import CORS
#     from flask_socketio import SocketIO, emit
#     import psycopg2
#     from psycopg2.extras import RealDictCursor
# except ImportError as e:
#     print(f"❌ Missing package: {e}")
#     print("Install: pip install flask flask-cors psycopg2-binary flask-socketio")
#     sys.exit(1)

# # Import DB config
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# try:
#     from database.db_config import DB_CONFIG as EXISTING_DB_CONFIG
#     DB_CONFIG = {
#         'host': EXISTING_DB_CONFIG['host'],
#         'port': int(EXISTING_DB_CONFIG['port']),
#         'dbname': EXISTING_DB_CONFIG['database'],
#         'user': EXISTING_DB_CONFIG['user'],
#         'password': EXISTING_DB_CONFIG['password']
#     }
# except ImportError:
#     DB_CONFIG = {
#         'host': 'localhost',
#         'port': 5432,
#         'dbname': 'army_logistics',
#         'user': 'postgres',
#         'password': 'mypass'
#     }


# # ═══════════════════════════════════════════════════════
# # FLASK APP SETUP
# # ═══════════════════════════════════════════════════════

# API_HOST = '0.0.0.0'
# API_PORT = 5000
# SIMULATION_MODE = True

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'ARMYLOGISTICS2025'
# CORS(app)
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# # ═══════════════════════════════════════════════════════
# # IN-MEMORY STORAGE (NO Database for trip data!)
# # ═══════════════════════════════════════════════════════

# # Active trips: Card → Gate → Here → Warehouse
# # {trip_id: {truck_number, driver_name, items[], ...}}
# active_trips = {}

# # Recent events for polling
# recent_events = []

# # Simulation counter
# sim_counter = 0


# # ═══════════════════════════════════════════════════════
# # DB CONNECTION (Only for inventory/warehouse lookup)
# # ═══════════════════════════════════════════════════════

# def get_db_conn():
#     """DB connection - ONLY for container/warehouse lookup."""
#     try:
#         return psycopg2.connect(**DB_CONFIG)
#     except Exception as e:
#         print(f"[DB] {e}")
#         return None


# def add_event(event_data):
#     """Add event to memory and broadcast."""
#     event_data['id'] = f"EVT-{int(time.time() * 1000)}"
#     event_data['time'] = datetime.now().isoformat()
#     recent_events.append(event_data)
#     if len(recent_events) > 100:
#         recent_events.pop(0)
#     socketio.emit('system_event', event_data)


# # ═══════════════════════════════════════════════════════
# # ROOT / HEALTH
# # ═══════════════════════════════════════════════════════

# @app.route('/', methods=['GET'])
# def home():
#     return jsonify({
#         'service': 'Army Logistics API v2.0',
#         'mode': 'In-Memory Trip Management',
#         'active_trips': len(active_trips),
#         'db_use': 'Inventory lookup only',
#     })


# @app.route('/api/v1/health', methods=['GET'])
# def health():
#     conn = get_db_conn()
#     db_ok = conn is not None
#     if conn:
#         conn.close()

#     return jsonify({
#         'status': 'healthy' if db_ok else 'degraded',
#         'database': 'up' if db_ok else 'down',
#         'database_purpose': 'inventory/containers only',
#         'active_trips': len(active_trips),
#         'recent_events': len(recent_events),
#         'simulation_mode': SIMULATION_MODE,
#         'server_time': datetime.now().isoformat(),
#     })


# # ═══════════════════════════════════════════════════════
# # AUTH
# # ═══════════════════════════════════════════════════════

# @app.route('/api/v1/auth/login', methods=['POST'])
# def api_login():
#     data = request.json or {}
#     app_type = data.get('app_type', 'UNKNOWN')
#     session_id = f"{app_type}-{int(time.time())}"
#     print(f"[LOGIN] {app_type}: {session_id}")
#     return jsonify({
#         'status': 'ok',
#         'session_id': session_id,
#         'message': f'{app_type} connected',
#     })


# # ═══════════════════════════════════════════════════════
# # GATE ENDPOINTS
# # ═══════════════════════════════════════════════════════

# @app.route('/api/v1/gate/find-items', methods=['POST'])
# def find_items():
#     """
#     Find where items are stored in warehouses.
#     THIS is the only endpoint that uses DB (inventory data).
#     """
#     data = request.json or {}
#     items = data.get('items', [])

#     if not items:
#         return jsonify({'error': 'No items'}), 400

#     conn = get_db_conn()
#     if not conn:
#         return jsonify({'error': 'Inventory DB unavailable'}), 503

#     try:
#         cur = conn.cursor(cursor_factory=RealDictCursor)
#         results = []

#         for item in items:
#             name = item.get('name', '').strip()
#             qty = int(item.get('qty', 0))
#             if not name:
#                 continue

#             cur.execute("""
#                 SELECT c.sku_id, c.container_name, c.warehouse_id,
#                        c.total_quantity, c.total_boxes,
#                        w.warehouse_name, w.location
#                 FROM containers c
#                 JOIN warehouses w ON c.warehouse_id = w.warehouse_id
#                 WHERE LOWER(c.item_name) = LOWER(%s)
#                   AND c.status = 'ACTIVE'
#                 ORDER BY c.total_quantity DESC;
#             """, (name,))

#             locations = [dict(r) for r in cur.fetchall()]
#             total_avail = sum(int(l.get('total_quantity', 0)) for l in locations)

#             best = None
#             for loc in locations:
#                 if int(loc.get('total_quantity', 0)) >= qty:
#                     best = loc
#                     break
#             if not best and locations:
#                 best = locations[0]

#             results.append({
#                 'item_name': name,
#                 'required_qty': qty,
#                 'is_available': total_avail >= qty,
#                 'total_available_qty': total_avail,
#                 'location_count': len(locations),
#                 'best_location': best,
#                 'all_locations': locations,
#             })

#         cur.close()
#         conn.close()

#         return jsonify({
#             'success': True,
#             'all_available': all(r['is_available'] for r in results),
#             'results': results,
#         })

#     except Exception as e:
#         if conn:
#             conn.close()
#         return jsonify({'error': str(e)}), 500


# @app.route('/api/v1/gate/assign-trip', methods=['POST'])
# def assign_trip():
#     """
#     Gate sends trip data from card → Store in MEMORY.
#     NO DATABASE WRITE!
#     Data flows: Card → Gate → API Memory → Warehouse
#     """
#     data = request.json or {}
#     trip_id = data.get('trip_id', '').strip()

#     if not trip_id:
#         trip_id = f"TRIP-{int(time.time())}"

#     items = data.get('items', [])
#     if not items:
#         return jsonify({'error': 'No items'}), 400

#     # Build items with tracking
#     tracked_items = []
#     for item in items:
#         tracked_items.append({
#             'name': item.get('name', ''),
#             'qty': int(item.get('qty', 0)),
#             'loaded': 0,
#             'status': 'PROCESSING',
#             'sku': item.get('sku'),
#             'warehouse_id': item.get('warehouse_id'),
#         })

#     # Store in MEMORY (not DB!)
#     active_trips[trip_id] = {
#         'trip_id': trip_id,
#         'truck_number': data.get('truck_number', ''),
#         'driver_id': data.get('driver_id', ''),
#         'driver_name': data.get('driver_name', ''),
#         'subdriver_id': data.get('subdriver_id', ''),
#         'subdriver_name': data.get('subdriver_name', ''),
#         'items': tracked_items,
#         'status': 'ACTIVE',
#         'assigned_at': datetime.now().isoformat(),
#     }

#     add_event({
#         'type': 'TRIP_ASSIGNED',
#         'trip_id': trip_id,
#         'truck': data.get('truck_number'),
#         'driver': data.get('driver_name'),
#         'items_count': len(tracked_items),
#     })

#     print(f"\n[ASSIGN] Trip: {trip_id}")
#     print(f"  Truck:  {data.get('truck_number')}")
#     print(f"  Driver: {data.get('driver_name')}")
#     print(f"  Items:  {len(tracked_items)}")
#     for item in tracked_items:
#         print(f"    • {item['name']} × {item['qty']}")

#     return jsonify({
#         'success': True,
#         'trip_id': trip_id,
#         'items_assigned': len(tracked_items),
#         'storage': 'in-memory (no database)',
#     })


# @app.route('/api/v1/gate/soldier/<sid>/live-status', methods=['GET'])
# def live_status(sid):
#     """
#     Gate polls this for real-time loading updates.
#     Reads from MEMORY.
#     """
#     trip = active_trips.get(sid)

#     if not trip:
#         return jsonify({
#             'success': False,
#             'items': [],
#             'all_complete': False,
#         }), 404

#     items = []
#     for idx, item in enumerate(trip.get('items', [])):
#         items.append({
#             'req_id': f"{sid}-{idx}",
#             'item_name': item.get('name'),
#             'required_qty': item.get('qty', 0),
#             'boxes_loaded': item.get('loaded', 0),
#             'status': item.get('status', 'PROCESSING'),
#         })

#     all_complete = all(i['status'] == 'COMPLETE' for i in items)

#     return jsonify({
#         'success': True,
#         'soldier_id': sid,
#         'items': items,
#         'all_complete': all_complete,
#         'server_time': datetime.now().isoformat(),
#     })


# # ═══════════════════════════════════════════════════════
# # WAREHOUSE ENDPOINTS (All from MEMORY!)
# # ═══════════════════════════════════════════════════════

# @app.route('/api/v1/wh/pending-loads', methods=['GET'])
# def wh_pending():
#     """
#     Warehouse fetches active trips from MEMORY.
#     Data came from: Card → Gate → API Memory → Here!
#     NO DATABASE!
#     """
#     pending = []

#     for trip_id, trip in active_trips.items():
#         if trip.get('status') == 'COMPLETE':
#             continue

#         for idx, item in enumerate(trip.get('items', [])):
#             pending.append({
#                 # Unique ID for this item
#                 'req_id': f"{trip_id}-{idx}",

#                 # Trip info (from MIFARE card via gate)
#                 'trip_id': trip.get('trip_id'),
#                 'truck_number': trip.get('truck_number'),
#                 'driver_id': trip.get('driver_id'),
#                 'driver_name': trip.get('driver_name'),
#                 'subdriver_id': trip.get('subdriver_id'),
#                 'subdriver_name': trip.get('subdriver_name'),

#                 # Item info
#                 'item_name': item.get('name'),
#                 'required_qty': item.get('qty', 0),
#                 'boxes_loaded': item.get('loaded', 0),
#                 'status': item.get('status', 'PROCESSING'),

#                 # Container/warehouse info
#                 'assigned_container': item.get('sku'),
#                 'assigned_warehouse': item.get('warehouse_id'),
#             })

#     return jsonify({
#         'success': True,
#         'pending': pending,
#         'count': len(pending),
#         'source': 'in-memory (from card data)',
#     })


# @app.route('/api/v1/wh/load-box', methods=['POST'])
# def wh_load_box():
#     """
#     Warehouse scans box → Update MEMORY.
#     NO DATABASE!
#     """
#     data = request.json or {}

#     req_id = data.get('req_id', '')
#     qty_in_box = int(data.get('qty_in_box', 1))
#     box_uid = data.get('box_uid') or f"SCAN-{int(time.time())}"

#     if not req_id:
#         return jsonify({'error': 'Missing req_id'}), 400

#     # Parse req_id: "TRIP-001-0" → trip_id="TRIP-001", idx=0
#     try:
#         last_dash = req_id.rfind('-')
#         trip_id = req_id[:last_dash]
#         item_idx = int(req_id[last_dash + 1:])
#     except (ValueError, IndexError):
#         return jsonify({'error': f'Invalid req_id format: {req_id}'}), 400

#     # Find trip in memory
#     trip = active_trips.get(trip_id)
#     if not trip:
#         return jsonify({'error': f'Trip {trip_id} not found in memory'}), 404

#     # Find item
#     items = trip.get('items', [])
#     if item_idx >= len(items):
#         return jsonify({'error': f'Item index {item_idx} out of range'}), 404

#     item = items[item_idx]

#     # Update loaded count
#     item['loaded'] = min(item.get('loaded', 0) + qty_in_box, item.get('qty', 0))
#     required = item.get('qty', 0)
#     is_item_complete = item['loaded'] >= required

#     if is_item_complete:
#         item['status'] = 'COMPLETE'
#     else:
#         item['status'] = 'LOADED'

#     # Check all items complete
#     all_complete = all(i.get('status') == 'COMPLETE' for i in items)
#     if all_complete:
#         trip['status'] = 'COMPLETE'
#         trip['completed_at'] = datetime.now().isoformat()

#     # Broadcast
#     add_event({
#         'type': 'BOX_LOADED',
#         'trip_id': trip_id,
#         'item': item['name'],
#         'loaded': item['loaded'],
#         'required': required,
#         'complete': is_item_complete,
#     })

#     print(f"[LOAD] {item['name']} +{qty_in_box} = {item['loaded']}/{required}"
#           f" {'✅' if is_item_complete else ''}")

#     return jsonify({
#         'status': 'ok',
#         'box_uid': box_uid,
#         'new_status': item['status'],
#         'progress': {
#             'loaded': item['loaded'],
#             'required': required,
#             'percent': round((item['loaded'] / required) * 100, 1) if required > 0 else 100,
#         },
#         'is_complete': is_item_complete,
#         'all_complete': all_complete,
#     })


# # ═══════════════════════════════════════════════════════
# # ADMIN / UTILITY ENDPOINTS
# # ═══════════════════════════════════════════════════════

# @app.route('/api/v1/admin/clear-trips', methods=['POST'])
# def clear_trips():
#     """Clear all in-memory trips (for testing)."""
#     global active_trips
#     count = len(active_trips)
#     active_trips = {}
#     print(f"[ADMIN] Cleared {count} trips from memory")
#     return jsonify({
#         'success': True,
#         'cleared': count,
#     })


# @app.route('/api/v1/admin/active-trips', methods=['GET'])
# def view_active_trips():
#     """View all active trips in memory (debug)."""
#     return jsonify({
#         'success': True,
#         'count': len(active_trips),
#         'trips': active_trips,
#     })


# @app.route('/api/v1/events/poll', methods=['GET'])
# def poll_events():
#     """Long-polling for events."""
#     since_id = request.args.get('since_id', '')
#     limit = int(request.args.get('limit', 20))

#     new_events = []
#     found = (since_id == '')

#     for evt in recent_events:
#         if not found:
#             if evt.get('id') == since_id:
#                 found = True
#             continue
#         new_events.append(evt)

#     if not found:
#         new_events = recent_events[-limit:]

#     return jsonify({
#         'events': new_events[-limit:],
#         'count': len(new_events),
#         'server_time': datetime.now().isoformat(),
#     })


# # ═══════════════════════════════════════════════════════
# # WEBSOCKET
# # ═══════════════════════════════════════════════════════

# @socketio.on('connect')
# def ws_connect():
#     print(f"[WS] Client connected")
#     emit('connected', {'msg': 'Welcome'})


# @socketio.on('disconnect')
# def ws_disconnect():
#     print(f"[WS] Client disconnected")


# # ═══════════════════════════════════════════════════════
# # MAIN
# # ═══════════════════════════════════════════════════════

# if __name__ == '__main__':
#     print("=" * 70)
#     print(" 🚀 ARMY LOGISTICS API SERVER v2.0")
#     print("    In-Memory Trip Management")
#     print("=" * 70)
#     print(f"   Host:    {API_HOST}:{API_PORT}")
#     print(f"   URL:     http://localhost:{API_PORT}")
#     print(f"   Health:  http://localhost:{API_PORT}/api/v1/health")
#     print(f"   Trips:   http://localhost:{API_PORT}/api/v1/admin/active-trips")
#     print("=" * 70)
#     print()
#     print("   DATA FLOW:")
#     print("   Card → Gate → API Memory → Warehouse")
#     print("   NO database for trip/driver data!")
#     print("   DB only for: container/warehouse inventory")
#     print()
#     print("=" * 70)

#     # Test DB
#     conn = get_db_conn()
#     if conn:
#         print("✅ Inventory DB: Connected (containers/warehouses)")
#         conn.close()
#     else:
#         print("⚠️  Inventory DB: Not available (find-items won't work)")

#     print()

#     try:
#         socketio.run(
#             app,
#             host=API_HOST,
#             port=API_PORT,
#             debug=False,
#             allow_unsafe_werkzeug=True
#         )
#     except KeyboardInterrupt:
#         print("\n Server stopped")
#     except Exception as e:
#         print(f"\n Error: {e}")


#!/usr/bin/env python3
"""
ARMY LOGISTICS - API SERVER v3.0
Updated for new schema: Warehouse → Sheds → Containers → Boxes

Trip data: Card → Gate → API Memory → Warehouse (in-memory)
Inventory: PostgreSQL (sheds, containers, boxes)

Run: python api_server.py
"""

import os
import sys
import json
import time
from datetime import datetime
import threading

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("Install: pip install flask flask-cors psycopg2-binary flask-socketio")
    sys.exit(1)

# Import DB config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from database.db_config import DB_CONFIG as EXISTING_DB_CONFIG
    DB_CONFIG = {
        'host': EXISTING_DB_CONFIG['host'],
        'port': int(EXISTING_DB_CONFIG['port']),
        'dbname': EXISTING_DB_CONFIG.get('database') or EXISTING_DB_CONFIG.get('dbname'),
        'user': EXISTING_DB_CONFIG['user'],
        'password': EXISTING_DB_CONFIG['password']
    }
except ImportError:
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'army_logistics',
        'user': 'postgres',
        'password': 'mypass'
    }


# ═══════════════════════════════════════════════════════
# FLASK APP SETUP
# ═══════════════════════════════════════════════════════

API_HOST = '0.0.0.0'
API_PORT = 5000
SIMULATION_MODE = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ARMYLOGISTICS2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# ═══════════════════════════════════════════════════════
# IN-MEMORY STORAGE (NO Database for trip data!)
# ═══════════════════════════════════════════════════════

# {trip_id: {truck_number, driver_name, items[], allocations[], ...}}
active_trips = {}

# Recent events for polling
recent_events = []


# ═══════════════════════════════════════════════════════
# DB CONNECTION (Only for inventory/warehouse lookup)
# ═══════════════════════════════════════════════════════

def get_db_conn():
    """DB connection - for inventory lookup and gate logs."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"[DB] {e}")
        return None


def add_event(event_data):
    """Add event to memory and broadcast."""
    event_data['id'] = f"EVT-{int(time.time() * 1000)}"
    event_data['time'] = datetime.now().isoformat()
    recent_events.append(event_data)
    if len(recent_events) > 100:
        recent_events.pop(0)
    try:
        socketio.emit('system_event', event_data)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
# ROOT / HEALTH
# ═══════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Army Logistics API v3.0',
        'mode': 'In-Memory Trip + New Schema',
        'schema': 'Warehouse → Sheds → Containers → Boxes',
        'active_trips': len(active_trips),
    })


@app.route('/api/v1/health', methods=['GET'])
def health():
    conn = get_db_conn()
    db_ok = conn is not None
    if conn:
        conn.close()

    return jsonify({
        'status': 'healthy' if db_ok else 'degraded',
        'database': 'up' if db_ok else 'down',
        'active_trips': len(active_trips),
        'recent_events': len(recent_events),
        'simulation_mode': SIMULATION_MODE,
        'server_time': datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/auth/login', methods=['POST'])
def api_login():
    data = request.json or {}
    app_type = data.get('app_type', 'UNKNOWN')
    session_id = f"{app_type}-{int(time.time())}"
    print(f"[LOGIN] {app_type}: {session_id}")
    return jsonify({
        'status': 'ok',
        'session_id': session_id,
        'message': f'{app_type} connected',
    })


# ═══════════════════════════════════════════════════════
# GATE ENDPOINTS - FIND ITEMS (Updated for new schema)
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/gate/find-items', methods=['POST'])
def find_items():
    """
    Find where items are stored in warehouse.
    Uses NEW SCHEMA: warehouse → sheds → containers → boxes
    
    Returns smart allocation:
    - If item available in single container: best_location
    - If spread across multiple: all_locations
    """
    data = request.json or {}
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'No items'}), 400

    conn = get_db_conn()
    if not conn:
        return jsonify({'error': 'Inventory DB unavailable'}), 503

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        results = []

        for item in items:
            name = item.get('name', '').strip()
            qty = int(item.get('qty', 0))
            if not name:
                continue

            # ✅ NEW SCHEMA QUERY: containers + sheds + warehouse + boxes
            cur.execute("""
                SELECT 
                    c.container_id AS sku_id,
                    c.container_name,
                    c.shed_id,
                    s.shed_name,
                    s.warehouse_id,
                    w.warehouse_name,
                    w.location,
                    c.total_quantity,
                    c.total_boxes,
                    COALESCE(SUM(b.quantity), 0) AS available_qty,
                    COUNT(b.box_uid) FILTER (WHERE b.status = 'IN_STOCK') AS available_boxes
                FROM containers c
                LEFT JOIN sheds s ON c.shed_id = s.shed_id
                LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
                LEFT JOIN boxes b ON c.container_id = b.container_id 
                                  AND b.status = 'IN_STOCK'
                WHERE LOWER(c.item_name) = LOWER(%s)
                  AND c.status = 'ACTIVE'
                GROUP BY c.container_id, c.container_name, c.shed_id,
                         s.shed_name, s.warehouse_id, w.warehouse_name,
                         w.location, c.total_quantity, c.total_boxes
                HAVING COALESCE(SUM(b.quantity), 0) > 0
                ORDER BY available_qty DESC;
            """, (name,))

            raw_locations = cur.fetchall()
            
            # Format locations
            locations = []
            for loc in raw_locations:
                loc_dict = dict(loc)
                # Add formatted display
                loc_dict['location'] = f"{loc_dict.get('shed_name', '?')} → {loc_dict.get('container_name', '?')}"
                locations.append(loc_dict)
            
            total_avail = sum(int(l.get('available_qty', 0)) for l in locations)

            # Find best single location that can fulfill
            best = None
            for loc in locations:
                if int(loc.get('available_qty', 0)) >= qty:
                    best = loc
                    break
            
            # If no single location, take the largest
            if not best and locations:
                best = locations[0]

            results.append({
                'item_name': name,
                'required_qty': qty,
                'is_available': total_avail >= qty,
                'total_available_qty': total_avail,
                'location_count': len(locations),
                'best_location': best,
                'all_locations': locations,
            })

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'all_available': all(r['is_available'] for r in results),
            'results': results,
        })

    except Exception as e:
        if conn:
            conn.close()
        print(f"[FIND-ITEMS ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════
# GATE ENDPOINTS - ASSIGN TRIP
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/gate/assign-trip', methods=['POST'])
def assign_trip():
    """
    Gate assigns trip → Store in MEMORY + Log to DB.
    
    Actions:
    1. Store trip in active_trips (memory)
    2. Log gate entry to gate_logs (database)
    3. Optionally allocate boxes to trip
    """
    data = request.json or {}
    trip_id = data.get('trip_id', '').strip()

    if not trip_id:
        trip_id = f"TRIP-{int(time.time())}"

    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'No items'}), 400

    # Build items with tracking
    tracked_items = []
    for item in items:
        tracked_items.append({
            'name': item.get('name', ''),
            'qty': int(item.get('qty', 0)),
            'loaded': 0,
            'status': 'PROCESSING',
            'sku': item.get('sku'),         # container_id
            'warehouse_id': item.get('warehouse_id'),
        })

    # Store in MEMORY
    active_trips[trip_id] = {
        'trip_id': trip_id,
        'truck_number': data.get('truck_number', ''),
        'driver_id': data.get('driver_id', ''),
        'driver_name': data.get('driver_name', ''),
        'subdriver_id': data.get('subdriver_id', ''),
        'subdriver_name': data.get('subdriver_name', ''),
        'items': tracked_items,
        'status': 'ACTIVE',
        'assigned_at': datetime.now().isoformat(),
    }

    # ✅ Log to database (gate_logs table)
    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO gate_logs 
                (trip_id, truck_number, driver_name, action, 
                 verification, notes, gate_officer)
                VALUES (%s, %s, %s, 'ENTRY', 'MATCH', %s, %s)
            """, (
                trip_id,
                data.get('truck_number', ''),
                data.get('driver_name', ''),
                f"Trip assigned with {len(tracked_items)} items",
                'gate_officer'
            ))
            
            # ✅ Create trip_allocations entries
            for item in tracked_items:
                cur.execute("""
                    INSERT INTO trip_allocations
                    (trip_id, truck_number, driver_id, driver_name,
                     item_name, requested_qty, container_id, allocated_qty,
                     status, entry_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', CURRENT_TIMESTAMP)
                """, (
                    trip_id,
                    data.get('truck_number', ''),
                    data.get('driver_id', ''),
                    data.get('driver_name', ''),
                    item['name'],
                    item['qty'],
                    item.get('sku'),
                    item['qty']
                ))
            
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"[GATE-LOG ERROR] {e}")
            conn.rollback()
        finally:
            conn.close()

    add_event({
        'type': 'TRIP_ASSIGNED',
        'trip_id': trip_id,
        'truck': data.get('truck_number'),
        'driver': data.get('driver_name'),
        'items_count': len(tracked_items),
    })

    print(f"\n[ASSIGN] Trip: {trip_id}")
    print(f"  Truck:  {data.get('truck_number')}")
    print(f"  Driver: {data.get('driver_name')}")
    print(f"  Items:  {len(tracked_items)}")
    for item in tracked_items:
        print(f"    • {item['name']} × {item['qty']} (from {item.get('sku')})")

    return jsonify({
        'success': True,
        'trip_id': trip_id,
        'items_assigned': len(tracked_items),
        'storage': 'in-memory + gate_logs',
    })


# ═══════════════════════════════════════════════════════
# GATE ENDPOINTS - LIVE STATUS (For polling)
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/gate/soldier/<sid>/live-status', methods=['GET'])
def live_status(sid):
    """
    Gate polls this for real-time loading updates.
    Reads from MEMORY.
    """
    trip = active_trips.get(sid)

    if not trip:
        return jsonify({
            'success': False,
            'items': [],
            'all_complete': False,
        }), 404

    items = []
    for idx, item in enumerate(trip.get('items', [])):
        items.append({
            'req_id': f"{sid}-{idx}",
            'item_name': item.get('name'),
            'required_qty': item.get('qty', 0),
            'boxes_loaded': item.get('loaded', 0),
            'status': item.get('status', 'PROCESSING'),
        })

    all_complete = all(i['status'] == 'COMPLETE' for i in items)

    return jsonify({
        'success': True,
        'soldier_id': sid,
        'items': items,
        'all_complete': all_complete,
        'server_time': datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# WAREHOUSE ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/wh/pending-loads', methods=['GET'])
def wh_pending():
    """
    Warehouse fetches active trips from MEMORY.
    """
    pending = []

    for trip_id, trip in active_trips.items():
        if trip.get('status') == 'COMPLETE':
            continue

        for idx, item in enumerate(trip.get('items', [])):
            pending.append({
                'req_id': f"{trip_id}-{idx}",
                'trip_id': trip.get('trip_id'),
                'truck_number': trip.get('truck_number'),
                'driver_id': trip.get('driver_id'),
                'driver_name': trip.get('driver_name'),
                'subdriver_id': trip.get('subdriver_id'),
                'subdriver_name': trip.get('subdriver_name'),
                'item_name': item.get('name'),
                'required_qty': item.get('qty', 0),
                'boxes_loaded': item.get('loaded', 0),
                'status': item.get('status', 'PROCESSING'),
                'assigned_container': item.get('sku'),
                'assigned_warehouse': item.get('warehouse_id'),
            })

    return jsonify({
        'success': True,
        'pending': pending,
        'count': len(pending),
        'source': 'in-memory (from card data)',
    })


@app.route('/api/v1/wh/load-box', methods=['POST'])
def wh_load_box():
    """
    Warehouse scans box → Update MEMORY + Mark box as DISPATCHED in DB.
    """
    data = request.json or {}

    req_id = data.get('req_id', '')
    qty_in_box = int(data.get('qty_in_box', 1))
    box_uid = data.get('box_uid') or f"SCAN-{int(time.time())}"

    if not req_id:
        return jsonify({'error': 'Missing req_id'}), 400

    # Parse req_id
    try:
        last_dash = req_id.rfind('-')
        trip_id = req_id[:last_dash]
        item_idx = int(req_id[last_dash + 1:])
    except (ValueError, IndexError):
        return jsonify({'error': f'Invalid req_id format: {req_id}'}), 400

    # Find trip
    trip = active_trips.get(trip_id)
    if not trip:
        return jsonify({'error': f'Trip {trip_id} not found in memory'}), 404

    items = trip.get('items', [])
    if item_idx >= len(items):
        return jsonify({'error': f'Item index {item_idx} out of range'}), 404

    item = items[item_idx]

    # Update loaded count
    item['loaded'] = min(item.get('loaded', 0) + qty_in_box, item.get('qty', 0))
    required = item.get('qty', 0)
    is_item_complete = item['loaded'] >= required

    if is_item_complete:
        item['status'] = 'COMPLETE'
    else:
        item['status'] = 'LOADED'

    # ✅ Mark box as DISPATCHED in database
    if box_uid and not box_uid.startswith('SCAN-'):
        conn = get_db_conn()
        if conn:
            try:
                cur = conn.cursor()
                
                # Get box info for logging
                cur.execute("""
                    SELECT b.box_uid, b.item_name, b.quantity, 
                           b.container_id, c.shed_id
                    FROM boxes b
                    LEFT JOIN containers c ON b.container_id = c.container_id
                    WHERE b.box_uid = %s
                """, (box_uid,))
                box_info = cur.fetchone()
                
                if box_info:
                    # Update box status
                    cur.execute("""
                        UPDATE boxes 
                        SET status = 'DISPATCHED',
                            allocated_to_trip = %s,
                            dispatched_at = CURRENT_TIMESTAMP
                        WHERE box_uid = %s
                    """, (trip_id, box_uid))
                    
                    # Log gate exit
                    cur.execute("""
                        INSERT INTO gate_logs
                        (trip_id, truck_number, driver_name, action,
                         box_uid, item_name, quantity, container_id, shed_id,
                         verification, gate_officer)
                        VALUES (%s, %s, %s, 'EXIT', %s, %s, %s, %s, %s, 'MATCH', %s)
                    """, (
                        trip_id,
                        trip.get('truck_number'),
                        trip.get('driver_name'),
                        box_uid,
                        box_info[1],  # item_name
                        box_info[2],  # quantity
                        box_info[3],  # container_id
                        box_info[4],  # shed_id
                        'gate_officer'
                    ))
                    
                    conn.commit()
                    print(f"[DB] Box {box_uid} marked DISPATCHED")
                
                cur.close()
            except Exception as e:
                print(f"[DB-UPDATE ERROR] {e}")
                conn.rollback()
            finally:
                conn.close()

    # Check all items complete
    all_complete = all(i.get('status') == 'COMPLETE' for i in items)
    if all_complete:
        trip['status'] = 'COMPLETE'
        trip['completed_at'] = datetime.now().isoformat()
        
        # Update allocations to COMPLETED
        conn = get_db_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE trip_allocations 
                    SET status = 'COMPLETED', exit_time = CURRENT_TIMESTAMP
                    WHERE trip_id = %s
                """, (trip_id,))
                conn.commit()
                cur.close()
            except Exception as e:
                print(f"[ALLOC-UPDATE ERROR] {e}")
            finally:
                conn.close()

    # Broadcast
    add_event({
        'type': 'BOX_LOADED',
        'trip_id': trip_id,
        'item': item['name'],
        'loaded': item['loaded'],
        'required': required,
        'complete': is_item_complete,
    })

    print(f"[LOAD] {item['name']} +{qty_in_box} = {item['loaded']}/{required}"
          f" {'✅' if is_item_complete else ''}")

    return jsonify({
        'status': 'ok',
        'box_uid': box_uid,
        'new_status': item['status'],
        'progress': {
            'loaded': item['loaded'],
            'required': required,
            'percent': round((item['loaded'] / required) * 100, 1) if required > 0 else 100,
        },
        'is_complete': is_item_complete,
        'all_complete': all_complete,
    })


# ═══════════════════════════════════════════════════════
# INVENTORY ENDPOINTS (Bonus - for dashboards)
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/inventory/items', methods=['GET'])
def inventory_items():
    """Get all available items with stock."""
    conn = get_db_conn()
    if not conn:
        return jsonify({'error': 'DB unavailable'}), 503
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT item_name,
                   SUM(quantity) AS total_quantity,
                   COUNT(*) AS box_count
            FROM boxes
            WHERE status = 'IN_STOCK'
            GROUP BY item_name
            ORDER BY item_name
        """)
        items = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items),
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/inventory/sheds', methods=['GET'])
def inventory_sheds():
    """Get all sheds with their stats."""
    conn = get_db_conn()
    if not conn:
        return jsonify({'error': 'DB unavailable'}), 503
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT s.shed_id, s.shed_name, s.shed_type,
                   s.warehouse_id, w.warehouse_name,
                   COUNT(DISTINCT c.container_id) AS containers,
                   COALESCE(SUM(c.total_boxes), 0) AS total_boxes,
                   COALESCE(SUM(c.total_quantity), 0) AS total_qty
            FROM sheds s
            LEFT JOIN warehouse w ON s.warehouse_id = w.warehouse_id
            LEFT JOIN containers c ON s.shed_id = c.shed_id
            WHERE s.status = 'ACTIVE'
            GROUP BY s.shed_id, s.shed_name, s.shed_type,
                     s.warehouse_id, w.warehouse_name
            ORDER BY s.shed_id
        """)
        sheds = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'sheds': sheds,
            'count': len(sheds),
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════
# ADMIN / UTILITY ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.route('/api/v1/admin/clear-trips', methods=['POST'])
def clear_trips():
    """Clear all in-memory trips."""
    global active_trips
    count = len(active_trips)
    active_trips = {}
    print(f"[ADMIN] Cleared {count} trips from memory")
    return jsonify({
        'success': True,
        'cleared': count,
    })


@app.route('/api/v1/admin/active-trips', methods=['GET'])
def view_active_trips():
    """View all active trips in memory."""
    return jsonify({
        'success': True,
        'count': len(active_trips),
        'trips': active_trips,
    })


@app.route('/api/v1/events/poll', methods=['GET'])
def poll_events():
    """Long-polling for events."""
    since_id = request.args.get('since_id', '')
    limit = int(request.args.get('limit', 20))

    new_events = []
    found = (since_id == '')

    for evt in recent_events:
        if not found:
            if evt.get('id') == since_id:
                found = True
            continue
        new_events.append(evt)

    if not found:
        new_events = recent_events[-limit:]

    return jsonify({
        'events': new_events[-limit:],
        'count': len(new_events),
        'server_time': datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════
# WEBSOCKET
# ═══════════════════════════════════════════════════════

@socketio.on('connect')
def ws_connect():
    print(f"[WS] Client connected")
    emit('connected', {'msg': 'Welcome'})


@socketio.on('disconnect')
def ws_disconnect():
    print(f"[WS] Client disconnected")


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print(" 🚀 ARMY LOGISTICS API SERVER v3.0")
    print("    In-Memory Trip Management + New Schema")
    print("=" * 70)
    print(f"   Host:    {API_HOST}:{API_PORT}")
    print(f"   URL:     http://localhost:{API_PORT}")
    print(f"   Health:  http://localhost:{API_PORT}/api/v1/health")
    print(f"   Trips:   http://localhost:{API_PORT}/api/v1/admin/active-trips")
    print(f"   Items:   http://localhost:{API_PORT}/api/v1/inventory/items")
    print(f"   Sheds:   http://localhost:{API_PORT}/api/v1/inventory/sheds")
    print("=" * 70)
    print()
    print("   SCHEMA:")
    print("   Warehouse → Sheds → Containers → Boxes")
    print()
    print("   DATA FLOW:")
    print("   Card → Gate → API Memory → Warehouse → DB")
    print()
    print("=" * 70)

    # Test DB
    conn = get_db_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM warehouse")
            wh_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sheds")
            sh_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM containers")
            ct_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM boxes")
            bx_count = cur.fetchone()[0]
            cur.close()
            print(f"✅ DB Connected: {wh_count} warehouses, {sh_count} sheds, "
                  f"{ct_count} containers, {bx_count} boxes")
        except Exception as e:
            print(f"⚠️  DB Schema check failed: {e}")
            print("   Run the SQL setup script first!")
        finally:
            conn.close()
    else:
        print("⚠️  Inventory DB: Not available")

    print()

    try:
        socketio.run(
            app,
            host=API_HOST,
            port=API_PORT,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n Server stopped")
    except Exception as e:
        print(f"\n Error: {e}")