<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGastoStore } from '../stores/gastoStore'
import { formatEUR, formatEURCompacto, formatFecha } from '../utils/formato'

const route = useRoute()
const store = useGastoStore()

onMounted(() => {
  void store.cargarFiltros()
  if (!store.resumenAecidBdns) void store.cargarResumenAecidBdns()
  // Siempre se fija explícitamente (a null si no hay query param), para no heredar un filtro de
  // país que haya quedado puesto en el store desde una visita anterior a /paises/:iso3.
  const paisQuery = route.query.bdns_pais
  store.filtroPaisConcesionesAecidBdns = typeof paisQuery === 'string' && paisQuery ? paisQuery : null
  void store.cargarConcesionesAecidBdns(1)
})

const opcionesPaisConcesiones = computed(() =>
  [...(store.resumenAecidBdns?.por_pais ?? [])].sort((a, b) => a.pais_nombre.localeCompare(b.pais_nombre))
)

function onChangePaisConcesiones(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  void store.setFiltroPaisConcesionesAecidBdns(value || null)
}

function irAPaginaConcesiones(pagina: number) {
  void store.cargarConcesionesAecidBdns(pagina)
}

const totalPaginasConcesiones = computed(() => Math.max(1, Math.ceil(store.totalConcesionesAecidBdns / 30)))
</script>

<template>
  <section class="page-head">
    <p class="kicker">Sobre los datos</p>
    <h1 class="h-page">Qué contiene esta web y qué no</h1>
  </section>
  <section class="prose">
    <p>
      <strong>Los datos son reales</strong>, publicados por la Agencia Española de Cooperación
      Internacional para el Desarrollo (AECID) a través del estándar internacional IATI
      (International Aid Transparency Initiative). No son estimaciones ni datos de ejemplo.
    </p>
    <p>
      El mapa de comunidades autónomas en la ficha de España usa una fuente distinta: la Base de
      Datos Nacional de Subvenciones (BDNS), que publica las concesiones de subvenciones públicas
      dentro de España. Es un dato de cooperación doméstica, no de cooperación internacional, y por
      eso no se suma al resto de totales por país de esta web.
    </p>
    <p>
      Además, algunas cifras de países muestran una línea "preliminares confirmados por AECID vía
      BDNS": son concesiones que AECID ya registró en la Base de Datos Nacional de Subvenciones,
      pero para las que no se encontró la actividad correspondiente en IATI. Se muestran aparte de
      "Comprometido con este país" porque BDNS no declara cómo se reparte un importe entre varios
      países cuando un proyecto cubre más de uno — a diferencia de IATI, que sí lo hace
      explícitamente. El país solo se identifica cuando el texto de la convocatoria lo menciona sin
      ambigüedad; si no, el importe se cuenta igual pero sin asignarlo a ningún país.
      <span v-if="store.resumenAecidBdns && store.resumenAecidBdns.sin_pais.importe_eur > 0">
        Además, hay {{ formatEURCompacto(store.resumenAecidBdns.sin_pais.importe_eur) }} en
        {{ store.resumenAecidBdns.sin_pais.n_concesiones }} concesión(es) de AECID ya registradas en
        BDNS para las que no se pudo identificar un país sin ambigüedad — no aparecen en ninguna
        ficha de país, pero sí forman parte del total que AECID ya tiene confirmado en BDNS.
      </span>
    </p>
    <p>
      Cuidado con la palabra "preliminares": no todas están en la misma situación. Para las
      concesiones de 2024 en adelante es razonable esperar que su actividad IATI aparezca más
      adelante (se verificó un desfase real de varios meses entre el registro en BDNS y la
      publicación en IATI). Pero AECID no tiene ninguna actividad publicada en IATI con fecha de
      inicio anterior al 1 de enero de 2024 — así que las concesiones de BDNS más antiguas (las hay
      desde 2022) no están realmente "pendientes de publicar": es improbable que lleguen a encontrar
      su actividad correspondiente algún día, porque ese periodo queda fuera de lo que AECID ha
      publicado en IATI hasta ahora.
    </p>
    <h2>Unidad de medida</h2>
    <p>
      La unidad básica es la intervención: un importe comprometido, un país receptor, un sector CRS,
      una entidad ejecutora y unas fechas de inicio y fin. Los totales por país, sector y año son
      sumas de esas intervenciones.
    </p>
    <h2>Reparto entre países</h2>
    <p>
      Cuando una misma actividad IATI reporta un importe conjunto para varios países sin desglosar
      cuánto corresponde a cada uno, se reparte el importe a partes iguales entre los países
      declarados. Esos proyectos llevan la marca "reparto estimado entre países" en su ficha.
    </p>
    <h2>Sectores</h2>
    <p>
      Cada intervención tiene un código CRS de 5 dígitos (la clasificación sectorial del Comité de
      Ayuda al Desarrollo de la OCDE). Esta web los agrupa en {{ store.gruposDisponibles.length }}
      categorías de 3 dígitos, con los nombres oficiales de la codelist <em>SectorCategory</em> de
      IATI, para que el filtro sea manejable.
    </p>
    <h2>Cobertura</h2>
    <p>
      Fuente: ingesta directa de actividades IATI publicadas por AECID. Los países sin proyectos
      registrados aparecen en gris en el mapa — no significa que no reciban cooperación española,
      solo que no hay actividades AECID cargadas para ese país con los filtros actuales.
    </p>
    <h2>Geografía</h2>
    <p>
      Las fronteras del mapa proceden de <em>world-atlas</em> (Natural Earth, dominio público), a
      escala 1:110 millones. Los límites mostrados no implican reconocimiento oficial de fronteras.
    </p>
  </section>
  <section id="concesiones-bdns" class="block">
    <div class="block-head">
      <h2 class="sec-title">Concesiones preliminares (AECID vía BDNS)</h2>
      <label class="ctl">
        <span>País</span>
        <select :value="store.filtroPaisConcesionesAecidBdns ?? ''" @change="onChangePaisConcesiones">
          <option value="">Todos los países</option>
          <option value="SIN_PAIS">Sin país identificado</option>
          <option v-for="p in opcionesPaisConcesiones" :key="p.iso_alpha3" :value="p.iso_alpha3">
            {{ p.pais_nombre }}
          </option>
        </select>
      </label>
    </div>
    <p v-if="store.errorConcesionesAecidBdns" class="error">{{ store.errorConcesionesAecidBdns }}</p>
    <p v-else-if="store.cargandoConcesionesAecidBdns" class="note">Cargando…</p>
    <p v-else-if="!store.concesionesAecidBdns.length" class="note">No hay concesiones con este filtro.</p>
    <div v-else class="tabla-wrap">
      <table class="tabla-concesiones">
        <thead>
          <tr>
            <th>País</th>
            <th>Beneficiario</th>
            <th>Convocatoria</th>
            <th>Importe</th>
            <th>Fecha</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in store.concesionesAecidBdns" :key="c.concesion_id">
            <td>{{ c.pais_nombre ?? c.iso_alpha3 ?? 'Sin país identificado' }}</td>
            <td>{{ c.beneficiario ?? '—' }}</td>
            <td>{{ c.titulo ?? '—' }}</td>
            <td class="t-importe">{{ formatEUR(c.importe_eur) }}</td>
            <td>{{ c.fecha_concesion ? formatFecha(c.fecha_concesion) : '—' }}</td>
            <td><a :href="c.url_bdns" target="_blank" rel="noopener">Ver en BDNS ↗</a></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="store.totalConcesionesAecidBdns > 30" class="paginacion">
      <button type="button" :disabled="store.paginaConcesionesAecidBdns <= 1" @click="irAPaginaConcesiones(store.paginaConcesionesAecidBdns - 1)">← Anterior</button>
      <span>Página {{ store.paginaConcesionesAecidBdns }} de {{ totalPaginasConcesiones }}</span>
      <button type="button" :disabled="store.paginaConcesionesAecidBdns >= totalPaginasConcesiones" @click="irAPaginaConcesiones(store.paginaConcesionesAecidBdns + 1)">Siguiente →</button>
    </div>
  </section>
