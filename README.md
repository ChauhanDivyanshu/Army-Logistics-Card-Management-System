# 🎖️ Indian Army Logistics System

A comprehensive military logistics management system with multi-tier architecture.

## Features
- Multi-role authentication (Admin, Gate, Unit, Warehouse)
- MIFARE NFC card integration
- UHF RFID bulk scanning
- Real-time inventory tracking
- REST API with WebSocket support
- Role-based access control

## Tech Stack
- Python 3.10+
- PostgreSQL 18
- Flask + Flask-SocketIO
- Tkinter (GUI)
- pyscard (MIFARE)

## Setup

### 1. Install Dependencies
\\\ash
pip install -r requirements.txt
\\\

### 2. Configure Database
\\\ash
# Copy example config
cp database/db_config.example.py database/db_config.py

# Edit and add your PostgreSQL credentials
\\\

### 3. Setup Database
\\\ash
# Create database in PostgreSQL
# Run the SQL setup script (see docs)
\\\

### 4. Run
\\\ash
# Start API server
python api_server.py

# In another terminal, start main app
python main.py
\\\

## Demo Credentials
- Admin: \dmin / admin123\
- Gate: \gate1 / password123\
- Unit: \unit1 / password123\
- Warehouse: \warehouse1 / password123\

## Build .exe
\\\ash
# See build instructions in docs
\\\

## License
© 2025 Indian Army
