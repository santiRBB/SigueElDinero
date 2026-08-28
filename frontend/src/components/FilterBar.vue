<script setup lang="ts">
import { useGastoStore } from '../stores/gastoStore'

const store = useGastoStore()

function onAnioChange(event: Event) {
  const valor = (event.target as HTMLSelectElement).value
  store.setFiltroAnio(valor === '' ? null : Number(valor))
}

function onGrupoChange(event: Event) {
  const valor = (event.target as HTMLSelectElement).value
  store.setFiltroGrupo(valor === '' ? null : valor)
}
</script>

<template>
  <div class="controls">
    <label class="ctl">
      <span>Año</span>
      <select :value="store.filtroAnio ?? ''" @change="onAnioChange">
        <option value="">Todos</option>
        <option v-for="anio in store.aniosDisponibles" :key="anio" :value="anio">{{ anio }}</option>
      </select>
    </label>
    <label class="ctl">
      <span>Sector</span>
      <select :value="store.filtroGrupo ?? ''" @change="onGrupoChange">
        <option value="">Todos los sectores</option>
        <option v-for="grupo in store.gruposDisponibles" :key="grupo.codigo_grupo" :value="grupo.codigo_grupo">
          {{ grupo.nombre }}
        </option>
      </select>
    </label>
  </div>
</template>

<style scoped>
.controls {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.ctl {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ctl span {
  font-size: 10.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--dim);
}
.ctl select {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--ink);
  border-radius: 0;
  padding: 7px 30px 7px 10px;
  appearance: none;
  cursor: pointer;
  background-image: linear-gradient(45deg, transparent 50%, var(--ink) 50%), linear-gradient(135deg, var(--ink) 50%, transparent 50%);
  background-position: calc(100% - 15px) 15px, calc(100% - 10px) 15px;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}
.ctl select:focus {
  outline: 2px solid var(--amber);
  outline-offset: 1px;
}
</style>
