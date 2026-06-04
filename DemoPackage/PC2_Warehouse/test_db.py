# test_db.py
# Quick test to verify database connection and operations

import sys
import os

# Add database folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))

from db_helper import DatabaseHelper


def main():
    print("\n" + "=" * 60)
    print("  🎖  ARMY LOGISTICS - DATABASE TEST")
    print("=" * 60)

    db = DatabaseHelper()

    # ─────────────────────────────────────────────────────
    # 1. Connection Test
    # ─────────────────────────────────────────────────────
    print("\n[1] Testing Database Connection...")
    success, msg = db.test_connection()
    if success:
        print(f"    ✅ Connected to PostgreSQL")
    else:
        print(f"    ❌ Connection Failed: {msg}")
        print(f"\n💡 Check db_config.py - password sahi h?")
        return

    # ─────────────────────────────────────────────────────
    # 2. System Overview
    # ─────────────────────────────────────────────────────
    print("\n[2] System Overview:")
    print("-" * 60)
    stats = db.get_system_stats()
    if stats:
        print(f"    🏭 Warehouses:    {stats['total_warehouses']}")
        print(f"    📦 Containers:    {stats['total_containers']}")
        print(f"    🗃  Boxes:         {stats['total_boxes']}")
        print(f"    🪖  Soldiers:      {stats['total_soldiers']}")
        print(f"    ⏳ Pending:       {stats['pending_requests']}")
        print(f"    ✅ Assigned:      {stats['assigned_requests']}")
        print(f"    ✔  Completed:    {stats['completed_requests']}")

    # ─────────────────────────────────────────────────────
    # 3. Warehouses List
    # ─────────────────────────────────────────────────────
    print("\n[3] All Warehouses:")
    print("-" * 60)
    print(f"    {'ID':<8} {'Name':<25} {'Location':<25}")
    print(f"    {'-'*8} {'-'*25} {'-'*25}")
    for w in db.get_all_warehouses():
        print(f"    {w['warehouse_id']:<8} "
              f"{w['warehouse_name']:<25} "
              f"{w['location']:<25}")

    # ─────────────────────────────────────────────────────
    # 4. Containers List
    # ─────────────────────────────────────────────────────
    print("\n[4] All Containers:")
    print("-" * 60)
    print(f"    {'SKU-ID':<12} {'Name':<15} {'Item':<10} "
          f"{'Boxes':<6} {'Qty':<6} {'Warehouse':<10}")
    print(f"    {'-'*12} {'-'*15} {'-'*10} {'-'*6} {'-'*6} {'-'*10}")
    for c in db.get_all_containers():
        print(f"    {c['sku_id']:<12} "
              f"{c['container_name']:<15} "
              f"{c['item_name']:<10} "
              f"{str(c['total_boxes']):<6} "
              f"{str(c['total_quantity']):<6} "
              f"{c['warehouse_id']:<10}")

    # ─────────────────────────────────────────────────────
    # 5. Boxes in Container CNT-A-101
    # ─────────────────────────────────────────────────────
    print("\n[5] Boxes inside Container CNT-A-101 (AK47):")
    print("-" * 60)
    boxes = db.get_boxes_by_container('CNT-A-101')
    for b in boxes:
        print(f"    {b['box_uid']:<10} | "
              f"Qty: {b['quantity']:<4} {b['unit']} | "
              f"Batch: {b['batch_number']}")

    # ─────────────────────────────────────────────────────
    # 6. Soldiers List
    # ─────────────────────────────────────────────────────
    print("\n[6] All Soldiers:")
    print("-" * 60)
    for s in db.get_all_soldiers():
        print(f"    {s['soldier_id']:<10} | "
              f"{s['soldier_name']:<20} | "
              f"Conductor: {s['conductor_name']}")

    # ─────────────────────────────────────────────────────
    # 7. 🎯 GATE OPERATOR SIMULATION
    # ─────────────────────────────────────────────────────
    print("\n[7] 🎯 GATE SCAN SIMULATION - Soldier SLD-1234")
    print("=" * 60)

    soldier = db.get_soldier_by_id('SLD-1234')
    if soldier:
        print(f"    👤 Soldier:    {soldier['soldier_name']} "
              f"({soldier['soldier_id']})")
        print(f"    🚗 Conductor:  {soldier['conductor_name']} "
              f"({soldier['conductor_id']})")
        print(f"    🏛  Unit:       {soldier['unit_name']}")

        print(f"\n    📋 REQUIRED CARGO & ASSIGNMENTS:")
        print(f"    {'-'*56}")

        assignment = db.get_soldier_full_assignment('SLD-1234')
        for a in assignment:
            print(f"\n    Item: {a['required_item']} × {a['required_qty']}")
            if a['container_id']:
                print(f"      📦 Container:  {a['container_id']} "
                      f"({a['container_name']})")
                print(f"      🏭 Warehouse:  {a['warehouse_name']} "
                      f"({a['warehouse_id']})")
                print(f"      📍 Location:   {a['warehouse_location']}")
                print(f"      📊 Available:  {a['available_qty']} units "
                      f"in {a['available_boxes']} boxes")
            else:
                print(f"      ⚠️  NOT AVAILABLE in any warehouse")

    # ─────────────────────────────────────────────────────
    # 8. Auto-Assign Test
    # ─────────────────────────────────────────────────────
    print("\n\n[8] 🤖 AUTO ASSIGNMENT - Soldier SLD-1236")
    print("=" * 60)
    assigned = db.auto_assign_warehouses('SLD-1236')
    for a in assigned:
        print(f"    ✅ {a['item']:<10} × {a['qty']:<4} → "
              f"Container: {a['container'] or 'N/A':<12} | "
              f"Warehouse: {a['warehouse_name']}")

    # ─────────────────────────────────────────────────────
    # 9. Search Test
    # ─────────────────────────────────────────────────────
    print("\n\n[9] 🔍 SEARCH RESULTS for 'AK'")
    print("-" * 60)
    items = db.search_items('AK')
    for i in items:
        print(f"    {i['item_name']:<10} | "
              f"Qty: {i['total_quantity']:<5} | "
              f"Container: {i['sku_id']:<12} | "
              f"Warehouse: {i['warehouse_name']}")

    print("\n" + "=" * 60)
    print("  ✅ ALL TESTS PASSED SUCCESSFULLY!")
    print("  🎉 Database is ready for use!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()