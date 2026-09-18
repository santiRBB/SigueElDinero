import { describe, expect, it } from 'vitest'
import type { Articulo } from './analisis.js'
import { cuerpoArticulo, cuerpoIndice } from './plugin-analisis.js'

function articulo(sobrescribir: Partial<Articulo> = {}): Articulo {
  return {
    slug: 'demo',
    titulo: 'Demo',
    descripcion: 'd',
    fecha: '2026-09-18',
    resumen: 'r',
    html: '<p>x</p>',
    ...sobrescribir,
  }
}

describe('cuerpoArticulo', () => {
  it('escapa el título con caracteres especiales', () => {
    const html = cuerpoArticulo(articulo({ titulo: 'Cooperación & desarrollo <bis>' }))
    expect(html).toContain('Cooperación &amp; desarrollo &lt;bis&gt;')
    expect(html).not.toContain('<bis>')
  })

  it('conserva el HTML del cuerpo del artículo sin escapar', () => {
    const html = cuerpoArticulo(articulo({ html: '<p>Texto <strong>real</strong>.</p>' }))
    expect(html).toContain('<p>Texto <strong>real</strong>.</p>')
  })
})

describe('cuerpoIndice', () => {
  it('escapa el título y el resumen de cada artículo listado', () => {
    const html = cuerpoIndice([articulo({ titulo: 'A & B', resumen: 'Resumen <raro>' })])
    expect(html).toContain('A &amp; B')
    expect(html).toContain('Resumen &lt;raro&gt;')
    expect(html).not.toContain('<raro>')
  })
})
