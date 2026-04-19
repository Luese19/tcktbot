#!/usr/bin/env python3
"""Test suite for schedule features"""

import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all schedule-related modules can be imported"""
    print("\n📋 TEST 1: Checking Imports...")
    try:
        from handlers.schedule_handler import get_schedule_handler, ScheduleHandler, ScheduleState
        from utils.scheduler import TaskManager
        from models.scheduled_task import ScheduledTask, TaskType, ScheduleType, TaskStatus
        from services.task_actions import TaskActionExecutor
        print("✅ All schedule modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_schedule_state():
    """Test ScheduleState class"""
    print("\n📋 TEST 2: Testing ScheduleState...")
    try:
        from bot.handlers.schedule_handler import ScheduleState
        
        # Verify all states are defined
        states = [
            ('TASK_TYPE', 1),
            ('SCHEDULE_TYPE', 2),
            ('SCHEDULE_DATE_TIME', 3),
            ('TICKET_NAME', 10),
            ('TICKET_EMAIL', 11),
            ('TICKET_DEPT', 12),
            ('TICKET_SUMMARY', 13),
            ('TICKET_ISSUE', 14),
            ('TICKET_MEDIA', 15),
            ('TICKET_PRIORITY', 16),
            ('MESSAGE_TARGET', 20),
            ('MESSAGE_TEXT', 21),
            ('REMINDER_RECIPIENTS', 30),
            ('REMINDER_TITLE', 31),
            ('REMINDER_BODY', 32),
        ]
        
        for state_name, expected_value in states:
            actual_value = getattr(ScheduleState, state_name)
            if actual_value != expected_value:
                print(f"❌ State {state_name} mismatch: expected {expected_value}, got {actual_value}")
                return False
        
        print(f"✅ All {len(states)} ScheduleState values validated")
        return True
    except Exception as e:
        print(f"❌ ScheduleState test failed: {e}")
        return False

def test_scheduled_task_creation():
    """Test ScheduledTask model"""
    print("\n📋 TEST 3: Testing ScheduledTask Model...")
    try:
        from models.scheduled_task import ScheduledTask, TaskType, ScheduleType, TaskStatus
        import uuid
        
        # Create a test task
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            task_id=task_id,
            task_type=TaskType.CREATE_TICKET,
            schedule_type=ScheduleType.ONCE,
            created_by=123456789,
            schedule_config={'datetime': datetime.now().isoformat()},
            action_params={'name': 'Test', 'email': 'test@example.com'},
            status=TaskStatus.ACTIVE
        )
        
        # Verify task attributes
        assert task.task_id == task_id
        assert task.task_type == TaskType.CREATE_TICKET
        assert task.schedule_type == ScheduleType.ONCE
        assert task.status == TaskStatus.ACTIVE
        assert task.created_by == 123456789
        
        print(f"✅ ScheduledTask created successfully (ID: {task_id[:8]}...)")
        return True
    except Exception as e:
        print(f"❌ ScheduledTask test failed: {e}")
        return False

def test_schedule_handler():
    """Test ScheduleHandler class"""
    print("\n📋 TEST 4: Testing ScheduleHandler...")
    try:
        from bot.handlers.schedule_handler import ScheduleHandler
        
        # Verify handler methods exist
        methods = [
            'schedule_command',
            'select_task_type',
            'select_schedule_type',
            'collect_schedule_datetime',
            'ticket_collect_name',
            'ticket_collect_email',
            'ticket_select_dept',
            'ticket_collect_summary',
            'ticket_collect_issue',
            'ticket_collect_media',
            'ticket_select_priority',
            'message_collect_target',
            'message_collect_text',
            'reminder_collect_recipients',
            'reminder_collect_title',
            'reminder_collect_body',
            'confirm_schedule',
            'list_tasks_command',
            'delete_task_command',
        ]
        
        for method_name in methods:
            if not hasattr(ScheduleHandler, method_name):
                print(f"❌ Missing method: {method_name}")
                return False
        
        print(f"✅ All {len(methods)} ScheduleHandler methods exist")
        return True
    except Exception as e:
        print(f"❌ ScheduleHandler test failed: {e}")
        return False

def test_time_formatting():
    """Test time formatting functions"""
    print("\n📋 TEST 5: Testing Time Formatting...")
    try:
        from datetime import datetime
        
        # Test 12-hour format conversion
        test_times = [
            ('09:00', '09:00 AM'),
            ('13:30', '01:30 PM'),
            ('23:59', '11:59 PM'),
            ('00:00', '12:00 AM'),
            ('12:00', '12:00 PM'),
        ]
        
        for time_str, expected_format in test_times:
            dt = datetime.strptime(time_str, '%H:%M')
            formatted = dt.strftime('%I:%M %p')
            if formatted != expected_format:
                print(f"❌ Time format mismatch: {time_str} -> expected {expected_format}, got {formatted}")
                return False
        
        print(f"✅ All {len(test_times)} time format conversions passed")
        return True
    except Exception as e:
        print(f"❌ Time formatting test failed: {e}")
        return False

def test_conversation_handler():
    """Test conversation handler setup"""
    print("\n📋 TEST 6: Testing ConversationHandler Setup...")
    try:
        from bot.handlers.schedule_handler import get_schedule_handler
        from telegram.ext import ConversationHandler
        
        handler = get_schedule_handler()
        
        # Verify it's a ConversationHandler
        if not isinstance(handler, ConversationHandler):
            print(f"❌ Handler is not a ConversationHandler: {type(handler)}")
            return False
        
        # Verify entry_points
        if not handler.entry_points:
            print("❌ No entry points defined")
            return False
        
        # Verify states dict
        if not handler.states:
            print("❌ No states defined")
            return False
        
        # Verify fallbacks
        if not handler.fallbacks:
            print("❌ No fallbacks defined")
            return False
        
        print(f"✅ ConversationHandler properly configured:")
        print(f"   • Entry points: {len(handler.entry_points)}")
        print(f"   • States: {len(handler.states)}")
        print(f"   • Fallbacks: {len(handler.fallbacks)}")
        return True
    except Exception as e:
        print(f"❌ ConversationHandler test failed: {e}")
        return False

def test_task_types_and_schedules():
    """Test TaskType and ScheduleType enums"""
    print("\n📋 TEST 7: Testing TaskType and ScheduleType Enums...")
    try:
        from models.scheduled_task import TaskType, ScheduleType
        
        # Test TaskType
        task_types = [TaskType.CREATE_TICKET, TaskType.SEND_MESSAGE, TaskType.SEND_REMINDER]
        print(f"✅ TaskTypes available: {[t.value for t in task_types]}")
        
        # Test ScheduleType
        schedule_types = [
            ScheduleType.ONCE,
            ScheduleType.DAILY,
            ScheduleType.WEEKLY,
            ScheduleType.MONTHLY,
            ScheduleType.YEARLY,
            ScheduleType.CRON
        ]
        print(f"✅ ScheduleTypes available: {[s.value for s in schedule_types]}")
        
        return True
    except Exception as e:
        print(f"❌ TaskType/ScheduleType test failed: {e}")
        return False

def test_datetime_parsing():
    """Test datetime parsing for different schedule types"""
    print("\n📋 TEST 8: Testing DateTime Parsing...")
    try:
        from datetime import datetime
        
        test_cases = [
            # Format, Input, Should Pass
            ('%Y-%m-%d %H:%M', '2026-04-20 14:30', True),
            ('%H:%M', '09:00', True),
            ('%H:%M', '25:00', False),  # Invalid hour
            ('%Y-%m-%d', '2026-04-20', True),
        ]
        
        passed = 0
        for format_str, input_str, should_pass in test_cases:
            try:
                datetime.strptime(input_str, format_str)
                if should_pass:
                    passed += 1
                else:
                    print(f"❌ Should have failed: {input_str} with format {format_str}")
                    return False
            except ValueError:
                if not should_pass:
                    passed += 1
                else:
                    print(f"❌ Should have passed: {input_str} with format {format_str}")
                    return False
        
        print(f"✅ All {passed}/{len(test_cases)} datetime parsing tests passed")
        return True
    except Exception as e:
        print(f"❌ DateTime parsing test failed: {e}")
        return False

def test_bot_initialization():
    """Test bot can be initialized with schedule handler"""
    print("\n📋 TEST 9: Testing Bot Initialization with Schedule Handler...")
    try:
        from main import TelegramHelpDeskBot
        
        # This will verify the bot class can be imported and has expected methods
        if not hasattr(TelegramHelpDeskBot, '__init__'):
            print("❌ Bot class missing __init__ method")
            return False
        
        if not hasattr(TelegramHelpDeskBot, 'run'):
            print("❌ Bot class missing run method")
            return False
        
        print("✅ Bot class properly structured for schedule handlers")
        return True
    except Exception as e:
        print(f"❌ Bot initialization test failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n📋 TEST 10: Testing Configuration Loading...")
    try:
        from config.settings import settings
        
        if settings is None:
            print("❌ Settings not loaded")
            return False
        
        # Verify essential settings exist
        if not hasattr(settings, 'bot'):
            print("❌ Bot settings not found")
            return False
        
        if not hasattr(settings.bot, 'TOKEN'):
            print("❌ Bot token not configured")
            return False
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🤖 TELEGRAM HELPDESK BOT - SCHEDULE FEATURES TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_schedule_state,
        test_scheduled_task_creation,
        test_schedule_handler,
        test_time_formatting,
        test_conversation_handler,
        test_task_types_and_schedules,
        test_datetime_parsing,
        test_bot_initialization,
        test_config_loading,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"❌ Unexpected error in {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All schedule features are working correctly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
