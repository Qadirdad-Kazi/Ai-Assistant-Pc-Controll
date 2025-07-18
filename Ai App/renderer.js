window.onerror = function(message, source, lineno, colno, error) {
  console.error('Renderer window.onerror:', {
    message: message,
    source: source,
    lineno: lineno,
    colno: colno,
    error: error
  });
  return false; 
};

window.addEventListener('unhandledrejection', event => {
  console.error('Renderer Unhandled Rejection:', event.reason);
});

// Global state
let isListening = false;
let currentTheme = 'dark';
let settings = {
    voiceGender: 'female',
    language: 'en',
    wakeWord: 'Hey Wolf',
    alwaysListen: false,
    theme: 'dark'
};

// Voice Controller
let voiceController = null;

// Face animations controller
let faceAnimations;
let audioContext;
let analyser;
let dataArray;
let waveformAnimationId;
let socket;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let commandInput, sendCommandBtn;
let aiModeBtn, pcControlModeBtn, cancelActionBtn;
let currentMode = 'ai'; // Default mode

// Face animations will be loaded via script tag in HTML

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize face animations (loaded via script tag)
    faceAnimations = window.assistantFace;
    
    // Initialize voice controller
    await initializeVoiceController();
    if (typeof window.electronAPI === 'undefined') {
        console.error('CRITICAL: window.electronAPI is undefined. Preload script may not have run correctly or contextIsolation is not working as expected.');
        const body = document.querySelector('body');
        if (body) {
            body.innerHTML = '<div style="color: red; font-size: 20px; padding: 40px; text-align: center;">CRITICAL ERROR: Application cannot load. Preload script failed. Check console.</div>';
        }
        return; // Stop further execution
    }
    try {
        // Initialize Feather icons
        if (typeof feather !== 'undefined' && feather && typeof feather.replace === 'function') {
          feather.replace();
        } else {
          console.warn('Feather icons library not available or replace method missing. Skipping feather.replace().');
          // Optionally, you could try to call it again after a short delay or show a specific UI warning
        }
        
        // Load settings
        await loadSettings();
        
        // Setup WebSocket connection
        setupWebSocket();
        
        // Get references to ALL interactive elements first
        commandInput = document.getElementById('command-input');
        sendCommandBtn = document.getElementById('send-command-btn');
        aiModeBtn = document.getElementById('ai-mode-btn');
        pcControlModeBtn = document.getElementById('pc-control-mode-btn');
        cancelActionBtn = document.getElementById('cancel-action-btn');
        // Ensure other elements needed by setupEventListeners are also defined here if not already global

        // Setup event listeners (now that elements are defined)
        setupEventListeners();
        
        // Setup audio visualization
        setupAudioVisualization();
        
        // Setup Python message listeners
        setupPythonListeners();

        // Set initial mode (this will also update button states)
        setMode(currentMode); 

        // Apply theme from settings
        applyTheme(settings.theme || 'dark');
        
        // Update UI with current settings
        updateUISettings();
        
        console.log('Wolf AI Assistant initialized');
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to initialize application. Please check the console for details.');
    }
});

// WebSocket connection management
function setupWebSocket() {
    // Use a direct WebSocket URL since we're in Electron
    const wsUrl = 'ws://localhost:5001/ws';
    console.log('Connecting to WebSocket:', wsUrl);
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        updateStatus('Connected to server');
        
        // Send initial handshake
        socket.send(JSON.stringify({
            type: 'handshake',
            client: 'web'
        }));
    };
    
    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    socket.onclose = (event) => {
        console.log('WebSocket disconnected - Code:', event.code, 'Reason:', event.reason, 'Clean:', event.wasClean);
        updateStatus('Disconnected. Reconnecting...');
        
        // Show more detailed error message based on close code
        if (event.code === 1006) {
            console.error('WebSocket connection failed. Is the backend server running?');
        }
        
        // Attempt to reconnect
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // Exponential backoff
            reconnectAttempts++;
            
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
            
            setTimeout(() => {
                setupWebSocket();
            }, delay);
        } else {
            const errorMsg = `Connection lost after ${MAX_RECONNECT_ATTEMPTS} attempts. ` +
                          `Please check if the backend server is running on port 5001.`;
            showError(errorMsg);
            console.error(errorMsg);
        }
    };
    
    socket.onerror = (error) => {
        console.error('WebSocket error event:', error);
        console.error('Error details:', {
            type: error.type,
            message: error.message,
            error: error.error
        });
    };
}

