<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGastoStore } from '../stores/gastoStore'
import { aplicarHead } from '../utils/head'
import StatTile from '../components/StatTile.vue'
import BarList from '../components/BarList.vue'
import YearBars from '../components/YearBars.vue'
import FilterBar from '../components/FilterBar.vue'
import { formatEURCompacto } from '../utils/formato'

const route = useRoute()
const store = useGastoStore()

const codigoIne = computed(() => String(route.params.codigoIne))

function cargarDetalle() {
  void store.seleccionarCcaa(codigoIne.value)
}

onMounted(() => {
  if (!store.aniosDisponibles.length) void store.cargarFiltros()
  cargarDetalle()
  void store.cargarCcaaPorAnio(codigoIne.value)
})
watch(codigoIne, () => {
  cargarDetalle()
  void store.cargarCcaaPorAnio(codigoIne.value)
})
watch(() => store.filtroAnio, cargarDetalle)
watch(
  () => store.detalleCcaa,
  (detalle) => {
    if (!detalle) return
    aplicarHead({
      titulo: `Subvenciones de cooperación en ${detalle.ccaa.nombre}`,
      descripcion: `Concesiones de subvenciones públicas registradas en BDNS en ${detalle.ccaa.nombre}: importe, organismos concedentes y evolución por año.`,
      indexable: false,
      ruta: `/ccaa/${detalle.ccaa.codigo_ine}`,
    })
  },
  { immediate: true },
)

const filasOrganismos = computed(() =>
  (store.detalleCcaa?.organismos ?? []).map((o) => ({ etiqueta: o.organismo, valor: o.importe_total_eur }))
)

function onSelectYear(anio: number) {
  store.setFiltroAnio(store.filtroAnio === anio ? null : anio)
}
</script>

<template>
  <section class="page-head">
    <p class="kicker"><router-link to="/paises/ESP">España</router-link></p>
    <h1 class="h-page">{{ store.detalleCcaa?.ccaa.nombre ?? codigoIne }}</h1>
    <FilterBar solo-anio />
  </section>

  <p v-if="store.detalleCcaaError" class="error">{{ store.detalleCcaaError }}</p>
  <p v-else-if="!store.detalleCcaa" class="note">Cargando…</p>

  <template v-if="store.detalleCcaa">
    <section class="stats">
      <StatTile :valor="formatEURCompacto(store.detalleCcaa.importe_total_eur)" etiqueta="Concedido en esta comunidad" />
      <StatTile :valor="String(store.detalleCcaa.n_concesiones)" etiqueta="Concesiones" />
    </section>

    <section class="cols">
      <div class="block">
        <h2 class="sec-title">Por organismo</h2>
        <BarList v-if="filasOrganismos.length" :filas="filasOrganismos" />
        <p v-else class="note">Sin datos con este filtro.</p>
      </div>
      <div class="block">
        <h2 class="sec-title">Evolución</h2>
        <YearBars :datos="store.ccaaPorAnio" :anio-activo="store.filtroAnio" @select="onSelectYear" />
      </div>
    </section>
  </template>
</template>

<style scoped>
.error {
  margin: 14px 0 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
}
</style>
