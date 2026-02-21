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
