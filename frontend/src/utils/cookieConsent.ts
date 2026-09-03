import * as CookieConsent from 'vanilla-cookieconsent'
import 'vanilla-cookieconsent/dist/cookieconsent.css'
import { ref } from 'vue'

export const adsConsent = ref(false)
export const supportConsent = ref(false)

function getAdSensePublisherId(): string | undefined {
  const id = import.meta.env.VITE_ADSENSE_PUBLISHER_ID as string | undefined
  return id ? id : undefined
}

export function loadAdSense(): void {
  const publisherId = getAdSensePublisherId()
  if (!publisherId || document.querySelector('script[data-cc-script="adsense"]')) return

  const script = document.createElement('script')
  script.async = true
  script.crossOrigin = 'anonymous'
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${publisherId}`
  script.setAttribute('data-cc-script', 'adsense')
  document.head.appendChild(script)
}

export function loadBuyMeACoffee(): void {
  if (document.querySelector('script[data-cc-script="bmc"]')) return

  const script = document.createElement('script')
  script.src = 'https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js'
  script.setAttribute('data-cc-script', 'bmc')
  script.setAttribute('data-name', 'BMC-Widget')
  script.setAttribute('data-cfasync', 'false')
  script.setAttribute('data-id', 'santirbb')
  script.setAttribute('data-description', 'Support me on Buy me a coffee!')
  script.setAttribute('data-message', 'Apoya el proyecto con un café ☕')
  script.setAttribute('data-color', '#40DCA5')
  script.setAttribute('data-position', 'Right')
  script.setAttribute('data-x_margin', '18')
  script.setAttribute('data-y_margin', '18')
  document.body.appendChild(script)
}

export function handleConsentUpdate(): void {
  const previousAds = adsConsent.value
  const previousSupport = supportConsent.value
  const nowAds = CookieConsent.acceptedCategory('ads')
  const nowSupport = CookieConsent.acceptedCategory('support')

  if ((previousAds && !nowAds) || (previousSupport && !nowSupport)) {
    window.location.reload()
    return
  }

  adsConsent.value = nowAds
  supportConsent.value = nowSupport
  if (nowAds) loadAdSense()
  if (nowSupport) loadBuyMeACoffee()
}

export function initCookieConsent(): void {
  void CookieConsent.run({
    categories: {
      necessary: { enabled: true, readOnly: true },
      ads: {},
      support: {},
    },
    language: {
      default: 'es',
      translations: {
        es: {
          consentModal: {
            title: 'Usamos cookies',
            description:
              'Usamos cookies solo para mostrar publicidad (Google AdSense) y el widget de apoyo ' +
              'al proyecto (Buy Me a Coffee). Ninguna de las dos se activa hasta que la aceptes. ' +
              'Más detalles en la <a href="#/cookies">política de cookies</a>.',
            acceptAllBtn: 'Aceptar todo',
            acceptNecessaryBtn: 'Rechazar todo',
            showPreferencesBtn: 'Personalizar',
          },
          preferencesModal: {
            title: 'Preferencias de cookies',
            acceptAllBtn: 'Aceptar todo',
            acceptNecessaryBtn: 'Rechazar todo',
            savePreferencesBtn: 'Guardar preferencias',
            closeIconLabel: 'Cerrar',
            sections: [
              {
                title: 'Cookies necesarias',
                description: 'Recuerdan tu elección de cookies. Siempre activas.',
                linkedCategory: 'necessary',
              },
              {
                title: 'Publicidad',
                description: 'Cargan Google AdSense para mostrar el anuncio del sitio.',
                linkedCategory: 'ads',
              },
              {
                title: 'Apoyo al proyecto',
                description: 'Cargan el widget de Buy Me a Coffee.',
                linkedCategory: 'support',
              },
            ],
          },
        },
      },
    },
    onConsent: handleConsentUpdate,
    onChange: handleConsentUpdate,
  })
}

export function openCookiePreferences(): void {
  CookieConsent.showPreferences()
}
