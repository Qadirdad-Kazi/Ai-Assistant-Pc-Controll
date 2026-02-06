from core.knowledge_base import KnowledgeBase
import sys

print("Testing KnowledgeBase initialization...")
try:
    kb = KnowledgeBase()
    if kb._db is not None:
        print("SUCCESS: Database initialized.")
    else:
        print("FAILURE: Database is None.")
except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
