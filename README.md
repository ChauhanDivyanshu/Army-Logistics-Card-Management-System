# 🎖 Army Logistics Card Management System

A complete logistics management system for the Indian Army using **MIFARE Classic 1K** cards and **PostgreSQL** database.

![Status](https://img.shields.io/badge/Status-Complete-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Features

- ✅ **5 Independent Applications** with launcher
- ✅ **PostgreSQL Database** integration
- ✅ **MIFARE Card Read/Write** support
- ✅ **Auto Warehouse Assignment** logic
- ✅ **Real-time Card Detection**
- ✅ **Professional Army-themed UI**
- ✅ **Gate Verification System**
- ✅ **Printable Assignment Slips**

## 🏗️ Project Structure

\```
army_logistics/
├── main.py                  # Main launcher
├── database/
│   ├── db_config.py        # DB credentials (not in git)
│   ├── db_config.example.py # Template
│   └── db_helper.py        # Database operations
├── shared/
│   ├── theme.py            # UI colors/fonts
│   └── mifare_core.py      # MIFARE handler
└── apps/
    ├── warehouse_app.py    # Warehouse management
    ├── container_app.py    # Container tags
    ├── box_app.py          # Box tags
    ├── soldier_app.py      # Soldier cards
    └── gate_app.py         # Gate verification ⭐
\```