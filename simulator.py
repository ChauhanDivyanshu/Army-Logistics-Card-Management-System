# #!/usr/bin/env python3
# """
# UHF BOX LOADING SIMULATOR
# Simulates warehouse operator scanning boxes via UHF.
# No real UHF hardware needed - uses fake EPC codes.

# Run in NEW terminal (keep api_server.py running):
#     python simulator.py
# """

# import requests
# import time
# import random
# import sys

# # ───── CONFIG ─────
# API_BASE = "http://localhost:5000/api/v1"


# def print_banner():
#     print("\n" + "=" * 70)
#     print("   📦 UHF BOX LOADING SIMULATOR")
#     print("=" * 70)
#     print("   Simulates physical box scanning at warehouse")
#     print("   No real UHF hardware needed - generates fake EPC codes")
#     print("=" * 70 + "\n")


# def check_server():
#     """Verify API server is running."""
#     try:
#         r = requests.get(f"{API_BASE}/health", timeout=5)
#         if r.ok:
#             data = r.json()
#             print(f"✓ Server:   {data['status']}")
#             print(f"✓ Database: {data['database']}")
#             print(f"✓ Mode:     {'Simulation' if data['simulation_mode'] else 'Production'}\n")
#             return True
#         return False
#     except Exception as e:
#         print(f"✗ Server NOT reachable!")
#         print(f"  Error: {e}")
#         print(f"  Start it first: python api_server.py\n")
#         return False


# def get_pending_loads():
#     """Fetch what needs to be loaded."""
#     try:
#         r = requests.get(f"{API_BASE}/wh/pending-loads", timeout=10)
#         if r.ok:
#             return r.json().get('pending', [])
#         return []
#     except Exception as e:
#         print(f"  Error fetching: {e}")
#         return []


# def get_soldier_cargo(soldier_id):
#     """Get soldier's assignments."""
#     try:
#         r = requests.get(
#             f"{API_BASE}/gate/soldier/{soldier_id}/cargo",
#             timeout=10
#         )
#         if r.ok:
#             return r.json().get('data', [])
#         return []
#     except Exception as e:
#         print(f"  Error: {e}")
#         return []


# def simulate_box_scan(req_id, item_name, qty_in_box=1):
#     """Simulate one box being scanned."""
#     payload = {
#         'req_id': req_id,
#         'item_name': item_name,
#         'operator': 'WH_Operator_Demo',
#         'qty_in_box': qty_in_box
#     }
    
#     try:
#         r = requests.post(
#             f"{API_BASE}/wh/load-box",
#             json=payload,
#             timeout=10
#         )
#         if r.ok:
#             return r.json()
#         else:
#             print(f"  Error: {r.status_code} - {r.text[:100]}")
#             return None
#     except Exception as e:
#         print(f"  Exception: {e}")
#         return None


# def show_menu():
#     print("\n" + "━" * 60)
#     print("  CHOOSE AN ACTION:")
#     print("━" * 60)
#     print("  1. View pending loads")
#     print("  2. Simulate single box scan (manual)")
#     print("  3. Auto-load ALL pending boxes")
#     print("  4. Load specific soldier's cargo (slow demo)")
#     print("  5. Refresh server status")
#     print("  6. ⚡ FAST COMPLETE soldier's cargo (DEMO)")    # ← NEW
#     print("  0. Exit")
#     print("━" * 60)
#     return input("\n  Choice: ").strip()


# def action_view_pending():
#     """Show all pending box loads."""
#     print("\n📋 Fetching pending loads...\n")
#     pending = get_pending_loads()
    
#     if not pending:
#         print("  No pending loads found.")
#         print("  Use Gate App to assign items first!\n")
#         return
    
#     print(f"  Total pending: {len(pending)}\n")
#     print(f"  {'#':<4} {'Req':<6} {'Item':<12} {'Need':<8} {'Done':<8} {'Status':<12}")
#     print(f"  {'-' * 60}")
    
