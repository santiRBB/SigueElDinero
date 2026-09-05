<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useGastoStore } from '../stores/gastoStore'
import FilterBar from '../components/FilterBar.vue'
import ProjectCard from '../components/ProjectCard.vue'
import SortSelect from '../components/SortSelect.vue'
import { formatEURCompacto } from '../utils/formato'

const store = useGastoStore()

onMounted(() => {
  void store.cargarFiltros()
  void store.buscarProyectos()
})

function onInput(event: Event) {
  store.queryBusqueda = (event.target as HTMLInputElement).value
  void store.buscarProyectos()
}

function irAPagina(pagina: number) {
  void store.buscarProyectos(pagina)
}

watch(
  () => [store.filtroAnio, store.filtroGrupo, store.ordenBusqueda],
  () => { void store.buscarProyectos() },
)

const totalPaginas = computed(() => Math.max(1, Math.ceil(store.totalBusqueda / 30)))
const totalPaginaActual = computed(() => store.resultadosBusqueda.reduce((acc, p) => acc + p.importe_pais_eur, 0))
</script>

<template>
  <section class="page-head">
    <p class="kicker">Proyectos</p>
    <h1 class="h-page">Busca un proyecto o una entidad</h1>
    <div class="searchrow">
      <input
        class="search"
        type="search"
        placeholder="Escribe un país, una ONG o una palabra del título"
        :value="store.queryBusqueda"
        @input="onInput"
      />
      <FilterBar />
      <SortSelect v-model="store.ordenBusqueda" />
    </div>
    <p class="note">
      {{ store.totalBusqueda }} proyectos
      <template v-if="store.resultadosBusqueda.length">· {{ formatEURCompacto(totalPaginaActual) }} en esta página</template>
    </p>
  </section>

  <p v-if="store.errorBusqueda" class="error">{{ store.errorBusqueda }}</p>
  <p v-else-if="store.cargandoBusqueda" class="note">Buscando…</p>

  <section class="block">
    <p v-if="!store.cargandoBusqueda && !store.resultadosBusqueda.length" class="note">Ningún proyecto coincide con estos filtros.</p>
    <ul class="plist">
      <ProjectCard
        v-for="p in store.resultadosBusqueda"
        :key="p.aid"
        :proyecto="p"
        :importe-estandar="false"
        :pais-nombre="p.pais_nombre"
        :pais-iso3="p.pais_iso3"
      />
    </ul>

    <div v-if="store.totalBusqueda > 30" class="paginacion">
      <button type="button" :disabled="store.paginaBusqueda <= 1" @click="irAPagina(store.paginaBusqueda - 1)">← Anterior</button>
      <span>Página {{ store.paginaBusqueda }} de {{ totalPaginas }}</span>
      <button type="button" :disabled="store.paginaBusqueda >= totalPaginas" @click="irAPagina(store.paginaBusqueda + 1)">Siguiente →</button>
    </div>
  </section>
</template>

<style scoped>
.error {
  margin: 14px 0 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
}
.searchrow {
  display: flex;
  gap: 22px;
  align-items: flex-end;
  flex-wrap: wrap;
  margin-top: 26px;
}
.search {
  flex: 1;
  min-width: 260px;
  font-family: 'Newsreader', serif;
  font-size: 19px;
  padding: 8px 0;
  background: none;
  border: 0;
  border-bottom: 1px solid var(--ink);
  color: var(--ink);
}
@media (max-width: 860px) {
  .search {
    min-width: 0;
  }
}
.search:focus {
  outline: 0;
  border-bottom-color: var(--amber);
}
.search::placeholder {
  color: #9a9ea2;
}
.paginacion {
  display: flex;
  align-items: center;
  gap: 14px;
  justify-content: center;
  margin-top: 20px;
  font-size: 13px;
  color: var(--dim);
}
.paginacion button {
  font-family: inherit;
  font-size: 13px;
  background: none;
  border: 1px solid var(--ink);
  padding: 6px 12px;
  cursor: pointer;
}
.paginacion button:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
