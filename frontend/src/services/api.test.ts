import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buscarProyectos,
  getAnios,
  getDetallePais,
  getPaisPorAnio,
  getResumenPaises,
  getResumenPorAnio,
  getResumenPorGrupo,
  getSectores,
} from './api'

describe('api service', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('getResumenPaises includes anio and grupo as query params when provided', async () => {
    const mockData = [{ iso_alpha3: 'COL', nombre: 'Colombia', importe_total_eur: 100, n_intervenciones: 2 }]
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockData } as Response)

    const result = await getResumenPaises(2025, '720')

    expect(fetch).toHaveBeenCalledTimes(1)
    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/paises/resumen')
    expect(calledUrl).toContain('anio=2025')
    expect(calledUrl).toContain('grupo=720')
    expect(result).toEqual(mockData)
  })

  it('getResumenPaises omits query params when not provided', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getResumenPaises()

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).not.toContain('anio=')
    expect(calledUrl).not.toContain('grupo=')
  })

  it('getDetallePais requests the country-specific path', async () => {
    const mockDetalle = { pais: { iso_alpha3: 'COL', nombre: 'Colombia', region: null }, categorias: [], proyectos: [] }
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockDetalle } as Response)

    const result = await getDetallePais('COL', 2024)

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/paises/COL/detalle')
    expect(calledUrl).toContain('anio=2024')
    expect(result).toEqual(mockDetalle)
  })

  it('getPaisPorAnio requests the evolution path with the grupo filter', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getPaisPorAnio('COL', '720')

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/paises/COL/por-anio')
    expect(calledUrl).toContain('grupo=720')
  })

  it('throws a descriptive error when the response is not ok', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response)

    await expect(getDetallePais('ZZZ')).rejects.toThrow('404')
  })

  it('attaches the HTTP status code to the thrown error', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response)

    await expect(getDetallePais('ZZZ')).rejects.toMatchObject({ status: 404 })
  })

  it('getAnios and getSectores call the filtros endpoints', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getAnios()
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('/api/filtros/anios')

    await getSectores()
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('/api/filtros/sectores')
  })

  it('getResumenPorAnio and getResumenPorGrupo call the resumen endpoints', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getResumenPorAnio('720')
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('/api/resumen/por-anio')
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('grupo=720')

    await getResumenPorGrupo(2024)
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('/api/resumen/por-grupo')
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('anio=2024')
  })

  it('buscarProyectos sends all provided filters as query params', async () => {
    const mockResultado = { total: 0, pagina: 1, por_pagina: 30, resultados: [] }
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockResultado } as Response)

    const result = await buscarProyectos({ q: 'agua', anio: 2024, grupo: '720', pais: 'COL', pagina: 2, por_pagina: 10 })

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/proyectos/buscar')
    expect(calledUrl).toContain('q=agua')
    expect(calledUrl).toContain('anio=2024')
    expect(calledUrl).toContain('grupo=720')
    expect(calledUrl).toContain('pais=COL')
    expect(calledUrl).toContain('pagina=2')
    expect(calledUrl).toContain('por_pagina=10')
    expect(result).toEqual(mockResultado)
  })
})
