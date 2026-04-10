import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    plugins: [vue()],

    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },

    build: {
        // Vite Stage 1 в Dockerfile кладёт output сюда
        outDir: '../backend/static',
        emptyOutDir: true,
        assetsDir: 'assets', // явно, чтобы не зависеть от дефолта
    },

    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/ws': {
                target: 'ws://localhost:8000',
                ws: true,
                changeOrigin: true,
                rewriteWsOrigin: true, // [MAJOR FIX] Vite 6: корректный проброс Origin для WS handshake
            },
        },
    },
})