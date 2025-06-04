// Global state
let isListening = false;
let currentTheme = 'dark';
let settings = {};
let audioContext;
let analyser;
let dataArray;
let waveformAnimationId;

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Feather icons
    feather.replace();
    
    // Load settings
    await loadSettings();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup audio visualization
    setupAudioVisualization();
    
    // Setup Python message listeners
    setupPythonListeners();
    
    // Apply theme
    applyTheme(currentTheme);
    
    console.log('Wolf AI Assistant initialized');
});

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
    
    // Quick action buttons
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const command = e.currentTarget.dataset.command;
            if (command) {
                sendCommand(command);
            }
        });
    });
    
    // Modal click outside to close
    document.getElementById('settings-modal').addEventListener('click', (e) => {
        if (e.target.id === 'settings-modal') {
            closeSettings();
        }
    });
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

// Voice Control Functions
async function toggleListening() {
    isListening = !isListening;
    const micBtn = document.getElementById('mic-btn');
    const statusText = document.getElementById('status-text');
    
    if (isListening) {
        micBtn.classList.add('listening');
        statusText.textContent = 'Listening...';
        startWaveformAnimation();
    } else {
        micBtn.classList.remove('listening');
        statusText.textContent = 'Ready';
        stopWaveformAnimation();
    }
    
    try {
        const result = await window.electronAPI.toggleListening(isListening);
        if (!result.success) {
            showError(result.error);
            isListening = false;
            micBtn.classList.remove('listening');
            statusText.textContent = 'Ready';
        }
    } catch (error) {
        console.error('Error toggling listening:', error);
        showError('Failed to toggle listening');
    }
}

async function sendCommand(command) {
    addMessageToChat('user', command);
    showLoading(true);
    
    try {
        const result = await window.electronAPI.sendCommand(command);
        if (!result.success) {
            showError(result.error);
        }
    } catch (error) {
        console.error('Error sending command:', error);
        showError('Failed to send command');
    } finally {
        showLoading(false);
    }
}

// Message Handlers
function handleWakeWordDetected() {
    const statusText = document.getElementById('status-text');
    statusText.textContent = 'Wake word detected!';
    
    // Auto-start listening
    if (!isListening) {
        toggleListening();
    }
}

function handleSpeechRecognized(data) {
    const { text } = data;
    addMessageToChat('user', text);
    updateStatus('Processing...');
}

function handleAIResponse(data) {
    const { text, type } = data;
    addMessageToChat('assistant', text);
    updateStatus('Ready');
    showLoading(false);
}

function handleCommandExecuted(data) {
    const { command, result, success } = data;
    if (success) {
        addMessageToChat('assistant', `✅ ${result}`);
    } else {
        addMessageToChat('assistant', `❌ Failed to execute: ${result}`);
    }
    updateStatus('Ready');
    showLoading(false);
}

// Chat Functions
function addMessageToChat(sender, text) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            ${sender === 'user' ? '<i data-feather="user"></i>' : '<i data-feather="zap"></i>'}
        </div>
        <div class="message-bubble">
            <div class="message-text">${escapeHtml(text)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    chatMessages.appendChild(messageDiv);
    feather.replace();
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
