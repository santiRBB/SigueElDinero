import { describe, expect, it } from 'vitest'
import { componerPagina, componerSitemap } from './prerender'

const PLANTILLA = [
  '<!doctype html>',
  '<html lang="es"><head>',
  '<meta name="description" content="Descripción del sitio" />',
  '<link rel="canonical" href="https://sigueeldinero.es/" />',
  '<title>Sigue el dinero — Cooperación española</title>',
  '</head><body>',
  '<div id="app"><!--respaldo--><div class="respaldo">Respaldo</div><!--/respaldo--></div>',
  '</body></html>',
].join('\n')

describe('componerPagina', () => {
  const pagina = {
    titulo: 'Qué es IATI — Sigue el dinero',
    descripcion: 'Una descripción del artículo',
    url: 'https://sigueeldinero.es/analisis/que-es-iati',
    cuerpo: '<article class="prose"><p>Texto real del artículo.</p></article>',
  }

  it('sustituye el título', () => {
    expect(componerPagina(PLANTILLA, pagina)).toContain('<title>Qué es IATI — Sigue el dinero</title>')
  })

  it('sustituye la descripción sin duplicar la etiqueta', () => {
    const html = componerPagina(PLANTILLA, pagina)
    expect(html).toContain('content="Una descripción del artículo"')
    expect(html).not.toContain('Descripción del sitio')
    expect(html.match(/name="description"/g)).toHaveLength(1)
  })

  it('apunta la canonical a la URL de la página', () => {
    expect(componerPagina(PLANTILLA, pagina)).toContain(
      '<link rel="canonical" href="https://sigueeldinero.es/analisis/que-es-iati" />',
    )
  })

  it('sustituye el bloque de respaldo por el cuerpo, conservando los marcadores', () => {
    const html = componerPagina(PLANTILLA, pagina)
    expect(html).toContain('Texto real del artículo.')
    expect(html).not.toContain('class="respaldo"')
    expect(html).toContain('<!--respaldo-->')
    expect(html).toContain('<!--/respaldo-->')
  })

  it('conserva el resto de la plantilla', () => {
    expect(componerPagina(PLANTILLA, pagina)).toContain('<html lang="es">')
  })

  it('falla si la plantilla no tiene los marcadores de respaldo', () => {
    expect(() => componerPagina('<html><body><div id="app"></div></body></html>', pagina)).toThrow(
      /respaldo/i,
    )
  })
})

describe('componerSitemap', () => {
  it('emite una entrada absoluta por ruta', () => {
    const xml = componerSitemap('https://sigueeldinero.es', ['/', '/mapa'])
    expect(xml).toContain('<loc>https://sigueeldinero.es/</loc>')
    expect(xml).toContain('<loc>https://sigueeldinero.es/mapa</loc>')
    expect(xml.match(/<url>/g)).toHaveLength(2)
  })

  it('empieza por la declaración XML y el espacio de nombres', () => {
    const xml = componerSitemap('https://sigueeldinero.es', ['/'])
    expect(xml.startsWith('<?xml version="1.0" encoding="UTF-8"?>')).toBe(true)
    expect(xml).toContain('http://www.sitemaps.org/schemas/sitemap/0.9')
  })
})
