<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts/core'
import { MapChart } from 'echarts/charts'
import { TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { feature } from 'topojson-client'
import spainTopo from 'es-atlas/es/autonomous_regions.json'
import type { CcaaResumen } from '../services/api'
import { formatEUR } from '../utils/formato'
import { RAMP, calcularCortes } from '../utils/mapaColores'
import MapLegend from './MapLegend.vue'

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps<{
  ccaaResumen: CcaaResumen[]
}>()

const emit = defineEmits<{
  (e: 'ccaa-click', codigoIne: string): void
}>()

const mapaListo = ref(false)

onMounted(() => {
  const topoObjects = (spainTopo as { objects: { autonomous_regions: unknown } }).objects.autonomous_regions
  const geoJson = feature(spainTopo, topoObjects)

  // es-atlas ya trae el codigo_ine como id (p.ej. "09"), a diferencia de
  // world-atlas no hace falta mapeo numerico->alpha: se usa tal cual.
  for (const f of geoJson.features) {
    f.properties = { ...f.properties, name: String(f.id) }
  }

  echarts.registerMap('spain', geoJson as unknown as Parameters<typeof echarts.registerMap>[1])
  mapaListo.value = true
})

const seriesData = computed(() =>
  props.ccaaResumen.map((c) => ({
    name: c.codigo_ine,
    nombre: c.nombre,
    value: c.importe_total_eur,
    n: c.n_concesiones,
  }))
)

const pieces = computed(() => {
  const valores = props.ccaaResumen.map((c) => c.importe_total_eur).filter((v) => v > 0)
  const cortes = calcularCortes(valores)
  const limites = [0, ...cortes, Infinity]
  return RAMP.map((color, i) => ({ min: limites[i], max: limites[i + 1], color }))
})

const option = computed(() => ({
  tooltip: {
    trigger: 'item' as const,
    formatter: (params: { name: string; data?: { nombre?: string; value?: number; n?: number } }) => {
      const nombre = params.data?.nombre ?? params.name
      if (params.data?.value == null) {
        return `${nombre}<br/>Sin datos`
      }
      return `${nombre}<br/>${formatEUR(params.data.value)}<br/>${params.data.n} concesion(es)`
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
      map: 'spain',
      roam: true,
      nameProperty: 'name',
      itemStyle: { areaColor: '#E6E1D7', borderColor: '#FAF7F0', borderWidth: 0.5 },
      emphasis: { itemStyle: { areaColor: '#C9791C' } },
      data: seriesData.value,
    },
  ],
}))

function onClick(params: { name: string }) {
  emit('ccaa-click', params.name)
}
</script>

<template>
  <div class="spain-map-wrap">
    <v-chart v-if="mapaListo" class="spain-map" :option="option" autoresize @click="onClick" />
    <MapLegend />
  </div>
</template>

<style scoped>
.spain-map-wrap {
  width: 100%;
}
.spain-map {
  width: 100%;
  height: 420px;
}
</style>
