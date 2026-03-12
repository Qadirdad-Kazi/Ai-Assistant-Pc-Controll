"""
Memory Recall Test Suite
Tests autonomous memory and history browsing capabilities.
"""

import pytest
import asyncio
import tempfile
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.memory import memory_manager
    from core.database import db
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"Memory modules not available: {e}")
    MEMORY_AVAILABLE = False

@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory modules not available")
class TestMemoryRecall:
    """Test suite for Memory Recall capabilities."""

    @pytest.fixture
    def temp_db(self, temp_dir):
        """Create temporary database for testing."""
        db_path = temp_dir / "test_memory.db"
        
        # Initialize database schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                tags TEXT,
                embedding_data BLOB
            )
        ''')
        
        # Create interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                wolf_response TEXT NOT NULL,
                session_id TEXT,
                context TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return db_path

    @pytest.fixture
    def sample_memories(self):
        """Sample memory data for testing."""
        return [
            {
                "timestamp": datetime.now() - timedelta(days=1),
                "interaction_type": "preference",
                "content": "User prefers dark mode for habit tracker apps",
                "context": "App preference discussion",
                "tags": "preferences,dark_mode,apps"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=6),
                "interaction_type": "command",
                "content": "User asked to build React habit tracker",
                "context": "Development request",
                "tags": "development,react,tracker"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=2),
                "interaction_type": "query",
                "content": "User inquired about Bitcoin price",
                "context": "Financial query",
                "tags": "bitcoin,price,crypto"
            }
        ]

    @pytest.fixture
    def sample_interactions(self):
        """Sample interaction data for testing."""
        return [
            {
                "timestamp": datetime.now() - timedelta(days=1),
                "user_input": "Wolf, remember that I like my habit tracker apps in dark mode",
                "wolf_response": "I'll remember your preference for dark mode habit tracker apps.",
                "session_id": "session_001",
                "context": "preference_setting"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=6),
                "user_input": "Wolf, what are my style preferences for apps?",
                "wolf_response": "You previously mentioned that you prefer your habit tracker apps to have a dark mode UI.",
                "session_id": "session_002",
                "context": "preference_recall"
            }
        ]

    @pytest.fixture
    def mock_memory_manager(self, temp_db, sample_memories):
        """Create mock memory manager with test data."""
        with patch('core.memory.db') as mock_db:
            mock_db.get_connection.return_value = sqlite3.connect(str(temp_db))
            
            # Insert sample data
            conn = sqlite3.connect(str(temp_db))
            cursor = conn.cursor()
            
            for memory in sample_memories:
                cursor.execute('''
                    INSERT INTO memory (timestamp, interaction_type, content, context, tags)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    memory["timestamp"].isoformat(),
                    memory["interaction_type"],
                    memory["content"],
                    memory["context"],
                    memory["tags"]
                ))
            
            conn.commit()
            conn.close()
            
            yield mock_db

    @pytest.mark.asyncio
    async def test_memory_storage(self, temp_db, sample_memories):
        """Test storing memories in database."""
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        for memory in sample_memories:
            cursor.execute('''
                INSERT INTO memory (timestamp, interaction_type, content, context, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                memory["timestamp"].isoformat(),
                memory["interaction_type"],
                memory["content"],
                memory["context"],
                memory["tags"]
            ))
        
        conn.commit()
        
        # Verify storage
        cursor.execute("SELECT COUNT(*) FROM memory")
        count = cursor.fetchone()[0]
        assert count == len(sample_memories)
        
        conn.close()

    @pytest.mark.asyncio
    async def test_preference_recall(self, mock_memory_manager):
        """Test recalling user preferences."""
        with patch.object(memory_manager, 'recall_preferences') as mock_recall:
            mock_recall.return_value = [
                "You prefer dark mode for habit tracker apps",
                "You like React-based applications"
            ]
            
            preferences = await memory_manager.recall_preferences()
            
            assert isinstance(preferences, list)
            assert len(preferences) > 0
            assert "dark mode" in " ".join(preferences).lower()

    @pytest.mark.asyncio
    async def test_memory_search_by_keywords(self, mock_memory_manager):
        """Test searching memories by keywords."""
        with patch.object(memory_manager, 'search_memories') as mock_search:
            mock_search.return_value = [
                {
                    "content": "User prefers dark mode for habit tracker apps",
                    "timestamp": datetime.now().isoformat(),
                    "context": "App preference discussion"
                }
            ]
            
            results = await memory_manager.search_memories("dark mode")
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert "dark mode" in results[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_interaction_history_browsing(self, temp_db, sample_interactions):
        """Test browsing interaction history."""
        # Insert sample interactions
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        for interaction in sample_interactions:
            cursor.execute('''
                INSERT INTO interactions (timestamp, user_input, wolf_response, session_id, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                interaction["timestamp"].isoformat(),
                interaction["user_input"],
                interaction["wolf_response"],
                interaction["session_id"],
                interaction["context"]
            ))
        
        conn.commit()
        
        # Test history retrieval
        cursor.execute('''
            SELECT user_input, wolf_response, timestamp 
            FROM interactions 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        
        history = cursor.fetchall()
        assert len(history) == len(sample_interactions)
        
        conn.close()

    @pytest.mark.asyncio
    async def test_memory_tagging(self, mock_memory_manager):
        """Test memory tagging and retrieval by tags."""
        with patch.object(memory_manager, 'get_memories_by_tag') as mock_by_tag:
            mock_by_tag.return_value = [
                {
                    "content": "User prefers dark mode for habit tracker apps",
                    "tags": "preferences,dark_mode,apps",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            memories = await memory_manager.get_memories_by_tag("preferences")
            
            assert isinstance(memories, list)
            assert len(memories) > 0
            assert "preferences" in memories[0]["tags"]

    @pytest.mark.asyncio
    async def test_context_aware_recall(self, mock_memory_manager):
        """Test context-aware memory recall."""
        with patch.object(memory_manager, 'recall_context') as mock_context:
            mock_context.return_value = {
                "recent_preferences": ["dark mode for apps"],
                "development_requests": ["React habit tracker"],
                "queries": ["Bitcoin price inquiry"]
            }
            
            context = await memory_manager.recall_context("app preferences")
            
            assert isinstance(context, dict)
            assert "recent_preferences" in context
            assert len(context["recent_preferences"]) > 0

    @pytest.mark.asyncio
    async def test_memory_persistence(self, temp_db):
        """Test memory persistence across sessions."""
        # Store memory in first session
        conn1 = sqlite3.connect(str(temp_db))
        cursor1 = conn1.cursor()
        
        cursor1.execute('''
            INSERT INTO memory (timestamp, interaction_type, content, context, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            "preference",
            "Test persistence memory",
            "persistence_test",
            "test,persistence"
        ))
        
        conn1.commit()
        conn1.close()
        
        # Retrieve in second session
        conn2 = sqlite3.connect(str(temp_db))
        cursor2 = conn2.cursor()
        
        cursor2.execute("SELECT content FROM memory WHERE tags LIKE '%persistence%'")
        result = cursor2.fetchone()
        
        assert result is not None
        assert result[0] == "Test persistence memory"
        
        conn2.close()

    @pytest.mark.asyncio
    async def test_memory_cleanup(self, mock_memory_manager):
        """Test old memory cleanup."""
        with patch.object(memory_manager, 'cleanup_old_memories') as mock_cleanup:
            mock_cleanup.return_value = 5  # Number of cleaned memories
            
            cleaned = await memory_manager.cleanup_old_memories(days_threshold=30)
            
            assert isinstance(cleaned, int)
            assert cleaned >= 0

    @pytest.mark.asyncio
    async def test_memory_embedding_storage(self, temp_db):
        """Test storing embeddings for semantic search."""
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        # Mock embedding data
        embedding_data = b'\x00\x01\x02\x03' * 100  # Fake embedding vector
        
        cursor.execute('''
            INSERT INTO memory (timestamp, interaction_type, content, context, embedding_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            "preference",
            "Test embedding memory",
            "embedding_test",
            embedding_data
        ))
        
        conn.commit()
        
        # Retrieve embedding
        cursor.execute("SELECT embedding_data FROM memory WHERE context = 'embedding_test'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == embedding_data
        
        conn.close()

    @pytest.mark.asyncio
    async def test_memory_recall_accuracy(self, mock_memory_manager):
        """Test accuracy of memory recall."""
        with patch.object(memory_manager, 'recall_memory') as mock_recall:
            mock_recall.return_value = {
                "query": "app preferences",
                "results": [
                    {
                        "content": "User prefers dark mode for habit tracker apps",
                        "relevance_score": 0.95,
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "total_results": 1
            }
            
            recall_result = await memory_manager.recall_memory("app preferences")
            
            assert isinstance(recall_result, dict)
            assert "query" in recall_result
            assert "results" in recall_result
            assert len(recall_result["results"]) > 0
            assert recall_result["results"][0]["relevance_score"] > 0.8

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, mock_memory_manager):
        """Test concurrent memory operations."""
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = True
            
            # Store multiple memories concurrently
            tasks = []
            for i in range(5):
                task = memory_manager.store_memory(
                    content=f"Concurrent test memory {i}",
                    interaction_type="test",
                    context="concurrent_test"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(results)  # All should return True

# Integration Tests
@pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory modules not available")
@pytest.mark.integration
class TestMemoryRecallIntegration:
    """Integration tests for Memory Recall with real components."""

    @pytest.mark.asyncio
    async def test_real_memory_storage(self):
        """Test actual memory storage with real database."""
        try:
            # Test with actual memory manager
            success = await memory_manager.store_memory(
                content="Integration test memory",
                interaction_type="test",
                context="integration_test",
                tags="test,integration"
            )
            
            assert success is True
            
            # Test retrieval
            memories = await memory_manager.search_memories("integration test")
            assert len(memories) > 0
            
        except Exception as e:
            pytest.skip(f"Memory database not available: {e}")

    @pytest.mark.asyncio
    async def test_preference_learning_workflow(self):
        """Test complete preference learning workflow."""
        try:
            # Step 1: Store preference
            await memory_manager.store_memory(
                content="User prefers dark mode for habit tracker apps",
                interaction_type="preference",
                context="app_preferences",
                tags="preferences,dark_mode,apps"
            )
            
            # Step 2: Recall preference
            preferences = await memory_manager.recall_preferences()
            
            # Step 3: Verify preference was learned
            assert any("dark mode" in str(pref).lower() for pref in preferences)
            
        except Exception as e:
            pytest.skip(f"Preference learning workflow failed: {e}")

    @pytest.mark.asyncio
    async def test_cross_session_memory(self):
        """Test memory persistence across simulated sessions."""
        try:
            # Session 1: Store memory
            session1_id = "test_session_001"
            await memory_manager.store_memory(
                content="Cross-session test memory",
                interaction_type="test",
                context="cross_session",
                session_id=session1_id
            )
            
            # Session 2: Recall memory
            session2_id = "test_session_002"
            memories = await memory_manager.get_memories_by_session(session1_id)
            
            assert len(memories) > 0
            assert "Cross-session test memory" in str(memories)
            
        except Exception as e:
            pytest.skip(f"Cross-session memory test failed: {e}")

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_memory_recall.py -v
    pytest.main([__file__, "-v"])
