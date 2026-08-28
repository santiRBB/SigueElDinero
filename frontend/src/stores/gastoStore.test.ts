import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as api from '../services/api'
import { useGastoStore } from './gastoStore'

vi.mock('../services/api')

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

  it('seleccionarPais sets the selected country and loads its detail', async () => {
    const mockDetalle = { pais: { iso_alpha3: 'COL', nombre: 'Colombia', region: null }, categorias: [], proyectos: [] }
    vi.mocked(api.getDetallePais).mockResolvedValue(mockDetalle)

    const store = useGastoStore()
    await store.seleccionarPais('COL')

    expect(api.getDetallePais).toHaveBeenCalledWith('COL', undefined)
    expect(store.paisSeleccionado).toBe('COL')
    expect(store.detallePais).toEqual(mockDetalle)
  })

  it('cerrarPanel clears the selected country and its detail', async () => {
    vi.mocked(api.getDetallePais).mockResolvedValue({ pais: { iso_alpha3: 'COL', nombre: 'Colombia', region: null }, categorias: [], proyectos: [] })
    const store = useGastoStore()
    await store.seleccionarPais('COL')

    store.cerrarPanel()

    expect(store.paisSeleccionado).toBeNull()
    expect(store.detallePais).toBeNull()
  })

  it('setFiltroAnio updates the filter and re-fetches the resumen with it', async () => {
    vi.mocked(api.getResumenPaises).mockResolvedValue([])
    const store = useGastoStore()

    await store.setFiltroAnio(2025)

    expect(store.filtroAnio).toBe(2025)
    expect(api.getResumenPaises).toHaveBeenCalledWith(2025, undefined)
  })

  it('setFiltroSector updates the filter and re-fetches the resumen with it', async () => {
    vi.mocked(api.getResumenPaises).mockResolvedValue([])
    const store = useGastoStore()

    await store.setFiltroSector('72050')

    expect(store.filtroSector).toBe('72050')
    expect(api.getResumenPaises).toHaveBeenCalledWith(undefined, '72050')
  })

  it('cargarFiltros populates aniosDisponibles and sectoresDisponibles', async () => {
    vi.mocked(api.getAnios).mockResolvedValue([2023, 2024, 2025])
    vi.mocked(api.getSectores).mockResolvedValue([{ codigo_crs: '72050', nombre: 'Ayuda humanitaria' }])

    const store = useGastoStore()
    await store.cargarFiltros()

    expect(store.aniosDisponibles).toEqual([2023, 2024, 2025])
    expect(store.sectoresDisponibles).toEqual([{ codigo_crs: '72050', nombre: 'Ayuda humanitaria' }])
  })
})
