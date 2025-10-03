class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
        
        // Load notification styles
        this.loadStyles();
        
        // Audio context for sound feedback
        this.audioContext = null;
        this.initializeAudio();
        
        // Notification queue
        this.queue = [];
        this.isProcessingQueue = false;
    }
    
    loadStyles() {
        // Check if styles are already loaded
        if (document.getElementById('notification-styles')) return;
        
        const link = document.createElement('link');
        link.id = 'notification-styles';
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = 'static/css/notifications.css';
        document.head.appendChild(link);
    }
    
    initializeAudio() {
        try {
            // Create audio context for sound feedback
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.audioContext = new AudioContext();
            }
        } catch (e) {
            console.warn('Web Audio API not supported in this browser');
        }
    }
    
    playSound(type) {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        // Configure sound based on notification type
        switch(type) {
            case 'success':
                oscillator.frequency.setValueAtTime(523.25, this.audioContext.currentTime); // C5
                oscillator.frequency.exponentialRampToValueAtTime(659.25, this.audioContext.currentTime + 0.2); // E5
                break;
            case 'error':
                oscillator.frequency.setValueAtTime(440, this.audioContext.currentTime); // A4
                oscillator.frequency.setValueAtTime(349.23, this.audioContext.currentTime + 0.1); // F4
                break;
            case 'warning':
                oscillator.frequency.setValueAtTime(392, this.audioContext.currentTime); // G4
                oscillator.frequency.setValueAtTime(493.88, this.audioContext.currentTime + 0.1); // B4
                break;
            case 'info':
            default:
                oscillator.frequency.setValueAtTime(440, this.audioContext.currentTime); // A4
                break;
        }
        
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + 0.5);
    }
    
    showNotification(options) {
        const defaultOptions = {
            title: '',
            message: '',
            type: 'info', // success, error, warning, info
            duration: 5000, // ms
            sound: true,
            icon: null,
            onClick: null,
            onClose: null
        };
        
        const notification = { ...defaultOptions, ...options };
        this.queue.push(notification);
        this.processQueue();
    }
    
    processQueue() {
        if (this.isProcessingQueue || this.queue.length === 0) return;
        
        this.isProcessingQueue = true;
        const notification = this.queue.shift();
        
        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.className = `notification ${notification.type}`;
        notificationEl.setAttribute('role', 'alert');
        notificationEl.setAttribute('aria-live', 'polite');
        
        // Add icon based on type if not provided
        let icon = notification.icon;
        if (!icon) {
            switch(notification.type) {
                case 'success':
                    icon = 'check-circle';
                    break;
                case 'error':
                    icon = 'alert-circle';
                    break;
                case 'warning':
                    icon = 'alert-triangle';
                    break;
                case 'info':
                default:
                    icon = 'info';
            }
        }
        
        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'notification-close';
        closeButton.setAttribute('aria-label', 'Close notification');
        closeButton.innerHTML = '<i data-feather="x"></i>';
        closeButton.addEventListener('click', () => this.closeNotification(notificationEl, notification));
        
        // Create progress bar
        const progressBar = document.createElement('div');
        progressBar.className = 'notification-progress';
        
        // Create sound wave animation if sound is enabled
        let soundWave = '';
        if (notification.sound) {
            soundWave = `
                <div class="sound-wave">
                    <span></span>
                    <span></span>
                    <span></span>
                    <span></span>
                </div>`;
        }
        
        // Set notification content
        notificationEl.innerHTML = `
            <i class="notification-icon" data-feather="${icon}"></i>
            <div class="notification-content">
                <div class="notification-title">${notification.title}</div>
                <div class="notification-message">${notification.message}</div>
            </div>
            ${soundWave}
        `;
        
        notificationEl.appendChild(closeButton);
        notificationEl.appendChild(progressBar);
        
        // Add click handler if provided
        if (typeof notification.onClick === 'function') {
            notificationEl.style.cursor = 'pointer';
            notificationEl.addEventListener('click', (e) => {
                if (e.target !== closeButton) {
                    notification.onClick(e);
                }
            });
        }
        
        // Add to DOM
        this.container.appendChild(notificationEl);
        
        // Refresh Feather icons
        if (window.feather) {
            window.feather.replace({ 'aria-hidden': 'true' });
        }
        
        // Trigger animation
        requestAnimationFrame(() => {
            notificationEl.classList.add('show');
            
            // Play sound if enabled
            if (notification.sound) {
                this.playSound(notification.type);
            }
            
            // Auto-close after duration
            if (notification.duration > 0) {
                const startTime = Date.now();
                const endTime = startTime + notification.duration;
                
                const updateProgress = () => {
                    const remaining = endTime - Date.now();
                    const progress = Math.max(0, remaining / notification.duration);
                    
                    if (progress <= 0) {
                        this.closeNotification(notificationEl, notification);
                        return;
                    }
                    
                    progressBar.style.transform = `scaleX(${progress})`;
                    this.progressAnimationId = requestAnimationFrame(updateProgress);
                };
                
                this.progressAnimationId = requestAnimationFrame(updateProgress);
                
                // Pause on hover
                notificationEl.addEventListener('mouseenter', () => {
                    if (this.progressAnimationId) {
                        cancelAnimationFrame(this.progressAnimationId);
                        this.progressAnimationId = null;
                    }
                });
                
                notificationEl.addEventListener('mouseleave', () => {
                    if (!this.progressAnimationId) {
                        endTime = Date.now() + (notification.duration * progress);
                        updateProgress();
                    }
                });
            }
            
            // Mark as processed
            this.isProcessingQueue = false;
            this.processQueue();
        });
    }
    
    closeNotification(notificationEl, notification) {
        if (this.progressAnimationId) {
            cancelAnimationFrame(this.progressAnimationId);
            this.progressAnimationId = null;
        }
        
        notificationEl.classList.remove('show');
        notificationEl.classList.add('hide');
        
        // Call onClose callback if provided
        if (typeof notification.onClose === 'function') {
            notification.onClose();
        }
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (notificationEl.parentNode === this.container) {
                this.container.removeChild(notificationEl);
            }
        }, 300);
    }
    
    // Helper methods for different notification types
    success(title, message, options = {}) {
        this.showNotification({
            title,
            message,
            type: 'success',
            duration: 3000,
            ...options
        });
    }
    
    error(title, message, options = {}) {
        this.showNotification({
            title,
            message,
            type: 'error',
            duration: 5000,
            ...options
        });
    }
    
    warning(title, message, options = {}) {
        this.showNotification({
            title,
            message,
            type: 'warning',
            duration: 4000,
            ...options
        });
    }
    
    info(title, message, options = {}) {
        this.showNotification({
            title,
            message,
            type: 'info',
            duration: 3000,
            ...options
        });
    }
}

// Create global instance
window.notifications = new NotificationManager();