#     for i, p in enumerate(pending, 1):
#         req_id = p.get('req_id')
#         item = p.get('item_name', '-')
#         needed = p.get('required_qty', 0)
#         done = p.get('boxes_loaded', 0)
#         status = p.get('status', '?')
        
#         print(f"  {i:<4} {req_id:<6} {item:<12} {needed:<8} "
#               f"{done:<8} {status:<12}")
#     print()


# def action_single_scan():
#     """Manually scan one box."""
#     print("\n📡 SINGLE BOX SCAN SIMULATOR\n")
    
#     pending = get_pending_loads()
#     if not pending:
#         print("  No pending items to load!")
#         print("  First assign items via Gate App.\n")
#         return
    
#     print("  Available requirements:")
#     for i, p in enumerate(pending, 1):
#         print(f"    {i}. Req#{p['req_id']} - {p['item_name']} "
#               f"({p.get('boxes_loaded',0)}/{p['required_qty']})")
    
#     choice = input(f"\n  Pick number (1-{len(pending)}): ").strip()
    
#     try:
#         idx = int(choice) - 1
#         if 0 <= idx < len(pending):
#             target = pending[idx]
#         else:
#             print("  Invalid choice!")
#             return
#     except ValueError:
#         print("  Enter a number!")
#         return
    
#     qty = input("  Quantity in this box (default 1): ").strip()
#     qty = int(qty) if qty.isdigit() else 1
    
#     print("\n  📡 Scanning box...")
#     time.sleep(0.5)
    
#     result = simulate_box_scan(
#         target['req_id'],
#         target['item_name'],
#         qty
#     )
    
#     if result:
#         progress = result.get('progress', {})
#         print(f"\n  ✅ SCAN SUCCESSFUL!")
#         print(f"     Box UID:  {result.get('box_uid')}")
#         print(f"     Status:   {result.get('new_status')}")
#         print(f"     Progress: {progress.get('loaded')}/{progress.get('required')} "
#               f"({progress.get('percent')}%)")
        
#         if result.get('is_complete'):
#             print(f"\n  🎉 THIS ITEM IS COMPLETE!")
#     print()


# def action_auto_load():
#     """Auto-load all pending boxes with realistic delays."""
#     print("\n🤖 AUTO-LOAD MODE")
#     print("  Will simulate loading all pending boxes...\n")
    
#     pending = get_pending_loads()
#     if not pending:
#         print("  Nothing to load!")
#         print("  First assign items via Gate App.\n")
#         return
    
#     confirm = input(f"  Load {len(pending)} item types? (y/n): ").strip().lower()
#     if confirm != 'y':
#         print("  Cancelled.\n")
#         return
    
#     delay = input("  Delay between scans (seconds, default 2): ").strip()
#     try:
#         delay = float(delay) if delay else 2.0
#     except:
#         delay = 2.0
    
#     print(f"\n  Starting auto-load (delay={delay}s)...\n")
    
#     total_scanned = 0
    
#     for p in pending:
#         req_id = p['req_id']
#         item = p['item_name']
#         needed = p['required_qty']
#         already_done = p.get('boxes_loaded', 0)
#         remaining = needed - already_done
        
#         if remaining <= 0:
#             print(f"  ✓ {item} already complete!")
#             continue
        
#         print(f"\n  📦 Loading {item} (req#{req_id})")
#         print(f"     Need to scan {remaining} more units...")
        
#         while remaining > 0:
#             qty_in_this_box = min(remaining, random.randint(1, 5))
            
#             print(f"     📡 Scanning box ({qty_in_this_box} units)...", end=" ")
#             time.sleep(delay)
            
#             result = simulate_box_scan(req_id, item, qty_in_this_box)
            
#             if result:
#                 progress = result.get('progress', {})
#                 pct = progress.get('percent', 0)
#                 done = progress.get('loaded', 0)
#                 tot = progress.get('required', 0)
                
