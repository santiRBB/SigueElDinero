import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { cargarArticulos, parsearFrontmatter } from './analisis'

function directorioCon(ficheros: Record<string, string>): string {
  const dir = mkdtempSync(join(tmpdir(), 'analisis-'))
  for (const [nombre, contenido] of Object.entries(ficheros)) {
    writeFileSync(join(dir, nombre), contenido, 'utf8')
  }
  return dir
}

describe('parsearFrontmatter', () => {
  it('separa las claves del cuerpo', () => {
    const { datos, cuerpo } = parsearFrontmatter('---\ntitulo: Hola\nfecha: 2026-09-18\n---\n\nTexto.\n')
    expect(datos.titulo).toBe('Hola')
    expect(datos.fecha).toBe('2026-09-18')
    expect(cuerpo.trim()).toBe('Texto.')
  })

  it('quita las comillas envolventes de un valor', () => {
    const { datos } = parsearFrontmatter('---\ntitulo: "Con: dos puntos"\n---\nx\n')
    expect(datos.titulo).toBe('Con: dos puntos')
  })

  it('falla si no hay frontmatter', () => {
    expect(() => parsearFrontmatter('Sin frontmatter\n')).toThrow(/frontmatter/i)
  })
})

describe('cargarArticulos', () => {
  it('compila el Markdown a HTML y usa el nombre de fichero como slug', () => {
    const dir = directorioCon({
      'que-es-iati.md': '---\ntitulo: Qué es IATI\ndescripcion: d\nfecha: 2026-09-18\nresumen: r\n---\n\nUn **párrafo**.\n',
    })
    const [articulo] = cargarArticulos(dir)
    expect(articulo.slug).toBe('que-es-iati')
    expect(articulo.titulo).toBe('Qué es IATI')
    expect(articulo.html).toContain('<strong>párrafo</strong>')
  })

  it('ordena por fecha descendente', () => {
    const dir = directorioCon({
      'viejo.md': '---\ntitulo: Viejo\ndescripcion: d\nfecha: 2026-01-01\nresumen: r\n---\nx\n',
      'nuevo.md': '---\ntitulo: Nuevo\ndescripcion: d\nfecha: 2026-09-18\nresumen: r\n---\nx\n',
    })
    expect(cargarArticulos(dir).map((a) => a.slug)).toEqual(['nuevo', 'viejo'])
  })

  it('falla si a un artículo le falta una clave obligatoria', () => {
    const dir = directorioCon({ 'roto.md': '---\ntitulo: Roto\n---\nx\n' })
    expect(() => cargarArticulos(dir)).toThrow(/roto\.md/)
  })
})
