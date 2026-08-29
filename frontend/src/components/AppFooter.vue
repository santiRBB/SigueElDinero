<template>
  <footer class="site">
    <div class="wrap fr">
      <span>Datos de cooperación española (AECID/IATI). Esta fase cubre solo el gasto internacional.</span>
      <span>Geografía: world-atlas (Natural Earth) · <router-link to="/sobre">Metodología</router-link></span>
    </div>
  </footer>
</template>

<style scoped>
.site {
  border-top: 1px solid var(--ink);
  padding: 26px 0 60px;
  font-size: 12.5px;
  color: var(--dim);
}
.fr {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}
</style>
