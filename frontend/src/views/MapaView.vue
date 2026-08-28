<script setup lang="ts">
import { onMounted } from 'vue'
import { useGastoStore } from '../stores/gastoStore'
import WorldMap from '../components/WorldMap.vue'
import CountryPanel from '../components/CountryPanel.vue'
import FilterBar from '../components/FilterBar.vue'

const store = useGastoStore()

onMounted(() => {
  void Promise.all([store.cargarFiltros(), store.cargarResumen()])
})

function onCountryClick(iso3: string) {
  store.seleccionarPais(iso3)
}
</script>

<template>
  <div class="mapa-view">
    <p v-if="store.error" class="error">{{ store.error }}</p>
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
.error {
  margin: 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
}
</style>
