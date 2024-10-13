import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        background: resolve(__dirname, 'background.js'),
        content: resolve(__dirname, 'content.js'),
      },
      output: {
        entryFileNames: '[name].js',
      },
    },
  },
  publicDir: 'public',
});