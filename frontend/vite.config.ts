import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import { pluginAnalisis } from './build/plugin-analisis.js'

const raiz = dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), pluginAnalisis(raiz)],
})
