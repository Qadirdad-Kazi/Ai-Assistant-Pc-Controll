"""
GSM Gateway bridge for Pakistani Cellular Networks.
Uses AT commands via Serial to communicate with physical modules (like SIM800L) 
or a virtual Android serial bridge.
"""
import time
import threading
try:
    import serial
except ImportError:
    serial = None
    print("[GSM Gateway] pyserial not found. Please pip install pyserial.")

class GSMGateway:
    def __init__(self, port: str = "COM3", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self._listen_thread = None
        self._running = False
        self.on_call_incoming = None

    def connect(self) -> bool:
        """Attempt to open serial connection to the GSM modem."""
        if not serial:
            print("[GSM Gateway] Skipping connection, pyserial not available.")
            return False
            
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_connected = True
            print(f"[GSM Gateway] Successfully connected on {self.port} at {self.baudrate} baud.")
            
            # Send initial AT checks
            self._send_command("AT")
            time.sleep(0.5)
            # Enable Caller ID
            self._send_command("AT+CLIP=1")
            
            # Start background listener
            self._running = True
            self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listen_thread.start()
            
            return True
        except Exception as e:
            print(f"[GSM Gateway] Failed to connect: {e}")
            self.is_connected = False
            return False

    def _send_command(self, cmd: str) -> str:
        """Send an AT command and return the immediate response."""
        if not self.is_connected or not self.serial_conn:
            return ""
        try:
            self.serial_conn.write((cmd + "\r\n").encode())
            time.sleep(0.2)
            response = self.serial_conn.read_all().decode(errors="ignore")
            return response.strip()
        except Exception as e:
            print(f"[GSM Gateway] Serial write error: {e}")
            return ""

    def answer_call(self):
        """Answer an incoming call."""
        print("[GSM Gateway] Answering call...")
        self._send_command("ATA")

    def hangup_call(self):
        """Hang up the current call."""
        print("[GSM Gateway] Hanging up...")
        self._send_command("ATH")

    def dial(self, phone_number: str):
        """Dial an outgoing number."""
        print(f"[GSM Gateway] Dialing {phone_number}...")
        self._send_command(f"ATD{phone_number};")

    def _listen_loop(self):
        """Background loop to parse incoming serial data for RINGs or messages."""
        while self._running and self.serial_conn:
            try:
                line = self.serial_conn.readline().decode(errors="ignore").strip()
                if line:
                    if "RING" in line:
                        print("[GSM Gateway] Incoming Call detected!")
                    elif "+CLIP:" in line:
                        # Extract Caller ID
                        number = self._extract_caller_id(line)
                        print(f"[GSM Gateway] Caller ID: {number}")
                        if self.on_call_incoming:
                            self.on_call_incoming(number)
            except Exception as e:
                print(f"[GSM Gateway] Listener error: {e}")
                time.sleep(1)

    def _extract_caller_id(self, clip_line: str) -> str:
        # Example format: +CLIP: "03001234567",129,"",0,"",0
        try:
            parts = clip_line.split('"')
            if len(parts) > 1:
                return parts[1]
        except Exception:
            pass
        return "Unknown"

    def disconnect(self):
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
        print("[GSM Gateway] Disconnected.")

# Global instance (requires explicit manual initialization or config)
gsm_gateway = GSMGateway()
