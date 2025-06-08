// WebSocket connection with configuration
const socket = io({
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    transports: ['websocket', 'polling'],
    path: '/socket.io',
    secure: window.location.protocol === 'https:',
    port: 5002  // Match the port in app.py
});

// DOM Elements
const statusElement = document.getElementById('status');
const responseElement = document.getElementById('assistant-response');
const startButton = document.getElementById('start-button');
const stopButton = document.getElementById('stop-button');
const listeningIndicator = document.getElementById('listening-indicator');
const connectionStatus = document.getElementById('connection-status');
const statusDot = connectionStatus.querySelector('.status-dot');
const statusText = connectionStatus.querySelector('.status-text');

// Audio context for processing audio
let audioContext;
let processor;
let source;
let isListening = false;

// Connection state
let isConnected = false;

// Initialize the app
function init() {
    console.log('Initializing app...');
    setupEventListeners();
    setupSocketEvents();
    updateStatus('Connecting to server...', 'info');
    
    // Set a timeout to check if we're still connecting
    setTimeout(() => {
        if (!isConnected) {
            updateStatus('Connection taking longer than expected. Trying to reconnect...', 'error');
            socket.connect();
        }
    }, 5000);
}

// Set up WebSocket event listeners
function setupSocketEvents() {
    // Connection events
    socket.on('connect', () => {
        console.log('WebSocket connected');
        isConnected = true;
        updateConnectionStatus(true);
        updateStatus('Connected to server', 'success');
        
        // Request current state
        socket.emit('get_state');
    });
    
    socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        updateConnectionStatus(false);
        updateStatus('Connection error. Retrying...', 'error');
    });
    
    socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        isConnected = false;
        updateConnectionStatus(false);
        updateStatus('Disconnected from server', 'error');
        stopListening();
        
        // Try to reconnect
        if (reason === 'io server disconnect') {
            socket.connect();
        }
    });
    
    // Application events
    socket.on('assistant_state', (data) => {
        console.log('Assistant state update:', data);
        updateListeningState(data.active);
    });
    
    socket.on('assistant_response', (data) => {
        console.log('Assistant response:', data);
        if (data && data.text) {
            displayResponse(data.text);
        }
    });
    
    socket.on('error', (data) => {
        console.error('Server error:', data);
        updateStatus(`Error: ${data.message || 'Unknown error occurred'}`, 'error');
    });
    
    socket.on('status', (data) => {
        console.log('Status update:', data);
        if (data && data.message) {
            updateStatus(data.message, 'info');
        }
    });
}

// Set up UI event listeners
function setupEventListeners() {
    // Start/Stop buttons
    startButton.addEventListener('click', startListening);
    stopButton.addEventListener('click', stopListening);
    
    // Reconnect button if we add one
    const reconnectBtn = document.getElementById('reconnect-button');
    if (reconnectBtn) {
        reconnectBtn.addEventListener('click', () => {
            if (!isConnected) {
                socket.connect();
            }
        });
    }
}

// Update connection status UI
function updateConnectionStatus(connected) {
    if (connected) {
        connectionStatus.classList.add('connected');
        statusDot.style.backgroundColor = '#10b981'; // Success green
        statusText.textContent = 'Connected';
        startButton.disabled = false;
    } else {
        connectionStatus.classList.remove('connected');
        statusDot.style.backgroundColor = '#ef4444'; // Error red
        statusText.textContent = 'Disconnected';
        startButton.disabled = true;
    }
}

// Start listening to microphone
async function startListening() {
    if (isListening) return;
    
    try {
        updateStatus('Requesting microphone access...', 'info');
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Set up audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        await audioContext.audioWorklet.addModule('static/js/audio-processor.js')
            .catch(error => {
                console.error('Error loading audio worklet:', error);
                throw new Error('Failed to load audio processor');
            });
        
        // Create audio worklet node
        const audioWorkletNode = new AudioWorkletNode(audioContext, 'audio-processor');
        
        // Handle messages from the audio worklet
        audioWorkletNode.port.onmessage = (event) => {
            if (event.data.type === 'wakeword') {
                console.log('Wake word detected!');
                updateStatus('Wake word detected! Listening...', 'success');
                // Here you would process the wake word detection
            }
        };
        
        // Create media stream source
        source = audioContext.createMediaStreamSource(stream);
        
        // Connect nodes
        source.connect(audioWorkletNode);
        audioWorkletNode.connect(audioContext.destination);
        
        // Notify server we're starting to listen
        socket.emit('start_listening');
        isListening = true;
        updateStatus('Listening for wake word...', 'success');
        
        // Update UI
        startButton.disabled = true;
        stopButton.disabled = false;
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        updateStatus(`Error: ${error.message || 'Could not access microphone'}`, 'error');
        isListening = false;
        
        // Update UI
        startButton.disabled = false;
        stopButton.disabled = true;
    }
}

