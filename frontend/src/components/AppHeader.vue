<script setup lang="ts">
const links = [
  { to: '/', label: 'Inicio' },
  { to: '/mapa', label: 'Mapa' },
  { to: '/proyectos', label: 'Proyectos' },
  { to: '/analisis', label: 'Análisis' },
  { to: '/sobre', label: 'Sobre los datos' },
]
</script>

<template>
  <header class="site">
    <div class="wrap hd">
      <router-link class="brand" to="/">
        <b>Sigue el dinero</b>
        <span>Cooperación española</span>
      </router-link>
      <nav>
        <router-link v-for="link in links" :key="link.to" :to="link.to">{{ link.label }}</router-link>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site {
  border-bottom: 1px solid var(--ink);
  background: var(--paper);
  position: sticky;
  top: 0;
  z-index: 20;
}
.hd {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 24px;
  padding: 14px 0;
  flex-wrap: wrap;
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 12px;
  border: 0;
  text-decoration: none;
}
@media (max-width: 860px) {
  .brand {
    flex-wrap: wrap;
    row-gap: 2px;
  }
}
.brand b {
  font-family: 'Newsreader', serif;
  font-weight: 600;
  font-size: 23px;
  letter-spacing: -0.02em;
  color: var(--ink);
}
.brand span {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--dim);
}
nav {
  display: flex;
  gap: 22px;
  flex-wrap: wrap;
}
nav a {
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dim);
  border: 0;
  text-decoration: none;
  padding-bottom: 2px;
}
nav a:hover {
  color: var(--ink);
}
nav a.router-link-exact-active {
  color: var(--ink);
  box-shadow: inset 0 -2px 0 var(--amber);
}
</style>
