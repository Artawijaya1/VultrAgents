import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', 'VITE_');
    const backendTarget = env.VITE_BACKEND_PROXY_TARGET || 'http://127.0.0.1:8000';
    return {
        plugins: [react()],
        server: {
            proxy: {
                '/api': { target: backendTarget, changeOrigin: true },
                '/health': { target: backendTarget, changeOrigin: true },
                '/ready': { target: backendTarget, changeOrigin: true },
            },
        },
    };
});
