import * as React from "react";
import { Monitor, Sun, Moon, Activity, Contrast, MoonStar } from "lucide-react";

// Define available themes
export type Theme = 'light' | 'dark' | 'system' | 'jarvis' | 'contrast' | 'blue-light'

// Create a context for the theme
type ThemeContextType = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
};

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

// Theme configuration
export const themes: { value: Theme; label: string; icon: React.ComponentType<any> }[] = [
  { value: 'system', label: 'System', icon: Monitor },
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'jarvis', label: 'JARVIS', icon: Activity },
  { value: 'contrast', label: 'High Contrast', icon: Contrast },
  { value: 'blue-light', label: 'Blue Light', icon: MoonStar },
];

export function ThemeProvider({ 
  children,
  defaultTheme = 'system',
  storageKey = 'app-theme',
  ...props 
}: { 
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
} & React.HTMLAttributes<HTMLDivElement>) {
  const [theme, setThemeState] = React.useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(storageKey);
      return (saved as Theme) || defaultTheme;
    }
    return defaultTheme;
  });

  const [resolvedTheme, setResolvedTheme] = React.useState<'light' | 'dark'>(
    theme === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : theme === 'dark' || theme === 'jarvis' || theme === 'contrast'
      ? 'dark'
      : 'light'
  );

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, newTheme);
    }
  };

  // Apply theme class to document element
  React.useEffect(() => {
    const root = window.document.documentElement;
    const themes = ['light', 'dark', 'jarvis', 'contrast', 'blue-light'];
    root.classList.remove(...themes);
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
      setResolvedTheme(systemTheme);
      return;
    }
    
    root.classList.add(theme);
    setResolvedTheme(theme === 'dark' || theme === 'jarvis' || theme === 'contrast' ? 'dark' : 'light');
  }, [theme]);

  // Listen for system theme changes
  React.useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      const root = window.document.documentElement;
      const systemTheme = mediaQuery.matches ? 'dark' : 'light';
      root.classList.remove('light', 'dark');
      root.classList.add(systemTheme);
      setResolvedTheme(systemTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  const contextValue = React.useMemo(
    () => ({
      theme,
      setTheme,
      resolvedTheme,
    }),
    [theme, resolvedTheme]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      <div data-theme={theme} {...props}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = React.useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Helper hook to get the current theme configuration
export function useThemeConfig() {
  return {
    themes,
    ...useTheme(),
  };
};