#                 print(f"✓ ({done}/{tot} = {pct}%)")
#                 total_scanned += 1
#                 remaining -= qty_in_this_box
                
#                 if result.get('is_complete'):
#                     print(f"     🎉 ITEM COMPLETE!")
#                     break
#             else:
#                 print(f"✗ FAILED")
#                 break
    
#     print(f"\n  ✅ Auto-load done! Total {total_scanned} boxes scanned.\n")


# def action_load_soldier():
#     """Load specific soldier's cargo - FIXED VERSION."""
#     sid = input("\n  Enter Soldier ID (e.g., SLD-1234): ").strip()
#     if not sid:
#         return
    
#     print(f"\n  Fetching {sid}'s cargo...\n")
#     cargo = get_soldier_cargo(sid)
    
#     if not cargo:
#         print(f"  No cargo found for {sid}!")
#         print(f"  Check if soldier exists and has assignments.\n")
#         return
    
#     print(f"  Found {len(cargo)} items:")
#     for c in cargo:
#         loaded = c.get('boxes_loaded', 0)
#         print(f"    • {c['item_name']} (Req#{c['req_id']}) "
#               f"qty={c['required_qty']} loaded={loaded} status={c['status']}")
    
#     confirm = input(f"\n  Load all for {sid}? (y/n): ").strip().lower()
#     if confirm != 'y':
#         return
    
#     delay = input("  Delay between scans (default 1.5s): ").strip()
#     try:
#         delay = float(delay) if delay else 1.5
#     except:
#         delay = 1.5
    
#     print(f"\n  Starting loads...\n")
    
#     for c in cargo:
#         if c['status'] == 'COMPLETE':
#             print(f"  ✓ {c['item_name']} already complete - skip")
#             continue
        
#         needed = c['required_qty']
#         already_loaded = c.get('boxes_loaded', 0)
#         remaining = needed - already_loaded
        
#         if remaining <= 0:
#             print(f"  ✓ {c['item_name']} already complete - skip")
#             continue
        
#         print(f"\n  📦 {c['item_name']} (need {needed}, "
#               f"already {already_loaded}, remaining {remaining})")
        
#         # ✅ FIXED: Use API response to track actual progress
#         scan_count = 0
#         max_scans = 100  # Safety limit
        
#         while scan_count < max_scans:
#             # Pick random qty for this box
#             qty = min(remaining, random.randint(5, 15))
            
#             print(f"     📡 Scan box ({qty} units)...", end=" ", flush=True)
#             time.sleep(delay)
            
#             result = simulate_box_scan(c['req_id'], c['item_name'], qty)
            
#             if result:
#                 progress = result.get('progress', {})
#                 actual_loaded = progress.get('loaded', 0)
#                 actual_required = progress.get('required', needed)
#                 pct = progress.get('percent', 0)
                
#                 print(f"✓ ({actual_loaded}/{actual_required} = {pct}%)")
#                 scan_count += 1
                
#                 # ✅ FIXED: Check ACTUAL loaded from API, not local counter
#                 remaining = actual_required - actual_loaded
                
#                 if result.get('is_complete') or remaining <= 0:
#                     print(f"     🎉 COMPLETE!")
#                     break
#             else:
#                 print(f"FAILED")
#                 break
        
#         if scan_count >= max_scans:
#             print(f"  ⚠ Hit safety limit ({max_scans} scans)")
    
#     print(f"\n  ✅ Done loading {sid}'s cargo!\n")

# def action_fast_complete():
#     """⚡ FAST MODE: Complete soldier's loading instantly."""
#     sid = input("\n  Enter Soldier ID (e.g., SLD-1234): ").strip()
#     if not sid:
#         return
    
#     print(f"\n  Fetching {sid}'s cargo...\n")
#     cargo = get_soldier_cargo(sid)
    
#     if not cargo:
#         print(f"  No cargo found!\n")
#         return
    
