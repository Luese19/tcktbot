#!/usr/bin/env python3
"""
Quick diagnostic to check lock file state and running processes
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("TICKETING BOT - LOCK FILE DIAGNOSTICS")
print("=" * 60)

# Check lock file
lock_file = Path.home() / ".ticketingbot.lock"
print(f"\n1. Lock File Check:")
print(f"   Path: {lock_file}")
print(f"   Exists: {lock_file.exists()}")

if lock_file.exists():
    try:
        with open(lock_file, 'r') as f:
            pid_content = f.read().strip()
        print(f"   Content (PID): {pid_content}")
        
        # Try to validate the PID
        try:
            import psutil
            pid_int = int(pid_content)
            if psutil.pid_exists(pid_int):
                proc = psutil.Process(pid_int)
                print(f"   Process Name: {proc.name()}")
                print(f"   Process Cmdline: {proc.cmdline()}")
            else:
                print(f"   ⚠️  PID {pid_content} does NOT exist (stale lock)")
        except Exception as e:
            print(f"   Error checking process: {e}")
    except Exception as e:
        print(f"   Error reading lock file: {e}")
else:
    print(f"   ✓ Lock file does not exist (good)")

# Check for running Python processes with 'python'
print(f"\n2. Running Python Processes:")
try:
    import psutil
    python_procs = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                    if 'python' in p.name().lower()]
    
    if python_procs:
        for p in python_procs:
            print(f"   PID {p.pid}: {p.name()} - {' '.join(p.cmdline()[:3])}")
    else:
        print(f"   No Python processes found")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Recommendation:")
if lock_file.exists():
    print(f"   ⚠️  STALE LOCK DETECTED")
    print(f"   Solution: Delete the lock file with:")
    print(f"   python -c \"from pathlib import Path; Path.home().joinpath('.ticketingbot.lock').unlink()\"")
    print(f"   Or: Remove-Item $env:USERPROFILE\\.ticketingbot.lock (PowerShell)")
else:
    print(f"   ✓ No lock file issues detected")
    print(f"   If still getting errors, the issue might be elsewhere")

print("\n" + "=" * 60)
