from core.pc_control import pc_controller

print("Testing pc_control...")
print(pc_controller.execute("volume", "50"))
print(pc_controller.execute("volume", "up"))
print(pc_controller.execute("volume", "down"))
print(pc_controller.execute("open_app", "calculator"))
print(pc_controller.execute("close_app", "calculator"))
print("Done.")
