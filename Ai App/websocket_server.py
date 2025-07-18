"""
WebSocket server for Wolf AI Voice Assistant
Handles real-time communication between frontend and backend
"""
import asyncio
import websockets
import json
import threading
import time
from voice_backend import VoiceBackend

class WebSocketServer:
    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None  # To store the asyncio event loop
        # MODIFIED: Pass the method for VoiceBackend to use
        self.backend = VoiceBackend(send_ws_func=self.send_message_sync)
        # REMOVED: This line is no longer the correct approach as send_ws_func is injected
        # self.backend.send_message = self.send_message_sync
        
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"New client connected. Total clients: {len(self.clients)}")
        await self.broadcast("status", "Connected to WebSocket server")  # Call broadcast directly from async context
        
    async def unregister(self, websocket):
        self.clients.discard(websocket)
        print(f"Client disconnected. Remaining clients: {len(self.clients)}")
        
    def send_message_sync(self, msg_type, data):
        """Synchronous wrapper to schedule broadcast on the event loop."""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.broadcast(msg_type, data), self.loop)
        else:
            print("WebSocketServer: Event loop not available to send message.")

    async def send_error(self, websocket, error_message):
        """Send an error message to a specific client"""
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "data": error_message,
                "timestamp": time.time()
            }))
        except Exception as e:
            print(f"[WebSocket] Error sending error message: {e}")
    
    async def broadcast(self, msg_type, data):
        """Send a message to all connected clients"""
        if not self.clients:
            return
            
        message = json.dumps({
            "type": msg_type,
            "data": data,
            "timestamp": time.time()
        })
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                print(f"Error sending message to client: {e}")
    
    async def handle_client(self, websocket, path=None):
        """Handle a new WebSocket connection"""
        # Configure WebSocket settings
        websocket.max_size = 20 * 1024 * 1024  # 20MB max message size for audio chunks
        websocket.ping_interval = 20  # Send ping every 20 seconds
        websocket.ping_timeout = 30   # Wait 30 seconds for pong response
        
        await self.register(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        client_id = id(websocket)
        print(f"[WebSocket] Client {client_id} connected from {client_ip}")
        
        try:
            # Send initial handshake
            await websocket.send(json.dumps({
                "type": "connection_established",
                "data": {
                    "client_id": client_id,
                    "timestamp": time.time(),
                    "max_message_size": websocket.max_size,
                    "server_version": "1.0.0"
                }
            }))
            
            # Initialize audio buffer for this client
            audio_buffer = bytearray()
            
            # Main message loop
            async for message in websocket:
                try:
                    # Handle binary messages (audio data)
                    if isinstance(message, (bytes, bytearray)):
                        if not message:
                            print("[WebSocket] Received empty binary message")
                            continue
                            
                        message_size = len(message)
                        print(f"[WebSocket] Received binary message: {message_size} bytes")
                        
                        # Forward binary data to the backend if it's a reasonable size
                        if 0 < message_size <= 20 * 1024 * 1024:  # Up to 20MB
                            try:
                                # Add to audio buffer
                                audio_buffer.extend(message)
                                
                                # If we have enough data, process it
                                if len(audio_buffer) >= 4096:  # Process in 4KB chunks
                                    chunk = bytes(audio_buffer[:4096])
                                    audio_buffer = audio_buffer[4096:]
                                    
                                    if hasattr(self.backend, 'handle_audio_data'):
                                        try:
                                            # Process the audio chunk in a separate thread
                                            threading.Thread(
                                                target=self.backend.handle_audio_data,
                                                args=(chunk,),
                                                daemon=True
                                            ).start()
                                        except Exception as e:
                                            print(f"[WebSocket] Error in audio processing thread: {e}")
                                            
                            except Exception as e:
                                error_msg = f"Error processing audio data: {e}"
                                print(f"[WebSocket] {error_msg}")
                                await self.send_error(websocket, error_msg)
                                
                            # Clear buffer if it gets too large
                            if len(audio_buffer) > 10 * 1024 * 1024:  # 10MB
                                print("[WebSocket] Audio buffer too large, clearing")
                                audio_buffer = bytearray()
                                
                        else:
                            print(f"[WebSocket] Invalid audio data size: {message_size} bytes")
                            
                        # Send acknowledgment
                        await websocket.send(json.dumps({
                            "type": "audio_ack",
                            "timestamp": time.time(),
                            "buffer_size": len(audio_buffer)
                        }))
                        continue
                    
                    # Handle text messages (JSON commands)
                    try:
                        data = json.loads(message)
                        print(f"[WebSocket] Received message: {data}")
                        if not isinstance(data, dict) or 'type' not in data:
                            print(f"[WebSocket] Invalid message format: {data}")
                            continue
                            
                    except json.JSONDecodeError as e:
                        print(f"[WebSocket] Invalid JSON received: {e}")
                        await self.send_error(websocket, f"Invalid JSON: {str(e)}")
                        continue
                    
                    # Process valid JSON messages
                    if isinstance(data, dict) and 'type' in data:
                        if data['type'] == 'start_listening':
                            self.backend.start_listening()
                        elif data['type'] == 'process_text' and 'text' in data:
                            self.backend.process_command(data['text'])
                        elif data['type'] == 'text_command' and 'command' in data:
                            command_text = data['command']
                            print(f"Processing text command: {command_text}")
                            # Process the command through the backend
                            self.backend.process_command(command_text)
                            # Send acknowledgment back to client
                            await self.broadcast("command_received", {"command": command_text, "status": "processing"})
                        elif data['type'] == 'set_operation_mode' and 'mode' in data:
                            print("DEBUG: Entered 'set_operation_mode' block in websocket_server.py")
                            new_mode = data['mode']
                            print(f"DEBUG: Extracted new_mode: {new_mode}")
                            if hasattr(self.backend, 'set_operation_mode'):
                                print(f"DEBUG: self.backend has 'set_operation_mode'. Calling it with {new_mode}.")
                                self.backend.set_operation_mode(new_mode) # This should trigger logs in VoiceBackend
                                print(f"[websocket_server.py] Operation mode set to: {new_mode} (after calling backend)")
                            else:
                                print("DEBUG ERROR: self.backend does NOT have 'set_operation_mode' method!")
                        elif data['type'] == 'cancel_action_request':
                            print("[WebSocketServer] Received cancel_action_request")
                            if hasattr(self.backend, 'cancel_current_actions'):
                                self.backend.cancel_current_actions()
                            else:
                                print("[WebSocketServer] ERROR: Backend has no cancel_current_actions method.")
                        elif data['type'] == 'ping':
                            await websocket.send(json.dumps({
                                'type': 'pong',
                                'timestamp': time.time()
                            }))
                        elif data['type'] == 'toggle-listening' and 'listening' in data:
                            # Forward the toggle-listening command to the backend
                            print(f"[WebSocket] Forwarding toggle-listening: {data['listening']}")
                            self.backend.handle_input(json.dumps({
                                'type': 'toggle-listening',
                                'data': {'listening': data['listening']}
                            }))
                except json.JSONDecodeError as e:
                    print(f"Received invalid JSON: {message}")
                    print(f"Error: {e}")
                except Exception as e:
                    print(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Unexpected error in handle_client: {e}")
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server"""
        self.loop = asyncio.get_running_loop() # Store the current event loop
        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            if hasattr(self.backend, 'notify_websocket_ready') and callable(self.backend.notify_websocket_ready):
                self.backend.notify_websocket_ready() # Notify backend that WebSocket is up
            return self.server
        except Exception as e:
            print(f"WebSocket server error: {e}")
            raise
            
    def stop(self):
        """Stop the WebSocket server"""
        if hasattr(self, 'server'):
            self.server.close()
            print("WebSocket server stopped")

async def start_websocket_server():
    server = WebSocketServer()
    try:
        await server.start()
        # Keep the server running
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(start_websocket_server())
    except KeyboardInterrupt:
        print("\nWebSocket server stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Shutting down...")
