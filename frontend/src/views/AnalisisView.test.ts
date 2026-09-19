// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { mount } from '@vue/test-utils'
import { articulos } from 'virtual:analisis'
import AnalisisView from './AnalisisView.vue'

// Si vitest.config.ts no registra pluginAnalisis (a diferencia de vite.config.ts), esta
// importación de virtual:analisis falla con un error de resolución de módulo opaco, y esta
// vista (y ArticuloView.vue) queda sin poder probarse nunca.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div />' } },
    { path: '/analisis/:slug', component: { template: '<div />' } },
  ],
})

describe('AnalisisView', () => {
  it('lista los artículos de virtual:analisis', async () => {
    await router.push('/')
    await router.isReady()

    const wrapper = mount(AnalisisView, { global: { plugins: [router] } })

    expect(articulos.length).toBeGreaterThan(0)
    expect(wrapper.findAll('.lista li a').map((enlace) => enlace.text())).toEqual(
      articulos.map((a) => a.titulo),
    )
  })
})
