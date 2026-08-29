<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PaisResumen } from '../services/api'
import { formatEUR, formatPorcentaje } from '../utils/formato'

const props = defineProps<{
  paises: PaisResumen[]
}>()

type Columna = 'nombre' | 'n_intervenciones' | 'importe_total_eur'

const columna = ref<Columna>('importe_total_eur')
const descendente = ref(true)

const total = computed(() => props.paises.reduce((acc, p) => acc + p.importe_total_eur, 0))

const filasOrdenadas = computed(() => {
  const filas = [...props.paises]
  filas.sort((a, b) => {
    const va = a[columna.value]
    const vb = b[columna.value]
    const cmp = typeof va === 'string' ? va.localeCompare(vb as string) : (va as number) - (vb as number)
    return descendente.value ? -cmp : cmp
  })
  return filas
})

function ordenarPor(col: Columna) {
  if (columna.value === col) {
    descendente.value = !descendente.value
  } else {
    columna.value = col
    descendente.value = true
  }
}

function porcentajeDelTotal(valor: number): number {
  return total.value ? (valor / total.value) * 100 : 0
}
</script>

<template>
  <table class="tbl">
    <thead>
      <tr>
        <th @click="ordenarPor('nombre')">País</th>
        <th class="r" @click="ordenarPor('n_intervenciones')">Proyectos</th>
        <th class="r" @click="ordenarPor('importe_total_eur')">Importe</th>
        <th class="r">% del total</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="fila in filasOrdenadas" :key="fila.iso_alpha3">
        <td><router-link :to="`/paises/${fila.iso_alpha3}`">{{ fila.nombre }}</router-link></td>
        <td class="r">{{ fila.n_intervenciones }}</td>
        <td class="r num">{{ formatEUR(fila.importe_total_eur) }}</td>
        <td class="r dim">{{ formatPorcentaje(porcentajeDelTotal(fila.importe_total_eur)) }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.tbl th {
  text-align: left;
  font-weight: 400;
  font-size: 10.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--dim);
  padding: 0 12px 9px 0;
  border-bottom: 1px solid var(--ink);
  cursor: pointer;
  user-select: none;
}
.tbl td {
  padding: 10px 12px 10px 0;
  border-bottom: 1px solid var(--rule2);
}
.tbl tr:hover td {
  background: rgba(11, 59, 92, 0.035);
}
.tbl .r {
  text-align: right;
  padding-right: 0;
}
.tbl th.r {
  padding-right: 0;
}
.tbl .dim {
  color: var(--dim);
}
.tbl .num {
  font-variant-numeric: tabular-nums;
}
.tbl a {
  color: inherit;
  text-decoration: none;
  border: 0;
}
.tbl a:hover {
  color: var(--amber);
}

@media (max-width: 860px) {
  .tbl td:nth-child(2),
  .tbl th:nth-child(2) {
    display: none;
  }
}
</style>
