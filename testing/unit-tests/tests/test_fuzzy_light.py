
import sys
from unittest.mock import MagicMock, patch
import pytest

# Use a fixture to safely mock modules only for this test module
@pytest.fixture(autouse=True)
def mock_core_modules():
    """Mock core modules before importing function_executor to avoid side effects."""
    with patch.dict(sys.modules, {
        "core.router": MagicMock(),
        "core.tts": MagicMock(),
        "core.llm": MagicMock(),
        "core.tasks": MagicMock(),
        "core.calendar_manager": MagicMock(),
        "core.weather": MagicMock(),
        "core.news": MagicMock(),
        "core.kasa_control": MagicMock(),
        "duckduckgo_search": MagicMock(),
    }):
        yield

# Helper to load executor AFTER mocking
@pytest.fixture
def executor():
    # We must reload or import inside the test/fixture after mocks are in place
    if "core.function_executor" in sys.modules:
        del sys.modules["core.function_executor"]
    from core.function_executor import executor
    return executor

@pytest.mark.asyncio
async def test_fuzzy_light_matching_off(executor):
    """Test fuzzy matching for turning off lights."""
    print("Testing Fuzzy Matching Logic...")
    
    # Setup Mock Kasa Manager
    mock_kasa = MagicMock()
    mock_kasa.devices = {
        "192.168.1.10": {"alias": "Left Office Light", "is_on": True},
        "192.168.1.11": {"alias": "Right Office Light", "is_on": True},
        "192.168.1.12": {"alias": "Kitchen Light", "is_on": True}
    }
    
    # Async mock methods
    async def mock_success(*args, **kwargs):
        return True
    
    mock_kasa.turn_off.side_effect = mock_success
    executor.kasa_manager = mock_kasa
    
    # Execute
    print("\nCommand: 'turn off office'")
    # _control_light calls asyncio.run internaly, but usually we mock that too or call _async_control_light
    # Since executor._control_light does asyncio.run(), we can call it synchronously in a non-async test,
    # OR better: test the underlying async method directly to avoid nesting event loops if pytest-asyncio is used.
    
    # However, since the production code uses asyncio.run(), calling it here might conflict if a loop is already running.
    # The executor code: return asyncio.run(self._async_control_light(params))
    # It is safer to call _async_control_light directly in an async test.
    
    result = await executor._async_control_light({"action": "off", "device_name": "office"})
    
    print("\nResult (OFF):", result)
    
    assert result.get('success') is True
    
    msg = result.get('message', '')
    assert "Turned off Left Office Light" in msg
    assert "Turned off Right Office Light" in msg

@pytest.mark.asyncio
async def test_fuzzy_light_matching_color(executor):
    """Test fuzzy matching for changing color."""
    
    # Setup Mock matches fixture setup
    mock_kasa = MagicMock()
    mock_kasa.devices = {
        "192.168.1.10": {"alias": "Left Office Light", "is_on": True},
        "192.168.1.11": {"alias": "Right Office Light", "is_on": True},
        "192.168.1.12": {"alias": "Kitchen Light", "is_on": True}
    }
    
    async def mock_success(*args, **kwargs):
        return True
        
    mock_kasa.set_hsv.side_effect = mock_success
    mock_kasa.turn_on.side_effect = mock_success
    executor.kasa_manager = mock_kasa

    print("\nCommand: 'turn office blue'")
    # Executor expects action="on" when color is provided, not action="color"
    result_color = await executor._async_control_light({"action": "on", "device_name": "office", "color": "blue"})
    print("\nResult (COLOR):", result_color)
    
    assert result_color.get('success') is True
    
    msg_color = result_color.get('message', '')
    assert "Set color to blue for Left Office Light" in msg_color
    assert "Set color to blue for Right Office Light" in msg_color

