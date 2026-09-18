import type { Router } from 'vue-router'
import { NOMBRE_SITIO, ORIGEN } from '../router/meta'

export interface OpcionesHead {
  titulo: string
  descripcion: string
  indexable: boolean
  ruta: string
}

function fijarMeta(nombre: string, contenido: string | null): void {
  const existente = document.head.querySelector<HTMLMetaElement>(`meta[name="${nombre}"]`)
  if (contenido === null) {
    existente?.remove()
    return
  }
  const meta = existente ?? document.head.appendChild(document.createElement('meta'))
  meta.setAttribute('name', nombre)
  meta.setAttribute('content', contenido)
}

function fijarPropiedad(propiedad: string, contenido: string): void {
  const existente = document.head.querySelector<HTMLMetaElement>(`meta[property="${propiedad}"]`)
  const meta = existente ?? document.head.appendChild(document.createElement('meta'))
  meta.setAttribute('property', propiedad)
  meta.setAttribute('content', contenido)
}

function fijarCanonical(url: string): void {
  const existente = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  const link = existente ?? document.head.appendChild(document.createElement('link'))
  link.setAttribute('rel', 'canonical')
  link.setAttribute('href', url)
}

export function aplicarHead(opciones: OpcionesHead): void {
  const titulo =
    opciones.titulo === NOMBRE_SITIO ? NOMBRE_SITIO : `${opciones.titulo} — ${NOMBRE_SITIO}`
  const url = `${ORIGEN}${opciones.ruta}`

  document.title = titulo
  fijarMeta('description', opciones.descripcion)
  fijarMeta('robots', opciones.indexable ? null : 'noindex, follow')
  fijarCanonical(url)
  fijarPropiedad('og:title', titulo)
  fijarPropiedad('og:description', opciones.descripcion)
  fijarPropiedad('og:url', url)
}

export function instalarHead(router: Router): void {
  router.afterEach((to) => {
    // `to.meta` es el objeto que cada ruta recibió vía `meta: metaDe(path)` en el router: se lee
    // directamente en vez de volver a buscarlo en META_RUTAS por la ruta registrada, porque para
    // el catch-all (`/:pathMatch(.*)*`) esa ruta registrada no coincide con ninguna clave de
    // META_RUTAS (la clave es '/404') y la búsqueda por ruta nunca encontraría nada.
    const meta = to.meta
    aplicarHead({
      titulo: meta.titulo,
      descripcion: meta.descripcion,
      indexable: meta.indexable,
      ruta: to.path,
    })
  })
}
