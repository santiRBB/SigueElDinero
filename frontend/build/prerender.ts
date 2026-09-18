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

function escaparTexto(valor: string): string {
  return valor.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export function componerPagina(plantilla: string, pagina: PaginaEstatica): string {
  if (!MARCADOR_RESPALDO.test(plantilla)) {
    throw new Error('La plantilla no contiene los marcadores <!--respaldo--> / <!--/respaldo-->')
  }

  return plantilla
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${escaparTexto(pagina.titulo)}</title>`)
    .replace(
      /<meta\s+name="description"[\s\S]*?\/>/,
      `<meta name="description" content="${escaparAtributo(pagina.descripcion)}" />`,
    )
    .replace(
      /<link\s+rel="canonical"[\s\S]*?\/>/,
      `<link rel="canonical" href="${escaparAtributo(pagina.url)}" />`,
    )
    .replace(MARCADOR_RESPALDO, `<!--respaldo-->${pagina.cuerpo}<!--/respaldo-->`)
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
