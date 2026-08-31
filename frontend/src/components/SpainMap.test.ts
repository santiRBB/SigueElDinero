// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { shallowMount } from '@vue/test-utils'
import VChart from 'vue-echarts'
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
})