function handleWebSocketMessage(data) {
    console.log('[DEBUG] handleWebSocketMessage received:', JSON.stringify(data));
    if (!data || !data.type) return;
    
    switch (data.type) {
        case 'connection_established':
            console.log('Connection established with server');
            updateStatus('Ready');
            break;
            
        case 'status':
            updateStatus(data.message);
            break;
            
        case 'speech_recognized':
            handleSpeechRecognized(data.data);
            break;

        case 'ai_response':
            console.log('[DEBUG] Received ai_response:', JSON.stringify(data));
            handleAIResponse(data.data);
            break;

        case 'pc_control_result':
            console.log('[DEBUG] Received pc_control_result:', JSON.stringify(data));
            if (data.data && data.data.message) {
                addMessageToChat('assistant', data.data.message);
            } else {
                console.warn('pc_control_result received without data.message:', data);
            }
            break;
            
        case 'error':
            showError(data.message);
            break;
            
        case 'typing':
            // Handle typing indicator
            document.getElementById('typing-indicator').style.display = 
                data.is_typing ? 'flex' : 'none';
            break;
            
        default:
            console.log('Unhandled message type:', data.type, data);
    }
}

function sendWebSocketMessage(type, data = {}) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type,
            ...data,
            timestamp: Date.now()
        }));
        return true;
    } else {
        console.warn('WebSocket is not connected');
        return false;
    }
}

function updateUISettings() {
    // Update settings modal
    document.getElementById('voice-gender').value = settings.voiceGender || 'female';
    document.getElementById('language').value = settings.language || 'en';
    document.getElementById('wake-word').value = settings.wakeWord || 'Hey Wolf';
    document.getElementById('always-listen').checked = settings.alwaysListen || false;
    
    // Apply theme
    if (settings.theme) {
        currentTheme = settings.theme;
        applyTheme(currentTheme);
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Settings modal
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    document.getElementById('close-settings').addEventListener('click', closeSettings);
    document.getElementById('save-settings').addEventListener('click', saveSettings);
    
    // Microphone button
    document.getElementById('mic-btn').addEventListener('click', toggleListening);

    // Cancel Action Button listener
    if (cancelActionBtn) {
        cancelActionBtn.addEventListener('click', () => {
            console.log('Cancel Action button clicked. Sending WebSocket message.');
            sendWebSocketMessage('cancel_action_request'); // Directly send over WebSocket
            updateStatus('Cancelling action...'); // Optional: provide immediate UI feedback
        });
    } else {
        console.warn('Cancel Action button not found in the DOM.');
    }
    
    // Quick action buttons (HTML removed, listeners no longer needed)
    // Modal click outside to close
    document.getElementById('settings-modal').addEventListener('click', (e) => {
        if (e.target.id === 'settings-modal') {
            closeSettings();
        }
    });

    // Text command input listeners
    if (sendCommandBtn) {
        sendCommandBtn.addEventListener('click', sendTextCommand);
    } else {
        console.warn('Send command button (#send-command-btn) not found during setupEventListeners.');
    }

    if (commandInput) {
        commandInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) { // Send on Enter
                event.preventDefault(); // Prevent default (e.g., form submission or newline)
                sendTextCommand();
            }
        });
    } else {
        console.warn('Command input field (#command-input) not found during setupEventListeners.');
    }

    // Mode selection buttons
    if (aiModeBtn) {
        aiModeBtn.addEventListener('click', () => setMode('ai'));
    } else {
        console.warn('AI mode button (#ai-mode-btn) not found.');
    }

    if (pcControlModeBtn) {
        pcControlModeBtn.addEventListener('click', () => {
            console.log('[Renderer DEBUG] PC Control Mode button clicked. Calling setMode("pc_control").');
            setMode('pc_control');
        });
    } else {
        console.warn('PC control mode button (#pc-control-mode-btn) not found.');
    }
}

// Python Communication
function setupPythonListeners() {
    window.electronAPI.onPythonMessage((event, data) => {
        try {
            const message = JSON.parse(data.trim());
            handlePythonMessage(message);
        } catch (error) {
            console.log('Python output:', data.trim());
        }
    });
    
    window.electronAPI.onPythonError((event, error) => {
        console.error('Python Error:', error);
        showError('Voice processing error: ' + error);
    });
}