#     print(f"  Found {len(cargo)} items:")
#     total_remaining = 0
#     for c in cargo:
#         loaded = c.get('boxes_loaded', 0)
#         remaining = c['required_qty'] - loaded
#         total_remaining += remaining
#         print(f"    • {c['item_name']}: {loaded}/{c['required_qty']} "
#               f"(need {remaining} more)")
    
#     if total_remaining == 0:
#         print(f"\n  ✅ Everything already loaded!\n")
#         return
    
#     print(f"\n  Total to load: {total_remaining} units")
#     confirm = input(f"  ⚡ Fast complete (1 big scan per item)? (y/n): ").strip().lower()
#     if confirm != 'y':
#         return
    
#     print(f"\n  ⚡ FAST LOADING...\n")
    
#     for c in cargo:
#         if c['status'] == 'COMPLETE':
#             print(f"  ✓ {c['item_name']} already done")
#             continue
        
#         needed = c['required_qty']
#         loaded = c.get('boxes_loaded', 0)
#         remaining = needed - loaded
        
#         if remaining <= 0:
#             continue
        
#         print(f"  📦 {c['item_name']}: Loading {remaining} units in 1 scan...", end=" ", flush=True)
        
#         # Send 1 big scan with all remaining qty
#         result = simulate_box_scan(c['req_id'], c['item_name'], remaining)
        
#         if result:
#             p = result.get('progress', {})
#             print(f"✓ ({p.get('loaded')}/{p.get('required')}) 🎉")
#         else:
#             print(f"FAILED")
    
#     print(f"\n  ⚡✅ FAST LOAD COMPLETE!\n")


# def main():
#     print_banner()
    
#     if not check_server():
#         sys.exit(1)
    
#     while True:
#         try:
#             choice = show_menu()
            
#             if choice == '0':
#                 print("\n  👋 Goodbye!\n")
#                 break
#             elif choice == '1':
#                 action_view_pending()
#             elif choice == '2':
#                 action_single_scan()
#             elif choice == '3':
#                 action_auto_load()
#             elif choice == '4':
#                 action_load_soldier()
            
#             elif choice == '5':
#                 check_server()
#             else:
#                 print("  Invalid choice!")
            
#             input("\n  Press Enter to continue...")
            
#         except KeyboardInterrupt:
#             print("\n\n  👋 Stopped by user.\n")
#             break
#         except Exception as e:
#             print(f"\n  Error: {e}\n")


# if __name__ == '__main__':
#     main()

#!/usr/bin/env python3
"""
UHF BOX LOADING SIMULATOR - v2.0
With Fast Complete Mode for quick demos.
"""

import requests
import time
import random
import sys

API_BASE = "http://localhost:5000/api/v1"


def print_banner():
    print("\n" + "=" * 70)
    print("   📦 UHF BOX LOADING SIMULATOR v2.0")
    print("=" * 70)
    print("   Fast Mode | Real-time API | Demo Ready")
    print("=" * 70 + "\n")


def check_server():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.ok:
            data = r.json()
            print(f"✓ Server:   {data['status']}")
            print(f"✓ Database: {data['database']}")
            print(f"✓ Mode:     {'Simulation' if data['simulation_mode'] else 'Production'}\n")
            return True
        return False
    except Exception as e:
        print(f"✗ Server NOT reachable! {e}")
        print(f"  Start it first: python api_server.py\n")
        return False


def get_pending_loads():
    try:
        r = requests.get(f"{API_BASE}/wh/pending-loads", timeout=10)
        if r.ok:
            return r.json().get('pending', [])
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def get_soldier_cargo(soldier_id):
    try:
        r = requests.get(
            f"{API_BASE}/gate/soldier/{soldier_id}/cargo",
            timeout=10
        )
        if r.ok:
            return r.json().get('data', [])
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def simulate_box_scan(req_id, item_name, qty_in_box=1):
    payload = {
        'req_id': req_id,
        'item_name': item_name,
        'operator': 'WH_Operator_Demo',
        'qty_in_box': qty_in_box
    }
    
    try:
        r = requests.post(
            f"{API_BASE}/wh/load-box",
            json=payload,
            timeout=10
        )
        if r.ok:
            return r.json()
        else:
            return None
    except Exception as e:
        return None


