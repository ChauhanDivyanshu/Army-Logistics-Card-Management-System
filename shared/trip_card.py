# shared/trip_card.py
# 🚛 TRIP CARD - Supports long names (32 chars)

class TripCard:
    """
    MIFARE 1K Layout (Updated for longer names):
    ────────────────────────────────────────────
    Sector 1: Truck & Driver ID
      Block 4: Truck Number (16 chars)
      Block 5: Driver ID (16 chars)
      Block 6: Driver Name PART 1 (16 chars)
    
    Sector 2: Driver Name continuation + Sub-driver
      Block 8:  Driver Name PART 2 (16 chars) → Total 32 chars
      Block 9:  Sub-driver ID (16 chars)
      Block 10: Sub-driver Name PART 1 (16 chars)
    
    Sector 3: Sub-driver Name continuation + Trip ID + Item count
      Block 12: Sub-driver Name PART 2 (16 chars) → Total 32 chars
      Block 13: Trip ID (16 chars)
      Block 14: Item count
    
    Sectors 4-15: Items
    ────────────────────────────────────────────
    """

    ITEM_BLOCKS = [
        16, 17, 18,
        20, 21, 22,
        24, 25, 26,
        28, 29, 30,
        32, 33, 34,
        36, 37, 38,
        40, 41, 42,
        44, 45, 46,
        48, 49, 50,
        52, 53, 54,
        56, 57, 58,
        60, 61, 62,
    ]

    def __init__(self):
        self.truck_number = ""
        self.driver_id = ""
        self.driver_name = ""
        self.subdriver_id = ""
        self.subdriver_name = ""
        self.trip_id = ""
        self.items = []

    def _split_name(self, name, max_total=32):
        """Split name into 2 parts (16 + 16 chars)."""
        name = str(name)[:max_total]
        part1 = name[:16]
        part2 = name[16:32] if len(name) > 16 else ""
        return part1, part2

    def _combine_name(self, part1, part2):
        """Combine 2 parts into full name."""
        return (str(part1 or "") + str(part2 or "")).strip()

    def write(self, core):
        """Write trip data with support for 32-char names."""
        
        # Sector 1: Truck + Driver ID + Driver Name Part 1
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")
        
        core.write_block(4, core.encode(self.truck_number, 16))
        core.write_block(5, core.encode(self.driver_id, 16))
        
        # Split driver name into 2 parts
        dn_p1, dn_p2 = self._split_name(self.driver_name)
        core.write_block(6, core.encode(dn_p1, 16))

        # Sector 2: Driver Name Part 2 + Sub-driver ID + Sub-driver Name Part 1
        if not core.authenticate(2):
            raise Exception("Auth failed - Sector 2")
        
        core.write_block(8, core.encode(dn_p2, 16))
        core.write_block(9, core.encode(self.subdriver_id, 16))
        
        # Split sub-driver name into 2 parts
        sn_p1, sn_p2 = self._split_name(self.subdriver_name)
        core.write_block(10, core.encode(sn_p1, 16))

        # Sector 3: Sub-driver Name Part 2 + Trip ID + Item count
        if not core.authenticate(3):
            raise Exception("Auth failed - Sector 3")
        
        core.write_block(12, core.encode(sn_p2, 16))
        core.write_block(13, core.encode(self.trip_id, 16))
        core.write_block(14, core.encode(str(len(self.items)), 16))

        # Sectors 4+: Items
        current_sector = None
        for i, item in enumerate(self.items):
            if i >= len(self.ITEM_BLOCKS):
                break
            block = self.ITEM_BLOCKS[i]
            sector = block // 4
            if sector != current_sector:
                if not core.authenticate(sector):
                    raise Exception(f"Auth failed - Sector {sector}")
                current_sector = sector
            item_str = f"{item['name']}|{item['qty']}"
            core.write_block(block, core.encode(item_str, 16))

        return True

    def read(self, core):
        """Read trip data with support for 32-char names."""
        
        # Sector 1
        if not core.authenticate(1):
            raise Exception("Auth failed - Sector 1")
        
        b = core.read_block(4)
        if b:
            self.truck_number = core.decode(b)
        b = core.read_block(5)
        if b:
            self.driver_id = core.decode(b)
        
        # Driver name part 1
        driver_p1 = ""
        b = core.read_block(6)
        if b:
            driver_p1 = core.decode(b)

        # Sector 2
        driver_p2 = ""
        subdriver_p1 = ""
        try:
            if core.authenticate(2):
                b = core.read_block(8)
                if b:
                    driver_p2 = core.decode(b)
                b = core.read_block(9)
                if b:
                    self.subdriver_id = core.decode(b)
                b = core.read_block(10)
                if b:
                    subdriver_p1 = core.decode(b)
        except Exception:
            pass

        # Sector 3
        subdriver_p2 = ""
        item_count = 0
        try:
            if core.authenticate(3):
                b = core.read_block(12)
                if b:
                    subdriver_p2 = core.decode(b)
                b = core.read_block(13)
                if b:
                    self.trip_id = core.decode(b)
                b = core.read_block(14)
                if b:
                    try:
                        item_count = int(core.decode(b))
                    except ValueError:
                        item_count = 0
        except Exception:
            pass

        # Combine name parts
        self.driver_name = self._combine_name(driver_p1, driver_p2)
        self.subdriver_name = self._combine_name(subdriver_p1, subdriver_p2)

        # Read items
        self.items = []
        current_sector = None
        for i in range(item_count):
            if i >= len(self.ITEM_BLOCKS):
                break
            block = self.ITEM_BLOCKS[i]
            sector = block // 4
            if sector != current_sector:
                try:
                    if not core.authenticate(sector):
                        continue
                    current_sector = sector
                except Exception:
                    continue
            try:
                b = core.read_block(block)
                if b:
                    raw = core.decode(b)
                    if '|' in raw:
                        parts = raw.split('|')
                        name = parts[0].strip()
                        try:
                            qty = int(parts[1].strip())
                        except (ValueError, IndexError):
                            qty = 0
                        if name:
                            self.items.append({'name': name, 'qty': qty})
            except Exception:
                continue

        return True

    def to_dict(self):
        return {
            'truck_number': self.truck_number,
            'driver_id': self.driver_id,
            'driver_name': self.driver_name,
            'subdriver_id': self.subdriver_id,
            'subdriver_name': self.subdriver_name,
            'trip_id': self.trip_id,
            'items': self.items,
            'item_count': len(self.items),
        }

    def is_valid(self):
        return bool(self.truck_number and self.truck_number.strip())

    def add_item(self, name, qty):
        self.items.append({'name': str(name), 'qty': int(qty)})

    def clear_items(self):
        self.items = []