function handlePythonMessage(message) {
    switch (message.type) {
        case 'wake_word_detected':
            handleWakeWordDetected();
            break;
        case 'speech_recognized':
            handleSpeechRecognized(message.data);
            break;
        case 'ai_response':
            handleAIResponse(message.data);
            break;
        case 'command_executed':
            handleCommandExecuted(message.data);
            break;
        case 'error':
            showError(message.data);
            break;
        case 'status':
            updateStatus(message.data);
            break;
        default:
            console.log('Unknown message type:', message.type);
    }
}

// Voice Controller Initialization
async function initializeVoiceController() {
    try {
        // Load the voice controller script
        const script = document.createElement('script');
        script.src = 'voice/voice_controller.js';
        script.type = 'text/javascript';
        
        // Wait for the script to load
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = () => reject(new Error('Failed to load voice controller'));
            document.head.appendChild(script);
        });
        
        // Initialize with settings from the UI or defaults
        voiceController = new VoiceController({
            wakeWord: settings.wakeWord || 'Hey Wolf',
            speech_timeout: 5,
            speech_phrase_limit: 10,
            tts_rate: 200,
            tts_volume: 1.0,
            tts_voice: settings.voiceGender === 'male' ? 'Alex' : 'Samantha'
        });
        
        // Set up event callbacks
        setupVoiceControllerCallbacks();
        
        console.log('Voice controller initialized successfully');
    } catch (error) {
        console.error('Failed to initialize voice controller:', error);
        showError('Failed to initialize voice system: ' + (error.message || 'Unknown error'));
    }
}

// Set up voice controller callbacks
function setupVoiceControllerCallbacks() {
    if (!voiceController) return;
    
    // Wake word detected
    voiceController.register_callback('on_wake', () => {
        console.log('Wake word detected!');
        if (faceAnimations) {
            faceAnimations.startListening();
        }
        updateStatus('Wake word detected, listening...');
    });
    
    // Speech recognized
    voiceController.register_callback('on_speech', (data) => {
        console.log('Speech recognized:', data.text);
        if (data.text) {
            // Process the recognized text as a command
            sendCommand(data.text);
        }
    });
    
    // TTS started
    voiceController.register_callback('on_tts_start', (data) => {
        console.log('TTS started:', data.text);
        if (faceAnimations) {
            faceAnimations.startTalking();
        }
    });
    
    // TTS ended
    voiceController.register_callback('on_tts_end', () => {
        console.log('TTS ended');
        if (faceAnimations) {
            faceAnimations.stopTalking();
        }
    });
    
    // Error occurred
    voiceController.register_callback('on_error', (error) => {
        console.error('Voice system error:', error);
        showError(`Voice error: ${error.message || 'Unknown error'}`);
    });
}

// Voice Control Functions
async function toggleListening() {
    try {
        if (!voiceController) {
            console.error('Voice controller not initialized');
            showError('Voice system not ready');
            return;
        }
        
        // Toggle the listening state
        const newListeningState = !isListening;
        
        // Update the UI immediately for better responsiveness
        updateUIForListening(newListeningState);
        
        // Update face animation based on the new listening state
        if (faceAnimations) {
            if (newListeningState) {
                faceAnimations.startListening();
            } else {
                faceAnimations.stopListening();
            }
        }
        
        // Update the listening state using the voice controller
        voiceController.toggle_listening();
        
        // Update the global state
        isListening = newListeningState;
        
        // Send the state to the backend via WebSocket
        sendWebSocketMessage('toggle-listening', { 
            listening: newListeningState,
            wake_word: settings.wakeWord || 'Hey Wolf'
        });
        
        // Log the state change
        console.log(`Voice input ${newListeningState ? 'started' : 'stopped'}`);
        updateStatus(newListeningState ? 'Listening...' : 'Ready');
        
    } catch (error) {
        console.error('Error in toggleListening:', error);
        showError('Error toggling voice input');
        
        // Reset the UI state on error
        isListening = false;
        updateUIForListening(false);
        if (faceAnimations) {
            faceAnimations.stopListening();
        }
    }
}

