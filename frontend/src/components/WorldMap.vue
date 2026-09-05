<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts/core'
import { MapChart } from 'echarts/charts'
import { TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { feature } from 'topojson-client'
import worldTopo from 'world-atlas/countries-110m.json'
import isoMapping from '../assets/iso-numeric-to-alpha3.json'
import type { PaisResumen } from '../services/api'
import { formatEUR } from '../utils/formato'
import { COLOR_SIN_DATOS, calcularPieces } from '../utils/mapaColores'
import MapLegend from './MapLegend.vue'

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  paisesResumen: PaisResumen[]
}>()

const emit = defineEmits<{
  (e: 'country-click', iso3: string): void
}>()

const mapaListo = ref(false)

const esTactil = window.matchMedia('(pointer: coarse)').matches

type Anillo = [number, number][]

// world-atlas deja los anillos de países que cruzan el antimeridiano (Rusia,
// Fiyi) tocando exactamente -180/180 pero sin partirlos, pensados para una
// proyección que envuelve el globo. echarts dibuja lon/lat linealmente sin
// envolver, así que ese tramo se pinta como una línea recta que cruza todo
// el mapa. Se parte el anillo en ese punto para evitarlo.
function partirEnAntimeridiano(anillo: Anillo): Anillo[] {
  const partes: Anillo[] = []
  let actual: Anillo = [anillo[0]]
  for (let i = 1; i < anillo.length; i++) {
    if (Math.abs(anillo[i][0] - anillo[i - 1][0]) > 180) {
      partes.push(actual)
      actual = []
    }
    actual.push(anillo[i])
  }
  partes.push(actual)
  return partes
}

function repararAntimeridiano<T extends { type: string; coordinates: unknown }>(geometry: T): T {
  const poligonos: Anillo[][] =
    geometry.type === 'Polygon'
      ? [geometry.coordinates as Anillo[]]
      : geometry.type === 'MultiPolygon'
        ? (geometry.coordinates as Anillo[][])
        : []
  if (poligonos.length === 0) return geometry

  const anillos = poligonos.flat()
  const necesitaReparo = anillos.some((anillo) => partirEnAntimeridiano(anillo).length > 1)
  if (!necesitaReparo) return geometry

  return {
    ...geometry,
    type: 'MultiPolygon',
    coordinates: anillos.flatMap((anillo) =>
      partirEnAntimeridiano(anillo)
        .filter((parte) => parte.length >= 4)
        .map((parte) => [parte])
    ),
  }
}

onMounted(() => {
  const topoObjects = (worldTopo as { objects: { countries: unknown } }).objects.countries
  const geoJson = feature(worldTopo, topoObjects)
  const mapping = isoMapping as Record<string, string>

  for (const f of geoJson.features) {
    const codigoNumerico = String(f.id ?? '').padStart(3, '0')
    const alpha3 = mapping[codigoNumerico]
    if (alpha3) {
      f.properties = { ...f.properties, name: alpha3 }
    }
    f.geometry = repararAntimeridiano(f.geometry)
  }

  echarts.registerMap('world', geoJson as unknown as Parameters<typeof echarts.registerMap>[1])
  mapaListo.value = true
})

const seriesData = computed(() =>
  props.paisesResumen.map((p) => ({
    name: p.iso_alpha3,
    nombre: p.nombre,
    value: p.importe_total_eur,
    n: p.n_intervenciones,
  }))
)

const pieces = computed(() => calcularPieces(props.paisesResumen.map((p) => p.importe_total_eur)))

const option = computed(() => ({
  tooltip: {
    trigger: 'item' as const,
    formatter: (params: { name: string; data?: { nombre?: string; value?: number; n?: number } }) => {
      const nombre = params.data?.nombre ?? params.name
      if (params.data?.value == null) {
        return `${nombre}<br/>Sin datos`
      }
      return `${nombre}<br/>${formatEUR(params.data.value)}<br/>${params.data.n} proyecto(s)`
    },
  },
  visualMap: {
    type: 'piecewise' as const,
    show: false,
    pieces: pieces.value,
  },
  series: [
    {
      type: 'map' as const,
      map: 'world',
      roam: esTactil ? 'scale' : true,
      nameProperty: 'name',
      itemStyle: { areaColor: COLOR_SIN_DATOS, borderColor: '#FAF7F0', borderWidth: 0.5 },
      emphasis: { itemStyle: { areaColor: '#C9791C' } },
      data: seriesData.value,
    },
  ],
}))

function onClick(params: { name: string }) {
  emit('country-click', params.name)
}
</script>

<template>
  <div class="world-map-wrap">
    <v-chart v-if="mapaListo" class="world-map" :option="option" autoresize @click="onClick" />
    <MapLegend />
  </div>
</template>

<style scoped>
.world-map-wrap {
  width: 100%;
}
.world-map {
  width: 100%;
  height: 500px;
}
</style>
