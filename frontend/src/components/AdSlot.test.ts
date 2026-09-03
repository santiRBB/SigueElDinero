// @vitest-environment jsdom
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('vanilla-cookieconsent', () => ({
  run: vi.fn(),
  showPreferences: vi.fn(),
  acceptedCategory: vi.fn(),
}))

import * as CookieConsent from 'vanilla-cookieconsent'
import { adsConsent } from '../utils/cookieConsent'
import AdSlot from './AdSlot.vue'

describe('AdSlot', () => {
  let wrapper: any

  beforeEach(() => {
    adsConsent.value = false
    window.adsbygoogle = []
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', 'ca-pub-test123')
    vi.stubEnv('VITE_ADSENSE_SLOT_ID', '1234567890')
  })

  afterEach(() => {
    if (wrapper) wrapper.unmount()
  })

  it('shows the consent notice instead of the ad when ads are not accepted', () => {
    wrapper = mount(AdSlot)
    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(true)
  })

  it('renders the ad unit and requests an ad once ads are accepted', async () => {
    adsConsent.value = true
    wrapper = mount(AdSlot)
    await wrapper.vm.$nextTick()

    const ins = wrapper.find('ins.adsbygoogle')
    expect(ins.exists()).toBe(true)
    expect(ins.attributes('data-ad-client')).toBe('ca-pub-test123')
    expect(ins.attributes('data-ad-slot')).toBe('1234567890')
    expect(window.adsbygoogle).toHaveLength(1)
  })

  it('reopens cookie preferences when the notice button is clicked', async () => {
    wrapper = mount(AdSlot)

    await wrapper.find('.ad-placeholder button').trigger('click')

    expect(CookieConsent.showPreferences).toHaveBeenCalledTimes(1)
  })

  it('shows nothing when ads are accepted but ad config is incomplete', () => {
    adsConsent.value = true
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', '')
    vi.stubEnv('VITE_ADSENSE_SLOT_ID', '1234567890')
    wrapper = mount(AdSlot)

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
  })

  it('renders ad when consent changes from false to true after mount', async () => {
    wrapper = mount(AdSlot)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(true)
    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(false)

    adsConsent.value = true
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('ins.adsbygoogle').exists()).toBe(true)
    expect(wrapper.find('.ad-placeholder').exists()).toBe(false)
    expect(window.adsbygoogle).toHaveLength(1)
  })
})
