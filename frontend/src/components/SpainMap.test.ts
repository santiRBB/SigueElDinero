// @vitest-environment jsdom
import { describe, expect, it, vi, afterEach, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { shallowMount } from '@vue/test-utils'
import VChart from 'vue-echarts'
import { feature } from 'topojson-client'
import spainTopo from 'es-atlas/es/autonomous_regions.json'
import SpainMap from './SpainMap.vue'

describe('SpainMap', () => {
  beforeEach(() => {
    // jsdom does not implement matchMedia, and SpainMap.vue reads it at setup.
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  function stubPointerCoarse(matches: boolean) {
    vi.unstubAllGlobals()
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({ matches, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
    )
  }

  it('disables map panning (keeps pinch-zoom) on touch devices so a vertical swipe scrolls the page', async () => {
    stubPointerCoarse(true)
    const wrapper = shallowMount(SpainMap, { props: { ccaaResumen: [] } })
    await nextTick()

    const option = wrapper.findComponent(VChart).props('option') as any

    expect(option.series[0].roam).toBe('scale')
  })

  it('keeps full pan+zoom roam on non-touch (mouse/trackpad) devices', async () => {
    stubPointerCoarse(false)
    const wrapper = shallowMount(SpainMap, { props: { ccaaResumen: [] } })
    await nextTick()

    const option = wrapper.findComponent(VChart).props('option') as any

    expect(option.series[0].roam).toBe(true)
  })

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
