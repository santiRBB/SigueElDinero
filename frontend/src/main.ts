import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { initCookieConsent } from './utils/cookieConsent'
import './styles/tokens.css'

createApp(App).use(createPinia()).use(router).mount('#app')
initCookieConsent()
