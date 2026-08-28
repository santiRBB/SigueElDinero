<script setup lang="ts">
import { computed } from 'vue'
import { formatEURCompacto } from '../utils/formato'

export interface FilaBarra {
  etiqueta: string
  valor: number
  to?: string
}

const props = defineProps<{
  filas: FilaBarra[]
  conRango?: boolean
}>()

const maxValor = computed(() => props.filas.reduce((max, f) => Math.max(max, f.valor), 0))

function porcentaje(valor: number): number {
  return maxValor.value ? (valor / maxValor.value) * 100 : 0
}
</script>

<template>
  <ul class="bars">
    <li v-for="(fila, i) in filas" :key="fila.etiqueta">
      <span v-if="conRango" class="b-rank">{{ i + 1 }}</span>
      <span class="b-label">
        <router-link v-if="fila.to" :to="fila.to">{{ fila.etiqueta }}</router-link>
        <template v-else>{{ fila.etiqueta }}</template>
      </span>
      <span class="b-track"><span class="b-fill" :style="{ width: porcentaje(fila.valor).toFixed(1) + '%' }"></span></span>
      <span class="b-val">{{ formatEURCompacto(fila.valor) }}</span>
    </li>
  </ul>
</template>

<style scoped>
.bars {
  list-style: none;
  margin: 0;
  padding: 0;
}
.bars li {
  display: grid;
  grid-template-columns: auto minmax(150px, 1.7fr) 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 9px 0;
  border-bottom: 1px solid var(--rule2);
}
.b-rank {
  font-size: 11px;
  color: var(--dim);
  width: 18px;
  font-variant-numeric: tabular-nums;
}
.b-label {
  font-size: 14px;
  line-height: 1.3;
}
.b-label a {
  color: inherit;
  text-decoration: none;
  border: 0;
}
.b-label a:hover {
  color: var(--amber);
}
.b-track {
  background: var(--paper2);
  height: 11px;
  position: relative;
}
.b-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--navy);
}
.b-val {
  font-size: 13px;
  color: var(--dim);
  font-variant-numeric: tabular-nums;
  text-align: right;
  min-width: 72px;
}

@media (max-width: 860px) {
  .bars li {
    grid-template-columns: auto 1fr auto;
    gap: 10px;
  }
  .b-track {
    display: none;
  }
}
</style>
