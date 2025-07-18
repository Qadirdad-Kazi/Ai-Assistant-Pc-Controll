/**
 * Voice Controller for Wolf AI Assistant (JavaScript Version)
 * Manages voice input/output and wake word detection
 */

class VoiceController {
    /**
     * Initialize the voice controller
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        // Default settings
        this.settings = {
            wakeWord: options.wakeWord || 'hey wolf',
            speechTimeout: options.speech_timeout || 5,
            speechPhraseLimit: options.speech_phrase_limit || 10,
            ttsRate: options.tts_rate || 200,
            ttsVolume: options.tts_volume || 1.0,
            ttsVoice: options.tts_voice || null
        };

        // State
        this.isListening = false;
        this.isInitialized = false;
        this.callbacks = {
            on_wake: [],
            on_speech: [],
            on_tts_start: [],
            on_tts_end: [],
            on_error: []
        };

        // WebSocket connection
        this.ws = null;
        this.wsUrl = 'ws://localhost:5001';

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the voice controller
     */
    async initialize() {
        try {
            // Check for Web Speech API support
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                throw new Error('Speech recognition not supported in this browser');
            }

            // Set up WebSocket connection
            this.setupWebSocket();

            // Set up speech recognition
            this.setupSpeechRecognition();

            // Set up text-to-speech
            this.setupTextToSpeech();

            this.isInitialized = true;
            console.log('Voice controller initialized');
        } catch (error) {
            console.error('Error initializing voice controller:', error);
            this.triggerCallback('on_error', { error: error.message });
        }
    }

    /**
     * Set up WebSocket connection to backend
     */
    setupWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected to voice backend');
                // Send initialization message
                this.sendWebSocketMessage('init', {
                    wakeWord: this.settings.wakeWord,
                    speechTimeout: this.settings.speechTimeout,
                    speechPhraseLimit: this.settings.speechPhraseLimit
                });
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket connection closed');
                // Try to reconnect after a delay
                setTimeout(() => this.setupWebSocket(), 3000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.triggerCallback('on_error', { error: 'WebSocket connection error' });
            };
        } catch (error) {
            console.error('Error setting up WebSocket:', error);
            this.triggerCallback('on_error', { error: 'Failed to connect to voice backend' });
        }
    }

    /**
     * Set up speech recognition
     */
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            const transcript = event.results[event.results.length - 1][0].transcript;
            if (transcript.trim().toLowerCase().includes(this.settings.wakeWord.toLowerCase())) {
                this.triggerCallback('on_wake');
            } else {
                this.triggerCallback('on_speech', { text: transcript });
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.triggerCallback('on_error', { error: `Speech recognition error: ${event.error}` });
        };
    }

    /**
     * Set up text-to-speech
     */
    setupTextToSpeech() {
        if (!('speechSynthesis' in window)) {
            throw new Error('Text-to-speech not supported in this browser');
        }
        
        this.synth = window.speechSynthesis;
        this.utterance = new SpeechSynthesisUtterance();
        
        this.utterance.onstart = () => {
            this.triggerCallback('on_tts_start', { text: this.utterance.text });
        };
        
        this.utterance.onend = () => {
            this.triggerCallback('on_tts_end');
        };
        
        this.utterance.onerror = (event) => {
            console.error('TTS error:', event);
            this.triggerCallback('on_error', { error: 'Text-to-speech error' });
        };
    }

    /**
     * Toggle listening state
     */
    toggle_listening() {
        if (!this.isInitialized) {
            console.error('Voice controller not initialized');
            return false;
        }

        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
        
        return this.isListening;
    }

    /**
     * Start listening for voice input
     */
    startListening() {
        if (this.isListening || !this.recognition) return;
        
        try {
            this.recognition.start();
            this.isListening = true;
            console.log('Started listening for voice input');
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.triggerCallback('on_error', { error: 'Failed to start listening' });
        }
    }

    /**
     * Stop listening for voice input
     */
    stopListening() {
        if (!this.isListening || !this.recognition) return;
        
        try {
            this.recognition.stop();
            this.isListening = false;
            console.log('Stopped listening for voice input');
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }

    /**
     * Speak text using text-to-speech
     * @param {string} text - The text to speak
     */
    speak(text) {
        if (!this.synth || !this.utterance) {
            console.error('Text-to-speech not available');
            return;
        }
        
        try {
            // Cancel any ongoing speech
            this.synth.cancel();
            
            // Set up the utterance
            this.utterance.text = text;
            this.utterance.rate = this.settings.ttsRate / 100;
            this.utterance.volume = this.settings.ttsVolume;
            
            // Set voice if available
            if (this.settings.ttsVoice) {
                const voices = this.synth.getVoices();
                const voice = voices.find(v => v.name === this.settings.ttsVoice);
                if (voice) {
                    this.utterance.voice = voice;
                }
            }
            
            // Speak
            this.synth.speak(this.utterance);
        } catch (error) {
            console.error('Error in text-to-speech:', error);
            this.triggerCallback('on_error', { error: 'Failed to speak text' });
        }
    }

    /**
     * Register a callback for voice events
     * @param {string} event - Event name ('on_wake', 'on_speech', 'on_tts_start', 'on_tts_end', 'on_error')
     * @param {Function} callback - Callback function
     */
    register_callback(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        } else {
            console.warn(`Unknown event type: ${event}`);
        }
    }

    /**
     * Trigger callbacks for an event
     * @private
     */
    triggerCallback(event, data = {}) {
        if (!this.callbacks[event]) return;
        
        this.callbacks[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in ${event} callback:`, error);
            }
        });
    }

    /**
     * Send a message via WebSocket
     * @private
     */
    sendWebSocketMessage(type, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...data }));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    /**
     * Handle incoming WebSocket messages
     * @private
     */
    handleWebSocketMessage(message) {
        if (!message || !message.type) return;

        switch (message.type) {
            case 'wake_word_detected':
                this.triggerCallback('on_wake');
                break;
            case 'speech_recognized':
                this.triggerCallback('on_speech', { text: message.text });
                break;
            case 'tts_start':
                this.triggerCallback('on_tts_start', { text: message.text });
                break;
            case 'tts_end':
                this.triggerCallback('on_tts_end');
                break;
            case 'error':
                this.triggerCallback('on_error', { error: message.error });
                break;
            default:
                console.warn('Unknown message type:', message.type);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceController;
}
