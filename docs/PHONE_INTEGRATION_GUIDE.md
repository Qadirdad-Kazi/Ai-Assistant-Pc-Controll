# 📞 Phone Integration Guide (Receptionist Mode)

Wolf AI 2.0 is designed to integrate deeply with the real world, including **Physical Phone Lines**. Unlike standard cloud-based Twilio or VoIP setups, this application is designed for absolute privacy and local processing. This guide explains how to connect a physical Cellular adapter to your PC so Wolf AI can answer, speak to, and transcribe incoming phone calls.

---

## 🏗️ 1. Hardware Requirements

To connect your PC directly to a local cellular network (e.g., in Pakistan or anywhere globally), you need:

1. **A GSM Modem Module:** The **SIM800L** or **SIM900** modules are the industry standard for this. They are incredibly cheap and connect to any standard 2G/3G network.
2. **A USB to TTL Serial Adapter:** (e.g., FTDI CP2102). This allows your PC to send text-based AT commands to the modem (like "Answer Call" or "Hang Up").
3. **An active SIM Card:** Inserted into the GSM modem.
4. **An Audio Interface (or Sound Card):** Your PC needs a physical 3.5mm microphone jack (`Line-In`) and a speaker jack (`Line-Out`).

---

## 🔌 2. Wiring the Connection

This is the tricky part—you must connect both the **Data** (to control the modem) and the **Audio** (so Wolf can hear and speak to the caller).

### Data Connection (Serial/UART):
Connect the pins from the SIM800L to the USB TTL Adapter:
- **TXD** (Modem) ➜ **RXD** (USB adapter)
- **RXD** (Modem) ➜ **TXD** (USB adapter)
- **GND** (Modem) ➜ **GND** (USB adapter)

*Note: The SIM800L requires a stable 3.7V - 4.2V power supply. Do not power it directly from a 5V USB pin without a regulator, or it may crash during calls.*

### Audio Routing (The "Bridge"):
To ensure Wolf AI speaks to the caller (and not into your room), and listens to the caller (and not your desktop noises), you must cross-wire the audio:

1. **Modem SPK (Speaker Out) ➜ PC Mic (Line-In)** 
   *(This lets Wolf's STT engine hear the caller).*
2. **Modem MIC (Microphone In) ➜ PC Speaker (Line-Out)**
   *(This lets Wolf's TTS voice speak to the caller).*

---

## 💻 3. Software Configuration

### 1. Identify your COM Port
Once plugged into windows, open **Device Manager** and expand **Ports (COM & LPT)**. Find your USB Serial device and note its COM port (e.g., `COM3`, `COM5`).

### 2. Configure Wolf AI UI
1. Launch Wolf AI.
2. Go to the **Settings** tab.
3. Scroll to the **God-Mode Integrations** section.
4. Enter the COM port you found in step 1 into the **GSM Gateway COM Port** text box.

### 3. Audio Device Indexing
By default, Wolf will output TTS to your system's primary speaker. In a full production setup with the GSM modem, you'll need two sound cards (e.g., a cheap USB sound dongle for the modem, and your main motherboard audio for your headset).

If you look at `core/audio_bridge.py`, you will see:
```python
self.modem_input_device_index = None  
self.modem_output_device_index = None
```
*If you are an advanced user, you can use the `sounddevice` python library to list your audio device indices and hardcode these values so Wolf knows exactly which physical jacks belong to the Cellular Modem.*

---

## 🗣️ 4. The Receptionist Loop in Action

When a call comes in over the cellular network:
1. The SIM800L sends the text `RING` and the Caller ID `+923001234567` over the USB serial cable.
2. The `core/gsm_gateway.py` script catches this text.
3. It checks `core/receptionist.py` to see if you mapped a directive for this number (e.g., *"If Rafay calls, ask about the meeting"*).
4. **Answer:** It sends the `ATA` serial command back to the modem to answer the call.
5. **Bridge:** `core/audio_bridge.py` locks the STT and TTS engines to the modem's audio jacks.
6. **Converse:** Wolf speaks the LLaMA-generated greeting, waits for the caller's response via the line-in STT pipeline, logs it, and hangs up using the `ATH` command.

If the "Handover Protocol" is triggered (the caller asks for you), the audio bridge simply cross-routes your personal Headset Mic/Speakers to the Modem's Mic/Speakers so you can finish the call manually.
