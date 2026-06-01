# auth/auth_helper.py
# 🔑 Authentication helper functions
# Password hashing & verification

import hashlib


def hash_password(password):
    """
    Hash a password using SHA-256.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password (64-character hex string)
    """
    if not password:
        return ""
    
    # Convert to bytes and hash
    password_bytes = password.encode("utf-8")
    hash_obj = hashlib.sha256(password_bytes)
    return hash_obj.hexdigest()


def verify_password(plain_password, hashed_password):
    """
    Verify if plain password matches the hash.
    
    Args:
        plain_password:  User input
        hashed_password: Stored hash from database
    
    Returns:
        True if match, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
    
    return hash_password(plain_password) == hashed_password


# ═══════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  AUTH HELPER - TEST MODE")
    print("=" * 60)

    # Test hashing
    print("\n📝 Password Hashing Test:")
    test_passwords = ["admin123", "password123", "test@1234"]
    for pwd in test_passwords:
        hashed = hash_password(pwd)
        print(f"   '{pwd}' → {hashed}")

    # Test verification
    print("\n📝 Password Verification Test:")
    pwd = "admin123"
    hashed = hash_password(pwd)
    print(f"   Original:  {pwd}")
    print(f"   Hash:      {hashed}")
    print(f"   Verify OK: {verify_password('admin123', hashed)}")
    print(f"   Verify NO: {verify_password('wrongpass', hashed)}")

    print("\n" + "=" * 60)
    print("  ✅ AUTH HELPER TESTS COMPLETED")
    print("=" * 60)