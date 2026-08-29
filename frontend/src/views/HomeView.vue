<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGastoStore } from '../stores/gastoStore'
import FilterBar from '../components/FilterBar.vue'
import WorldMap from '../components/WorldMap.vue'
import StatTile from '../components/StatTile.vue'
import YearBars from '../components/YearBars.vue'
import BarList from '../components/BarList.vue'
import { formatEURCompacto } from '../utils/formato'

const store = useGastoStore()
const router = useRouter()

onMounted(() => {
  void Promise.all([
    store.cargarFiltros(),
    store.cargarResumen(),
    store.cargarResumenPorAnio(),
    store.cargarResumenPorGrupo(),
  ])
})

const totalImporte = computed(() => store.paisesResumen.reduce((acc, p) => acc + p.importe_total_eur, 0))
const nPaises = computed(() => store.paisesResumen.length)
const nProyectos = computed(() => store.paisesResumen.reduce((acc, p) => acc + p.n_intervenciones, 0))
const grupoTop = computed(() => {
  const filas = [...store.resumenPorGrupo].sort((a, b) => b.importe_eur - a.importe_eur)
  return filas[0]?.nombre ?? filas[0]?.codigo_grupo ?? '—'
})
const etiquetaAnio = computed(() => (store.filtroAnio === null ? 'en el periodo disponible' : `en ${store.filtroAnio}`))

const filasPaises = computed(() =>
  [...store.paisesResumen]
    .sort((a, b) => b.importe_total_eur - a.importe_total_eur)
    .slice(0, 12)
    .map((p) => ({ etiqueta: p.nombre, valor: p.importe_total_eur, to: `/paises/${p.iso_alpha3}` }))
)
const filasGrupos = computed(() =>
  [...store.resumenPorGrupo]
    .sort((a, b) => b.importe_eur - a.importe_eur)
    .map((g) => ({ etiqueta: g.nombre ?? g.codigo_grupo ?? 'Sin grupo', valor: g.importe_eur }))
)

function onCountryClick(iso3: string) {
  router.push(`/paises/${iso3}`)
}

function onSelectYear(anio: number) {
  store.setFiltroAnio(store.filtroAnio === anio ? null : anio)
}
</script>

<template>
  <section class="hero">
    <p class="kicker">Cooperación española · datos AECID/IATI</p>
    <h1>España destinó <em>{{ formatEURCompacto(totalImporte) }}</em> a {{ nPaises }} países {{ etiquetaAnio }}.</h1>
    <p class="deck">
      Cada euro de este mapa está asociado a un proyecto con país, sector, entidad ejecutora y fechas.
      Elige un año o un grupo de sector para ver cómo cambia el reparto, o pincha en un país para ver
      qué se financia allí.
    </p>
  </section>

  <p v-if="store.error" class="error">{{ store.error }}</p>

  <section class="stats">
    <StatTile :valor="formatEURCompacto(totalImporte)" :etiqueta="`Comprometido ${etiquetaAnio}`" />
    <StatTile :valor="String(nProyectos)" etiqueta="Intervenciones" />
    <StatTile :valor="String(nPaises)" etiqueta="Países receptores" />
    <StatTile :valor="grupoTop" etiqueta="Sector con más fondos" />
  </section>

  <section class="block">
    <h2 class="sec-title">Por año</h2>
    <YearBars :datos="store.resumenPorAnio" :anio-activo="store.filtroAnio" @select="onSelectYear" />
  </section>

  <section class="block">
    <div class="block-head">
      <h2 class="sec-title">Dónde va el dinero</h2>
      <FilterBar />
    </div>
    <div class="map-wrap">
      <WorldMap :paises-resumen="store.paisesResumen" @country-click="onCountryClick" />
    </div>
    <p class="note">Pasa el cursor por un país para ver el total; pincha para abrir su ficha.</p>
  </section>

  <section class="cols">
    <div class="block">
      <h2 class="sec-title">Principales receptores</h2>
      <BarList :filas="filasPaises" con-rango />
      <p class="note"><router-link to="/mapa">Ver la tabla completa</router-link></p>
    </div>
    <div class="block">
      <h2 class="sec-title">Reparto por sector</h2>
      <BarList :filas="filasGrupos" />
    </div>
  </section>
</template>

<style scoped>
.error {
  margin: 14px 0 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
}
.map-wrap {
  position: relative;
  margin-top: 8px;
  background: var(--paper);
}
</style>
