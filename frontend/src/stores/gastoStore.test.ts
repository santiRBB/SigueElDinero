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

    expect(api.getDetallePais).toHaveBeenCalledWith('COL', undefined)
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
})
