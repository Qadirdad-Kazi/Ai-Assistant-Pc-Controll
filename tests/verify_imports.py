import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

print("Testing imports in core.voice_assistant...")
try:
    from core.voice_assistant import (
        emotional_analyzer,
        attention_manager,
        intuition_engine,
        energy_manager,
        reasoning_engine,
        curiosity_engine,
        function_executor,
        self_reflection_engine,
        personality_system,
        adaptive_personalizer,
        quantify_and_disclose_uncertainty,
        ensure_llama_loaded,
        mark_llama_used,
        SentenceBuffer,
        metacognition_engine
    )
    print("[OK] All required imports for VoiceAssistant are resolved.")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error during import: {e}")
    sys.exit(1)

print("\nTesting AdvancedTaskExecutor imports...")
try:
    from core.advanced_task_executor import db
    print("[OK] db import in AdvancedTaskExecutor is resolved.")
except ImportError as e:
    print(f"[FAIL] db import failed: {e}")
    sys.exit(1)

print("\nAll core variable accessibility tests PASSED.")