def show_menu():
    print("\n" + "━" * 60)
    print("  CHOOSE AN ACTION:")
    print("━" * 60)
    print("  1. View pending loads")
    print("  2. ⚡ FAST COMPLETE soldier (RECOMMENDED for demo)")
    print("  3. 🐢 Slow demo loading (with visual delay)")
    print("  4. Single box manual scan")
    print("  5. Refresh server status")
    print("  6. Reset soldier's cargo (clean restart)")
    print("  0. Exit")
    print("━" * 60)
    return input("\n  Choice: ").strip()


def action_view_pending():
    print("\n📋 Fetching pending loads...\n")
    pending = get_pending_loads()
    
    if not pending:
        print("  No pending loads found.\n")
        return
    
    print(f"  Total pending: {len(pending)}\n")
    print(f"  {'#':<4} {'Req':<6} {'Item':<12} {'Need':<8} {'Done':<8} {'Status':<12}")
    print(f"  {'-' * 60}")
    
    for i, p in enumerate(pending, 1):
        print(f"  {i:<4} {p.get('req_id'):<6} {p.get('item_name', '-'):<12} "
              f"{p.get('required_qty', 0):<8} {p.get('boxes_loaded', 0):<8} "
              f"{p.get('status', '?'):<12}")
    print()


def action_fast_complete():
    """⚡ FAST MODE - Complete soldier loading instantly."""
    sid = input("\n  Enter Soldier ID (e.g., SLD-1234): ").strip()
    if not sid:
        return
    
    print(f"\n  Fetching {sid}'s cargo...\n")
    cargo = get_soldier_cargo(sid)
    
    if not cargo:
        print(f"  No cargo found for {sid}!\n")
        return
    
    print(f"  Found {len(cargo)} items:")
    total_remaining = 0
    for c in cargo:
        loaded = c.get('boxes_loaded', 0)
        remaining = c['required_qty'] - loaded
        total_remaining += remaining
        print(f"    • {c['item_name']}: {loaded}/{c['required_qty']} "
              f"(remaining {remaining})")
    
    if total_remaining == 0:
        print(f"\n  ✅ Already fully loaded!\n")
        return
    
    print(f"\n  Total units to load: {total_remaining}")
    confirm = input(f"  ⚡ Fast complete? (y/n): ").strip().lower()
    if confirm != 'y':
        return
    
    print(f"\n  ⚡ FAST LOADING...\n")
    
    for c in cargo:
        if c['status'] == 'COMPLETE':
            print(f"  ✓ {c['item_name']} already complete - skip")
            continue
        
        needed = c['required_qty']
        loaded = c.get('boxes_loaded', 0)
        remaining = needed - loaded
        
        if remaining <= 0:
            continue
        
        print(f"  📦 {c['item_name']}: {remaining} units...", end=" ", flush=True)
        time.sleep(0.5)
        
        result = simulate_box_scan(c['req_id'], c['item_name'], remaining)
        
        if result:
            p = result.get('progress', {})
            print(f"✓ ({p.get('loaded')}/{p.get('required')}) 🎉")
        else:
            print(f"FAILED")
    
    print(f"\n  ⚡✅ FAST LOAD COMPLETE!\n")