async function startListening() {
    if (isListening) return;
    
    isListening = true;
    updateUIForListening(true);
    
    // Update face animation
    if (faceAnimations) {
        faceAnimations.startListening();
    }
    
    // Update microphone button
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.add('listening');
        micBtn.setAttribute('title', 'Listening...');
        // Start audio visualization
        startWaveformAnimation();
    }
    
    try {
        // Notify main process to start listening using the toggle-listening method
        await window.electronAPI.toggleListening(true);
    } catch (error) {
        console.error('Error starting voice input:', error);
        showError('Error starting voice input');
        stopListening();
    }
}

async function stopListening() {
    if (!isListening && !document.getElementById('mic-btn').classList.contains('listening')) return;
    
    isListening = false;
    updateUIForListening(false);
    
    // Update microphone button
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        micBtn.classList.remove('listening');
        micBtn.setAttribute('title', 'Start Listening');
    }
    
    // Stop audio visualization
    stopWaveformAnimation();
    
    try {
        // Notify main process to stop listening
        await window.electronAPI.toggleListening(false);
        
        // Send stop listening command to backend
        sendWebSocketMessage('stop_listening');
        
        // Reset face animation if available
        if (faceAnimations) {
            faceAnimations.stopListening();
            faceAnimations.setEmotion('neutral');
        }
    } catch (error) {
        console.error('Error stopping voice input:', error);
        showError('Error stopping voice input');
    }
}

async function sendCommand(command) {
    if (!command || typeof command !== 'string' || command.trim() === '') {
        console.warn('Attempted to send empty or invalid command');
        return false;
    }
    
    try {
        // Add user message to chat
        addMessageToChat('user', command);
        
        // Show typing indicator
        document.getElementById('typing-indicator').style.display = 'flex';
        
        // Scroll to bottom of chat
        const chatContainer = document.querySelector('.chat-messages');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Send command to backend
        const success = sendWebSocketMessage('process_text', { 
            text: command,
            timestamp: new Date().toISOString()
        });
        
        if (!success) {
            throw new Error('Failed to send command to server');
        }
        
        return true;
        
    } catch (error) {
        console.error('Error sending command:', error);
        showError('Failed to send command. Please try again.');
        return false;
    }

}

function setMode(newMode) {
    currentMode = newMode;
    console.log(`Mode set to: ${currentMode}`);

    if (aiModeBtn && pcControlModeBtn) {
        aiModeBtn.classList.toggle('active', newMode === 'ai');
        pcControlModeBtn.classList.toggle('active', newMode === 'pc_control');
    }

    if (commandInput && sendCommandBtn) {
        commandInput.disabled = false;
        sendCommandBtn.disabled = false;
        commandInput.placeholder = 'Type command (AI or PC)...';
    }

    // Notify backend of mode change
    console.log(`[Renderer DEBUG] In setMode('${newMode}'), about to send WebSocket message. Socket state: ${socket ? socket.readyState : 'null'}`);
    if (socket && socket.readyState === WebSocket.OPEN) {
        sendWebSocketMessage('set_operation_mode', { mode: currentMode });
    } else {
        console.error(`[Renderer ERROR] WebSocket not open or not initialized when trying to set mode to ${newMode}. State: ${socket ? socket.readyState : 'null'}`);
        // Optionally, try to queue the message or re-establish connection if appropriate
    }
    updateStatus(currentMode === 'ai' ? 'AI Mode: Ready' : 'PC Control Mode: Ready');
}

function sendTextCommand() {
    if (!commandInput) {
        console.warn('Command input field not available for sendTextCommand.');
        return;
    }
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.error('Cannot send text command: WebSocket not ready.');
        addMessageToChat('assistant', '⚠️ Error: Not connected to the server. Please wait or try restarting.');
        return;
    }

    const text = commandInput.value.trim();
    if (text) { // Allow sending in any mode, backend will handle routing
        addMessageToChat('user', text); // Display user's typed message in chat
        sendWebSocketMessage('text_command', { command: text }); // Send to backend
        commandInput.value = ''; // Clear the input field
        commandInput.focus(); // Keep focus on input for easy next command
        scrollToBottom(); // Scroll chat to the new message
    }
}

