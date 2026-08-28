import { describe, expect, it } from 'vitest'
import type { Proyecto } from '../services/api'
import { detectarImportesEstandar } from './proyectos'

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