def action_slow_demo():
    """🐢 Slow demo - good for showing real-time updates."""
    sid = input("\n  Enter Soldier ID: ").strip()
    if not sid:
        return
    
    cargo = get_soldier_cargo(sid)
    if not cargo:
        print(f"  No cargo!\n")
        return
    
    print(f"\n  Found {len(cargo)} items - starting slow loading...\n")
    
    delay = input("  Delay (default 1s): ").strip()
    try:
        delay = float(delay) if delay else 1.0
    except:
        delay = 1.0
    
    for c in cargo:
        if c['status'] == 'COMPLETE':
            continue
        
        needed = c['required_qty']
        loaded = c.get('boxes_loaded', 0)
        remaining = needed - loaded
        
        if remaining <= 0:
            continue
        
        print(f"\n  📦 {c['item_name']} (need {remaining})")
        
        scan_count = 0
        while scan_count < 50:  # Safety limit
            qty = min(remaining, random.randint(5, 15))
            print(f"     📡 Scan ({qty} units)...", end=" ", flush=True)
            time.sleep(delay)
            
            result = simulate_box_scan(c['req_id'], c['item_name'], qty)
            
            if result:
                p = result.get('progress', {})
                actual_loaded = p.get('loaded', 0)
                actual_required = p.get('required', needed)
                print(f"✓ ({actual_loaded}/{actual_required})")
                scan_count += 1
                
                remaining = actual_required - actual_loaded
                if result.get('is_complete') or remaining <= 0:
                    print(f"     🎉 COMPLETE!")
                    break
            else:
                print(f"FAILED")
                break
    
    print(f"\n  ✅ Demo complete!\n")


def action_single_scan():
    """Manual single box scan."""
    pending = get_pending_loads()
    if not pending:
        print(f"  No pending items!\n")
        return
    
    print("\n  Available:")
    for i, p in enumerate(pending, 1):
        print(f"    {i}. Req#{p['req_id']} - {p['item_name']} "
              f"({p.get('boxes_loaded',0)}/{p['required_qty']})")
    
    choice = input(f"\n  Pick number (1-{len(pending)}): ").strip()
    try:
        idx = int(choice) - 1
        target = pending[idx]
    except:
        print("  Invalid!\n")
        return
    
    qty = input("  Quantity (default 1): ").strip()
    qty = int(qty) if qty.isdigit() else 1
    
    print("  📡 Scanning...")
    result = simulate_box_scan(target['req_id'], target['item_name'], qty)
    
    if result:
        p = result.get('progress', {})
        print(f"  ✅ Loaded! ({p.get('loaded')}/{p.get('required')})\n")
    else:
        print("  ❌ Failed!\n")


def action_reset_soldier():
    """Reset soldier's cargo for fresh demo."""
    sid = input("\n  Soldier ID to reset: ").strip()
    if not sid:
        return
    
    confirm = input(f"  ⚠ Delete all loading logs for {sid}? (y/n): ").strip().lower()
    if confirm != 'y':
        return
    
    try:
        r = requests.post(
            f"{API_BASE}/admin/reset-soldier",
            json={'soldier_id': sid},
            timeout=10
        )
        if r.ok:
            print(f"  ✅ Reset complete!\n")
        else:
            print(f"  ⚠ API doesn't have reset endpoint yet.")
            print(f"  Run this in pgAdmin:")
            print(f"     DELETE FROM box_loading_log;")
            print(f"     UPDATE cargo_requirements SET boxes_loaded=0, status='ASSIGNED' WHERE soldier_id='{sid}';\n")
    except Exception as e:
        print(f"  Error: {e}\n")


def main():
    print_banner()
    
    if not check_server():
        sys.exit(1)
    
    while True:
        try:
            choice = show_menu()
            
            if choice == '0':
                print("\n  👋 Goodbye!\n")
                break
            elif choice == '1':
                action_view_pending()
            elif choice == '2':
                action_fast_complete()
            elif choice == '3':
                action_slow_demo()
            elif choice == '4':
                action_single_scan()
            elif choice == '5':
                check_server()
            elif choice == '6':
                action_reset_soldier()
            else:
                print("  Invalid choice!")
            
            input("\n  Press Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n  👋 Stopped.\n")
            break
        except Exception as e:
            print(f"\n  Error: {e}\n")


if __name__ == '__main__':
    main()