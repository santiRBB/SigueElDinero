<script setup lang="ts">
import type { Proyecto } from '../services/api'
import AmountBadge from './AmountBadge.vue'
import { formatEUR, formatFecha } from '../utils/formato'

defineProps<{
  proyecto: Proyecto
  importeEstandar: boolean
  paisNombre?: string
  paisIso3?: string
}>()
</script>

<template>
  <li class="pcard">
    <div class="p-main">
      <h3>{{ proyecto.titulo ?? proyecto.aid }}</h3>
      <p class="p-org">{{ proyecto.organismo_ejecutor ?? 'Organismo no especificado' }}</p>
    </div>
    <div class="p-meta">
      <span class="p-amt">{{ formatEUR(proyecto.importe_pais_eur) }}</span>
      <span class="p-tags">
        <router-link v-if="paisIso3" class="tag" :to="`/paises/${paisIso3}`">{{ paisNombre }}</router-link>
        <a v-if="proyecto.url_fuente" class="tag" :href="proyecto.url_fuente" target="_blank" rel="noopener">Ver proyecto original ↗</a>
        <a v-if="proyecto.url_bdns" class="tag" :href="proyecto.url_bdns" target="_blank" rel="noopener">Ver convocatoria BDNS ↗</a>
      </span>
      <AmountBadge :porcentaje-fuente="proyecto.porcentaje_fuente" />
      <p v-if="importeEstandar" class="nota-estandar">Importe estándar de esta convocatoria</p>
      <span v-if="proyecto.bdns_tipo_convocatoria" class="p-bdns-tipo">{{ proyecto.bdns_tipo_convocatoria }}</span>
      <span class="p-dates">{{ formatFecha(proyecto.start_date) }} — {{ formatFecha(proyecto.end_date) }}</span>
    </div>
  </li>
</template>

<style scoped>
.pcard {
  display: grid;
  grid-template-columns: 1fr minmax(250px, 290px);
  gap: 32px;
  padding: 20px 0;
  border-bottom: 1px solid var(--rule2);
  align-items: start;
  list-style: none;
}
.pcard:hover {
  background: rgba(11, 59, 92, 0.028);
}
.pcard h3 {
  font-size: 19px;
  line-height: 1.3;
  font-weight: 400;
  margin: 0;
}
.p-org {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--dim);
}
.p-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  text-align: right;
}
.p-amt {
  font-family: 'Newsreader', serif;
  font-size: 20px;
  color: var(--navy);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.p-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
  max-width: 100%;
}
.tag {
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--dim);
  border: 1px solid var(--rule);
  padding: 2px 7px;
  white-space: nowrap;
  text-decoration: none;
}
a.tag:hover {
  color: var(--amber);
  border-color: var(--amber);
}
.nota-estandar {
  font-size: 11px;
  color: var(--dim);
  font-style: italic;
  margin: 0;
}
.p-bdns-tipo {
  font-size: 11.5px;
  color: #8d9195;
}
.p-dates {
  font-size: 11.5px;
  color: #8d9195;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 860px) {
  .pcard {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .p-meta {
    align-items: flex-start;
    text-align: left;
  }
  .p-tags {
    justify-content: flex-start;
  }
}
</style>
