<script setup lang="ts">
import { computed } from 'vue'
import { useGastoStore } from '../stores/gastoStore'
import { detectarImportesEstandar } from '../utils/proyectos'
import ProjectCard from './ProjectCard.vue'

const store = useGastoStore()

const importesEstandar = computed(() =>
  store.detallePais ? detectarImportesEstandar(store.detallePais.proyectos) : new Set<string>()
)

function formatEUR(valor: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(valor)
}
</script>

<template>
  <aside v-if="store.paisSeleccionado" class="country-panel">
    <button class="cerrar" @click="store.cerrarPanel">Cerrar</button>
    <template v-if="store.detallePais">
      <h2>{{ store.detallePais.pais.nombre }}</h2>
      <section class="categorias">
        <h3>Por sector</h3>
        <ul>
          <li v-for="cat in store.detallePais.categorias" :key="cat.codigo_crs ?? 'sin-sector'">
            {{ cat.nombre ?? 'Sin sector' }} — {{ formatEUR(cat.importe_eur) }} ({{ cat.n_intervenciones }})
          </li>
        </ul>
      </section>
      <section class="proyectos">
        <h3>Proyectos ({{ store.detallePais.proyectos.length }})</h3>
        <ProjectCard
          v-for="proyecto in store.detallePais.proyectos"
          :key="proyecto.aid"
          :proyecto="proyecto"
          :importe-estandar="importesEstandar.has(proyecto.aid)"
        />
      </section>
    </template>
    <p v-else-if="store.detalleError" class="error">Sin datos de cooperación registrados para este país</p>
    <p v-else>Cargando…</p>
  </aside>
</template>

<style scoped>
.country-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 380px;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  overflow-y: auto;
}
.cerrar {
  float: right;
}
.error {
  clear: both;
  color: #b91c1c;
}
</style>
