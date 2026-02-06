import socket
import threading
import json
import time
from PySide6.QtCore import QObject, Signal

class PackLink(QObject):
    """
    Pack Link: Local P2P communication for Wolf AI instances.
    """
    peer_discovered = Signal(str, str) # IP, Hostname
    message_received = Signal(str, str) # Hostname, Message
    
    def __init__(self, port=19800):
        super().__init__()
        self.port = port
        self.hostname = socket.gethostname()
        self.peers = {} # IP -> Hostname
        self.running = False
        
    def start(self):
        self.running = True
        # Thread for discovery (Listening for UDP broadcasts)
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        
        # Thread for broadcasting own presence
        self.beacon_thread = threading.Thread(target=self._beacon_loop, daemon=True)
        self.beacon_thread.start()
        
    def _beacon_loop(self):
        """Broadcast presence every 10 seconds."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                msg = json.dumps({"type": "howl", "hostname": self.hostname}).encode()
                sock.sendto(msg, ('<broadcast>', self.port))
            except:
                pass
            time.sleep(10)

    def _discovery_loop(self):
        """Listen for other wolves."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.port))
        sock.settimeout(2)
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode())
                if msg.get("type") == "howl":
                    peer_ip = addr[0]
                    peer_host = msg.get("hostname")
                    if peer_ip not in self.peers and peer_host != self.hostname:
                        self.peers[peer_ip] = peer_host
                        self.peer_discovered.emit(peer_ip, peer_host)
            except socket.timeout:
                continue
            except:
                pass

    def send_howl(self, target_ip, text):
        """Send a direct message to a peer."""
        # For simplicity, we'll use UDP for messages too in this prototype
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg = json.dumps({"type": "msg", "hostname": self.hostname, "content": text}).encode()
        sock.sendto(msg, (target_ip, self.port))
