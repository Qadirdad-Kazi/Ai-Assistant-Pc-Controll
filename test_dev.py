from core.function_executor import executor

print(executor.execute("scaffold_website", {"prompt": "A modern web page layout", "framework": "html"}))
print(executor.execute("scaffold_website", {"prompt": "React app", "framework": "react"}))
print(executor.execute("scaffold_website", {"prompt": "Python script", "framework": "python"}))
print("Tests done.")
