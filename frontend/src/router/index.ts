import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { META_RUTAS, type MetaRuta } from './meta'

declare module 'vue-router' {
  interface RouteMeta extends MetaRuta {}
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: META_RUTAS['/'] },
    { path: '/mapa', name: 'mapa', component: () => import('../views/MapaView.vue'), meta: META_RUTAS['/mapa'] },
    { path: '/proyectos', name: 'proyectos', component: () => import('../views/ProyectosView.vue'), meta: META_RUTAS['/proyectos'] },
    { path: '/paises/:iso3', name: 'pais', component: () => import('../views/PaisView.vue'), meta: META_RUTAS['/paises/:iso3'] },
    { path: '/ccaa/:codigoIne', name: 'ccaa', component: () => import('../views/CcaaView.vue'), meta: META_RUTAS['/ccaa/:codigoIne'] },
    { path: '/sobre', name: 'sobre', component: () => import('../views/SobreView.vue'), meta: META_RUTAS['/sobre'] },
    { path: '/cookies', name: 'cookies', component: () => import('../views/PoliticaCookiesView.vue'), meta: META_RUTAS['/cookies'] },
  ],
  scrollBehavior(to) {
    if (to.hash && document.querySelector(to.hash)) {
      return { el: to.hash, top: 80 }
    }
    return { top: 0 }
  },
})

export default router
