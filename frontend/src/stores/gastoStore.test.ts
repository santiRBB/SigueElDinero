import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as api from '../services/api'
import { useGastoStore } from './gastoStore'

vi.mock('../services/api')

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('gastoStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('cargarResumen stores the result and resets loading/error state', async () => {
    const mockData = [{ iso_alpha3: 'COL', nombre: 'Colombia', importe_total_eur: 100, n_intervenciones: 2 }]
    vi.mocked(api.getResumenPaises).mockResolvedValue(mockData)

    const store = useGastoStore()
    const promise = store.cargarResumen()
    expect(store.cargando).toBe(true)
    await promise

    expect(store.paisesResumen).toEqual(mockData)
    expect(store.cargando).toBe(false)
    expect(store.error).toBeNull()
  })

  it('cargarResumen records the error message when the API call fails', async () => {
    vi.mocked(api.getResumenPaises).mockRejectedValue(new Error('Error 500'))

    const store = useGastoStore()
    await store.cargarResumen()

    expect(store.error).toBe('Error 500')
    expect(store.cargando).toBe(false)
  })

  it('cargarResumen ignores a stale response that resolves after a newer request', async () => {
    const mockDataFirst = [{ iso_alpha3: 'COL', nombre: 'Colombia', importe_total_eur: 100, n_intervenciones: 2 }]
    const mockDataSecond = [{ iso_alpha3: 'PER', nombre: 'Peru', importe_total_eur: 200, n_intervenciones: 3 }]
    const first = deferred<typeof mockDataFirst>()
    const second = deferred<typeof mockDataSecond>()

    vi.mocked(api.getResumenPaises).mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise)

    const store = useGastoStore()
    const call1 = store.cargarResumen()
    const call2 = store.cargarResumen()

    second.resolve(mockDataSecond)
    await call2
    first.resolve(mockDataFirst)
    await call1

    expect(store.paisesResumen).toEqual(mockDataSecond)
  })

  it('seleccionarPais loads the detail for the given country', async () => {
    const mockDetalle = { pais: { iso_alpha3: 'COL', nombre: 'Colombia', region: null }, categorias: [], proyectos: [] }
    vi.mocked(api.getDetallePais).mockResolvedValue(mockDetalle)

    const store = useGastoStore()
    await store.seleccionarPais('COL')

    expect(api.getDetallePais).toHaveBeenCalledWith('COL', undefined, undefined)
    expect(store.detallePais).toEqual(mockDetalle)
    expect(store.detalleError).toBeNull()
  })

  it('seleccionarPais shows a friendly message when the country has no data (404)', async () => {
    const notFound = Object.assign(new Error('Error 404 al llamar a /api/paises/XYZ/detalle'), { status: 404 })
    vi.mocked(api.getDetallePais).mockRejectedValue(notFound)

    const store = useGastoStore()
    await store.seleccionarPais('XYZ')

    expect(store.detallePais).toBeNull()
    expect(store.detalleError).toBe('Este país no tiene proyectos registrados.')
  })

  it('seleccionarPais keeps the raw error message for non-404 failures', async () => {
    const serverError = Object.assign(new Error('Error 500 al llamar a /api/paises/XYZ/detalle'), { status: 500 })
    vi.mocked(api.getDetallePais).mockRejectedValue(serverError)

    const store = useGastoStore()
    await store.seleccionarPais('XYZ')

    expect(store.detallePais).toBeNull()
    expect(store.detalleError).toBe('Error 500 al llamar a /api/paises/XYZ/detalle')
  })

  it('seleccionarPais ignores a stale detalle response that resolves after a newer selection', async () => {
    const detalleA = { pais: { iso_alpha3: 'COL', nombre: 'Colombia', region: null }, categorias: [], proyectos: [] }
    const detalleB = { pais: { iso_alpha3: 'PER', nombre: 'Peru', region: null }, categorias: [], proyectos: [] }
    const first = deferred<typeof detalleA>()
    const second = deferred<typeof detalleB>()

    vi.mocked(api.getDetallePais).mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise)

    const store = useGastoStore()
    const call1 = store.seleccionarPais('COL')
    const call2 = store.seleccionarPais('PER')

    second.resolve(detalleB)
    await call2
    first.resolve(detalleA)
    await call1

    expect(store.detallePais).toEqual(detalleB)
  })

  it('cargarPaisPorAnio stores the yearly evolution for a country', async () => {
    const datos = [{ anio: 2024, importe_eur: 100, n_intervenciones: 2 }]
    vi.mocked(api.getPaisPorAnio).mockResolvedValue(datos)

    const store = useGastoStore()
    await store.cargarPaisPorAnio('COL')

    expect(api.getPaisPorAnio).toHaveBeenCalledWith('COL', undefined)
    expect(store.paisPorAnio).toEqual(datos)
  })

  it('cargarPaisPorAnio clears stale data immediately so a previous country never flashes under a new one', async () => {
    const datosPrevios = [{ anio: 2024, importe_eur: 100, n_intervenciones: 2 }]
    const pending = deferred<typeof datosPrevios>()
    vi.mocked(api.getPaisPorAnio).mockReturnValue(pending.promise)

    const store = useGastoStore()
    store.paisPorAnio = datosPrevios

    const call = store.cargarPaisPorAnio('BOL')
    expect(store.paisPorAnio).toEqual([])

    pending.resolve([{ anio: 2024, importe_eur: 200, n_intervenciones: 3 }])
    await call

    expect(store.paisPorAnio).toEqual([{ anio: 2024, importe_eur: 200, n_intervenciones: 3 }])
  })

  it('cargarResumenCcaa stores the result', async () => {
    const mockData = [{ codigo_ine: '09', nombre: 'Cataluña', importe_total_eur: 100, n_concesiones: 2 }]
    vi.mocked(api.getResumenCcaa).mockResolvedValue(mockData)

    const store = useGastoStore()
    await store.cargarResumenCcaa()

    expect(store.resumenCcaa).toEqual(mockData)
  })

  it('cargarResumenCcaa clears stale data immediately so a previous filter never flashes under a new one', async () => {
    const datosPrevios = [{ codigo_ine: '09', nombre: 'Cataluña', importe_total_eur: 100, n_concesiones: 2 }]
    const pending = deferred<typeof datosPrevios>()
    vi.mocked(api.getResumenCcaa).mockReturnValue(pending.promise)

    const store = useGastoStore()
    store.resumenCcaa = datosPrevios

    const call = store.cargarResumenCcaa()
    expect(store.resumenCcaa).toEqual([])

    pending.resolve([{ codigo_ine: '13', nombre: 'Comunidad de Madrid', importe_total_eur: 200, n_concesiones: 3 }])
    await call

    expect(store.resumenCcaa).toEqual([{ codigo_ine: '13', nombre: 'Comunidad de Madrid', importe_total_eur: 200, n_concesiones: 3 }])
  })

  it('cargarResumenCcaa resets resumenCcaa on failure without touching the shared error field', async () => {
    vi.mocked(api.getResumenCcaa).mockRejectedValue(new Error('Error 500 al llamar a /api/ccaa/resumen'))

    const store = useGastoStore()
    store.resumenCcaa = [{ codigo_ine: '09', nombre: 'Cataluña', importe_total_eur: 100, n_concesiones: 2 }]
    store.error = null
    await store.cargarResumenCcaa()

    expect(store.resumenCcaa).toEqual([])
    expect(store.error).toBeNull()
  })

  it('seleccionarCcaa loads the detail for the given ccaa', async () => {
    const mockDetalle = {
      ccaa: { codigo_ine: '09', nombre: 'Cataluña' },
      importe_total_eur: 500,
      n_concesiones: 3,
      organismos: [],
    }
    vi.mocked(api.getDetalleCcaa).mockResolvedValue(mockDetalle)

    const store = useGastoStore()
    await store.seleccionarCcaa('09')

    expect(api.getDetalleCcaa).toHaveBeenCalledWith('09', undefined)
    expect(store.detalleCcaa).toEqual(mockDetalle)
    expect(store.detalleCcaaError).toBeNull()
  })

  it('seleccionarCcaa shows a friendly message when the ccaa has no data (404)', async () => {
    const notFound = Object.assign(new Error('Error 404 al llamar a /api/ccaa/99/detalle'), { status: 404 })
    vi.mocked(api.getDetalleCcaa).mockRejectedValue(notFound)

    const store = useGastoStore()
    await store.seleccionarCcaa('99')

    expect(store.detalleCcaa).toBeNull()
    expect(store.detalleCcaaError).toBe('Esta comunidad no tiene concesiones registradas.')
  })

  it('seleccionarCcaa ignores a stale detalle response that resolves after a newer selection', async () => {
    const detalleA = {
      ccaa: { codigo_ine: '09', nombre: 'Cataluña' },
      importe_total_eur: 500,
      n_concesiones: 3,
      organismos: [],
    }
    const detalleB = {
      ccaa: { codigo_ine: '13', nombre: 'Comunidad de Madrid' },
      importe_total_eur: 700,
      n_concesiones: 5,
      organismos: [],
    }
    const first = deferred<typeof detalleA>()
    const second = deferred<typeof detalleB>()

    vi.mocked(api.getDetalleCcaa).mockImplementationOnce(() => first.promise).mockImplementationOnce(() => second.promise)

    const store = useGastoStore()
    const call1 = store.seleccionarCcaa('09')
    const call2 = store.seleccionarCcaa('13')

    second.resolve(detalleB)
    await call2
    first.resolve(detalleA)
    await call1

    expect(store.detalleCcaa).toEqual(detalleB)
  })

  it('cargarCcaaPorAnio stores the yearly evolution for a ccaa', async () => {
    const datos = [{ anio: 2024, importe_eur: 100, n_concesiones: 2 }]
    vi.mocked(api.getCcaaPorAnio).mockResolvedValue(datos)

    const store = useGastoStore()
    await store.cargarCcaaPorAnio('09')

    expect(api.getCcaaPorAnio).toHaveBeenCalledWith('09')
    expect(store.ccaaPorAnio).toEqual(datos)
  })

  it('cargarResumenAecidBdns loads the preliminary AECID/BDNS summary', async () => {
    const fake = {
      por_pais: [{ iso_alpha3: 'CRI', pais_nombre: 'Costa Rica', importe_eur: 261818.6, n_concesiones: 1 }],
      sin_pais: { importe_eur: 50000, n_concesiones: 3 },
    }
    vi.mocked(api.getResumenAecidBdns).mockResolvedValue(fake)

    const store = useGastoStore()
    await store.cargarResumenAecidBdns()

    expect(store.resumenAecidBdns).toEqual(fake)
  })

  it('cargarResumenAecidBdns leaves resumenAecidBdns null on failure', async () => {
    vi.mocked(api.getResumenAecidBdns).mockRejectedValue(new Error('boom'))

    const store = useGastoStore()
    await store.cargarResumenAecidBdns()

    expect(store.resumenAecidBdns).toBeNull()
  })

  it('cargarCcaaPorAnio clears stale data immediately so a previous ccaa never flashes under a new one', async () => {
    const datosPrevios = [{ anio: 2024, importe_eur: 100, n_concesiones: 2 }]
    const pending = deferred<typeof datosPrevios>()
    vi.mocked(api.getCcaaPorAnio).mockReturnValue(pending.promise)

    const store = useGastoStore()
    store.ccaaPorAnio = datosPrevios

    const call = store.cargarCcaaPorAnio('13')
    expect(store.ccaaPorAnio).toEqual([])

    pending.resolve([{ anio: 2024, importe_eur: 200, n_concesiones: 3 }])
    await call

    expect(store.ccaaPorAnio).toEqual([{ anio: 2024, importe_eur: 200, n_concesiones: 3 }])
  })

  it('setFiltroAnio updates the filter and re-fetches resumen and resumenPorGrupo', async () => {
    vi.mocked(api.getResumenPaises).mockResolvedValue([])
    vi.mocked(api.getResumenPorGrupo).mockResolvedValue([])
    const store = useGastoStore()

    await store.setFiltroAnio(2025)

    expect(store.filtroAnio).toBe(2025)
    expect(api.getResumenPaises).toHaveBeenCalledWith(2025, undefined)
    expect(api.getResumenPorGrupo).toHaveBeenCalledWith(2025)
  })

  it('setFiltroGrupo updates the filter and re-fetches resumen and resumenPorAnio', async () => {
    vi.mocked(api.getResumenPaises).mockResolvedValue([])
    vi.mocked(api.getResumenPorAnio).mockResolvedValue([])
    const store = useGastoStore()

    await store.setFiltroGrupo('720')

    expect(store.filtroGrupo).toBe('720')
    expect(api.getResumenPaises).toHaveBeenCalledWith(undefined, '720')
    expect(api.getResumenPorAnio).toHaveBeenCalledWith('720')
  })

  it('cargarFiltros populates aniosDisponibles and gruposDisponibles', async () => {
    vi.mocked(api.getAnios).mockResolvedValue([2023, 2024, 2025])
    vi.mocked(api.getSectores).mockResolvedValue([{ codigo_grupo: '720', nombre: 'Emergency Response' }])

    const store = useGastoStore()
    await store.cargarFiltros()

    expect(store.aniosDisponibles).toEqual([2023, 2024, 2025])
    expect(store.gruposDisponibles).toEqual([{ codigo_grupo: '720', nombre: 'Emergency Response' }])
  })

  it('cargarFiltros records the error message when the API call fails', async () => {
    vi.mocked(api.getAnios).mockRejectedValue(new Error('Error 500 al llamar a /api/filtros/anios'))
    vi.mocked(api.getSectores).mockResolvedValue([])

    const store = useGastoStore()
    await store.cargarFiltros()

    expect(store.error).toBe('Error 500 al llamar a /api/filtros/anios')
  })

  it('cargarFiltros clears a previous error once a later call succeeds', async () => {
    vi.mocked(api.getAnios).mockRejectedValueOnce(new Error('Error 500 al llamar a /api/filtros/anios'))
    vi.mocked(api.getSectores).mockResolvedValue([])

    const store = useGastoStore()
    await store.cargarFiltros()
    expect(store.error).toBe('Error 500 al llamar a /api/filtros/anios')

    vi.mocked(api.getAnios).mockResolvedValueOnce([2023, 2024, 2025])
    await store.cargarFiltros()

    expect(store.error).toBeNull()
  })

  it('cargarResumenPorAnio and cargarResumenPorGrupo store their results', async () => {
    vi.mocked(api.getResumenPorAnio).mockResolvedValue([{ anio: 2024, importe_eur: 100, n_intervenciones: 2 }])
    vi.mocked(api.getResumenPorGrupo).mockResolvedValue([{ codigo_grupo: '720', nombre: 'Emergency Response', importe_eur: 500, n_intervenciones: 1 }])

    const store = useGastoStore()
    await store.cargarResumenPorAnio()
    await store.cargarResumenPorGrupo()

    expect(store.resumenPorAnio).toEqual([{ anio: 2024, importe_eur: 100, n_intervenciones: 2 }])
    expect(store.resumenPorGrupo).toEqual([{ codigo_grupo: '720', nombre: 'Emergency Response', importe_eur: 500, n_intervenciones: 1 }])
  })

  it('buscarProyectos stores results, total, and pagina, and resets loading state', async () => {
    const mockResultado = { total: 1, pagina: 1, por_pagina: 30, resultados: [{ aid: 'AID-1' }] }
    vi.mocked(api.buscarProyectos).mockResolvedValue(mockResultado as never)

    const store = useGastoStore()
    store.queryBusqueda = 'agua'
    const promise = store.buscarProyectos()
    expect(store.cargandoBusqueda).toBe(true)
    await promise

    expect(api.buscarProyectos).toHaveBeenCalledWith({ q: 'agua', anio: undefined, grupo: undefined, pagina: 1, orden: 'importe_desc' })
    expect(store.resultadosBusqueda).toEqual(mockResultado.resultados)
    expect(store.totalBusqueda).toBe(1)
    expect(store.cargandoBusqueda).toBe(false)
    expect(store.errorBusqueda).toBeNull()
  })

  it('buscarProyectos passes the selected ordenBusqueda to the API', async () => {
    const mockResultado = { total: 0, pagina: 1, por_pagina: 30, resultados: [] }
    vi.mocked(api.buscarProyectos).mockResolvedValue(mockResultado as never)

    const store = useGastoStore()
    store.ordenBusqueda = 'fecha_asc'
    await store.buscarProyectos()

    expect(api.buscarProyectos).toHaveBeenCalledWith(expect.objectContaining({ orden: 'fecha_asc' }))
  })

  it('buscarProyectos records the error message when the API call fails', async () => {
    vi.mocked(api.buscarProyectos).mockRejectedValue(new Error('Error 500 al llamar a /api/proyectos/buscar'))

    const store = useGastoStore()
    await store.buscarProyectos()

    expect(store.errorBusqueda).toBe('Error 500 al llamar a /api/proyectos/buscar')
    expect(store.cargandoBusqueda).toBe(false)
  })

  it('cargarConcesionesAecidBdns stores results, total, and pagina, and resets loading state', async () => {
    const mockResultado = {
      total: 1, pagina: 1, por_pagina: 30,
      resultados: [{
        concesion_id: 1, beneficiario: 'ONG X', titulo: 'Convocatoria X', importe_eur: 1000,
        fecha_concesion: '2026-01-01', iso_alpha3: 'MLI', pais_nombre: 'Mali',
        url_bdns: 'https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/1',
      }],
    }
    vi.mocked(api.getConcesionesAecidBdns).mockResolvedValue(mockResultado as never)

    const store = useGastoStore()
    const promise = store.cargarConcesionesAecidBdns()
    expect(store.cargandoConcesionesAecidBdns).toBe(true)
    await promise

    expect(store.concesionesAecidBdns).toEqual(mockResultado.resultados)
    expect(store.totalConcesionesAecidBdns).toBe(1)
    expect(store.paginaConcesionesAecidBdns).toBe(1)
    expect(store.cargandoConcesionesAecidBdns).toBe(false)
    expect(store.errorConcesionesAecidBdns).toBeNull()
    expect(api.getConcesionesAecidBdns).toHaveBeenCalledWith({ iso_alpha3: undefined, pagina: 1, por_pagina: 30 })
  })

  it('cargarConcesionesAecidBdns records the error message when the API call fails', async () => {
    vi.mocked(api.getConcesionesAecidBdns).mockRejectedValue(new Error('Error 500'))

    const store = useGastoStore()
    await store.cargarConcesionesAecidBdns()

    expect(store.errorConcesionesAecidBdns).toBe('Error 500')
    expect(store.cargandoConcesionesAecidBdns).toBe(false)
  })

  it('cargarConcesionesAecidBdns clears stale concesiones/total on failure so a previous country never keeps showing under a new one', async () => {
    const mockResultado = {
      total: 1, pagina: 1, por_pagina: 30,
      resultados: [{
        concesion_id: 1, beneficiario: 'ONG X', titulo: 'Convocatoria X', importe_eur: 1000,
        fecha_concesion: '2026-01-01', iso_alpha3: 'MLI', pais_nombre: 'Mali',
        url_bdns: 'https://www.pap.hacienda.gob.es/bdnstrans/GE/es/convocatorias/1',
      }],
    }
    vi.mocked(api.getConcesionesAecidBdns).mockResolvedValueOnce(mockResultado as never)

    const store = useGastoStore()
    await store.cargarConcesionesAecidBdns()
    expect(store.concesionesAecidBdns).toEqual(mockResultado.resultados)
    expect(store.totalConcesionesAecidBdns).toBe(1)

    vi.mocked(api.getConcesionesAecidBdns).mockRejectedValueOnce(new Error('Error de red'))
    await store.cargarConcesionesAecidBdns()

    expect(store.errorConcesionesAecidBdns).toBe('Error de red')
    expect(store.concesionesAecidBdns).toEqual([])
    expect(store.totalConcesionesAecidBdns).toBe(0)
  })

  it('cargarConcesionesAecidBdns ignores a stale response that resolves after a newer request', async () => {
    const mockFirst = { total: 1, pagina: 1, por_pagina: 30, resultados: [{ concesion_id: 1 }] }
    const mockSecond = { total: 2, pagina: 1, por_pagina: 30, resultados: [{ concesion_id: 2 }] }
    const first = deferred<typeof mockFirst>()
    const second = deferred<typeof mockSecond>()

    vi.mocked(api.getConcesionesAecidBdns).mockImplementationOnce(() => first.promise as never).mockImplementationOnce(() => second.promise as never)

    const store = useGastoStore()
    const call1 = store.cargarConcesionesAecidBdns()
    const call2 = store.cargarConcesionesAecidBdns()

    second.resolve(mockSecond)
    await call2
    first.resolve(mockFirst)
    await call1

    expect(store.totalConcesionesAecidBdns).toBe(2)
  })

  it('setFiltroPaisConcesionesAecidBdns sets the filter and reloads at page 1', async () => {
    vi.mocked(api.getConcesionesAecidBdns).mockResolvedValue({ total: 0, pagina: 1, por_pagina: 30, resultados: [] } as never)

    const store = useGastoStore()
    store.paginaConcesionesAecidBdns = 3
    await store.setFiltroPaisConcesionesAecidBdns('MLI')

    expect(store.filtroPaisConcesionesAecidBdns).toBe('MLI')
    expect(api.getConcesionesAecidBdns).toHaveBeenCalledWith({ iso_alpha3: 'MLI', pagina: 1, por_pagina: 30 })
  })
})
