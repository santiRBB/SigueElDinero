import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import type { Plugin } from 'vite'
import { cargarArticulos, type Articulo } from './analisis.js'
import { componerPagina, componerSitemap, escaparTexto } from './prerender.js'
import { META_RUTAS, NOMBRE_SITIO, ORIGEN, RUTAS_INDEXABLES } from '../src/router/meta.js'

const ID_VIRTUAL = 'virtual:analisis'
const ID_RESUELTO = '\0' + ID_VIRTUAL

export function pluginAnalisis(raiz: string): Plugin {
  const directorio = resolve(raiz, 'content/analisis')
  let esBuild = false

  return {
    name: 'sigueeldinero-analisis',

    resolveId(id) {
      return id === ID_VIRTUAL ? ID_RESUELTO : null
    },

    load(id) {
      if (id !== ID_RESUELTO) return null
      return `export const articulos = ${JSON.stringify(cargarArticulos(directorio))}`
    },

    configureServer(servidor) {
      servidor.watcher.add(directorio)
      servidor.watcher.on('all', (_evento, ruta) => {
        if (!ruta.startsWith(directorio)) return
        const modulo = servidor.moduleGraph.getModuleById(ID_RESUELTO)
        if (modulo) servidor.moduleGraph.invalidateModule(modulo)
        servidor.ws.send({ type: 'full-reload' })
      })
    },

    configResolved(config) {
      esBuild = config.command === 'build'
    },

    closeBundle() {
      if (!esBuild) return

      const salida = resolve(raiz, 'dist')
      const plantilla = readFileSync(resolve(salida, 'index.html'), 'utf8')
      const articulos = cargarArticulos(directorio)

      escribir(
        resolve(salida, 'analisis/index.html'),
        componerPagina(plantilla, {
          titulo: `${META_RUTAS['/analisis'].titulo} — ${NOMBRE_SITIO}`,
          descripcion: META_RUTAS['/analisis'].descripcion,
          url: `${ORIGEN}/analisis`,
          cuerpo: cuerpoIndice(articulos),
        }),
      )

      for (const articulo of articulos) {
        escribir(
          resolve(salida, `analisis/${articulo.slug}/index.html`),
          componerPagina(plantilla, {
            titulo: `${articulo.titulo} — ${NOMBRE_SITIO}`,
            descripcion: articulo.descripcion,
            url: `${ORIGEN}/analisis/${articulo.slug}`,
            cuerpo: cuerpoArticulo(articulo),
          }),
        )
      }

      escribir(
        resolve(salida, 'sitemap.xml'),
        componerSitemap(ORIGEN, [
          ...RUTAS_INDEXABLES,
          ...articulos.map((a) => `/analisis/${a.slug}`),
        ]),
      )
    },
  }
}

function escribir(ruta: string, contenido: string): void {
  mkdirSync(resolve(ruta, '..'), { recursive: true })
  writeFileSync(ruta, contenido, 'utf8')
}

export function cuerpoIndice(articulos: Articulo[]): string {
  return [
    '<section class="page-head">',
    '<p class="kicker">Análisis</p>',
    '<h1 class="h-page">Cómo leer el dinero de la cooperación</h1>',
    '</section>',
    '<ul class="lista">',
    ...articulos.map(
      (a) =>
        `<li><a href="/analisis/${a.slug}">${escaparTexto(a.titulo)}</a><p class="resumen">${escaparTexto(a.resumen)}</p></li>`,
    ),
    '</ul>',
  ].join('')
}

export function cuerpoArticulo(articulo: Articulo): string {
  const fecha = escaparTexto(articulo.fecha)
  return [
    '<section class="page-head">',
    '<p class="kicker"><a href="/analisis">Análisis</a></p>',
    `<h1 class="h-page">${escaparTexto(articulo.titulo)}</h1>`,
    `<p class="note"><time datetime="${fecha}">${fecha}</time></p>`,
    '</section>',
    `<article class="prose">${articulo.html}</article>`,
  ].join('')
}
