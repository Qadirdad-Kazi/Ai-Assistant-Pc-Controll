import React from 'react';
import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import dynamic from 'next/dynamic';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a client
const queryClient = new QueryClient();

// Dynamically import the client-side only app with no SSR
const ClientApp = dynamic(
  () => import('../components/AppContent'),
  { ssr: false }
);

function App({ Component, pageProps }: AppProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ClientApp>
        <Component {...pageProps} />
      </ClientApp>
    </QueryClientProvider>
  );
}

export default App;
