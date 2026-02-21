import os

files_to_remove = [
    "core/kasa_control.py",
    "core/janitor.py",
    "core/knowledge_base.py",
    "core/calendar_manager.py",
    "core/weather.py",
    "core/tasks.py",
    "gui/tabs/planner.py",
    "gui/tabs/browser.py",
    "gui/tabs/home_automation.py",
    "gui/tabs/grimoire.py",
    "gui/tabs/sentinel.py",
    "gui/tabs/janitor.py",
    "gui/tabs/briefing.py"
]

for f in files_to_remove:
    path = os.path.join(os.getcwd(), f.replace("/", os.sep))
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"Removed: {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")
    else:
        print(f"Not found: {f}")

# Remove data files
data_files = ["data/calendar.db", "data/tasks.db", "data/user_stats.json"]
for f in data_files:
    path = os.path.join(os.getcwd(), f.replace("/", os.sep))
    if os.path.exists(path):
        os.remove(path)
