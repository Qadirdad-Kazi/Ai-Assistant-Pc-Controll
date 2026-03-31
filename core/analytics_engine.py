"""
Analytics Engine - Strategic insights from call data.
Calculates KPIs: Pipeline Value, Top Clients, Success Rates.
"""
import sqlite3
from typing import List, Dict, Any
from core.database import db

class AnalyticsEngine:
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Aggregate high-level business KPIs."""
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Total Pipeline Value
            cursor.execute("SELECT SUM(estimated_deal_size) as total FROM call_logs")
            pipeline_value = cursor.fetchone()['total'] or 0.0
            
            # 2. Total Call Volume
            cursor.execute("SELECT COUNT(*) as count FROM call_logs")
            total_calls = cursor.fetchone()['count'] or 0
            
            # 3. Success Rate (Completed Tasks vs Total Tasks)
            cursor.execute("SELECT COUNT(*) as total_tasks FROM tasks")
            total_tasks = cursor.fetchone()['total_tasks'] or 0
            cursor.execute("SELECT COUNT(*) as completed_tasks FROM tasks WHERE status = 'completed'")
            completed_tasks = cursor.fetchone()['completed_tasks'] or 0
            
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "pipeline_value": round(pipeline_value, 2),
                "total_calls": total_calls,
                "total_tasks": total_tasks,
                "success_rate": round(success_rate, 1)
            }

    def get_top_clients(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identify most engaged clients by call frequency and deal value."""
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT caller_id, COUNT(*) as call_count, SUM(estimated_deal_size) as total_value, AVG(sentiment_score) as avg_sentiment
                FROM call_logs
                GROUP BY caller_id
                ORDER BY call_count DESC, total_value DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_deal_heatmap(self) -> List[Dict[str, Any]]:
        """Group deals by mood/sentiment for strategic visualization."""
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT client_mood as mood, COUNT(*) as count, SUM(estimated_deal_size) as value
                FROM call_logs
                GROUP BY client_mood
                ORDER BY value DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

# Global instance
analytics_engine = AnalyticsEngine()
