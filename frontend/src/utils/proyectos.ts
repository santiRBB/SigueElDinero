import type { Orden, Proyecto } from '../services/api'

export function detectarImportesEstandar(proyectos: Proyecto[]): Set<string> {
  const conteos = new Map<string, number>()
  for (const p of proyectos) {
    const clave = `${p.importe_pais_eur}|${p.start_date}`
    conteos.set(clave, (conteos.get(clave) ?? 0) + 1)
  }

  const aidsEstandar = new Set<string>()
  for (const p of proyectos) {
    const clave = `${p.importe_pais_eur}|${p.start_date}`
    if ((conteos.get(clave) ?? 0) > 1) {
      aidsEstandar.add(p.aid)
    }
  }
  return aidsEstandar
}

export function ordenarProyectos<T extends Proyecto>(proyectos: T[], orden: Orden): T[] {
  const copia = [...proyectos]
  switch (orden) {
    case 'importe_asc':
      return copia.sort((a, b) => a.importe_pais_eur - b.importe_pais_eur)
    case 'fecha_desc':
      return copia.sort((a, b) => compararFechas(a.start_date, b.start_date, -1))
    case 'fecha_asc':
      return copia.sort((a, b) => compararFechas(a.start_date, b.start_date, 1))
    case 'importe_desc':
    default:
      return copia.sort((a, b) => b.importe_pais_eur - a.importe_pais_eur)
  }
}

// Null dates always sort last, regardless of direction.
function compararFechas(a: string | null, b: string | null, direccion: 1 | -1): number {
  if (a === b) return 0
  if (a === null) return 1
  if (b === null) return -1
  return direccion * (a < b ? -1 : 1)
}
