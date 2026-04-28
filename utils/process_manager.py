#!/usr/bin/env python3
"""
Process Manager - Ensures only one bot instance runs at a time
Implements file-based locking and cleanup
"""

import os
import sys
import signal
import atexit
from pathlib import Path
from typing import Optional


class ProcessManager:
    """Manages single-instance bot process"""
    
    LOCK_FILE = Path.home() / ".ticketingbot.lock"
    
    def __init__(self):
        self.lock_acquired = False
        self.pid = os.getpid()
    
    def acquire_lock(self) -> bool:
        """Acquire exclusive lock or return False if another instance is running"""
        try:
            # Check if lock file exists and contains a valid PID
            if self.LOCK_FILE.exists():
                with open(self.LOCK_FILE, 'r') as f:
                    old_pid = f.read().strip()
                
                # Try to check if old process is still running
                if old_pid.isdigit():
                    old_pid_int = int(old_pid)
                    # On Windows, we can't use os.kill to check, so we'll just warn
                    print(f"⚠️  Previous bot instance (PID: {old_pid}) may still be running.")
                    print(f"Please stop it first: kill -9 {old_pid}")
                    print("Or wait a few seconds for it to timeout.\n")
                    return False
            
            # Write current PID to lock file
            self.LOCK_FILE.write_text(str(self.pid))
            self.lock_acquired = True
            
            # Register cleanup on exit
            atexit.register(self.release_lock)
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            return True
        
        except Exception as e:
            print(f"❌ Failed to acquire process lock: {e}")
            return False
    
    def release_lock(self):
        """Release the lock file"""
        try:
            if self.LOCK_FILE.exists():
                self.LOCK_FILE.unlink()
            self.lock_acquired = False
        except Exception as e:
            print(f"Warning: Failed to release lock: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        print("\n\n⚠️  Shutting down bot gracefully...")
        self.release_lock()
        sys.exit(0)


# Global instance
_process_manager: Optional[ProcessManager] = None


def check_single_instance() -> bool:
    """Check and enforce single instance constraint"""
    global _process_manager
    _process_manager = ProcessManager()
    return _process_manager.acquire_lock()


def cleanup_on_exit():
    """Cleanup function called on exit"""
    global _process_manager
    if _process_manager:
        _process_manager.release_lock()
