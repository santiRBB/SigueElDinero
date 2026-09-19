import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { initCookieConsent } from './utils/cookieConsent'
import { instalarHead } from './utils/head'
import './styles/tokens.css'

instalarHead(router)
createApp(App).use(createPinia()).use(router).mount('#app')
initCookieConsent()
