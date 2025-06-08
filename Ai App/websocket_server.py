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
    def __init__(self, host='localhost', port=5000):
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
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"Received message: {data}")
                    if isinstance(data, dict) and 'type' in data:
                        if data['type'] == 'start_listening':
                            self.backend.start_listening()
                        elif data['type'] == 'process_text' and 'text' in data:
                            self.backend.process_command(data['text'])
                        elif data['type'] == 'text_command' and 'data' in data and 'command' in data['data']:
                            command_text = data['data']['command']
                            print(f"Processing text command: {command_text}")
                            # Assuming self.backend.process_command will handle execution and response
                            self.backend.process_command(command_text)
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
