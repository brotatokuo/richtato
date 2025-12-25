import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
// Use 'backend' as hostname when running in Docker, otherwise localhost
const backendHost = process.env.DOCKER_ENV === 'true' ? 'backend' : 'localhost';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Allow access from all network interfaces
    // Removed allowedHosts restriction to allow local network access
    proxy: {
      '/api': {
        target: `http://${backendHost}:8000`,
        changeOrigin: true,
      },
      '/demo-login': {
        target: `http://${backendHost}:8000`,
        changeOrigin: true,
      },
    },
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
