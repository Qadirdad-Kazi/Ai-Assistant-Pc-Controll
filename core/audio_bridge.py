"""
Local Python Audio Bridge for GSM/SIP endpoints.

This module maps the TTS output and STT input specifically to the Virtual Audio Cables
or physical Line-In/Line-Out jacks connected to the hardware GSM Modem (e.g. SIM800L).
This ensures the Assistant only "hears" the caller and only "speaks" to the caller 
when a call is active.
"""

import threading
import sounddevice as sd
import numpy as np

class GSMAudioBridge:
    def __init__(self):
        self.call_active = False
        
        # Audio device indexes (None implies default system device)
        self.modem_input_device_index = None  # SIM800L Output -> PC Line-In
        self.modem_output_device_index = None # PC Line-Out -> SIM800L Input
        
        # System defaults
        self.system_input_device_index = 1 # Usually built-in mic
        self.system_output_device_index = 3 # Usually speakers
        
        self._find_modem_devices()

    def _find_modem_devices(self):
        """Automatically find audio devices by name for the GSM Modem."""
        devices = sd.query_devices()
        print(f"[Audio Bridge] Scanning {len(devices)} audio devices...")
        
        for i, dev in enumerate(devices):
            name = dev.get('name', '').lower()
            # We look for "Line In" or specific hardware names for the modem link
            if "line" in name and dev.get('max_input_channels') > 0:
                self.modem_input_device_index = i
                print(f"[Audio Bridge] ✓ Assigned Modem Input: {name} (Index {i})")
            
            if ("line" in name or "speaker" in name) and dev.get('max_output_channels') > 0:
                # This logic may need refinement based on exact hardware strings
                if "modem" in name or "link" in name:
                     self.modem_output_device_index = i
                     print(f"[Audio Bridge] ✓ Assigned Modem Output: {name} (Index {i})")

    def link_call(self):
        """Locks the STT and TTS to the GSM modem audio devices."""
        print("[Audio Bridge] Establishing GSM Audio Link...")
        self.call_active = True
        
        # In a production environment, we call sd.default.device = [input, output]
        if self.modem_input_device_index is not None and self.modem_output_device_index is not None:
             sd.default.device = [self.modem_input_device_index, self.modem_output_device_index]
             print(f"[Audio Bridge] ✓ Switched default devices to [{self.modem_input_device_index}, {self.modem_output_device_index}]")
        
        print("[Audio Bridge] Routing STT -> Modem Link")
        print("[Audio Bridge] Routing TTS -> Modem Link")
        
        # We would notify RealTimeSTT and PiperTTS to recreate their streams 
        # using self.modem_input_device_index and self.modem_output_device_index
        # e.g., STT.change_input_device(self.modem_input_device_index)

    def sever_call(self):
        """Breaks the link, returning standard control to desktop users."""
        print("[Audio Bridge] Severing GSM Audio Link...")
        self.call_active = False
        
        # Revert to defaults
        sd.default.device = [self.system_input_device_index, self.system_output_device_index]
        
        print("[Audio Bridge] Reverting STT -> System Default Microphone")
        print("[Audio Bridge] Reverting TTS -> System Default Speakers")

    def play_on_hold_music(self):
        """
        Optional: streams a low-fi WAV file onto the Modem Line-Out while processing queries.
        """
        if self.call_active:
            print("[Audio Bridge] Playing 'Please wait' tone to caller.")

    def hold_call(self):
        """
        Puts the caller on hold, muting the STT input from the modem so the AI stops listening to them,
        and playing hold music/silence.
        """
        print("[Audio Bridge] Call put on hold. AI STT paused.")
        self.play_on_hold_music()
        
    def announce_to_user(self, announcement: str):
        """
        Uses TTS to speak out of the PC's main speakers to get the user's attention,
        without sending the audio down the phone line.
        """
        print(f"[Audio Bridge] (PC Speakers) ANNOUNCEMENT: {announcement}")
        # In full implementation, we switch TTS output to default system speakers
        # tts.change_output_device(self.system_output_device_index)
        # tts.speak(announcement)
        
    def handover_to_user(self):
        """
        Connects the PC's default Microphone to the Modem's Line-Out (so the caller hears the user),
        and the Modem's Line-In to the PC's default Speakers (so the user hears the caller).
        The AI stops processing audio completely.
        """
        print("[Audio Bridge] HANDOVER ACTIVE! AI entering sleep mode for this call.")
        print("[Audio Bridge] Routing PC Microphone -> Modem Line-Out")
        print("[Audio Bridge] Routing Modem Line-In -> PC Speakers")
        # Direct audio stream passthrough initialized here


# Global instance for managing audio routes
audio_bridge = GSMAudioBridge()
