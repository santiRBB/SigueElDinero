<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGastoStore } from '../stores/gastoStore'
import WorldMap from '../components/WorldMap.vue'
import FilterBar from '../components/FilterBar.vue'
import CountryTable from '../components/CountryTable.vue'
import { formatEURCompacto } from '../utils/formato'

const store = useGastoStore()
const router = useRouter()

onMounted(() => {
  void Promise.all([store.cargarFiltros(), store.cargarResumen()])
})

function onCountryClick(iso3: string) {
  router.push(`/paises/${iso3}`)
}
</script>

<template>
  <section class="page-head">
    <p class="kicker">Mapa</p>
    <h1 class="h-page">El reparto, país a país</h1>
    <FilterBar />
  </section>

  <p v-if="store.error" class="error">{{ store.error }}</p>

  <div class="map-wrap">
    <WorldMap class="mapa-grande" :paises-resumen="store.paisesResumen" @country-click="onCountryClick" />
  </div>

  <section class="block">
    <h2 class="sec-title">
      {{ store.paisesResumen.length }} países ·
      {{ formatEURCompacto(store.paisesResumen.reduce((acc, p) => acc + p.importe_total_eur, 0)) }}
    </h2>
    <CountryTable :paises="store.paisesResumen" />
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
  margin-top: 26px;
  position: relative;
}
.mapa-grande {
  min-height: 560px;
}
@media (max-width: 860px) {
  .mapa-grande {
    min-height: 0;
  }
}
</style>
