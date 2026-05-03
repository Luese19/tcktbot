#!/usr/bin/env python3
"""
Comprehensive bot startup diagnostic
Run this INSTEAD of main.py to see detailed diagnostics
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup path
_root_dir = str(Path(__file__).parent.resolve())
if _root_dir in sys.path:
    sys.path.remove(_root_dir)
sys.path.insert(0, _root_dir)

# Load env
_env_path = Path(_root_dir) / '.env'
load_dotenv(_env_path, override=True)

print("=" * 80)
print("TICKETING BOT - DETAILED STARTUP DIAGNOSTIC")
print("=" * 80)

# Pre-check 1: Check lock file state BEFORE importing process manager
lock_file = Path.home() / ".ticketingbot.lock"
print(f"\n1. PRE-CHECK: Lock file state (before imports)")
print(f"   Path: {lock_file}")
print(f"   Exists: {lock_file.exists()}")
if lock_file.exists():
    with open(lock_file, 'r') as f:
        content = f.read().strip()
    print(f"   Content: '{content}'")
    
    # Check if it's a valid PID
    try:
        pid_int = int(content)
        print(f"   Parsed as PID: {pid_int}")
        
        import psutil
        exists = psutil.pid_exists(pid_int)
        print(f"   PID exists: {exists}")
        
        if exists:
            try:
                proc = psutil.Process(pid_int)
                print(f"   Process name: {proc.name()}")
                print(f"   Cmd: {' '.join(proc.cmdline()[:3])}")
                print(f"   'python' in name: {'python' in proc.name().lower()}")
            except Exception as e:
                print(f"   Error getting process info: {e}")
    except ValueError as e:
        print(f"   ERROR: Not a valid PID integer: {e}")

# Pre-check 2: Environment
print(f"\n2. ENVIRONMENT CHECK:")
print(f"   Python version: {sys.version}")
print(f"   Current PID: {os.getpid()}")
print(f"   Working dir: {os.getcwd()}")
print(f"   Bot token set: {'TELEGRAM_BOT_TOKEN' in os.environ and bool(os.environ.get('TELEGRAM_BOT_TOKEN'))}")

# Pre-check 3: Try importing process manager
print(f"\n3. IMPORTING PROCESS MANAGER:")
try:
    from utils.process_manager import check_single_instance
    print(f"   ✓ Process manager imported successfully")
except Exception as e:
    print(f"   ✗ ERROR importing process manager: {e}")
    sys.exit(1)

# Pre-check 4: Try to acquire lock
print(f"\n4. ATTEMPTING LOCK ACQUISITION:")
try:
    result = check_single_instance()
    print(f"   Result: {result}")
    
    if not result:
        print(f"   ✗ Lock acquisition FAILED")
        print(f"\n   CHECK: Lock file status after failed acquisition")
        if lock_file.exists():
            with open(lock_file, 'r') as f:
                content = f.read().strip()
            print(f"      Lock file content: '{content}'")
        sys.exit(1)
    else:
        print(f"   ✓ Lock acquisition SUCCEEDED")
        if lock_file.exists():
            with open(lock_file, 'r') as f:
                content = f.read().strip()
            print(f"      Lock file now contains: '{content}' (our PID)")
        
except Exception as e:
    print(f"   ✗ ERROR during lock acquisition: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n" + "=" * 80)
print(f"✓ ALL CHECKS PASSED - BOT READY TO START")
print(f"=" * 80)
print(f"\nYou can now run: python main.py")
