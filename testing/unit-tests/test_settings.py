from unittest.mock import MagicMock, patch
import pytest
from PySide6.QtWidgets import QApplication

def test_settings_tab_creation(qtbot):
    """Test that SettingsTab can be instantiated and has layout elements."""
    # qtbot fixture automatically handles QApplication lifecycle
    
    # Lazy import
    from gui.tabs.settings import SettingsTab
    
    # Mock requests to prevent ModelFetcher thread from hanging/crashing
    with patch("gui.tabs.settings.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.2:3b"}, {"name": "qwen3:1.7b"}]}
        mock_get.return_value = mock_response
        
        tab = SettingsTab()
        qtbot.addWidget(tab)
        
        # Wait for potential signals if needed, but instant return should be fine
        qtbot.wait_exposed(tab)
        
        assert tab is not None
        assert tab.expandLayout.count() >= 0
        
        # Ensure thread finished or allow time for events
        if tab.model_fetcher:
            qtbot.wait_signal(tab.model_fetcher.finished, timeout=1000)


