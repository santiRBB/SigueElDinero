import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getAnios, getDetallePais, getResumenPaises, getSectores } from './api'

describe('api service', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('getResumenPaises includes anio and sector as query params when provided', async () => {
    const mockData = [{ iso_alpha3: 'COL', nombre: 'Colombia', importe_total_eur: 100, n_intervenciones: 2 }]
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockData } as Response)

    const result = await getResumenPaises(2025, '72050')

    expect(fetch).toHaveBeenCalledTimes(1)
    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/paises/resumen')
    expect(calledUrl).toContain('anio=2025')
    expect(calledUrl).toContain('sector=72050')
    expect(result).toEqual(mockData)
  })

  it('getResumenPaises omits query params when not provided', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getResumenPaises()

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).not.toContain('anio=')
    expect(calledUrl).not.toContain('sector=')
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

  it('throws a descriptive error when the response is not ok', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response)

    await expect(getDetallePais('ZZZ')).rejects.toThrow('404')
  })

  it('getAnios and getSectores call the filtros endpoints', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getAnios()
    expect(vi.mocked(fetch).mock.calls[0][0]).toContain('/api/filtros/anios')

    await getSectores()
    expect(vi.mocked(fetch).mock.calls[1][0]).toContain('/api/filtros/sectores')
  })
})
