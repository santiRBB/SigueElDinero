<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGastoStore } from '../stores/gastoStore'
import type { Orden } from '../services/api'
import { detectarImportesEstandar, ordenarProyectos } from '../utils/proyectos'
import { aplicarHead } from '../utils/head'
import ProjectCard from '../components/ProjectCard.vue'
import YearBars from '../components/YearBars.vue'
import StatTile from '../components/StatTile.vue'
import BarList from '../components/BarList.vue'
import FilterBar from '../components/FilterBar.vue'
import SortSelect from '../components/SortSelect.vue'
import SpainMap from '../components/SpainMap.vue'
import { formatEUR, formatEURCompacto, formatFecha, formatPorcentaje } from '../utils/formato'

const route = useRoute()
const router = useRouter()
const store = useGastoStore()

const iso3 = computed(() => String(route.params.iso3).toUpperCase())

function cargarDetalle() {
  void store.seleccionarPais(iso3.value)
}

function cargarCcaaSiEspana() {
  if (iso3.value === 'ESP') void store.cargarResumenCcaa()
}

const concesionesExpandido = ref(false)
const concesionesTop10 = computed(() => store.concesionesAecidBdns.slice(0, 10))

function onToggleConcesiones() {
  concesionesExpandido.value = !concesionesExpandido.value
  if (concesionesExpandido.value) {
    void store.setFiltroPaisConcesionesAecidBdns(iso3.value)
  }
}

onMounted(() => {
  if (!store.aniosDisponibles.length) void store.cargarFiltros()
  cargarDetalle()
  void store.cargarPaisPorAnio(iso3.value)
  if (!store.paisesResumen.length) void store.cargarResumen()
  if (!store.resumenAecidBdns) void store.cargarResumenAecidBdns()
  cargarCcaaSiEspana()
})
watch(iso3, () => {
  cargarDetalle()
  void store.cargarPaisPorAnio(iso3.value)
  cargarCcaaSiEspana()
  concesionesExpandido.value = false
})
watch(() => store.filtroAnio, () => {
  cargarDetalle()
  cargarCcaaSiEspana()
})
watch(() => store.filtroGrupo, () => {
  cargarDetalle()
  void store.cargarPaisPorAnio(iso3.value)
})
watch(
  () => store.detallePais,
  (detalle) => {
    if (!detalle) return
    aplicarHead({
      titulo: `Cooperación española en ${detalle.pais.nombre}`,
      descripcion: `Importe comprometido, sectores, entidades ejecutoras y proyectos de la cooperación española en ${detalle.pais.nombre}.`,
      indexable: false,
      ruta: `/paises/${detalle.pais.iso_alpha3}`,
    })
  },
  { immediate: true },
)

function onCcaaClick(codigoIne: string) {
  router.push(`/ccaa/${codigoIne}`)
}

const importesEstandar = computed(() =>
  store.detallePais ? detectarImportesEstandar(store.detallePais.proyectos) : new Set<string>()
)
const ordenProyectos = ref<Orden>('importe_desc')
const proyectosOrdenados = computed(() =>
  store.detallePais ? ordenarProyectos(store.detallePais.proyectos, ordenProyectos.value) : []
)
const totalPais = computed(() => store.detallePais?.categorias.reduce((acc, c) => acc + c.importe_eur, 0) ?? 0)
const totalGlobal = computed(() => store.paisesResumen.reduce((acc, p) => acc + p.importe_total_eur, 0))
const share = computed(() => (totalGlobal.value ? (totalPais.value / totalGlobal.value) * 100 : 0))
const grupoPrincipal = computed(() => {
  const filas = store.detallePais?.categorias ?? []
  const top = [...filas].sort((a, b) => b.importe_eur - a.importe_eur)[0]
  return top ? (top.nombre ?? top.codigo_grupo ?? '—') : '—'
})
const filasGrupos = computed(() =>
  (store.detallePais?.categorias ?? []).map((c) => ({ etiqueta: c.nombre ?? c.codigo_grupo ?? 'Sin grupo', valor: c.importe_eur }))
)
const totalCcaa = computed(() => store.resumenCcaa.reduce((acc, c) => acc + c.importe_total_eur, 0))
const concesionesCcaa = computed(() => store.resumenCcaa.reduce((acc, c) => acc + c.n_concesiones, 0))
const preliminarAecidBdns = computed(() =>
  store.resumenAecidBdns?.por_pais.find((p) => p.iso_alpha3 === iso3.value) ?? null
)

function onSelectYear(anio: number) {
  store.setFiltroAnio(store.filtroAnio === anio ? null : anio)
}
</script>

