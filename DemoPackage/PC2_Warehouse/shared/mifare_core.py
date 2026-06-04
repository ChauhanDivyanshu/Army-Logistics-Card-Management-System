# mifare_core.py
# Shared MIFARE Classic 1K handler used by all card apps.
# Provides low-level read/write/auth operations.

from smartcard.System import readers


class MifareCore:
    """
    Low-level MIFARE Classic 1K operations.
    All card apps (soldier/container/box) use this same handler.
    """

    DEFAULT_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

    def __init__(self, log_callback=None):
        self.reader     = None
        self.connection = None
        self.log        = log_callback or (lambda m, l="info": None)

    # ─────────────────────────────────────────────────────
    # READER MANAGEMENT
    # ─────────────────────────────────────────────────────

    def find_reader(self):
        """Detect first available NFC reader."""
        try:
            r_list = readers()
            if r_list:
                self.reader = r_list[0]
                self.log(f"Reader found: {self.reader}", "ok")
                return True
            self.log("No NFC reader detected", "err")
            return False
        except Exception as e:
            self.log(f"Reader search error: {e}", "err")
            return False

    def connect(self):
        """Connect to card currently on reader."""
        try:
            if not self.reader:
                self.find_reader()
            if not self.reader:
                return False
            self.connection = self.reader.createConnection()
            self.connection.connect()
            return True
        except Exception:
            self.connection = None
            return False

    def disconnect(self):
        """Cleanly disconnect from card."""
        try:
            if self.connection:
                self.connection.disconnect()
        except Exception:
            pass
        self.connection = None

    def get_atr(self):
        """Get card ATR (Answer To Reset) as hex string."""
        try:
            atr = self.connection.getATR()
            return " ".join(f"{b:02X}" for b in atr)
        except Exception:
            return "Unknown"

    # ─────────────────────────────────────────────────────
    # AUTHENTICATION (Tries Key A then Key B)
    # ─────────────────────────────────────────────────────

    def authenticate(self, sector):
        """
        Authenticate sector using default key (FF FF FF FF FF FF).
        Tries Key A first, then Key B as fallback.
        """
        block_num = sector * 4

        for key_type, label in [(0x60, "Key A"), (0x61, "Key B")]:
            try:
                # Load default key into reader
                load_cmd = ([0xFF, 0x82, 0x00, 0x00, 0x06]
                            + self.DEFAULT_KEY)
                self.connection.transmit(load_cmd)

                # Authenticate block
                auth_cmd = [
                    0xFF, 0x86, 0x00, 0x00, 0x05,
                    0x01, 0x00, block_num, key_type, 0x00
                ]
                _, sw1, sw2 = self.connection.transmit(auth_cmd)

                if sw1 == 0x90:
                    self.log(
                        f"Auth OK – Sector {sector} ({label})", "lock"
                    )
                    return True
            except Exception:
                pass

        self.log(f"Auth FAILED – Sector {sector}", "err")
        return False

    # ─────────────────────────────────────────────────────
    # BLOCK READ / WRITE
    # ─────────────────────────────────────────────────────

    def read_block(self, block_num):
        """Read 16 bytes from specified block."""
        try:
            cmd  = [0xFF, 0xB0, 0x00, block_num, 0x10]
            resp, sw1, sw2 = self.connection.transmit(cmd)
            if sw1 == 0x90:
                return resp
            self.log(
                f"Read Block {block_num} FAIL "
                f"SW:{sw1:02X}{sw2:02X}", "err"
            )
            return None
        except Exception as e:
            self.log(f"Read exception: {e}", "err")
            return None

    def write_block(self, block_num, data):
        """Write exactly 16 bytes to specified block."""
        try:
            data = (list(data) + [0x00] * 16)[:16]
            cmd  = [0xFF, 0xD6, 0x00, block_num, 0x10] + data
            _, sw1, sw2 = self.connection.transmit(cmd)
            if sw1 == 0x90:
                return True
            self.log(
                f"Write Block {block_num} FAIL "
                f"SW:{sw1:02X}{sw2:02X}", "err"
            )
            return False
        except Exception as e:
            self.log(f"Write exception: {e}", "err")
            return False

    # ─────────────────────────────────────────────────────
    # ENCODING HELPERS
    # ─────────────────────────────────────────────────────

    @staticmethod
    def encode(text, length):
        """Convert string to fixed-length byte list (null-padded)."""
        raw = str(text).encode("ascii", errors="replace")[:length]
        return list(raw) + [0x00] * (length - len(raw))

    @staticmethod
    def decode(byte_list):
        """Convert byte list to clean string (nulls stripped)."""
        return bytes(
            b for b in byte_list if b != 0x00
        ).decode("ascii", errors="replace").strip()

    @staticmethod
    def encode_int(value, length=2):
        """Convert integer to big-endian bytes."""
        return list(int(value).to_bytes(length, "big"))

    @staticmethod
    def decode_int(byte_list):
        """Convert bytes to integer (big-endian)."""
        return int.from_bytes(bytes(byte_list), "big")


# ─────────────────────────────────────────────────────
# SHARED UI THEME (used by all apps for consistency)
# ─────────────────────────────────────────────────────

COLORS = {
    "bg":        "#ECEFF1",
    "primary":   "#1B5E20",
    "secondary": "#2E7D32",
    "accent":    "#FFB300",
    "danger":    "#C62828",
    "info":      "#1565C0",
    "success":   "#2E7D32",
    "warning":   "#E65100",
    "dark":      "#263238",
    "white":     "#FFFFFF",
    "text":      "#212121",
    "muted":     "#607D8B",
    "border":    "#CFD8DC",
}