<script setup lang="ts">
import type { Orden } from '../services/api'

defineProps<{ modelValue: Orden }>()
const emit = defineEmits<{ 'update:modelValue': [value: Orden] }>()

function onChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLSelectElement).value as Orden)
}
</script>

<template>
  <label class="ctl">
    <span>Ordenar por</span>
    <select :value="modelValue" @change="onChange">
      <option value="importe_desc">Cantidad (mayor a menor)</option>
      <option value="importe_asc">Cantidad (menor a mayor)</option>
      <option value="fecha_desc">Fecha (más reciente)</option>
      <option value="fecha_asc">Fecha (más antigua)</option>
    </select>
  </label>
</template>

<style scoped>
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
