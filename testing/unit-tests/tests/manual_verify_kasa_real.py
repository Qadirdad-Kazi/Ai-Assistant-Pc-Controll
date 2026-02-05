
import asyncio
import sys
import logging
from unittest.mock import MagicMock

# Mock transformers to prevent import error
sys.modules["transformers"] = MagicMock()
sys.modules["core.router"] = MagicMock() # Router imports transformers

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from core.kasa_control import kasa_manager

async def run_real_test():
    print("\n=== STARTING REAL-WORLD KASA TEST ===\n")
    
    # 1. Discovery
    print("1. Discovering devices (this may take 2-5 seconds)...")
    devices = await kasa_manager.discover_devices()
    
    if not devices:
        print("!!! NO DEVICES FOUND !!!")
        print("Please ensure your computer is on the same network as your Kasa devices.")
        return

    print(f"\nSUCCESS: Found {len(devices)} devices:")
    for d in devices:
        print(f"  - [{d['alias']}] IP: {d['ip']} Model: {d['model']} On: {d['is_on']}")

    # 2. Test Control on First Device
    target = devices[0]
    target_ip = target['ip']
    target_alias = target['alias']
    target_obj = target['obj'] # The actual python-kasa SmartDevice object
    
    print(f"\n2. Testing control on: {target_alias} ({target_ip})")
    print("   Note: We are using the OPTIMIZED path passing the device object directly.")
    
    # Toggle cycle
    print(f"   Turning OFF {target_alias}...")
    await kasa_manager.turn_off(target_ip, dev=target_obj)
    await asyncio.sleep(1) # Wait a bit
    
    print(f"   Turning ON {target_alias}...")
    await kasa_manager.turn_on(target_ip, dev=target_obj)
    await asyncio.sleep(1)
    
    # Brightness (if supported)
    if target.get('brightness') is not None:
        print(f"   Setting brightness to 50%...")
        await kasa_manager.set_brightness(target_ip, 50, dev=target_obj)
        await asyncio.sleep(1)
        print(f"   Setting brightness to 100%...")
        await kasa_manager.set_brightness(target_ip, 100, dev=target_obj)
        await asyncio.sleep(1)
        
    # Color (if supported)
    if target.get('is_color'):
        print(f"   Setting color to RED...")
        # Red HSV: 0, 100, 100
        await kasa_manager.set_hsv(target_ip, 0, 100, 100, dev=target_obj)
        await asyncio.sleep(1)
        
        print(f"   Setting color to BLUE...")
        # Blue HSV: 240, 100, 100
        await kasa_manager.set_hsv(target_ip, 240, 100, 100, dev=target_obj)
        await asyncio.sleep(1)
        
        print("   Restoring to White/Daylight...")
        await kasa_manager.set_hsv(target_ip, 0, 0, 100, dev=target_obj)
        
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    try:
        # Use existing loop if available (e.g. running in IDE/Jupyter) or create new
        try:
             asyncio.run(run_real_test())
        except RuntimeError: 
             # If loop is already running
             loop = asyncio.get_event_loop()
             loop.create_task(run_real_test())
    except KeyboardInterrupt:
        print("\nTest cancelled.")
