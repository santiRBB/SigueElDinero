export interface PaginaEstatica {
  titulo: string
  descripcion: string
  url: string
  cuerpo: string
}

const MARCADOR_RESPALDO = /<!--respaldo-->[\s\S]*?<!--\/respaldo-->/

function escaparAtributo(valor: string): string {
  return valor.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')
}

export function escaparTexto(valor: string): string {
  return valor.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function reemplazarEtiqueta(html: string, patron: RegExp, reemplazo: string, etiqueta: string): string {
  if (!patron.test(html)) {
    throw new Error(`La plantilla no contiene la etiqueta ${etiqueta}`)
  }
  return html.replace(patron, reemplazo)
}

export function componerPagina(plantilla: string, pagina: PaginaEstatica): string {
  if (!MARCADOR_RESPALDO.test(plantilla)) {
    throw new Error('La plantilla no contiene los marcadores <!--respaldo--> / <!--/respaldo-->')
  }

  let resultado = plantilla

  resultado = reemplazarEtiqueta(
    resultado,
    /<title>[\s\S]*?<\/title>/,
    `<title>${escaparTexto(pagina.titulo)}</title>`,
    '<title>',
  )
  resultado = reemplazarEtiqueta(
    resultado,
    /<meta\s+name="description"[\s\S]*?\/>/,
    `<meta name="description" content="${escaparAtributo(pagina.descripcion)}" />`,
    'meta[name="description"]',
  )
  resultado = reemplazarEtiqueta(
    resultado,
    /<link\s+rel="canonical"[\s\S]*?\/>/,
    `<link rel="canonical" href="${escaparAtributo(pagina.url)}" />`,
    'link[rel="canonical"]',
  )
  resultado = reemplazarEtiqueta(
    resultado,
    /<meta\s+property="og:title"[\s\S]*?\/>/,
    `<meta property="og:title" content="${escaparAtributo(pagina.titulo)}" />`,
    'meta[property="og:title"]',
  )
  resultado = reemplazarEtiqueta(
    resultado,
    /<meta\s+property="og:description"[\s\S]*?\/>/,
    `<meta property="og:description" content="${escaparAtributo(pagina.descripcion)}" />`,
    'meta[property="og:description"]',
  )
  resultado = reemplazarEtiqueta(
    resultado,
    /<meta\s+property="og:url"[\s\S]*?\/>/,
    `<meta property="og:url" content="${escaparAtributo(pagina.url)}" />`,
    'meta[property="og:url"]',
  )

  return resultado.replace(MARCADOR_RESPALDO, `<!--respaldo-->${pagina.cuerpo}<!--/respaldo-->`)
}

export function componerSitemap(origen: string, rutas: string[]): string {
  const entradas = rutas
    .map((ruta) => `  <url>\n    <loc>${escaparTexto(origen + ruta)}</loc>\n  </url>`)
    .join('\n')

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    entradas,
    '</urlset>',
    '',
  ].join('\n')
}
