import sys
import os
import asyncio
from unittest.mock import MagicMock, patch
import pytest

# Add project root to path
sys.path.append(os.getcwd())

@pytest.fixture
def mock_modules():
    with patch.dict(sys.modules, {
        "transformers": MagicMock(),
        "core.router": MagicMock(),
        "core.tasks": MagicMock(),
        "core.calendar_manager": MagicMock(),
        "core.weather": MagicMock(),
        "core.news": MagicMock(),
        "core.kasa_control": MagicMock(),
    }):
        yield

@pytest.mark.asyncio
async def test_light_control_loop(mock_modules):
    """Test the light control loop management without side effects."""
    print("Testing light control loop management...")
    
    # Import inside test to ensure mocks are applied
    # We might need to unimport if it was already imported, but for now this is usually fine in fresh process
    if "core.function_executor" in sys.modules:
        del sys.modules["core.function_executor"]
    from core.function_executor import FunctionExecutor
    
    executor = FunctionExecutor()
    
    # Mock KasaManager logic
    async def mock_discover():
        print("Mock discovery called")
        devices = {"192.168.1.100": {"alias": "Office Light", "ip": "192.168.1.100"}}
        executor.kasa_manager.devices = devices
        return devices

    async def mock_turn_on(ip):
        return True

    async def mock_turn_off(ip):
        return True

    async def mock_set_hsv(ip, h, s, v):
        return True

    # Setup the mock manager
    executor.kasa_manager = MagicMock()
    executor.kasa_manager.devices = {} # Start empty
    executor.kasa_manager.discover_devices = mock_discover
    executor.kasa_manager.turn_on = mock_turn_on
    executor.kasa_manager.turn_off = mock_turn_off
    executor.kasa_manager.set_hsv = mock_set_hsv
    # Mock _get_light_module to return a fake device that reports 'is_on=True'
    executor.kasa_manager._get_light_module = MagicMock(return_value=(MagicMock(is_on=True), None))
    
    print("\n--- Call 1: Turn On (Trigger Discovery) ---")
    # control_light in executor runs asyncio.run() internally.
    # calling it from an async test is problematic if it uses asyncio.run().
    # We should call the internal _async_control_light if possible, or we need to patch asyncio.run
    # But since we are mocking the manager methods which are async, we can just call _async_control_light
    
    res1 = await executor._async_control_light({"action": "on", "device_name": "office"})
    print(f"Result 1: {res1}")
    
    assert res1['success'] is True
    
    # Populate cache to simulate successful discovery for next calls
    executor.kasa_manager.devices = {"192.168.1.100": {"alias": "Office Light", "ip": "192.168.1.100"}}
    
    print("\n--- Call 2: Turn Off (Use Cache) ---")
    res2 = await executor._async_control_light({"action": "off", "device_name": "office"})
    print(f"Result 2: {res2}")
    
    assert res2['success'] is True
    
    print("\n--- Call 3: Set Color (Multiple Async Calls) ---")
    res3 = await executor._async_control_light({"action": "on", "color": "blue", "device_name": "office"})
    print(f"Result 3: {res3}")
    
    assert res3['success'] is True

