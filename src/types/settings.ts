export interface SettingsState {
  // Voice Settings
  voiceEnabled: boolean;
  autoSpeak: boolean;
  volume: number[];
  micSensitivity: number[];
  
  // AI Settings
  model: string;
  
  // Appearance Settings
  theme: string;
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

export interface ThemeContextType {
  theme: string;
  setTheme: (theme: string) => void;
  settings: SettingsState;
  updateSettings: (newSettings: Partial<SettingsState>) => void;
}
