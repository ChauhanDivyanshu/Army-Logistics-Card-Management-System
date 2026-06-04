# database/db_config.py
# Database connection configuration
# Yahan apne PostgreSQL credentials daalo

# DB_CONFIG = {
#     "host":     "localhost",         
#     "port":     "5432",               
#     "database": "army_logistics",      
#     "user":     "postgres",            
#     "password": "trustlayer123"             
# }

# database/db_config.py
import os
import sys

# Determine base path (works in .py and .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_CONFIG = {
    "host": "localhost",
    "database": "army_logistics",
    "user": "postgres",
    "password": "trustlayer123",  # ← Change to your password
    "port": 5432
}