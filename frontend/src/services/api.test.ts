import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buscarProyectos,
  getAnios,
  getCcaaPorAnio,
  getConcesionesAecidBdns,
  getDetalleCcaa,
  getDetallePais,
  getPaisPorAnio,
  getResumenCcaa,
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

  it('getResumenCcaa includes anio as query param when provided', async () => {
    const mockData = [{ codigo_ine: '09', nombre: 'Cataluña', importe_total_eur: 100, n_concesiones: 2 }]
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockData } as Response)

    const result = await getResumenCcaa(2025)

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/ccaa/resumen')
    expect(calledUrl).toContain('anio=2025')
    expect(result).toEqual(mockData)
  })

  it('getResumenCcaa omits anio when not provided', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => [] } as Response)

    await getResumenCcaa()

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).not.toContain('anio=')
  })

  it('getDetalleCcaa requests the ccaa-specific path', async () => {
    const mockDetalle = {
      ccaa: { codigo_ine: '09', nombre: 'Cataluña' },
      importe_total_eur: 500,
      n_concesiones: 3,
      organismos: [],
    }
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockDetalle } as Response)

    const result = await getDetalleCcaa('09', 2024)

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/ccaa/09/detalle')
    expect(calledUrl).toContain('anio=2024')
    expect(result).toEqual(mockDetalle)
  })

  it('getCcaaPorAnio requests the evolution path', async () => {
    const datos = [{ anio: 2024, importe_eur: 100, n_concesiones: 2 }]
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => datos } as Response)

    const result = await getCcaaPorAnio('09')

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/ccaa/09/por-anio')
    expect(result).toEqual(datos)
  })

  it('getConcesionesAecidBdns sends iso_alpha3, pagina, and por_pagina as query params', async () => {
    const mockResultado = {
      total: 1, pagina: 1, por_pagina: 30,
      resultados: [{
        concesion_id: 155744095, beneficiario: 'UNITED NATIONS-WORLD',
        titulo: 'PMA 2026', importe_eur: 20000000, fecha_concesion: '2026-07-14',
        iso_alpha3: 'MLI', pais_nombre: 'Mali',
        url_bdns: 'https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/921884',
      }],
    }
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => mockResultado } as Response)

    const result = await getConcesionesAecidBdns({ iso_alpha3: 'MLI', pagina: 2, por_pagina: 10 })

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).toContain('/api/aecid-bdns/concesiones')
    expect(calledUrl).toContain('iso_alpha3=MLI')
    expect(calledUrl).toContain('pagina=2')
    expect(calledUrl).toContain('por_pagina=10')
    expect(result).toEqual(mockResultado)
  })

  it('getConcesionesAecidBdns omits iso_alpha3 when not provided', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ total: 0, pagina: 1, por_pagina: 30, resultados: [] }) } as Response)

    await getConcesionesAecidBdns({})

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string
    expect(calledUrl).not.toContain('iso_alpha3=')
  })
})
