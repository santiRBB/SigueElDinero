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

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])

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

// visualMap has no native log scale, so amounts are pre-transformed with
// log10 for coloring while the real amount travels alongside for the tooltip.
const seriesData = computed(() =>
  props.paisesResumen.map((p) => ({
    name: p.iso_alpha3,
    value: p.importe_total_eur > 0 ? Math.log10(p.importe_total_eur) : 0,
    importeReal: p.importe_total_eur,
    n: p.n_intervenciones,
  }))
)

const maxLog = computed(() => {
  const maxImporte = props.paisesResumen.reduce((max, p) => Math.max(max, p.importe_total_eur), 1)
  return Math.max(Math.log10(maxImporte), 1)
})

function formatEUR(valor: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(valor)
}

const option = computed(() => ({
  tooltip: {
    trigger: 'item' as const,
    formatter: (params: { name: string; data?: { importeReal: number; n: number } }) => {
      if (!params.data) {
        return `${params.name}<br/>Sin datos`
      }
      return `${params.name}<br/>${formatEUR(params.data.importeReal)}<br/>${params.data.n} proyecto(s)`
    },
  },
  visualMap: {
    type: 'continuous' as const,
    min: 0,
    max: maxLog.value,
    calculable: false,
    show: false,
    inRange: { color: ['#dbeafe', '#1e3a8a'] },
  },
  series: [
    {
      type: 'map' as const,
      map: 'world',
      roam: true,
      nameProperty: 'name',
      itemStyle: { areaColor: '#d1d5db', borderColor: '#9ca3af' },
      emphasis: { itemStyle: { areaColor: '#93c5fd' } },
      data: seriesData.value,
    },
  ],
}))

function onClick(params: { name: string }) {
  emit('country-click', params.name)
}
</script>

<template>
  <v-chart v-if="mapaListo" class="world-map" :option="option" autoresize @click="onClick" />
</template>

<style scoped>
.world-map {
  width: 100%;
  height: 100%;
  min-height: 500px;
}
</style>
