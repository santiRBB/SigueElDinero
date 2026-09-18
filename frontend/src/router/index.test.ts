// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import router from './index'

describe('router', () => {
  it('resuelve URLs reales, sin fragmento hash', () => {
    expect(router.resolve('/mapa').href).toBe('/mapa')
    expect(router.resolve('/paises/ETH').href).toBe('/paises/ETH')
  })

  it('resuelve la raíz sin hash', () => {
    expect(router.resolve('/').href).toBe('/')
  })
})
