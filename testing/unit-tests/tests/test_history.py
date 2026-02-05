import sys
import os
import pytest
import shutil

# Correctly setup python path to include project root
sys.path.append(os.getcwd())

from core.history import ChatHistoryManager

TEST_DB = "test_history.db"

@pytest.fixture
def history_manager():
    """Fixture to provide a fresh ChatHistoryManager for each test."""
    # Setup
    mgr = ChatHistoryManager(db_path=TEST_DB)
    yield mgr
    # Teardown
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

def test_create_session(history_manager):
    sid = history_manager.create_session("Test Session")
    assert sid is not None
    
    sessions = history_manager.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]['title'] == "Test Session"

def test_add_message(history_manager):
    sid = history_manager.create_session("Chat 1")
    history_manager.add_message(sid, "user", "Hello")
    history_manager.add_message(sid, "assistant", "Hi there")
    
    msgs = history_manager.get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]['content'] == "Hello"
    assert msgs[1]['content'] == "Hi there"

def test_session_ordering(history_manager):
    sid1 = history_manager.create_session("Old")
    sid2 = history_manager.create_session("New")
    
    # New should be first (most recent)
    sessions = history_manager.get_sessions()
    assert sessions[0]['title'] == "New"
    
    # Update Old with new message - should bump it to top
    history_manager.add_message(sid1, "user", "bump")
    sessions = history_manager.get_sessions()
    assert sessions[0]['title'] == "Old"