</template>

<style scoped>
.prose {
  max-width: 66ch;
  padding-top: 34px;
}
.prose p {
  font-family: 'Newsreader', serif;
  font-size: 18px;
  line-height: 1.65;
  color: #2b3034;
}
.prose h2 {
  font-size: 20px;
  margin: 34px 0 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--rule);
}
.error {
  margin: 14px 0 0;
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #b91c1c;
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
@media (max-width: 860px) {
  .ctl select {
    padding-top: 11px;
    padding-bottom: 11px;
    background-position: calc(100% - 15px) 19px, calc(100% - 10px) 19px;
  }
}
.ctl select:focus {
  outline: 2px solid var(--amber);
  outline-offset: 1px;
}
.tabla-wrap {
  overflow-x: auto;
  margin-top: 16px;
}
.tabla-concesiones {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.tabla-concesiones th {
  text-align: left;
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dim);
  padding: 6px 10px;
  border-bottom: 1px solid var(--ink);
  white-space: nowrap;
}
.tabla-concesiones td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--rule2);
  vertical-align: top;
}
.t-importe {
  font-variant-numeric: tabular-nums;
  color: var(--navy);
  white-space: nowrap;
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
@media (max-width: 860px) {
  .paginacion {
    flex-wrap: wrap;
  }
  .paginacion button {
    padding: 10px 12px;
  }
}
</style>
