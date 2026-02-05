import asyncio
from kasa import Discover, Module
from typing import List, Dict, Any

class KasaManager:
    """
    Manager for interacting with TP-Link Kasa smart devices using the Module API.
    """
    def __init__(self):
        self.devices = {}

    async def discover_devices(self) -> Dict[str, Any]:
        """
        Scans the network for Kasa devices.
        Returns a dictionary of found devices keyed by IP.
        """
        print("Discovering Kasa devices...")
        try:
            # Increased timeout for more robust discovery
            found_devices = await Discover.discover(timeout=5) 
            
            # Convert to a dictionary format with device info
            device_dict = {}
            for ip, dev in found_devices.items():
                await dev.update() # Ensure we have the latest state
                
                # Check for Light Module
                light_mod = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
                
                is_dimmable = light_mod and light_mod.has_feature("brightness")
                is_color = light_mod and light_mod.has_feature("hsv")

                device_dict[ip] = {
                    "alias": dev.alias,
                    "ip": ip,
                    "model": dev.model,
                    "is_on": dev.is_on,
                    "type": dev.device_type.name if hasattr(dev, "device_type") else "Unknown",
                    "brightness": light_mod.brightness if is_dimmable else None,
                    "is_color": is_color,
                    "hsv": light_mod.hsv if is_color else None,
                    "obj": dev 
                }
            
            # Store the dictionary
            self.devices = device_dict
            return device_dict
        except Exception as e:
            print(f"Error discovering devices: {e}")
            return {}

    async def _get_light_module(self, ip: str):
        """Helper to get a fresh device and its light module."""
        try:
            dev = await Discover.discover_single(ip)
            if dev:
                await dev.update()
                if hasattr(dev, "modules") and Module.Light in dev.modules:
                    return dev, dev.modules[Module.Light]
            return dev, None
        except Exception as e:
            print(f"Error connecting to {ip}: {e}")
            return None, None

    async def turn_on(self, ip: str, dev: Any = None) -> bool:
        """Turns on the device with the given IP. Uses provided device object if available."""
        try:
            if dev is None:
                dev = await Discover.discover_single(ip)
            
            if dev:
                await dev.update()
                await dev.turn_on()
                return True
        except Exception as e:
            print(f"Error turning on {ip}: {e}")
        return False

    async def turn_off(self, ip: str, dev: Any = None) -> bool:
        """Turns off the device with the given IP. Uses provided device object if available."""
        try:
            if dev is None:
                dev = await Discover.discover_single(ip)
            
            if dev:
                await dev.update()
                await dev.turn_off()
                return True
        except Exception as e:
            print(f"Error turning off {ip}: {e}")
        return False
    
    async def set_brightness(self, ip: str, level: int, dev: Any = None) -> bool:
        """Sets brightness (0-100) for the device. Uses provided device object if available."""
        try:
            light = None
            if dev:
                # If we have the device, check if it has modules (smart strip/plug with children) or is a bulb
                await dev.update()
                if hasattr(dev, "modules") and Module.Light in dev.modules:
                    light = dev.modules[Module.Light]
            else:
                 dev, light = await self._get_light_module(ip)

            if light and light.has_feature("brightness"):
                await light.set_brightness(level)
                return True
        except Exception as e:
            print(f"Error setting brightness for {ip}: {e}")
        return False

    async def set_hsv(self, ip: str, h: int, s: int, v: int, dev: Any = None) -> bool:
        """Sets HSV color for the device. Uses provided device object if available."""
        try:
            light = None
            if dev:
                 await dev.update()
                 if hasattr(dev, "modules") and Module.Light in dev.modules:
                    light = dev.modules[Module.Light]
            else:
                dev, light = await self._get_light_module(ip)

            if light and light.has_feature("hsv"):
                await light.set_hsv(h, s, v)
                return True
        except Exception as e:
            print(f"Error setting HSV for {ip}: {e}")
        return False

# Global instance
kasa_manager = KasaManager()
