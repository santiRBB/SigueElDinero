import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import MarkdownIt from 'markdown-it'

export interface Articulo {
  slug: string
  titulo: string
  descripcion: string
  fecha: string
  resumen: string
  html: string
}

const CLAVES_OBLIGATORIAS = ['titulo', 'descripcion', 'fecha', 'resumen'] as const

const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

export function parsearFrontmatter(texto: string): {
  datos: Record<string, string>
  cuerpo: string
} {
  const coincidencia = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(texto)
  if (!coincidencia) throw new Error('El fichero no empieza por un bloque de frontmatter')

  const datos: Record<string, string> = {}
  for (const linea of coincidencia[1].split(/\r?\n/)) {
    const separador = linea.indexOf(':')
    if (separador === -1) continue
    const clave = linea.slice(0, separador).trim()
    const valor = linea.slice(separador + 1).trim()
    datos[clave] = valor.replace(/^["']|["']$/g, '')
  }
  return { datos, cuerpo: texto.slice(coincidencia[0].length) }
}

export function cargarArticulos(directorio: string): Articulo[] {
  const ficheros = readdirSync(directorio).filter((n) => n.endsWith('.md'))

  const articulos = ficheros.map((nombre) => {
    const { datos, cuerpo } = parsearFrontmatter(readFileSync(join(directorio, nombre), 'utf8'))
    for (const clave of CLAVES_OBLIGATORIAS) {
      if (!datos[clave]) throw new Error(`Falta la clave "${clave}" en el frontmatter de ${nombre}`)
    }
    return {
      slug: nombre.replace(/\.md$/, ''),
      titulo: datos.titulo,
      descripcion: datos.descripcion,
      fecha: datos.fecha,
      resumen: datos.resumen,
      html: md.render(cuerpo),
    }
  })

  return articulos.sort((a, b) => b.fecha.localeCompare(a.fecha))
}