<template>
  <section class="page-head">
    <p class="kicker"><router-link to="/mapa">Mapa</router-link></p>
    <h1 class="h-page">{{ store.detallePais?.pais.nombre ?? iso3 }}</h1>
    <FilterBar />
  </section>

  <p v-if="store.detalleError" class="error">{{ store.detalleError }}</p>
  <p v-else-if="!store.detallePais" class="note">Cargando…</p>

  <section v-if="iso3 === 'ESP'" class="block">
    <h2 class="sec-title">Subvenciones públicas por comunidad autónoma</h2>
    <p class="note">
      Dato distinto al de cooperación internacional de más abajo: viene de la Base de Datos Nacional
      de Subvenciones (BDNS), no de AECID/IATI. Se filtra por año; el filtro de sector no aplica a
      este dato, BDNS no clasifica sus concesiones por sector CRS.
    </p>
    <section class="stats">
      <StatTile :valor="formatEURCompacto(totalCcaa)" etiqueta="Concedido en España (BDNS)" />
      <StatTile :valor="String(concesionesCcaa)" etiqueta="Concesiones" />
    </section>
    <SpainMap :ccaa-resumen="store.resumenCcaa" @ccaa-click="onCcaaClick" />
  </section>

  <template v-if="store.detallePais">
    <section v-if="iso3 === 'ESP'" class="block">
      <p class="nota-distincion">
        Estas dos cifras no se suman ni se comparan entre sí: miden cosas distintas y a escalas muy
        distintas. La de arriba es el conjunto de subvenciones públicas de cualquier tipo concedidas
        en España (BDNS). La de abajo son programas concretos que gestiona AECID dentro de España —
        educación para el desarrollo, sensibilización, apoyo a organizaciones — publicados en IATI.
      </p>
    </section>
    <h2 v-if="iso3 === 'ESP'" class="sec-title">Cooperación internacional gestionada desde España (AECID)</h2>
    <section class="stats">
      <StatTile :valor="formatEURCompacto(totalPais)" etiqueta="Comprometido con este país" />
      <StatTile :valor="String(store.detallePais.proyectos.length)" etiqueta="Proyectos" />
      <StatTile :valor="formatPorcentaje(share)" etiqueta="Del total repartido" />
      <StatTile :valor="grupoPrincipal" etiqueta="Sector principal" />
    </section>
    <p v-if="preliminarAecidBdns && preliminarAecidBdns.importe_eur > 0 && !store.filtroAnio && !store.filtroGrupo" class="note nota-preliminar">
      + {{ formatEURCompacto(preliminarAecidBdns.importe_eur) }} preliminares confirmados por AECID vía
      BDNS sin actividad IATI encontrada ({{ preliminarAecidBdns.n_concesiones }} concesión(es)) — parte
      son de antes de 2024 y es improbable que lleguen a publicarse en IATI. Ver
      <router-link to="/sobre">Sobre los datos</router-link>.
    </p>
    <div v-if="preliminarAecidBdns && preliminarAecidBdns.importe_eur > 0 && !store.filtroAnio && !store.filtroGrupo" class="concesiones-bdns">
      <button type="button" class="btn-toggle-concesiones" @click="onToggleConcesiones">
        {{ concesionesExpandido ? 'Ocultar concesiones' : `Ver ${preliminarAecidBdns.n_concesiones} concesión(es)` }}
      </button>
      <ul v-if="concesionesExpandido" class="concesiones-list">
        <li v-if="store.cargandoConcesionesAecidBdns" class="note">Cargando…</li>
        <li v-else-if="store.errorConcesionesAecidBdns" class="note">{{ store.errorConcesionesAecidBdns }}</li>
        <template v-else>
          <li v-for="c in concesionesTop10" :key="c.concesion_id" class="concesion-item">
            <span class="c-benef">{{ c.beneficiario ?? 'Beneficiario no especificado' }}</span>
            <span class="c-importe">{{ formatEUR(c.importe_eur) }}</span>
            <span class="c-fecha">{{ c.fecha_concesion ? formatFecha(c.fecha_concesion) : '—' }}</span>
            <a :href="c.url_bdns" target="_blank" rel="noopener">Ver en BDNS ↗</a>
          </li>
          <li v-if="store.totalConcesionesAecidBdns > 10" class="note">
            <router-link :to="`/sobre?bdns_pais=${iso3}#concesiones-bdns`">
              Ver las {{ store.totalConcesionesAecidBdns }} en Sobre los datos →
            </router-link>
          </li>
        </template>
      </ul>
    </div>

    <section class="cols">
      <div class="block">
        <h2 class="sec-title">Por sector</h2>
        <BarList v-if="filasGrupos.length" :filas="filasGrupos" />
        <p v-else class="note">Sin datos con este filtro.</p>
      </div>
      <div class="block">
        <h2 class="sec-title">Evolución</h2>
        <YearBars :datos="store.paisPorAnio" :anio-activo="store.filtroAnio" @select="onSelectYear" />
      </div>
    </section>

    <section class="block">
      <div class="block-head">
        <h2 class="sec-title">Proyectos ({{ store.detallePais.proyectos.length }})</h2>
        <SortSelect v-if="store.detallePais.proyectos.length" v-model="ordenProyectos" />
      </div>
      <p v-if="!store.detallePais.proyectos.length" class="note">Ningún proyecto coincide con estos filtros.</p>
      <ul v-else class="plist">
        <ProjectCard
          v-for="proyecto in proyectosOrdenados"
          :key="proyecto.aid"
          :proyecto="proyecto"
          :importe-estandar="importesEstandar.has(proyecto.aid)"
        />
      </ul>
    </section>
  </template>
</template>

<style scoped>
.error {
  margin: 14px 0 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
}
.nota-preliminar {
  margin-top: -8px;
}
.nota-distincion {
  margin: 0;
  padding: 12px 16px;
  border-left: 3px solid var(--amber);
  background: var(--paper2);
  font-size: 13px;
  color: var(--ink);
}
.concesiones-bdns {
  margin-top: -8px;
}
.btn-toggle-concesiones {
  font-family: inherit;
  font-size: 12px;
  background: none;
  border: 0;
  padding: 0;
  color: var(--dim);
  text-decoration: underline;
  cursor: pointer;
}
.concesiones-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
}
.concesion-item {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: baseline;
  padding: 6px 0;
  border-bottom: 1px solid var(--rule2);
  font-size: 13px;
}
.c-benef {
  flex: 1;
  min-width: 160px;
}
.c-importe {
  font-variant-numeric: tabular-nums;
  color: var(--navy);
}
.c-fecha {
  color: var(--dim);
  font-size: 12px;
}
</style>
