import { createRouter, createWebHistory, type RouteMeta } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { META_RUTAS, type MetaRuta } from './meta'

declare module 'vue-router' {
  interface RouteMeta extends MetaRuta {}
}

function metaDe(path: string): RouteMeta {
  return META_RUTAS[path] as unknown as RouteMeta
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: metaDe('/') },
    { path: '/mapa', name: 'mapa', component: () => import('../views/MapaView.vue'), meta: metaDe('/mapa') },
    { path: '/proyectos', name: 'proyectos', component: () => import('../views/ProyectosView.vue'), meta: metaDe('/proyectos') },
    { path: '/paises/:iso3', name: 'pais', component: () => import('../views/PaisView.vue'), meta: metaDe('/paises/:iso3') },
    { path: '/ccaa/:codigoIne', name: 'ccaa', component: () => import('../views/CcaaView.vue'), meta: metaDe('/ccaa/:codigoIne') },
    { path: '/sobre', name: 'sobre', component: () => import('../views/SobreView.vue'), meta: metaDe('/sobre') },
    { path: '/cookies', name: 'cookies', component: () => import('../views/PoliticaCookiesView.vue'), meta: metaDe('/cookies') },
  ],
  scrollBehavior(to) {
    if (to.hash && document.querySelector(to.hash)) {
      return { el: to.hash, top: 80 }
    }
    return { top: 0 }
  },
})

export default router
