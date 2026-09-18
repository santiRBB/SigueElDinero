import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/mapa', name: 'mapa', component: () => import('../views/MapaView.vue') },
    { path: '/proyectos', name: 'proyectos', component: () => import('../views/ProyectosView.vue') },
    { path: '/paises/:iso3', name: 'pais', component: () => import('../views/PaisView.vue') },
    { path: '/ccaa/:codigoIne', name: 'ccaa', component: () => import('../views/CcaaView.vue') },
    { path: '/sobre', name: 'sobre', component: () => import('../views/SobreView.vue') },
    { path: '/cookies', name: 'cookies', component: () => import('../views/PoliticaCookiesView.vue') },
  ],
  scrollBehavior(to) {
    if (to.hash && document.querySelector(to.hash)) {
      return { el: to.hash, top: 80 }
    }
    return { top: 0 }
  },
})

export default router
