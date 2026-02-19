import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react(), tailwindcss()],
    base: './', // Important for Electron to find assets
    server: {
        port: 5173,
        strictPort: true,
    },
});
