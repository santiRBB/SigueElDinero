import { describe, expect, it } from 'vitest'
import type { Proyecto } from '../services/api'
import { detectarImportesEstandar, ordenarProyectos } from './proyectos'

function proyecto(overrides: Partial<Proyecto>): Proyecto {
  return {
    aid: 'AID-1',
    titulo: 'Proyecto',
    organismo_ejecutor: 'ONG',
    importe_pais_eur: 1000,
    porcentaje_pais: 100,
    porcentaje_fuente: 'declared',
    start_date: '2024-10-01',
    end_date: null,
    url_fuente: null,
    url_bdns: null,
    bdns_tipo_convocatoria: null,
    ...overrides,
  }
}

describe('detectarImportesEstandar', () => {
  it('marks projects that share both amount and start date', () => {
    const proyectos = [
      proyecto({ aid: 'A', importe_pais_eur: 985865, start_date: '2024-10-15' }),
      proyecto({ aid: 'B', importe_pais_eur: 985865, start_date: '2024-10-15' }),
      proyecto({ aid: 'C', importe_pais_eur: 500, start_date: '2024-10-15' }),
    ]

    expect(detectarImportesEstandar(proyectos)).toEqual(new Set(['A', 'B']))
  })

  it('does not mark projects with the same amount but different dates', () => {
    const proyectos = [
      proyecto({ aid: 'A', importe_pais_eur: 1000, start_date: '2024-10-15' }),
      proyecto({ aid: 'B', importe_pais_eur: 1000, start_date: '2024-11-01' }),
    ]

    expect(detectarImportesEstandar(proyectos).size).toBe(0)
  })

  it('returns an empty set for an empty list', () => {
    expect(detectarImportesEstandar([])).toEqual(new Set())
  })
})

describe('ordenarProyectos', () => {
  const proyectos = [
    proyecto({ aid: 'A', importe_pais_eur: 200, start_date: '2023-05-01' }),
    proyecto({ aid: 'B', importe_pais_eur: 500, start_date: '2024-01-01' }),
    proyecto({ aid: 'C', importe_pais_eur: 100, start_date: null }),
  ]

  it('sorts by importe descending by default', () => {
    expect(ordenarProyectos(proyectos, 'importe_desc').map((p) => p.aid)).toEqual(['B', 'A', 'C'])
  })

  it('sorts by importe ascending', () => {
    expect(ordenarProyectos(proyectos, 'importe_asc').map((p) => p.aid)).toEqual(['C', 'A', 'B'])
  })

  it('sorts by fecha descending, with null dates last', () => {
    expect(ordenarProyectos(proyectos, 'fecha_desc').map((p) => p.aid)).toEqual(['B', 'A', 'C'])
  })

  it('sorts by fecha ascending, with null dates last', () => {
    expect(ordenarProyectos(proyectos, 'fecha_asc').map((p) => p.aid)).toEqual(['A', 'B', 'C'])
  })

  it('does not mutate the original array', () => {
    const copia = [...proyectos]
    ordenarProyectos(proyectos, 'importe_asc')
    expect(proyectos).toEqual(copia)
  })
})
