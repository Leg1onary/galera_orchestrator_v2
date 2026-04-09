import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
    plugins: [vue()],

    // Resolve @ alias to src/
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },

    build: {
        // Output goes directly into backend/static/ so Docker can serve it
        outDir: '../backend/static',
        emptyOutDir: true,
        // Generate source maps for easier debugging in development
        sourcemap: false,
    },

    server: {
        port: 5173,
        proxy: {
            // Proxy all /api requests to FastAPI backend during development
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                // withCredentials is handled by axios; proxy just forwards cookies
            },
            // Proxy WebSocket connections to FastAPI backend
            '/ws': {
                target: 'ws://localhost:8000',
                ws: true,
                changeOrigin: true,
            },
        },
    },
})