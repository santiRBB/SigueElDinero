import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { pluginAnalisis } from './build/plugin-analisis.js'

const raiz = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue(), pluginAnalisis(raiz)],
  test: {
    environment: 'node',
  },
})
