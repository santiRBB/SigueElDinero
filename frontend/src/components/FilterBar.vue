<script setup lang="ts">
import { useGastoStore } from '../stores/gastoStore'

const store = useGastoStore()

function onAnioChange(event: Event) {
  const valor = (event.target as HTMLSelectElement).value
  store.setFiltroAnio(valor === '' ? null : Number(valor))
}

function onSectorChange(event: Event) {
  const valor = (event.target as HTMLSelectElement).value
  store.setFiltroSector(valor === '' ? null : valor)
}
</script>

<template>
  <div class="filter-bar">
    <label>
      Año
      <select :value="store.filtroAnio ?? ''" @change="onAnioChange">
        <option value="">Todos</option>
        <option v-for="anio in store.aniosDisponibles" :key="anio" :value="anio">{{ anio }}</option>
      </select>
    </label>
    <label>
      Sector
      <select :value="store.filtroSector ?? ''" @change="onSectorChange">
        <option value="">Todos</option>
        <option v-for="sector in store.sectoresDisponibles" :key="sector.codigo_crs" :value="sector.codigo_crs">
          {{ sector.nombre ?? sector.codigo_crs }}
        </option>
      </select>
    </label>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 1.5rem;
  padding: 1rem;
}
label {
  display: flex;
  flex-direction: column;
  font-size: 0.875rem;
  gap: 0.25rem;
}
</style>
