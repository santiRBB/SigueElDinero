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

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])

const RAMP = ['#D7E2EB', '#A9C1D5', '#7699B8', '#43709A', '#1D4E7B', '#0B3B5C']

const props = defineProps<{
  paisesResumen: PaisResumen[]
}>()

const emit = defineEmits<{
  (e: 'country-click', iso3: string): void
}>()

const mapaListo = ref(false)

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

// visualMap has no native quantile scale, so the 5 cut points are computed
// by hand from the values actually present (same criterion as the design
// reference's d3.scaleThreshold over quantiles). With fewer than 6 values
// there aren't enough data points for meaningful quantiles, so we fall back
// to evenly-spaced cuts between the min and max instead.
function calcularCortes(valores: number[]): number[] {
  const ordenados = [...valores].sort((a, b) => a - b)
  if (ordenados.length === 0) return [1, 2, 3, 4, 5]
  if (ordenados.length < 6) {
    const min = ordenados[0]
    const max = ordenados[ordenados.length - 1]
    const paso = (max - min) / 6 || 1
    return [1, 2, 3, 4, 5].map((i) => min + paso * i)
  }
  const cuantil = (p: number): number => {
    const idx = p * (ordenados.length - 1)
    const lo = Math.floor(idx)
    const hi = Math.ceil(idx)
    if (lo === hi) return ordenados[lo]
    return ordenados[lo] + (ordenados[hi] - ordenados[lo]) * (idx - lo)
  }
  return [0.16, 0.34, 0.52, 0.7, 0.86].map(cuantil)
}

const pieces = computed(() => {
  const valores = props.paisesResumen.map((p) => p.importe_total_eur).filter((v) => v > 0)
  const cortes = calcularCortes(valores)
  const limites = [0, ...cortes, Infinity]
  return RAMP.map((color, i) => ({ min: limites[i], max: limites[i + 1], color }))
})

const option = computed(() => ({
  tooltip: {
    trigger: 'item' as const,
    formatter: (params: { name: string; data?: { nombre?: string; value: number; n: number } }) => {
      const nombre = params.data?.nombre ?? params.name
      if (!params.data) {
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
      roam: true,
      nameProperty: 'name',
      itemStyle: { areaColor: '#E6E1D7', borderColor: '#FAF7F0', borderWidth: 0.5 },
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
    <div class="legend">
      <span class="lg-label">Menos</span>
      <span v-for="color in RAMP" :key="color" class="lg-sw" :style="{ background: color }"></span>
      <span class="lg-label">Más</span>
      <span class="lg-sw lg-none"></span>
      <span class="lg-label">Sin datos</span>
    </div>
  </div>
</template>

<style scoped>
.world-map-wrap {
  width: 100%;
}
.world-map {
  width: 100%;
  height: 100%;
  min-height: 500px;
}
.legend {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.lg-sw {
  width: 26px;
  height: 9px;
  display: inline-block;
}
.lg-none {
  background: #e6e1d7;
}
.lg-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dim);
  margin: 0 8px 0 4px;
}
</style>
