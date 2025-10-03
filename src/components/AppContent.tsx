'use client';

import { ReactNode, useEffect, useState } from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { ThemeProvider } from '@/contexts/theme-context';
import { SettingsProvider } from '@/contexts/settings-context';
import { Toaster } from '@/components/ui/toaster';

interface AppContentProps {
  children: ReactNode;
}

export default function AppContent({ children }: AppContentProps) {
  const [mounted, setMounted] = useState(false);

  // Ensure we're on the client before rendering providers
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    // Don't render anything until we're on the client
    return null;
  }

  return (
    <SettingsProvider>
      <ThemeProvider>
        <NextThemesProvider 
          attribute="class" 
          defaultTheme="system" 
          enableSystem
          disableTransitionOnChange
          storageKey="theme"
        >
          {children}
          <Toaster />
        </NextThemesProvider>
      </ThemeProvider>
    </SettingsProvider>
  );
}
