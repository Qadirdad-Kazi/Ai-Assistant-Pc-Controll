import React, { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'light' | 'dark' | 'system' | 'jarvis' | 'contrast' | 'blue-light';

export interface SettingsState {
  // Voice Settings
  voiceEnabled: boolean;
  autoSpeak: boolean;
  volume: number[];
  micSensitivity: number[];
  
  // AI Settings
  model: string;
  
  // Appearance Settings
  theme: Theme;
  accentColor: string;
  uiDensity: string;
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
  roundedCorners: boolean;
  borderRadius: number;
  animations: boolean;
  reduceMotion: boolean;
}

type SettingsContextType = {
  settings: SettingsState;
  setSettings: React.Dispatch<React.SetStateAction<SettingsState>>;
  isInitialized: boolean;
};

const defaultSettings: SettingsState = {
  // Voice Settings
  voiceEnabled: true,
  autoSpeak: true,
  volume: [80],
  micSensitivity: [70],
  
  // AI Settings
  model: 'llama3',
  
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

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);

  // Load settings from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('app-settings');
        if (saved) {
          setSettings(JSON.parse(saved));
        }
      } catch (error) {
        console.error('Error loading settings from localStorage:', error);
      } finally {
        setIsInitialized(true);
      }
    } else {
      setIsInitialized(true);
    }
  }, []);

  // Save settings to localStorage when they change
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      try {
        localStorage.setItem('app-settings', JSON.stringify(settings));
      } catch (error) {
        console.error('Error saving settings to localStorage:', error);
      }
    }
  }, [settings, isInitialized]);

  const value = React.useMemo(() => ({
    settings,
    setSettings,
    isInitialized
  }), [settings, isInitialized]);

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