// Message Handlers
function handleWakeWordDetected() {
    if (!isListening) {
        startListening();
    }
    
    // Visual feedback
    const micBtn = document.getElementById('mic-btn');
    const statusText = document.getElementById('status-text');
    
    micBtn.classList.add('listening');
    statusText.textContent = 'Listening...';
    
    // Start waveform animation
    startWaveformAnimation();
    
    // Show visual feedback
    const wakeFeedback = document.createElement('div');
    wakeFeedback.className = 'wake-feedback';
    wakeFeedback.innerHTML = '<i data-feather="zap" class="pulse"></i>';
    document.body.appendChild(wakeFeedback);
    
    // Remove feedback after animation
    setTimeout(() => {
        wakeFeedback.remove();
    }, 2000);
}

/**
 * Handles recognized speech from the voice recognition system
 * @param {Object} data - The recognized speech data
 * @param {string} data.text - The recognized text
 * @param {number} data.confidence - The confidence score (0-1) of the recognition
 * @param {number} data.timestamp - When the speech was recognized
 */
function handleSpeechRecognized(data) {
    if (!data || !data.text) {
        console.warn('Received empty or invalid speech recognition data:', data);
        return;
    }

    console.log('[DEBUG] Speech recognized:', data.text);
    
    // Add visual feedback for recognized speech
    const recognitionFeedback = document.createElement('div');
    recognitionFeedback.className = 'recognition-feedback';
    recognitionFeedback.innerHTML = `
        <div class="recognition-text">
            <i class="feather icon-mic" style="color: #4CAF50;"></i>
            <span>Recognized: "${escapeHtml(data.text)}"</span>
        </div>
    `;
    
    // Add to chat container with animation
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.appendChild(recognitionFeedback);
    
    // Scroll to show the new message
    setTimeout(() => {
        recognitionFeedback.style.opacity = '1';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 10);
    
    // Add the actual message to chat
    addMessageToChat('user', data.text, data.timestamp ? new Date(data.timestamp) : new Date());
    
    // If always listen is enabled, keep listening
    if (settings.alwaysListen) {
        setTimeout(() => {
            if (isListening) {
                console.log('[DEBUG] Re-starting listening (alwaysListen is true)');
                sendWebSocketMessage('start_listening');
            }
        }, 500);
    }
    
    // Process the command if we're in PC control mode
    if (currentMode === 'pc_control' && data.text.trim()) {
        console.log('[DEBUG] Sending command to backend:', data.text);
        sendCommand(data.text);
    }
}

function handleAIResponse(data) {
    const { response, isFinal, emotion } = data;
    try {
        showLoading(false);
        
        if (!data || !data.text) {
            throw new Error('Invalid response format');
        }
        
        // Add AI response to chat
        addMessageToChat('assistant', data.text);
        
        // If this is a command response, handle it
        if (data.is_command && data.command_type) {
            handleCommandExecuted({
                success: true,
                command: data.command_type,
                message: data.text
            });
        }
        
    } catch (error) {
        console.error('Error handling AI response:', error);
        showError('Failed to process AI response');
    }
}

// Chat Functions
function scrollToBottom() {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        // Use requestAnimationFrame for smooth scrolling
        requestAnimationFrame(() => {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        });
    }
}

function addMessageToChat(sender, text, timestamp = new Date()) {
    try {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return null;
        
        // Remove welcome message if it exists and this is the first user message
        if (sender === 'user') {
            const welcomeMessage = chatMessages.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
        }
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        // Format timestamp
        const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Create avatar based on sender
        let avatar = '';
        if (sender === 'assistant') {
            avatar = `
                <div class="message-avatar assistant-avatar">
                    <i data-feather="zap"></i>
                </div>`;
        } else {
            avatar = `
                <div class="message-avatar user-avatar">
                    <i data-feather="user"></i>
                </div>`;
        }
        
        // Set message content with markdown support
        const formattedText = formatMessageText(text);
        
        messageElement.innerHTML = `
            ${avatar}
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${sender === 'user' ? 'You' : 'Wolf AI'}</span>
                    <span class="message-time">${timeString}</span>
                </div>
                <div class="message-text">${formattedText}</div>
            </div>
        `;
        
        // Add to chat
        chatMessages.appendChild(messageElement);
        
        // Refresh feather icons for any new ones
        feather.replace();
        
        // Scroll to bottom after the message is fully rendered
        setTimeout(scrollToBottom, 10);
        
        return messageElement;
        
    } catch (error) {
        console.error('Error adding message to chat:', error);
        return null;
    }
}

