import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Set BASE_PATH (e.g. "/mpc-index/") when deploying under a sub-path.
export default defineConfig({
  plugins: [react()],
  base: process.env.BASE_PATH ?? '/',
});
