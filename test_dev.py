import time
from core.function_executor import executor
from core.dev_agent import dev_agent

# Simulation 1: Vague Prompt
print("🔹 Test 1: Vague Prompt")
res = executor.execute("scaffold_website", {"prompt": "Build a web"})
print(f"DevAgent said: {res['message']}")
print(f"Collected Requirements: {dev_agent.collected_requirements}")

# Simulation 2: User responds
print("\n🔹 Test 2: User gives details")
res = executor.execute("scaffold_website", {"prompt": "I want a React app using vite for a todo list with a dark theme."})
print(f"DevAgent said: {res['message']}")
print(f"Collected Requirements: {dev_agent.collected_requirements}")
