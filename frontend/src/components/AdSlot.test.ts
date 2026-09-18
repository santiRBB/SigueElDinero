// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import { mount } from '@vue/test-utils'

vi.mock('vanilla-cookieconsent', () => ({
  run: vi.fn(),
  showPreferences: vi.fn(),
  acceptedCategory: vi.fn(),
}))

// reactive(): igual que el objeto real que devuelve vue-router. Con un objeto plano, mutar
// rutaActual.path en el test de abajo no dispararía el watcher de route.path del componente,
// porque no habría ninguna dependencia reactiva que rastrear.
const rutaActual = reactive({ path: '/mapa', meta: { anuncios: true } as { anuncios: boolean } })
vi.mock('vue-router', () => ({ useRoute: () => rutaActual }))

import * as CookieConsent from 'vanilla-cookieconsent'
import { adsConsent } from '../utils/cookieConsent'
import AdSlot from './AdSlot.vue'

function montar(contenidoListo: boolean) {
  return mount(AdSlot, { props: { contenidoListo } })
}

describe('AdSlot', () => {
  let wrapper: ReturnType<typeof montar> | undefined

  beforeEach(() => {
    adsConsent.value = false
    rutaActual.path = '/mapa'
    rutaActual.meta = { anuncios: true }
    window.adsbygoogle = []
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', 'ca-pub-test123')
    vi.stubEnv('VITE_ADSENSE_SLOT_ID', '1234567890')
  })

  afterEach(() => {
    wrapper?.unmount()
    wrapper = undefined
    vi.unstubAllEnvs()
    vi.clearAllMocks()
  })

  it('no inserta nada en una ruta sin anuncios, aunque haya consentimiento y contenido', () => {
    rutaActual.meta = { anuncios: false }
    adsConsent.value = true
    wrapper = montar(true)

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
    expect(window.adsbygoogle).toHaveLength(0)
  })

  it('no inserta nada mientras el contenido no ha cargado', () => {
    adsConsent.value = true
    wrapper = montar(false)

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
    expect(window.adsbygoogle).toHaveLength(0)
  })

  it('muestra el aviso de consentimiento, no un anuncio, si no se aceptaron cookies', () => {
    wrapper = montar(true)

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(true)
    expect(window.adsbygoogle).toHaveLength(0)
  })

  it('inserta el anuncio y lo solicita cuando ruta, contenido y consentimiento coinciden', async () => {
    adsConsent.value = true
    wrapper = montar(true)
    await wrapper.vm.$nextTick()

    const ins = wrapper.find('ins.adsbygoogle')
    expect(ins.exists()).toBe(true)
    expect(ins.attributes('data-ad-client')).toBe('ca-pub-test123')
    expect(ins.attributes('data-ad-slot')).toBe('1234567890')
    expect(window.adsbygoogle).toHaveLength(1)
  })

  it('no solicita un anuncio dos veces para el mismo estado', async () => {
    adsConsent.value = true
    wrapper = montar(true)
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(window.adsbygoogle).toHaveLength(1)
  })

  it('solicita el anuncio cuando el contenido termina de cargar', async () => {
    adsConsent.value = true
    wrapper = montar(false)
    expect(window.adsbygoogle).toHaveLength(0)

    await wrapper.setProps({ contenidoListo: true })
    await wrapper.vm.$nextTick()

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(true)
    expect(window.adsbygoogle).toHaveLength(1)
  })

  it('solicita el anuncio cuando el consentimiento llega después del montaje', async () => {
    wrapper = montar(true)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(true)

    adsConsent.value = true
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(true)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
    expect(window.adsbygoogle).toHaveLength(1)
  })

  it('no muestra nada si falta la configuración de AdSense', () => {
    adsConsent.value = true
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', '')
    wrapper = montar(true)

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
  })

  it('reabre las preferencias de cookies desde el aviso', async () => {
    wrapper = montar(true)

    await wrapper.find('.ad-placeholder button').trigger('click')

    expect(CookieConsent.showPreferences).toHaveBeenCalledTimes(1)
  })

  it('solicita un anuncio nuevo cuando la misma instancia cambia de ruta', async () => {
    adsConsent.value = true
    wrapper = montar(true)
    await wrapper.vm.$nextTick()
    expect(window.adsbygoogle).toHaveLength(1)

    // Vue Router reutiliza la instancia del componente cuando solo cambia el parámetro de
    // una misma ruta (p. ej. entre dos artículos de /analisis/:slug): no hay desmontaje, así
    // que muestraAnuncio nunca deja de ser true y su watcher no vuelve a dispararse por sí
    // solo. El :key="route.path" del <ins> sí crea un nodo nuevo, pero un nodo nuevo sin un
    // pedirAnuncio() nuevo es un hueco de anuncio vacío para siempre.
    rutaActual.path = '/analisis/otro-articulo'
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(window.adsbygoogle).toHaveLength(2)
  })
})
