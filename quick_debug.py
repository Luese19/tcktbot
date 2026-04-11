#!/usr/bin/env python3
"""Quick test to see bot configuration and handler registration"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

def main():
    from config.settings import settings
    from handlers.mention_handler import GroupMentionHandler

    print("=" * 70)
    print("BOT CONFIGURATION DEBUG")
    print("=" * 70)

    print(f"\n1. Bot Token: {settings.bot.TOKEN[:30]}...")
    print(f"2. Queue Enabled: {settings.app.QUEUE_ENABLED}")
    print(f"3. Log Level: {settings.app.LOG_LEVEL}")

    print("\n" + "=" * 70)
    print("HANDLER REGISTRATION CHECK")
    print("=" * 70)

    handler = GroupMentionHandler.get_mention_handler()
    print(f"\n[OK] Mention handler created successfully")
    print(f"  Handler type: {type(handler)}")
    print(f"  Handler: {handler}")

    # Check the filters
    print(f"\n  Filters: {handler.filters}")

    print("\n" + "=" * 70)
    print("NEXT: Start the bot and send this in a group:")
    print("=" * 70)
    print("\n  @mevithelpdeskbot help kitchen no wifi\n")
    print("Then check the console output and logs/bot.log for debug messages")
    print("Look for messages starting with: [MENTION_HANDLER]\n")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
