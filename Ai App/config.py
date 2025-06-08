"""
Configuration Module
Handles configuration settings and environment variables for Wolf AI Assistant
"""

import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.config_dir = Path.home() / '.wolf_ai'
        self.config_file = self.config_dir / 'config.json'
        self.ensure_config_dir()
        self.load_config()

    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config()

    def get_default_config(self):
        """Get default configuration settings"""
        return {
            # Audio settings
            'audio': {
                'sample_rate': 16000,
                'chunk_size': 1024,
                'channels': 1,
                'energy_threshold': 300,
                'pause_threshold': 0.8,
                'phrase_threshold': 0.3
            },
            
            # Wake word settings
            'wake_word': {
                'enabled': True,
                'sensitivity': 0.7,
                'words': ['hey wolf', 'hi wolf', 'hello wolf', 'ok wolf']
            },
            
            # Voice settings
            'voice': {
                'gender': 'female',
                'rate': 180,
                'volume': 0.8,
                'language': 'en'
            },
            
            # AI settings
            'ai': {
                'model': 'llama2',
                'temperature': 0.7,
                'max_tokens': 200,
                'timeout': 30
            },
            
            # Database settings
            'database': {
                'path': str(self.config_dir / 'wolf_ai.db'),
                'backup_days': 30,
                'auto_cleanup_days': 90
            },
            
            # UI settings
            'ui': {
                'theme': 'dark',
                'window_width': 1200,
                'window_height': 800,
                'always_on_top': False
            },
            
            # System settings
            'system': {
                'auto_start': False,
                'minimize_to_tray': True,
                'enable_logging': True,
                'log_level': 'INFO'
            },
            
            # Security settings
            'security': {
                'require_confirmation_for_system_commands': True,
                'allowed_system_commands': [
                    'open_app', 'close_window', 'volume_control', 
                    'screenshot', 'media_control', 'time_date'
                ],
                'blocked_system_commands': [
                    'shutdown', 'restart', 'delete_files', 'format_drive'
                ]
            }
        }

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Get configuration value using dot notation (e.g., 'audio.sample_rate')"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key, value):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.save_config()

    def get_env_or_config(self, env_key, config_key, default=None):
        """Get value from environment variable first, then config, then default"""
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        config_value = self.get(config_key)
        if config_value is not None:
            return config_value
        
        return default

    def update_config(self, updates):
        """Update multiple configuration values"""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, updates)
        self.save_config()

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.get_default_config()
        self.save_config()

    def get_database_path(self):
        """Get database file path"""
        return self.get('database.path', str(self.config_dir / 'wolf_ai.db'))

    def get_log_path(self):
        """Get log file path"""
        return str(self.config_dir / 'wolf_ai.log')

    def get_audio_settings(self):
        """Get audio configuration as dictionary"""
        return self.get('audio', {})

    def get_wake_word_settings(self):
        """Get wake word configuration"""
        return self.get('wake_word', {})

    def get_voice_settings(self):
        """Get voice configuration"""
        return self.get('voice', {})

    def get_ai_settings(self):
        """Get AI configuration"""
        return self.get('ai', {})

    def get_security_settings(self):
        """Get security configuration"""
        return self.get('security', {})

    def is_system_command_allowed(self, command_type):
        """Check if a system command type is allowed"""
        allowed = self.get('security.allowed_system_commands', [])
        blocked = self.get('security.blocked_system_commands', [])
        
        if command_type in blocked:
            return False
        
        return command_type in allowed or len(allowed) == 0

    def get_ollama_settings(self):
        """Get Ollama-specific settings"""
        return {
            'url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'model': os.getenv('OLLAMA_MODEL', self.get('ai.model', 'llama2')),
            'temperature': self.get('ai.temperature', 0.7),
            'max_tokens': self.get('ai.max_tokens', 200),
            'timeout': self.get('ai.timeout', 30)
        }

    def validate_config(self):
        """Validate configuration and return any issues"""
        issues = []
        
        # Check required directories
        if not self.config_dir.exists():
            issues.append("Configuration directory does not exist")
        
        # Check database path
        db_path = Path(self.get_database_path())
        if not db_path.parent.exists():
            issues.append("Database directory does not exist")
        
        # Check audio settings
        audio_settings = self.get_audio_settings()
        if audio_settings.get('sample_rate', 0) < 8000:
            issues.append("Audio sample rate too low")
        
        # Check wake word settings
        wake_word_settings = self.get_wake_word_settings()
        if not wake_word_settings.get('words'):
            issues.append("No wake words configured")
        
        return issues

    def __str__(self):
        """String representation of config"""
        return json.dumps(self.config, indent=2)

# Test configuration
if __name__ == "__main__":
    config = Config()
    
    print("Configuration loaded:")
    print(f"Database path: {config.get_database_path()}")
    print(f"Log path: {config.get_log_path()}")
    print(f"Wake words: {config.get('wake_word.words')}")
    print(f"Voice gender: {config.get('voice.gender')}")
    print(f"Theme: {config.get('ui.theme')}")
    
    # Test validation
    issues = config.validate_config()
    if issues:
        print(f"\nConfiguration issues: {issues}")
    else:
        print("\nConfiguration is valid")
    
    # Test environment override
    ollama_settings = config.get_ollama_settings()
    print(f"\nOllama settings: {ollama_settings}")
