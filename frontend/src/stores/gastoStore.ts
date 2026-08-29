import { defineStore } from 'pinia'
import {
  buscarProyectos as apiBuscarProyectos,
  getAnios,
  getDetallePais,
  getPaisPorAnio,
  getResumenPaises,
  getResumenPorAnio,
  getResumenPorGrupo,
  getSectores,
} from '../services/api'
import type { AnioImporte, Grupo, GrupoImporte, Orden, PaisDetalle, PaisResumen, ProyectoBusqueda } from '../services/api'

interface GastoState {
  paisesResumen: PaisResumen[]
  detallePais: PaisDetalle | null
  detalleError: string | null
  paisPorAnio: AnioImporte[]
  aniosDisponibles: number[]
  gruposDisponibles: Grupo[]
  filtroAnio: number | null
  filtroGrupo: string | null
  cargando: boolean
  error: string | null
  resumenPorAnio: AnioImporte[]
  resumenPorGrupo: GrupoImporte[]
  resultadosBusqueda: ProyectoBusqueda[]
  totalBusqueda: number
  queryBusqueda: string
  paginaBusqueda: number
  ordenBusqueda: Orden
  cargandoBusqueda: boolean
  errorBusqueda: string | null
}

// Module-scoped request tokens guard against stale out-of-order async
// responses overwriting newer state, one per independently-triggered fetch.
// useGastoStore() is a singleton in this app, so plain module-level counters
// are sufficient and keep these implementation details out of the store's
// public reactive state.
let resumenRequestToken = 0
let detalleRequestToken = 0
let porAnioRequestToken = 0
let porGrupoRequestToken = 0
let paisPorAnioRequestToken = 0
let busquedaRequestToken = 0

export const useGastoStore = defineStore('gasto', {
  state: (): GastoState => ({
    paisesResumen: [],
    detallePais: null,
    detalleError: null,
    paisPorAnio: [],
    aniosDisponibles: [],
    gruposDisponibles: [],
    filtroAnio: null,
    filtroGrupo: null,
    cargando: false,
    error: null,
    resumenPorAnio: [],
    resumenPorGrupo: [],
    resultadosBusqueda: [],
    totalBusqueda: 0,
    queryBusqueda: '',
    paginaBusqueda: 1,
    ordenBusqueda: 'importe_desc',
    cargandoBusqueda: false,
    errorBusqueda: null,
  }),
  actions: {
    async cargarFiltros() {
      this.error = null
      try {
        const [anios, grupos] = await Promise.all([getAnios(), getSectores()])
        this.aniosDisponibles = anios
        this.gruposDisponibles = grupos
      } catch (e) {
        this.error = (e as Error).message
      }
    },
    async cargarResumen() {
      const token = ++resumenRequestToken
      this.cargando = true
      this.error = null
      try {
        const data = await getResumenPaises(this.filtroAnio ?? undefined, this.filtroGrupo ?? undefined)
        if (token !== resumenRequestToken) return
        this.paisesResumen = data
      } catch (e) {
        if (token !== resumenRequestToken) return
        this.error = (e as Error).message
      } finally {
        if (token === resumenRequestToken) {
          this.cargando = false
        }
      }
    },
    async cargarResumenPorAnio() {
      const token = ++porAnioRequestToken
      this.error = null
      try {
        const data = await getResumenPorAnio(this.filtroGrupo ?? undefined)
        if (token !== porAnioRequestToken) return
        this.resumenPorAnio = data
      } catch (e) {
        if (token !== porAnioRequestToken) return
        this.error = (e as Error).message
      }
    },
    async cargarResumenPorGrupo() {
      const token = ++porGrupoRequestToken
      this.error = null
      try {
        const data = await getResumenPorGrupo(this.filtroAnio ?? undefined)
        if (token !== porGrupoRequestToken) return
        this.resumenPorGrupo = data
      } catch (e) {
        if (token !== porGrupoRequestToken) return
        this.error = (e as Error).message
      }
    },
    async seleccionarPais(iso3: string) {
      const token = ++detalleRequestToken
      this.detallePais = null
      this.detalleError = null
      try {
        const data = await getDetallePais(iso3, this.filtroAnio ?? undefined)
        if (token !== detalleRequestToken) return
        this.detallePais = data
      } catch (e) {
        if (token !== detalleRequestToken) return
        const status = (e as { status?: number }).status
        this.detalleError =
          status === 404 ? 'Este país no tiene proyectos registrados.' : (e as Error).message
      }
    },
    async cargarPaisPorAnio(iso3: string) {
      const token = ++paisPorAnioRequestToken
      try {
        const data = await getPaisPorAnio(iso3, this.filtroGrupo ?? undefined)
        if (token !== paisPorAnioRequestToken) return
        this.paisPorAnio = data
      } catch {
        if (token !== paisPorAnioRequestToken) return
        this.paisPorAnio = []
      }
    },
    async setFiltroAnio(anio: number | null) {
      this.filtroAnio = anio
      await Promise.all([this.cargarResumen(), this.cargarResumenPorGrupo()])
    },
    async setFiltroGrupo(grupo: string | null) {
      this.filtroGrupo = grupo
      await Promise.all([this.cargarResumen(), this.cargarResumenPorAnio()])
    },
    async buscarProyectos(pagina = 1) {
      const token = ++busquedaRequestToken
      this.cargandoBusqueda = true
      this.errorBusqueda = null
      try {
        const data = await apiBuscarProyectos({
          q: this.queryBusqueda || undefined,
          anio: this.filtroAnio ?? undefined,
          grupo: this.filtroGrupo ?? undefined,
          pagina,
          orden: this.ordenBusqueda,
        })
        if (token !== busquedaRequestToken) return
        this.resultadosBusqueda = data.resultados
        this.totalBusqueda = data.total
        this.paginaBusqueda = data.pagina
      } catch (e) {
        if (token !== busquedaRequestToken) return
        this.errorBusqueda = (e as Error).message
      } finally {
        if (token === busquedaRequestToken) {
          this.cargandoBusqueda = false
        }
      }
    },
  },
})
