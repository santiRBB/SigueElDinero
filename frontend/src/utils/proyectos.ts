import type { Proyecto } from '../services/api'

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
