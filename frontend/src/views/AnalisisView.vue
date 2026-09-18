<script setup lang="ts">
import { articulos } from 'virtual:analisis'

function formatFechaLarga(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
}
</script>

<template>
  <section class="page-head">
    <p class="kicker">Análisis</p>
    <h1 class="h-page">Cómo leer el dinero de la cooperación</h1>
    <p class="note">
      Artículos sobre cómo se publica, se clasifica y se lee el gasto en cooperación española, y
      sobre lo que los datos oficiales no cuentan.
    </p>
  </section>

  <ul class="lista">
    <li v-for="articulo in articulos" :key="articulo.slug">
      <router-link :to="`/analisis/${articulo.slug}`">{{ articulo.titulo }}</router-link>
      <p class="resumen">{{ articulo.resumen }}</p>
      <p class="fecha">{{ formatFechaLarga(articulo.fecha) }}</p>
    </li>
  </ul>
</template>

<style scoped>
.lista {
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: 720px;
}
.lista li {
  padding: 26px 0;
  border-bottom: 1px solid var(--rule);
}
.lista a {
  font-family: 'Newsreader', serif;
  font-size: 24px;
  line-height: 1.25;
  color: var(--ink);
}
.resumen {
  font-family: 'Newsreader', serif;
  font-size: 17px;
  line-height: 1.55;
  color: #2b3034;
  margin: 8px 0 0;
}
.fecha {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dim);
  margin: 10px 0 0;
}
</style>
