# test_gate.py
# Quick test to see what gate app receives

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from db_helper import DatabaseHelper

db = DatabaseHelper()

print("\n" + "=" * 70)
print("  GATE APP DEBUG TEST - SLD-1234")
print("=" * 70)

# Get soldier
soldier = db.get_soldier_by_id('SLD-1234')
print(f"\nSoldier: {soldier}")

# Get full assignment
print(f"\n{'-'*70}")
print("FULL ASSIGNMENT DATA:")
print("-" * 70)

assignments = db.get_soldier_full_assignment('SLD-1234')

print(f"\nTotal records: {len(assignments)}")
print()

for i, a in enumerate(assignments, 1):
    print(f"Record {i}:")
    for key, value in a.items():
        print(f"   {key:25} = {value}")
    print()

print("=" * 70)