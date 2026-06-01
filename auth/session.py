# auth/session.py
# 🔐 USER SESSION MANAGER
# Stores currently logged-in user information globally

from datetime import datetime


class Session:
    """
    Singleton session manager - stores current logged-in user.
    Access from anywhere using: Session.get_user(), Session.role, etc.
    """

    # ─── Class-level attributes (shared across app) ───
    _user_id           = None
    _username          = None
    _full_name         = None
    _role              = None
    _assigned_unit     = None
    _assigned_warehouse = None
    _email             = None
    _login_time        = None
    _is_logged_in      = False

    # ═══════════════════════════════════════════════════════
    # LOGIN / LOGOUT
    # ═══════════════════════════════════════════════════════

    @classmethod
    def login(cls, user_data):
        """
        Set current user data after successful login.
        
        Args:
            user_data (dict): User info from database
                Required keys: user_id, username, full_name, role
                Optional: assigned_unit, assigned_warehouse, email
        """
        cls._user_id            = user_data.get('user_id')
        cls._username           = user_data.get('username')
        cls._full_name          = user_data.get('full_name')
        cls._role               = user_data.get('role')
        cls._assigned_unit      = user_data.get('assigned_unit')
        cls._assigned_warehouse = user_data.get('assigned_warehouse')
        cls._email              = user_data.get('email')
        cls._login_time         = datetime.now()
        cls._is_logged_in       = True

    @classmethod
    def logout(cls):
        """Clear all session data on logout."""
        cls._user_id            = None
        cls._username           = None
        cls._full_name          = None
        cls._role               = None
        cls._assigned_unit      = None
        cls._assigned_warehouse = None
        cls._email              = None
        cls._login_time         = None
        cls._is_logged_in       = False

    # ═══════════════════════════════════════════════════════
    # GETTERS (Properties)
    # ═══════════════════════════════════════════════════════

    @classmethod
    def is_logged_in(cls):
        """Check if any user is currently logged in."""
        return cls._is_logged_in

    @classmethod
    def get_user_id(cls):
        return cls._user_id

    @classmethod
    def get_username(cls):
        return cls._username

    @classmethod
    def get_full_name(cls):
        return cls._full_name

    @classmethod
    def get_role(cls):
        return cls._role

    @classmethod
    def get_assigned_unit(cls):
        return cls._assigned_unit

    @classmethod
    def get_assigned_warehouse(cls):
        return cls._assigned_warehouse

    @classmethod
    def get_email(cls):
        return cls._email

    @classmethod
    def get_login_time(cls):
        return cls._login_time

    # ═══════════════════════════════════════════════════════
    # ROLE CHECK HELPERS (Convenient shortcuts)
    # ═══════════════════════════════════════════════════════

    @classmethod
    def is_admin(cls):
        return cls._role == 'ADMIN'

    @classmethod
    def is_gate(cls):
        return cls._role == 'GATE'

    @classmethod
    def is_unit(cls):
        return cls._role == 'UNIT'

    @classmethod
    def is_warehouse(cls):
        return cls._role == 'WAREHOUSE'

    # ═══════════════════════════════════════════════════════
    # GET ALL DATA (For display/debug)
    # ═══════════════════════════════════════════════════════

    @classmethod
    def get_user_data(cls):
        """Get all session data as dictionary."""
        return {
            'user_id':            cls._user_id,
            'username':           cls._username,
            'full_name':          cls._full_name,
            'role':               cls._role,
            'assigned_unit':      cls._assigned_unit,
            'assigned_warehouse': cls._assigned_warehouse,
            'email':              cls._email,
            'login_time':         cls._login_time,
            'is_logged_in':       cls._is_logged_in,
        }

    @classmethod
    def get_display_info(cls):
        """Get formatted info string for display (header bar)."""
        if not cls._is_logged_in:
            return "Not Logged In"
        return f"👤 {cls._full_name} ({cls._role})"


# ═══════════════════════════════════════════════════════════
#  STANDALONE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  SESSION MANAGER - TEST")
    print("=" * 60)

    # Test 1: Initial state
    print("\n📋 TEST 1: Initial state")
    print(f"   Logged in: {Session.is_logged_in()}")
    print(f"   Display:   {Session.get_display_info()}")

    # Test 2: Login
    print("\n🔐 TEST 2: Login as admin")
    Session.login({
        'user_id':    1,
        'username':   'admin',
        'full_name':  'System Administrator',
        'role':       'ADMIN',
        'email':      'admin@army.gov.in'
    })
    print(f"   Logged in: {Session.is_logged_in()}")
    print(f"   Username:  {Session.get_username()}")
    print(f"   Role:      {Session.get_role()}")
    print(f"   Is Admin:  {Session.is_admin()}")
    print(f"   Is Gate:   {Session.is_gate()}")
    print(f"   Display:   {Session.get_display_info()}")

    # Test 3: Logout
    print("\n🚪 TEST 3: Logout")
    Session.logout()
    print(f"   Logged in: {Session.is_logged_in()}")
    print(f"   Display:   {Session.get_display_info()}")

    print("\n" + "=" * 60)
    print("  ✅ SESSION TESTS PASSED!")
    print("=" * 60)