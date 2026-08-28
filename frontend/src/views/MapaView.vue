<script setup lang="ts">
import { onMounted } from 'vue'
import { useGastoStore } from '../stores/gastoStore'
import WorldMap from '../components/WorldMap.vue'
import CountryPanel from '../components/CountryPanel.vue'
import FilterBar from '../components/FilterBar.vue'

const store = useGastoStore()

onMounted(async () => {
  await store.cargarFiltros()
  await store.cargarResumen()
})

function onCountryClick(iso3: string) {
  store.seleccionarPais(iso3)
}
</script>

<template>
  <div class="mapa-view">
    <FilterBar />
    <WorldMap class="mapa" :paises-resumen="store.paisesResumen" @country-click="onCountryClick" />
    <CountryPanel />
  </div>
</template>

<style scoped>
.mapa-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.mapa {
  flex: 1;
}
</style>
