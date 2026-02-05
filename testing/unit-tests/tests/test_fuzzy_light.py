
import sys
from unittest.mock import MagicMock

# MOCK EVERYTHING from core to prevent __init__.py from loading unwanted modules
sys.modules["core.router"] = MagicMock()
sys.modules["core.tts"] = MagicMock()
sys.modules["core.llm"] = MagicMock()
sys.modules["core.tasks"] = MagicMock()
sys.modules["core.calendar_manager"] = MagicMock()
sys.modules["core.weather"] = MagicMock()
sys.modules["core.news"] = MagicMock()
sys.modules["core.kasa_control"] = MagicMock()

# Also mock duckduckgo_search just in case
sys.modules["duckduckgo_search"] = MagicMock()

# Now import
from core.function_executor import executor

def run_sync_test():
    print("Testing Fuzzy Matching Logic...")
    
    # Setup Mock Kasa Manager
    mock_kasa = MagicMock()
    mock_kasa.devices = {
        "192.168.1.10": {"alias": "Left Office Light", "is_on": True},
        "192.168.1.11": {"alias": "Right Office Light", "is_on": True},
        "192.168.1.12": {"alias": "Kitchen Light", "is_on": True}
    }
    
    # Need to return an awaitable for run_until_complete
    async def mock_turn_off_action(ip):
        return True
    
    mock_kasa.turn_off.side_effect = mock_turn_off_action
    
    executor.kasa_manager = mock_kasa
    
    print("\nCommand: 'turn off office'")
    result = executor._control_light({"action": "off", "device_name": "office"})
    
    print("\nResult (OFF):", result)
    
    expected_msg_parts = ["Turned off Left Office Light", "Turned off Right Office Light"]
    success = True
    
    if not result.get('success'):
        print("FAIL: OFF Operation not successful")
        success = False
        
    msg = result.get('message', '')
    for part in expected_msg_parts:
        if part not in msg:
            print(f"FAIL: Message missing '{part}'")
            success = False

    # Test Color
    async def mock_set_hsv_action(ip, h, s, v):
        return True
    mock_kasa.set_hsv.side_effect = mock_set_hsv_action

    print("\nCommand: 'turn office blue'")
    result_color = executor._control_light({"action": "color", "device_name": "office", "color": "blue"})
    print("\nResult (COLOR):", result_color)
    
    expected_color_parts = ["Set color to blue for Left Office Light", "Set color to blue for Right Office Light"]
    
    if not result_color.get('success'):
        print("FAIL: COLOR Operation not successful")
        success = False
    
    msg_color = result_color.get('message', '')
    for part in expected_color_parts:
        if part not in msg_color:
            print(f"FAIL: Message missing '{part}'")
            success = False

    if success:
        print("\nPASS: Fuzzy matching and Color control worked correctly!")

if __name__ == "__main__":
    run_sync_test()
