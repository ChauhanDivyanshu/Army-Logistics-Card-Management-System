#!/usr/bin/env python3
"""
BUILD SCRIPT - Convert Army Logistics to .exe
Run: python build.py
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, 'dist')
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')
OUTPUT_DIR = os.path.join(DIST_DIR, 'ArmyLogistics')


def clean():
    """Remove old build files."""
    print("🧹 Cleaning old builds...")
    for folder in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    # Remove .spec files
    for f in os.listdir(PROJECT_ROOT):
        if f.endswith('.spec') and f != 'build_exe.spec':
            os.remove(os.path.join(PROJECT_ROOT, f))
    
    print("   ✅ Clean done")


def build_main():
    """Build main launcher as .exe"""
    print("\n📦 Building Main Launcher...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=ArmyLogistics',
        '--windowed',           # No console
        '--noconfirm',          # Overwrite without asking
        '--clean',              # Clean cache
        
        # Add all data files
        '--add-data', f'database{os.pathsep}database',
        '--add-data', f'shared{os.pathsep}shared',
        '--add-data', f'auth{os.pathsep}auth',
        '--add-data', f'config{os.pathsep}config',
        '--add-data', f'apps{os.pathsep}apps',
        
        # Hidden imports
        '--hidden-import=psycopg2',
        '--hidden-import=psycopg2.extras',
        '--hidden-import=psycopg2._psycopg',
        '--hidden-import=requests',
        '--hidden-import=hashlib',
        
        # Entry point
        'main.py'
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode == 0:
        print("   ✅ Main launcher built successfully!")
    else:
        print("   ❌ Build failed!")
        return False
    
    return True


def build_api_server():
    """Build API server as separate .exe"""
    print("\n📦 Building API Server...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=APIServer',
        '--console',            # Need console for server logs
        '--noconfirm',
        '--clean',
        
        '--add-data', f'database{os.pathsep}database',
        
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=flask_socketio',
        '--hidden-import=engineio',
        '--hidden-import=engineio.async_drivers',
        '--hidden-import=engineio.async_drivers.threading',
        '--hidden-import=psycopg2',
        '--hidden-import=psycopg2.extras',
        '--hidden-import=psycopg2._psycopg',
        
        'api_server.py'
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode == 0:
        print("   ✅ API Server built successfully!")
    else:
        print("   ❌ API Server build failed!")
        return False
    
    return True


def create_launcher_bat():
    """Create batch files for easy launching."""
    print("\n📝 Creating launcher scripts...")
    
    output = os.path.join(DIST_DIR, 'ArmyLogistics')
    
    # Start API Server batch
    api_bat = os.path.join(output, 'Start_API_Server.bat')
    with open(api_bat, 'w') as f:
        f.write('@echo off\n')
        f.write('echo ===================================\n')
        f.write('echo   Army Logistics - API Server\n')
        f.write('echo ===================================\n')
        f.write('echo Starting API Server on port 5000...\n')
        f.write('echo.\n')
        f.write('cd /d "%~dp0"\n')
        f.write('APIServer.exe\n')
        f.write('pause\n')
    
    # Start Main App batch
    app_bat = os.path.join(output, 'Start_ArmyLogistics.bat')
    with open(app_bat, 'w') as f:
        f.write('@echo off\n')
        f.write('echo ===================================\n')
        f.write('echo   Army Logistics - Main App\n')
        f.write('echo ===================================\n')
        f.write('echo.\n')
        f.write('echo IMPORTANT: Start API Server first!\n')
        f.write('echo.\n')
        f.write('cd /d "%~dp0"\n')
        f.write('ArmyLogistics.exe\n')
    
    # Start Both (recommended)
    both_bat = os.path.join(output, 'START_HERE.bat')
    with open(both_bat, 'w') as f:
        f.write('@echo off\n')
        f.write('echo ===================================\n')
        f.write('echo   Indian Army Logistics System\n')
        f.write('echo ===================================\n')
        f.write('echo.\n')
        f.write('echo Step 1: Starting API Server...\n')
        f.write('start "API Server" APIServer.exe\n')
        f.write('echo Waiting for API to initialize...\n')
        f.write('timeout /t 3 /nobreak >nul\n')
        f.write('echo.\n')
        f.write('echo Step 2: Starting Main Application...\n')
        f.write('start "Army Logistics" ArmyLogistics.exe\n')
        f.write('echo.\n')
        f.write('echo Both applications started!\n')
        f.write('echo Close this window anytime.\n')
        f.write('pause\n')
    
    # README
    readme = os.path.join(output, 'README.txt')
    with open(readme, 'w') as f:
        f.write('=============================================\n')
        f.write('  INDIAN ARMY LOGISTICS SYSTEM\n')
        f.write('=============================================\n\n')
        f.write('HOW TO USE:\n\n')
        f.write('1. Double-click "START_HERE.bat"\n')
        f.write('   This starts both API Server and Main App\n\n')
        f.write('2. Login with:\n')
        f.write('   Admin:     admin / admin123\n')
        f.write('   Gate:      gate1 / password123\n')
        f.write('   Unit:      unit1 / password123\n')
        f.write('   Warehouse: warehouse1 / password123\n\n')
        f.write('REQUIREMENTS:\n')
        f.write('- PostgreSQL must be running\n')
        f.write('- Database "army_logistics" must exist\n')
        f.write('- MIFARE reader (ACR122U) for card operations\n\n')
        f.write('TROUBLESHOOTING:\n')
        f.write('- If API error: Run Start_API_Server.bat first\n')
        f.write('- If DB error: Check PostgreSQL is running\n')
        f.write('- If login fails: Check db_config credentials\n\n')
        f.write('=============================================\n')
    
    print("   ✅ Launcher scripts created!")


def copy_api_to_main():
    """Copy API Server exe to main distribution folder."""
    print("\n📋 Merging builds...")
    
    api_dist = os.path.join(DIST_DIR, 'APIServer')
    main_dist = os.path.join(DIST_DIR, 'ArmyLogistics')
    
    if os.path.exists(api_dist) and os.path.exists(main_dist):
        # Copy all API server files to main folder
        for item in os.listdir(api_dist):
            src = os.path.join(api_dist, item)
            dst = os.path.join(main_dist, item)
            
            if os.path.isfile(src):
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
            elif os.path.isdir(src):
                if not os.path.exists(dst):
                    shutil.copytree(src, dst)
        
        # Clean up API separate folder
        shutil.rmtree(api_dist)
        print("   ✅ Builds merged!")
    else:
        print("   ⚠️ Could not merge (folder missing)")


def show_summary():
    """Show build summary."""
    output = os.path.join(DIST_DIR, 'ArmyLogistics')
    
    print("\n" + "=" * 60)
    print("  ✅ BUILD COMPLETE!")
    print("=" * 60)
    print(f"\n  Output folder: {output}")
    print(f"\n  Files created:")
    
    if os.path.exists(output):
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(output):
            for f in files:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                total_size += size
                file_count += 1
                if f.endswith(('.exe', '.bat', '.txt')):
                    print(f"    {'📦' if f.endswith('.exe') else '📝'} {f} ({size // 1024} KB)")
        
        print(f"\n  Total files: {file_count}")
        print(f"  Total size:  {total_size // (1024 * 1024)} MB")
    
    print(f"\n  HOW TO RUN:")
    print(f"  1. Open folder: {output}")
    print(f"  2. Double-click: START_HERE.bat")
    print(f"\n" + "=" * 60)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  🔨 ARMY LOGISTICS - BUILD SYSTEM")
    print("  Converting Python → .exe")
    print("=" * 60)
    
    # Step 1: Clean
    clean()
    
    # Step 2: Build main app
    if not build_main():
        print("\n❌ Main build failed! Aborting.")
        sys.exit(1)
    
    # Step 3: Build API server
    if not build_api_server():
        print("\n⚠️ API Server build failed (continuing...)")
    
    # Step 4: Merge builds
    copy_api_to_main()
    
    # Step 5: Create launcher scripts
    create_launcher_bat()
    
    # Step 6: Summary
    show_summary()