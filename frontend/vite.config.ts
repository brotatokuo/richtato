import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5927,
    host: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'staging.neuron.teserac.ai',
      '72.13.82.3',
    ],
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});
