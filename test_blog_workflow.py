from Wolf_pc_control import WolfPCControl
import json
from pathlib import Path

def run_test():
    pc = WolfPCControl()
    files = [
        {'name': 'index.html', 'code': '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>My Blog</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <script src="script.js"></script>\n</body>\n</html>'},
        {'name': 'style.css', 'code': 'body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 0;\n}'},
        {'name': 'script.js', 'code': 'console.log("Blog is ready!");'}
    ]
    
    print("Starting Workflow...")
    
    # 1. Directory Setup
    res1 = pc.action_create_folder(name='BlogWebsite')
    print(f"Directory Setup: {res1['message']}")
    
    # 2. VS Code Automation
    print("Initiating VS Code Automation...")
    res2 = pc.action_automate_vscode(files=files, folder_name='BlogWebsite')
    print(f"File Creation: {res2['message']}")
    
    print("Final Confirmation: BlogWebsite project setup complete. index.html, style.css, and script.js are ready in VS Code.")

if __name__ == "__main__":
    run_test()
