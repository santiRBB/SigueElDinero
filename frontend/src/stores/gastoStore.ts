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
      this.cargando = true
      this.error = null
      try {
        this.paisesResumen = await getResumenPaises(this.filtroAnio ?? undefined, this.filtroSector ?? undefined)
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.cargando = false
      }
    },
    async seleccionarPais(iso3: string) {
      this.paisSeleccionado = iso3
      this.detallePais = null
      this.detallePais = await getDetallePais(iso3, this.filtroAnio ?? undefined)
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
