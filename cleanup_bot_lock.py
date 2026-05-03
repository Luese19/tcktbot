#!/usr/bin/env python3
"""
Cleanup script - Remove stale lock files and prepare for fresh bot start
"""

import os
import sys
from pathlib import Path
import time

print("=" * 70)
print("TICKETING BOT - CLEANUP & RESET")
print("=" * 70)

def cleanup_lock_files():
    """Remove any stale lock files"""
    lock_locations = [
        Path.home() / ".ticketingbot.lock",
        Path(__file__).parent / ".ticketingbot.lock",
    ]
    
    removed = []
    for lock_file in lock_locations:
        if lock_file.exists():
            try:
                lock_file.unlink()
                removed.append(str(lock_file))
                print(f"✓ Removed: {lock_file}")
            except Exception as e:
                print(f"✗ Failed to remove {lock_file}: {e}")
    
    return removed

def check_python_processes():
    """Check for running Python processes"""
    try:
        import psutil
        python_procs = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                        if 'python' in p.name().lower()]
        
        # Filter out this script itself
        current_pid = os.getpid()
        other_procs = [p for p in python_procs if p.pid != current_pid]
        
        return other_procs
    except Exception as e:
        print(f"Warning: Could not check processes: {e}")
        return []

# Main cleanup
print("\n1. Removing stale lock files...")
removed = cleanup_lock_files()
if not removed:
    print("   (No lock files found - clean state)")

print("\n2. Checking for other Python processes...")
other_procs = check_python_processes()
if other_procs:
    print(f"   ⚠️  Found {len(other_procs)} other Python process(es):")
    for p in other_procs:
        print(f"      PID {p.pid}: {p.name()}")
    print("\n   ⚠️  If any of these are bot instances, you may need to kill them:")
    for p in other_procs:
        print(f"      Stop-Process -Id {p.pid} -Force")
else:
    print("   ✓ No other Python processes found")

print("\n3. Bot instance status:")
print("   ✓ Ready to start fresh bot instance")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("1. Run: python main.py")
print("2. If error persists, check the .env file is properly configured")
print("3. Check bot TOKEN is valid in .env")
print("\n" + "=" * 70)
