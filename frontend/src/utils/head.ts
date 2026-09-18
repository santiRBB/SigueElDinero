import type { Router } from 'vue-router'
import { META_RUTAS, NOMBRE_SITIO, ORIGEN } from '../router/meta'

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
    const meta = META_RUTAS[to.matched[to.matched.length - 1]?.path ?? to.path]
    if (!meta) return
    aplicarHead({
      titulo: meta.titulo,
      descripcion: meta.descripcion,
      indexable: meta.indexable,
      ruta: to.path,
    })
  })
}
