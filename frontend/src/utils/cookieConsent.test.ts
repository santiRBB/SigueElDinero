// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('vanilla-cookieconsent', () => ({
  run: vi.fn(),
  showPreferences: vi.fn(),
  acceptedCategory: vi.fn(),
}))

import * as CookieConsent from 'vanilla-cookieconsent'
import {
  adsConsent,
  supportConsent,
  handleConsentUpdate,
  loadAdSense,
  loadBuyMeACoffee,
  openCookiePreferences,
} from './cookieConsent'

describe('cookieConsent', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    document.body.innerHTML = ''
    adsConsent.value = false
    supportConsent.value = false
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', 'ca-pub-test123')
    vi.mocked(CookieConsent.acceptedCategory).mockReturnValue(false)
    vi.stubGlobal('location', { reload: vi.fn() } as any)
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('loadAdSense does nothing without a publisher id', () => {
    vi.stubEnv('VITE_ADSENSE_PUBLISHER_ID', '')
    loadAdSense()
    expect(document.querySelector('script[data-cc-script="adsense"]')).toBeNull()
  })

  it('loadAdSense injects the AdSense script with the publisher id in the src', () => {
    loadAdSense()
    const script = document.querySelector('script[data-cc-script="adsense"]')
    expect(script).not.toBeNull()
    expect(script?.getAttribute('src')).toContain('client=ca-pub-test123')
  })

  it('loadAdSense does not inject the script twice', () => {
    loadAdSense()
    loadAdSense()
    expect(document.querySelectorAll('script[data-cc-script="adsense"]')).toHaveLength(1)
  })

  it('loadBuyMeACoffee injects the widget script with the original data attributes', () => {
    loadBuyMeACoffee()
    const script = document.querySelector('script[data-cc-script="bmc"]')
    expect(script).not.toBeNull()
    expect(script?.getAttribute('data-id')).toBe('santirbb')
    expect(script?.getAttribute('data-x_margin')).toBe('18')
    expect(script?.getAttribute('data-y_margin')).toBe('18')
  })

  it('handleConsentUpdate does not load anything when no category is accepted', () => {
    handleConsentUpdate()
    expect(adsConsent.value).toBe(false)
    expect(supportConsent.value).toBe(false)
    expect(document.querySelector('script[data-cc-script="adsense"]')).toBeNull()
    expect(document.querySelector('script[data-cc-script="bmc"]')).toBeNull()
  })

  it('handleConsentUpdate loads AdSense once the ads category is accepted', () => {
    vi.mocked(CookieConsent.acceptedCategory).mockImplementation((category) => category === 'ads')
    handleConsentUpdate()
    expect(adsConsent.value).toBe(true)
    expect(document.querySelector('script[data-cc-script="adsense"]')).not.toBeNull()
  })

  it('handleConsentUpdate reloads the page when a previously accepted category is revoked', () => {
    adsConsent.value = true
    vi.mocked(CookieConsent.acceptedCategory).mockReturnValue(false)

    handleConsentUpdate()

    expect(window.location.reload).toHaveBeenCalledTimes(1)
  })

  it('openCookiePreferences delegates to CookieConsent.showPreferences', () => {
    openCookiePreferences()
    expect(CookieConsent.showPreferences).toHaveBeenCalledTimes(1)
  })
})
