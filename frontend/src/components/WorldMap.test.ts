// @vitest-environment jsdom
import { describe, expect, it, vi, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { shallowMount } from '@vue/test-utils'
import VChart from 'vue-echarts'
import WorldMap from './WorldMap.vue'

function stubPointerCoarse(matches: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockReturnValue({ matches, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
  )
}

describe('WorldMap', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('emits country-click with the iso3 of the clicked country', async () => {
    stubPointerCoarse(false)
    const wrapper = shallowMount(WorldMap, { props: { paisesResumen: [] } })
    await nextTick()

    await wrapper.findComponent(VChart).vm.$emit('click', { name: 'ESP' })

    expect(wrapper.emitted('country-click')).toEqual([['ESP']])
  })

  it('ignores clicks on geographies that never resolved to an ISO3 (e.g. Kosovo, Somaliland, N. Cyprus)', async () => {
    stubPointerCoarse(false)
    const wrapper = shallowMount(WorldMap, { props: { paisesResumen: [] } })
    await nextTick()

    await wrapper.findComponent(VChart).vm.$emit('click', { name: 'Kosovo' })

    expect(wrapper.emitted('country-click')).toBeUndefined()
  })

  it('disables map panning (keeps pinch-zoom) on touch devices so a vertical swipe scrolls the page', async () => {
    stubPointerCoarse(true)
    const wrapper = shallowMount(WorldMap, { props: { paisesResumen: [] } })
    await nextTick()

    const option = wrapper.findComponent(VChart).props('option') as any

    expect(option.series[0].roam).toBe('scale')
  })

  it('keeps full pan+zoom roam on non-touch (mouse/trackpad) devices', async () => {
    stubPointerCoarse(false)
    const wrapper = shallowMount(WorldMap, { props: { paisesResumen: [] } })
    await nextTick()

    const option = wrapper.findComponent(VChart).props('option') as any

    expect(option.series[0].roam).toBe(true)
  })
})
