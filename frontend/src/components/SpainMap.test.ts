// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { shallowMount } from '@vue/test-utils'
import VChart from 'vue-echarts'
import { feature } from 'topojson-client'
import spainTopo from 'es-atlas/es/autonomous_regions.json'
import SpainMap from './SpainMap.vue'

describe('SpainMap', () => {
  it('emits ccaa-click with the codigo_ine of the clicked region', async () => {
    const wrapper = shallowMount(SpainMap, {
      props: { ccaaResumen: [] },
    })
    await nextTick()

    await wrapper.findComponent(VChart).vm.$emit('click', { name: '09' })

    expect(wrapper.emitted('ccaa-click')).toEqual([['09']])
  })

  it('exposes exactly ids "01".."20" (19 codigo_ine regions + Gibraltar), matching dim_ccaa', () => {
    const topoObjects = (spainTopo as { objects: { autonomous_regions: unknown } }).objects.autonomous_regions
    const geoJson = feature(spainTopo, topoObjects)

    const ids = geoJson.features.map((f) => String(f.id)).sort()
    const esperados = Array.from({ length: 20 }, (_, i) => String(i + 1).padStart(2, '0'))

    expect(ids).toEqual(esperados)
  })
})
