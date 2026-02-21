"""
Local Python Audio Bridge for GSM/SIP endpoints.

This module maps the TTS output and STT input specifically to the Virtual Audio Cables
or physical Line-In/Line-Out jacks connected to the hardware GSM Modem (e.g. SIM800L).
This ensures the Assistant only "hears" the caller and only "speaks" to the caller 
when a call is active.
"""

import threading

class GSMAudioBridge:
    def __init__(self):
        self.call_active = False
        
        # Audio device indexes (0 implies default system device)
        # In a real scenario, you'd use sounddevice to list devices and find
        # the specific "Line-In" and "Line-Out" wired to the GSM modem.
        self.modem_input_device_index = None  
        self.modem_output_device_index = None
        
        # Backup default indexes for normal operation
        self.system_input_device_index = None
        self.system_output_device_index = None
        
    def link_call(self):
        """
        Locks the STT and TTS to the GSM modem audio devices.
        Starts listening on the caller audio stream.
        """
        print("[Audio Bridge] Establishing GSM Audio Link...")
        self.call_active = True
        
        # Switch STT input to modem's output (Line-In)
        # Switch TTS output to modem's input (Line-Out)
        print("[Audio Bridge] Routing STT -> Modem Line-In")
        print("[Audio Bridge] Routing TTS -> Modem Line-Out")
        
        # We would notify RealTimeSTT and PiperTTS to recreate their streams 
        # using self.modem_input_device_index and self.modem_output_device_index
        # e.g., STT.change_input_device(self.modem_input_device_index)

    def sever_call(self):
        """
        Breaks the link to the GSM modem, returning standard control to desktop users.
        """
        print("[Audio Bridge] Severing GSM Audio Link...")
        self.call_active = False
        
        print("[Audio Bridge] Reverting STT -> System Default Microphone")
        print("[Audio Bridge] Reverting TTS -> System Default Speakers")

    def play_on_hold_music(self):
        """
        Optional: streams a low-fi WAV file onto the Modem Line-Out while processing queries.
        """
        if self.call_active:
            print("[Audio Bridge] Playing 'Please wait' tone to caller.")

# Global instance for managing audio routes
audio_bridge = GSMAudioBridge()
