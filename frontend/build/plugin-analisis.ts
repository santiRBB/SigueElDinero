import { resolve } from 'node:path'
import type { Plugin } from 'vite'
import { cargarArticulos } from './analisis.js'

const ID_VIRTUAL = 'virtual:analisis'
const ID_RESUELTO = '\0' + ID_VIRTUAL

export function pluginAnalisis(raiz: string): Plugin {
  const directorio = resolve(raiz, 'content/analisis')

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
  }
}
