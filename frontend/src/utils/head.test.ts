// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'
import { aplicarHead } from './head'

function contenidoMeta(nombre: string): string | null {
  return document.head.querySelector<HTMLMetaElement>(`meta[name="${nombre}"]`)?.content ?? null
}

describe('aplicarHead', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    document.title = ''
  })

  it('compone el título con el nombre del sitio', () => {
    aplicarHead({ titulo: 'El reparto, país a país', descripcion: 'd', indexable: true, ruta: '/mapa' })
    expect(document.title).toBe('El reparto, país a país — Sigue el dinero')
  })

  it('no duplica el nombre del sitio en la portada', () => {
    aplicarHead({ titulo: 'Sigue el dinero', descripcion: 'd', indexable: true, ruta: '/' })
    expect(document.title).toBe('Sigue el dinero')
  })

  it('escribe la descripción y la canonical absoluta', () => {
    aplicarHead({ titulo: 't', descripcion: 'Una descripción', indexable: true, ruta: '/mapa' })
    expect(contenidoMeta('description')).toBe('Una descripción')
    expect(document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.href).toBe(
      'https://sigueeldinero.es/mapa',
    )
  })

  it('emite noindex solo en rutas no indexables', () => {
    aplicarHead({ titulo: 't', descripcion: 'd', indexable: false, ruta: '/cookies' })
    expect(contenidoMeta('robots')).toBe('noindex, follow')
  })

  it('retira el noindex al volver a una ruta indexable', () => {
    aplicarHead({ titulo: 't', descripcion: 'd', indexable: false, ruta: '/cookies' })
    aplicarHead({ titulo: 't', descripcion: 'd', indexable: true, ruta: '/mapa' })
    expect(contenidoMeta('robots')).toBeNull()
  })

  it('no acumula etiquetas duplicadas entre navegaciones', () => {
    aplicarHead({ titulo: 't', descripcion: 'a', indexable: true, ruta: '/mapa' })
    aplicarHead({ titulo: 't', descripcion: 'b', indexable: true, ruta: '/sobre' })
    expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(1)
    expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(1)
    expect(contenidoMeta('description')).toBe('b')
  })
})
