
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

# MOCK EVERYTHING that might cause import errors or side effects
sys.modules["transformers"] = MagicMock()
sys.modules["core.router"] = MagicMock()
sys.modules["core.tasks"] = MagicMock()
sys.modules["core.calendar_manager"] = MagicMock()
sys.modules["core.weather"] = MagicMock()
sys.modules["core.news"] = MagicMock()
sys.modules["core.kasa_control"] = MagicMock()

# Mock internal imports in function_executor if needed
# But we want to test the class logic.

from core.function_executor import FunctionExecutor

async def mock_discover():
    print("Mock discovery called")
    devices = {"192.168.1.100": {"alias": "Office Light", "ip": "192.168.1.100"}}
    # Side effect: update the manager's devices
    executor.kasa_manager.devices = devices
    return devices

async def mock_turn_on(ip):
    print(f"Mock turn_on called for {ip}")
    return True

async def mock_turn_off(ip):
    print(f"Mock turn_off called for {ip}")
    return True

async def mock_set_hsv(ip, h, s, v):
    print(f"Mock set_hsv called for {ip}: {h},{s},{v}")
    return True

def test_light_control_loop():
    print("Testing light control loop management...")
    
    executor = FunctionExecutor()
    
    # Mock KasaManager instance
    executor.kasa_manager = MagicMock()
    executor.kasa_manager.devices = {} # Start empty
    executor.kasa_manager.discover_devices = mock_discover
    executor.kasa_manager.turn_on = mock_turn_on
    executor.kasa_manager.turn_off = mock_turn_off
    executor.kasa_manager.set_hsv = mock_set_hsv
    executor.kasa_manager._get_light_module = MagicMock(return_value=(MagicMock(is_on=True), None))
    
    print("\n--- Call 1: Turn On (Trigger Discovery) ---")
    res1 = executor.execute("control_light", {"action": "on", "device_name": "office"})
    print(f"Result 1: {res1}")
    
    # Populate cache to simulate successful discovery
    executor.kasa_manager.devices = {"192.168.1.100": {"alias": "Office Light", "ip": "192.168.1.100"}}
    
    print("\n--- Call 2: Turn Off (Use Cache) ---")
    res2 = executor.execute("control_light", {"action": "off", "device_name": "office"})
    print(f"Result 2: {res2}")
    
    print("\n--- Call 3: Set Color (Multiple Async Calls) ---")
    res3 = executor.execute("control_light", {"action": "on", "color": "blue", "device_name": "office"})
    print(f"Result 3: {res3}")
    
    if res1['success'] and res2['success'] and res3['success']:
        print("\nSUCCESS: Multiple calls executed without event loop error.")
    else:
        print("\nFAILURE: One or more calls failed.")

if __name__ == "__main__":
    test_light_control_loop()
