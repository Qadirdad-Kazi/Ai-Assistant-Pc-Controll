import { useSettings } from '@/contexts/settings-context';

// Default settings that match the SettingsState interface
export const defaultSettings = {
  // Voice Settings
  voiceEnabled: true,
  autoSpeak: true,
  volume: [80],
  micSensitivity: [70],
  
  // AI Settings
  model: 'llama3.2:latest',
  
  // Appearance Settings
  theme: 'system',
  accentColor: 'blue',
  uiDensity: 'normal',
  fontFamily: 'sans',
  fontSize: 16,
  lineHeight: 1.5,
  roundedCorners: true,
  borderRadius: 0.5,
  animations: true,
  reduceMotion: false,
};

// Helper hook to safely use settings context
export function useSafeSettings() {
  try {
    const context = useSettings();
    // If we get here, the context is available
    return {
      ...context,
      isInitialized: true,
    };
  } catch (error) {
    // Return default values if context is not available
    return {
      settings: defaultSettings,
      isInitialized: true, // Set to true to prevent infinite loading
      setSettings: (newSettings: any) => {
        console.warn('Settings context not available, cannot save settings');
      },
    };
  }
}
