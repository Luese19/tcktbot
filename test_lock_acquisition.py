#!/usr/bin/env python3
"""
Test the lock acquisition process to reproduce the error
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("LOCK ACQUISITION TEST")
print("=" * 70)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

print(f"\nCurrent PID: {os.getpid()}")

# First, create a simulated stale lock with PID 1
lock_file = Path.home() / ".ticketingbot.lock"
print(f"Lock file path: {lock_file}")

# Test 1: Create a lock with PID 1 to simulate the error
print("\n--- TEST 1: Simulating stale lock with PID 1 ---")
lock_file.write_text("1")
print(f"Created lock file with content: 1")
print(f"Lock file exists: {lock_file.exists()}")

# Now try to acquire the lock
print("\n--- TEST 2: Attempting to acquire lock ---")
from utils.process_manager import ProcessManager

pm = ProcessManager()
result = pm.acquire_lock()
print(f"Acquire lock result: {result}")

# Check if lock was acquired
print(f"\nFinal lock file content:")
if lock_file.exists():
    with open(lock_file, 'r') as f:
        print(f"  {f.read().strip()}")
else:
    print(f"  (file doesn't exist)")

print("\n" + "=" * 70)
