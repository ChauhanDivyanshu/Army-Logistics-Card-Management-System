# apps/soldier_app.py
# 🚛 REDIRECT to Trip Card App
# Soldier management replaced with Trip Card Manager

import tkinter as tk
import os
import sys
import subprocess

def main():
    """Launch Trip Card App instead."""
    BASE = os.path.dirname(os.path.abspath(__file__))
    trip_app = os.path.join(BASE, 'trip_card_app.py')
    
    if os.path.exists(trip_app):
        # Launch trip card app
        subprocess.Popen([sys.executable, trip_app])
    else:
        # Show message
        root = tk.Tk()
        root.title("Module Replaced")
        root.geometry("500x200")
        root.configure(bg="#ECEFF1")
        
        tk.Label(root, text="ℹ️  Module Replaced",
                 font=("Segoe UI", 16, "bold"),
                 bg="#ECEFF1", fg="#1B5E20").pack(pady=20)
        
        tk.Label(root, text="Soldier App has been replaced by Trip Card App.\n\n"
                            "Please use:\n"
                            "python apps/trip_card_app.py",
                 font=("Segoe UI", 11),
                 bg="#ECEFF1", fg="#333").pack(pady=10)
        
        tk.Button(root, text="OK", command=root.destroy,
                  font=("Segoe UI", 10, "bold"),
                  bg="#1B5E20", fg="white",
                  relief=tk.FLAT, padx=30, pady=8).pack(pady=20)
        
        root.mainloop()

if __name__ == "__main__":
    main()