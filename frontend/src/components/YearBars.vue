<script setup lang="ts">
import { computed } from 'vue'
import { formatEURCompacto } from '../utils/formato'

export interface AnioValor {
  anio: number
  importe_eur: number
}

const props = defineProps<{
  datos: AnioValor[]
  anioActivo: number | null
}>()

const emit = defineEmits<{
  (e: 'select', anio: number): void
}>()

const maxValor = computed(() => Math.max(1, ...props.datos.map((d) => d.importe_eur)))

function altura(valor: number): number {
  return Math.max(6, (valor / maxValor.value) * 92)
}
</script>

<template>
  <div class="years">
    <button
      v-for="d in datos"
      :key="d.anio"
      type="button"
      class="yr"
      :class="{ on: d.anio === anioActivo }"
      @click="emit('select', d.anio)"
    >
      <span class="yr-bar" :style="{ height: altura(d.importe_eur) + 'px' }"></span>
      <span class="yr-v">{{ formatEURCompacto(d.importe_eur) }}</span>
      <span class="yr-y">{{ d.anio }}</span>
    </button>
  </div>
</template>

<style scoped>
.years {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.yr {
  flex: 1;
  background: none;
  border: 0;
  padding: 0 0 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 7px;
  font-family: inherit;
  border-bottom: 1px solid var(--rule);
  text-align: left;
}
@media (max-width: 860px) {
  .years {
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    padding-bottom: 4px;
  }
  .yr {
    flex: 0 0 auto;
    min-width: 64px;
    scroll-snap-align: start;
  }
}
.yr-bar {
  display: block;
  background: #c6d2dc;
  transition: background 0.15s;
}
.yr:hover .yr-bar {
  background: #9bb0c1;
}
.yr.on .yr-bar {
  background: var(--navy);
}
.yr-v {
  font-size: 12px;
  color: var(--dim);
}
.yr.on .yr-v {
  color: var(--ink);
}
.yr-y {
  font-size: 13px;
  letter-spacing: 0.06em;
  color: var(--dim);
}
.yr.on .yr-y {
  color: var(--ink);
  font-weight: 500;
}
</style>
