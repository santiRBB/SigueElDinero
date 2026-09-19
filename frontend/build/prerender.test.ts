import { describe, expect, it } from 'vitest'
import { componerPagina, componerSitemap } from './prerender.js'

const PLANTILLA = [
  '<!doctype html>',
  '<html lang="es"><head>',
  '<meta name="description" content="Descripción del sitio" />',
  '<link rel="canonical" href="https://sigueeldinero.es/" />',
  '<meta property="og:title" content="Sigue el dinero" />',
  '<meta',
  '  property="og:description"',
  '  content="Descripción del sitio para redes"',
  '/>',
  '<meta property="og:url" content="https://sigueeldinero.es/" />',
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

  it('sustituye las etiquetas Open Graph por los valores de la página, no los de portada', () => {
    const html = componerPagina(PLANTILLA, pagina)
    expect(html).toContain('<meta property="og:title" content="Qué es IATI — Sigue el dinero" />')
    expect(html).toContain('<meta property="og:description" content="Una descripción del artículo" />')
    expect(html).toContain(
      '<meta property="og:url" content="https://sigueeldinero.es/analisis/que-es-iati" />',
    )
    expect(html).not.toContain('og:title" content="Sigue el dinero"')
    expect(html).not.toContain('Descripción del sitio para redes')
    expect(html).not.toContain('og:url" content="https://sigueeldinero.es/"')
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

  it('falla nombrando la etiqueta si no hay un <title> reconocible', () => {
    const plantillaSinTitulo = PLANTILLA.replace(
      '<title>Sigue el dinero — Cooperación española</title>',
      '<h1>Sin título</h1>',
    )
    expect(() => componerPagina(plantillaSinTitulo, pagina)).toThrow(/title/i)
  })

  it('falla nombrando la etiqueta si el atributo name de la descripción cambia de posición', () => {
    const plantillaReordenada = PLANTILLA.replace(
      '<meta name="description" content="Descripción del sitio" />',
      '<meta content="Descripción del sitio" name="description" />',
    )
    expect(() => componerPagina(plantillaReordenada, pagina)).toThrow(/description/i)
  })

  it('falla nombrando la etiqueta si falta la canonical', () => {
    const plantillaSinCanonical = PLANTILLA.replace(
      '<link rel="canonical" href="https://sigueeldinero.es/" />',
      '',
    )
    expect(() => componerPagina(plantillaSinCanonical, pagina)).toThrow(/canonical/i)
  })

  it('falla nombrando la etiqueta si falta una etiqueta Open Graph', () => {
    const plantillaSinOgTitle = PLANTILLA.replace('<meta property="og:title" content="Sigue el dinero" />', '')
    expect(() => componerPagina(plantillaSinOgTitle, pagina)).toThrow(/og:title/i)
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
