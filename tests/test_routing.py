import pytest
from config.departments import get_auto_routed_priority

def test_priority_routing():
    # IT keywords
    assert get_auto_routed_priority("IT", "server down") == "URGENT"
    assert get_auto_routed_priority("IT", "forgot password") == "NORMAL"
    assert get_auto_routed_priority("IT", "broken laptop") == "HIGH"
    
    # HR keywords
    assert get_auto_routed_priority("HR", "resigning today") == "URGENT"
    assert get_auto_routed_priority("HR", "vacation request") == "NORMAL"
    
    # Missing department defaults
    assert get_auto_routed_priority("Unknown", "whatever") == "NORMAL"

def test_case_insensitivity():
    # Current implementation might be case sensitive, let's check
    assert get_auto_routed_priority("IT", "SERVER DOWN") == "URGENT"
