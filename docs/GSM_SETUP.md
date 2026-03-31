# 📞 GSM Telephony Setup Guide

Wolf AI 2.0 uses a physical GSM modem (SIM800L or similar) to handle calls without external APIs. This guide covers the physical wiring and audio routing.

## 🔌 Hardware Wiring Diagram

### 1. Serial Connection
| Connection Type | GSM PIN | Adapter PIN |
| :--- | :--- | :--- |
| **Data Out** | TX | RX |
| **Data In** | RX | TX |
| **Common** | GND | GND |
| **Power** | VCC (5V/4V) | 5V PSU |

> [!CAUTION]
> **Power Supply:** SIM800L modules require a high-current power supply (at least 2A peaks) for network transmission. Do NOT power the modem directly from a USB-to-TTL adapter.

### 2. Audio Bridging
To enable Wolf AI to hear and speak, you must bridge the modem's audio pins to your PC soundcard.

- **Modem SPK+ / SPK-** $\rightarrow$ **PC Line-In (Blue Port)** or **USB Microphone Input**.
- **Modem MIC+ / MIC-** $\rightarrow$ **PC Line-Out (Green Port)** or **USB Headphone Output**.

---

## ⚙️ Software Configuration

### 1. Port Identification
Identify your COM/Serial port:
- **Windows**: Device Manager $\rightarrow$ Ports (e.g., `COM3`).
- **Mac/Linux**: `/dev/ttyUSB0` or `/dev/cu.usbserial`.

### 2. Wolf AI Settings
Update your `config.py` or use the **Settings** screen in the Dashboard:
- `GSM_PORT`: "COM3" (Replace with your actual port).
- `GSM_BAUDRATE`: 115200.

---

## 🧠 Functional Flow
1. **Detection**: Wolf listens for `RING` and `+CLIP` (Caller ID) on the serial line.
2. **Acceptance**: If a directive exists, Wolf sends `ATA` to answer.
3. **Routing**: The **GSMAudioBridge** switches your system audio default to the "Modem In/Out" ports.
4. **Conversation**: Wolf speaks via the modem's MIC and hears via the modem's SPK.

---

## 🛠️ Troubleshooting
- **No Response to AT**: Check TX/RX crossover and common ground.
- **Modem Resets**: Verify your power supply is capable of 2A peaks.
- **Audio Echo**: Ensure "Listen to this device" is OFF in Windows Sound Settings for the modem's Line-In.