function formatMessageText(text) {
    if (!text) return '';
    
    // Simple markdown formatting
    let formatted = escapeHtml(text);
    
    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic: *text* or _text_
    formatted = formatted.replace(/(?:\*|_)(.*?)(?:\*|_)/g, '<em>$1</em>');
    
    // Code: `code`
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Links: [text](url)
    formatted = formatted.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Audio Visualization
function setupAudioVisualization() {
    const canvas = document.getElementById('waveform');
    const ctx = canvas.getContext('2d');
    
    // Create a simple animated waveform
    function drawWaveform() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (!isListening) {
            // Draw flat line when not listening
            ctx.strokeStyle = getComputedStyle(document.documentElement)
                .getPropertyValue('--muted-foreground').replace(/hsl\((.*)\)/, 'hsl($1, 0.3)');
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
            return;
        }
        
        // Animated waveform when listening
        const time = Date.now() * 0.005;
        const amplitude = 20;
        const frequency = 0.02;
        
        ctx.strokeStyle = getComputedStyle(document.documentElement)
            .getPropertyValue('--primary').replace(/hsl\((.*)\)/, 'hsl($1)');
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        for (let x = 0; x < canvas.width; x++) {
            const y = canvas.height / 2 + 
                     Math.sin(x * frequency + time) * amplitude * 
                     Math.sin(x * 0.01 + time * 0.5);
            if (x === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }
    
    // Start animation loop
    function animate() {
        drawWaveform();
        waveformAnimationId = requestAnimationFrame(animate);
    }
    animate();
}

function startWaveformAnimation() {
    // Animation is already running, just need to update the isListening state
}

function stopWaveformAnimation() {
    // Animation continues running, just changes appearance based on isListening
}

// Settings Functions
async function loadSettings() {
    try {
        settings = await window.electronAPI.getSettings();
        currentTheme = settings.theme || 'dark';
        
        // Update UI with settings
        document.getElementById('voice-gender').value = settings.voiceGender || 'female';
        document.getElementById('language').value = settings.language || 'en';
        document.getElementById('wake-word').value = settings.wakeWord || 'Hey Wolf';
        document.getElementById('always-listen').checked = settings.alwaysListen || false;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function openSettings() {
    document.getElementById('settings-modal').classList.add('show');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.remove('show');
}

async function saveSettings() {
    const newSettings = {
        theme: currentTheme,
        voiceGender: document.getElementById('voice-gender').value,
        language: document.getElementById('language').value,
        wakeWord: document.getElementById('wake-word').value,
        alwaysListen: document.getElementById('always-listen').checked
    };
    
    try {
        const result = await window.electronAPI.saveSettings(newSettings);
        if (result.success) {
            settings = newSettings;
            closeSettings();
            showSuccess('Settings saved successfully!');
        } else {
            showError(result.error);
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showError('Failed to save settings');
    }
}

// Theme Functions
function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(currentTheme);
}

/**
 * Updates the UI to reflect the current listening state
 * @param {boolean} isListening - Whether the app is currently listening for voice input
 */
function updateUIForListening(isListening) {
    const micBtn = document.getElementById('mic-btn');
    if (!micBtn) return;
    
    // Update the microphone button state
    if (isListening) {
        micBtn.classList.add('listening');
        micBtn.setAttribute('title', 'Stop Listening');
        startWaveformAnimation();
    } else {
        micBtn.classList.remove('listening');
        micBtn.setAttribute('title', 'Start Listening');
        stopWaveformAnimation();
    }
    
    // Update the global state
    isListening = isListening;
    
    // Log the state change
    console.log(`Voice input ${isListening ? 'started' : 'stopped'}`);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const themeIcon = document.querySelector('#theme-toggle i');
    if (theme === 'dark') {
        themeIcon.setAttribute('data-feather', 'sun');
    } else {
        themeIcon.setAttribute('data-feather', 'moon');
    }
    feather.replace();
}

// Utility Functions
function updateStatus(status) {
    const statusText = document.getElementById('status-text');
    statusText.textContent = status;
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function showError(message) {
    addMessageToChat('assistant', `❌ Error: ${message}`);
}

function showSuccess(message) {
    addMessageToChat('assistant', `✅ ${message}`);
}
