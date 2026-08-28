import { defineStore } from 'pinia'
import { getAnios, getDetallePais, getResumenPaises, getSectores } from '../services/api'
import type { PaisDetalle, PaisResumen, Sector } from '../services/api'

interface GastoState {
  paisesResumen: PaisResumen[]
  paisSeleccionado: string | null
  detallePais: PaisDetalle | null
  aniosDisponibles: number[]
  sectoresDisponibles: Sector[]
  filtroAnio: number | null
  filtroSector: string | null
  cargando: boolean
  error: string | null
}

// Module-scoped request tokens to guard against stale out-of-order async
// responses overwriting newer state. useGastoStore() is a singleton in this
// app, so plain module-level counters are sufficient and keep these
// implementation details out of the store's public reactive state.
let resumenRequestToken = 0
let detalleRequestToken = 0

export const useGastoStore = defineStore('gasto', {
  state: (): GastoState => ({
    paisesResumen: [],
    paisSeleccionado: null,
    detallePais: null,
    aniosDisponibles: [],
    sectoresDisponibles: [],
    filtroAnio: null,
    filtroSector: null,
    cargando: false,
    error: null,
  }),
  actions: {
    async cargarFiltros() {
      const [anios, sectores] = await Promise.all([getAnios(), getSectores()])
      this.aniosDisponibles = anios
      this.sectoresDisponibles = sectores
    },
    async cargarResumen() {
      const token = ++resumenRequestToken
      this.cargando = true
      this.error = null
      try {
        const data = await getResumenPaises(this.filtroAnio ?? undefined, this.filtroSector ?? undefined)
        if (token !== resumenRequestToken) return
        this.paisesResumen = data
      } catch (e) {
        if (token !== resumenRequestToken) return
        this.error = (e as Error).message
      } finally {
        if (token !== resumenRequestToken) return
        this.cargando = false
      }
    },
    async seleccionarPais(iso3: string) {
      const token = ++detalleRequestToken
      this.paisSeleccionado = iso3
      this.detallePais = null
      const data = await getDetallePais(iso3, this.filtroAnio ?? undefined)
      if (token !== detalleRequestToken) return
      this.detallePais = data
    },
    cerrarPanel() {
      this.paisSeleccionado = null
      this.detallePais = null
    },
    async setFiltroAnio(anio: number | null) {
      this.filtroAnio = anio
      await this.cargarResumen()
    },
    async setFiltroSector(sector: string | null) {
      this.filtroSector = sector
      await this.cargarResumen()
    },
  },
})
