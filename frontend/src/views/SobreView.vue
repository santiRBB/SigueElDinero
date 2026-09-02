<script setup lang="ts">
import { onMounted } from 'vue'
import { useGastoStore } from '../stores/gastoStore'
import { formatEURCompacto } from '../utils/formato'

const store = useGastoStore()

onMounted(() => {
  void store.cargarFiltros()
  if (!store.resumenAecidBdns) void store.cargarResumenAecidBdns()
})
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
      pero que todavía no publicó como actividad en IATI (se verificó un desfase real de varios
      meses entre ambas). Se muestran aparte de "Comprometido con este país" porque BDNS no declara
      cómo se reparte un importe entre varios países cuando un proyecto cubre más de uno — a
      diferencia de IATI, que sí lo hace explícitamente. El país solo se identifica cuando el texto
      de la convocatoria lo menciona sin ambigüedad; si no, el importe se cuenta igual pero sin
      asignarlo a ningún país.
      <span v-if="store.resumenAecidBdns && store.resumenAecidBdns.sin_pais.importe_eur > 0">
        Además, hay {{ formatEURCompacto(store.resumenAecidBdns.sin_pais.importe_eur) }} en
        {{ store.resumenAecidBdns.sin_pais.n_concesiones }} concesión(es) de AECID ya registradas en
        BDNS para las que no se pudo identificar un país sin ambigüedad — no aparecen en ninguna
        ficha de país, pero sí forman parte del total que AECID ya tiene confirmado en BDNS.
      </span>
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
</style>
