import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/mapa', name: 'mapa', component: () => import('../views/MapaView.vue') },
    { path: '/proyectos', name: 'proyectos', component: () => import('../views/ProyectosView.vue') },
    { path: '/paises/:iso3', name: 'pais', component: () => import('../views/PaisView.vue') },
    { path: '/sobre', name: 'sobre', component: () => import('../views/SobreView.vue') },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