// Stop listening to microphone
function stopListening() {
    if (!isListening) return;
    
    console.log('Stopping microphone access...');
    
    try {
        // Disconnect and clean up audio nodes
        if (source) {
            try {
                // Stop all tracks in the stream
                const tracks = source.mediaStream?.getTracks() || [];
                tracks.forEach(track => {
                    track.stop();
                    console.log('Stopped audio track:', track.id);
                });
                
                // Disconnect the source
                source.disconnect();
                console.log('Disconnected audio source');
            } catch (e) {
                console.error('Error stopping audio source:', e);
            }
            source = null;
        }
        
        // Close the audio context
        if (audioContext) {
            if (audioContext.state !== 'closed') {
                audioContext.close()
                    .then(() => {
                        console.log('AudioContext closed successfully');
                    })
                    .catch(e => {
                        console.error('Error closing AudioContext:', e);
                    });
            }
            audioContext = null;
        }
        
        // Notify server we're stopping
        console.log('Notifying server to stop listening...');
        socket.emit('stop_listening');
        
        // Update state and UI
        isListening = false;
        updateStatus('Microphone is off', 'info');
        startButton.disabled = false;
        stopButton.disabled = true;
        
        console.log('Microphone access stopped');
        
    } catch (error) {
        console.error('Error in stopListening:', error);
        updateStatus('Error stopping microphone', 'error');
    }
}

// Update UI based on listening state
function updateListeningState(isActive) {
    listeningIndicator.style.display = isActive ? 'block' : 'none';
    startButton.disabled = isActive;
    stopButton.disabled = !isActive;
}

// Display assistant response with typing animation
async function displayResponse(text) {
    // Clear any existing content
    responseElement.innerHTML = '';
    
    // Create a typing indicator
    const typingIndicator = document.createElement('span');
    typingIndicator.className = 'typing-indicator';
    responseElement.appendChild(typingIndicator);
    
    // Simple typing effect
    let i = 0;
    const speed = 20; // milliseconds per character
    
    function typeWriter() {
        if (i < text.length) {
            // Remove typing indicator when we start showing text
            if (typingIndicator.parentNode) {
                responseElement.removeChild(typingIndicator);
            }
            
            // Add text character by character
            responseElement.innerHTML += text.charAt(i);
            i++;
            
            // Auto-scroll to the bottom
            responseElement.scrollTop = responseElement.scrollHeight;
            
            // Schedule next character
            setTimeout(typeWriter, speed);
            
            // If we're done typing, speak the response
            if (i === text.length) {
                speakResponse(text);
            }
        }
    }
    
    // Start the typing effect
    setTimeout(typeWriter, 500);
}

// Speak the response using the Web Speech API
function speakResponse(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set voice properties
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.lang.startsWith('en') && voice.name.includes('Samantha')
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        // Set other properties
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Handle speech errors
        utterance.onerror = (event) => {
            console.error('SpeechSynthesis error:', event);
        };
        
        // Speak the text
        window.speechSynthesis.speak(utterance);
    }
}

// Update status message
function updateStatus(message, type = 'info') {
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Add CSS for typing indicator
const style = document.createElement('style');
style.textContent = `
    .typing-indicator {
        display: inline-block;
        width: 10px;
        height: 1em;
        background-color: currentColor;
        animation: blink 1s infinite;
        margin-left: 2px;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
`;
document.head.appendChild(style);

// Initialize the app when the DOM is loaded and voices are loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load voices before we need them
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = init;
    } else {
        init();
    }
});
