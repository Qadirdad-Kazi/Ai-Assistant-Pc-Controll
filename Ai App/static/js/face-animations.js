/**
 * FaceAnimations - Controls the animated face and emotions for the AI assistant
 */
class FaceAnimations {
    constructor() {
        this.faceElement = document.getElementById('assistant-face');
        this.statusElement = document.getElementById('assistant-status');
        this.currentEmotion = 'neutral';
        this.emotionTimeout = null;
        
        // Initialize the face
        this.init();
    }
    
    init() {
        if (!this.faceElement) {
            console.error('Face element not found');
            return;
        }
        
        // Set initial state
        this.setEmotion('neutral');
        this.setStatus('Ready');
    }
    
    /**
     * Set the current emotion of the face
     * @param {string} emotion - The emotion to display (neutral, happy, sad, surprised, thinking, listening)
     * @param {number} duration - Optional duration in ms before returning to neutral
     */
    setEmotion(emotion, duration = null) {
        if (!this.faceElement) return;
        
        // Clear any existing timeouts
        if (this.emotionTimeout) {
            clearTimeout(this.emotionTimeout);
            this.emotionTimeout = null;
        }
        
        // Remove all emotion classes
        const emotions = ['neutral', 'happy', 'sad', 'surprised', 'thinking', 'listening'];
        this.faceElement.classList.remove(...emotions);
        
        // Add the new emotion class
        this.faceElement.classList.add(emotion);
        this.currentEmotion = emotion;
        
        // Set a timeout to return to neutral if duration is specified
        if (duration && emotion !== 'neutral') {
            this.emotionTimeout = setTimeout(() => {
                this.setEmotion('neutral');
            }, duration);
        }
    }
    
    /**
     * Set the status text below the face
     * @param {string} text - The status text to display
     */
    setStatus(text) {
        if (this.statusElement) {
            this.statusElement.textContent = text;
        }
    }
    
    /**
     * Animate a blink
     */
    blink() {
        if (this.currentEmotion !== 'neutral') return;
        
        this.faceElement.classList.add('blinking');
        setTimeout(() => {
            this.faceElement.classList.remove('blinking');
        }, 200);
    }
    
    /**
     * Start listening animation
     */
    startListening() {
        this.setEmotion('listening');
        this.setStatus('Listening...');
    }
    
    /**
     * Stop listening animation
     */
    stopListening() {
        this.setEmotion('neutral');
        this.setStatus('Ready');
    }
    
    /**
     * Show thinking animation
     */
    startThinking() {
        this.setEmotion('thinking');
        this.setStatus('Thinking...');
    }
    
    /**
     * Stop thinking animation
     */
    stopThinking() {
        this.setEmotion('neutral');
        this.setStatus('Ready');
    }
    
    /**
     * Show happy expression
     * @param {number} duration - How long to show the expression in ms
     */
    showHappy(duration = 2000) {
        this.setEmotion('happy', duration);
        this.setStatus('Happy to help!');
    }
    
    /**
     * Show sad expression
     * @param {number} duration - How long to show the expression in ms
     */
    showSad(duration = 2000) {
        this.setEmotion('sad', duration);
        this.setStatus('I\'m sorry about that...');
    }
    
    /**
     * Show surprised expression
     * @param {number} duration - How long to show the expression in ms
     */
    showSurprised(duration = 1500) {
        this.setEmotion('surprised', duration);
        this.setStatus('Oh!');
    }
    
    /**
     * Initialize random blinking
     */
    initRandomBlinking() {
        const randomBlink = () => {
            if (this.currentEmotion === 'neutral') {
                this.blink();
            }
            // Random time between 2-5 seconds
            const nextBlink = 2000 + Math.random() * 3000;
            setTimeout(randomBlink, nextBlink);
        };
        
        // Start the blinking loop
        setTimeout(randomBlink, 3000); // Initial delay before first blink
    }
}

// Initialize the face animations when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.assistantFace = new FaceAnimations();
    window.assistantFace.initRandomBlinking();
});
