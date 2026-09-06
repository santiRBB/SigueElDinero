<script setup lang="ts">
import { openCookiePreferences } from '../utils/cookieConsent'
</script>

<template>
  <footer class="site">
    <div class="wrap fr">
      <span>Datos de cooperación española (AECID/IATI) y subvenciones públicas en España (BDNS).</span>
      <span>Geografía: world-atlas (Natural Earth) · <router-link to="/sobre">Metodología</router-link></span>
      <span>
        <router-link to="/cookies">Política de cookies</router-link> ·
        <button type="button" class="link-btn" @click="openCookiePreferences">
          Preferencias de cookies
        </button>
      </span>
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
.link-btn {
  all: unset;
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
  color: var(--navy);
  border-bottom: 1px solid rgba(11, 59, 92, 0.3);
}
.link-btn:hover {
  color: var(--amber);
  border-bottom-color: var(--amber);
}
</style>
