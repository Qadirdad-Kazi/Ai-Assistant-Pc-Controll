#!/usr/bin/env python3
"""
JARIS Web GUI Test Script
Tests all the web GUI capabilities
"""

import requests
import time
import subprocess
import os
import sys

def test_web_gui():
    """Test the JARIS Web GUI functionality"""
    print("🧪 Testing JARIS Web GUI")
    print("=" * 40)
    
    # Test 1: Check if web GUI is running
    print("1️⃣ Testing Web GUI Connection...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Web GUI is running")
        else:
            print(f"❌ Web GUI returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Web GUI is not running")
        print("💡 Start it with: python3 jaris_web_gui.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Web GUI: {e}")
        return False
    
    # Test 2: Check API status
    print("\n2️⃣ Testing API Status...")
    try:
        response = requests.get("http://localhost:8080/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data}")
            if data.get('ollama_running'):
                print("✅ Ollama is connected")
            else:
                print("⚠️ Ollama not running - AI features may not work")
        else:
            print(f"❌ API Status returned {response.status_code}")
    except Exception as e:
        print(f"❌ API Status error: {e}")
    
    # Test 3: Test AI Chat
    print("\n3️⃣ Testing AI Chat...")
    try:
        response = requests.post("http://localhost:8080/api/chat", 
                               json={"message": "Hello JARIS"}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Chat working: {data.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ AI Chat failed: {response.status_code}")
    except Exception as e:
        print(f"❌ AI Chat error: {e}")
    
    # Test 4: Test PC Control
    print("\n4️⃣ Testing PC Control...")
    try:
        response = requests.post("http://localhost:8080/api/chat", 
                               json={"message": "list files"}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PC Control working: {data.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ PC Control failed: {response.status_code}")
    except Exception as e:
        print(f"❌ PC Control error: {e}")
    
    # Test 5: Test Voice API
    print("\n5️⃣ Testing Voice API...")
    try:
        response = requests.get("http://localhost:8080/api/voice/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Voice API working: {data}")
        else:
            print(f"❌ Voice API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Voice API error: {e}")
    
    print("\n🎉 Web GUI Test Complete!")
    print("\n📱 Open your browser and go to: http://localhost:8080")
    print("🎤 Try the voice features by clicking the microphone buttons")
    print("💻 Test PC control commands in the PC Control tab")

def start_web_gui():
    """Start the web GUI if not running"""
    print("🚀 Starting JARIS Web GUI...")
    try:
        # Check if already running
        response = requests.get("http://localhost:8080", timeout=2)
        print("✅ Web GUI is already running!")
        return True
    except:
        pass
    
    try:
        # Start the web GUI
        print("🔄 Starting web GUI process...")
        process = subprocess.Popen([sys.executable, "jaris_web_gui.py"], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
        
        # Wait a bit for it to start
        time.sleep(3)
        
        # Check if it's running
        try:
            response = requests.get("http://localhost:8080", timeout=5)
            if response.status_code == 200:
                print("✅ Web GUI started successfully!")
                print("🌐 Open your browser and go to: http://localhost:8080")
                return True
        except:
            print("❌ Web GUI failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Web GUI: {e}")
        return False

if __name__ == "__main__":
    print("🤖 JARIS Web GUI Test Suite")
    print("=" * 50)
    
    # Check if we should start the GUI
    if len(sys.argv) > 1 and sys.argv[1] == "start":
        start_web_gui()
    else:
        # Just test if it's running
        test_web_gui()
    
    print("\n💡 Usage:")
    print("  python3 test_web_gui.py        # Test if GUI is running")
    print("  python3 test_web_gui.py start  # Start GUI and test")
