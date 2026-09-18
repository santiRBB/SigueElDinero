<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { articulos } from 'virtual:analisis'
import { aplicarHead } from '../utils/head'

const route = useRoute()
const articulo = computed(() => articulos.find((a) => a.slug === String(route.params.slug)) ?? null)

watch(
  articulo,
  (actual) => {
    if (!actual) return
    aplicarHead({
      titulo: actual.titulo,
      descripcion: actual.descripcion,
      indexable: true,
      ruta: `/analisis/${actual.slug}`,
    })
  },
  { immediate: true },
)

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
  <template v-if="articulo">
    <section class="page-head">
      <p class="kicker"><router-link to="/analisis">Análisis</router-link></p>
      <h1 class="h-page">{{ articulo.titulo }}</h1>
      <p class="note">{{ formatFechaLarga(articulo.fecha) }}</p>
    </section>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <article class="prose prose-estrecha" v-html="articulo.html" />
  </template>
  <section v-else class="page-head">
    <h1 class="h-page">Artículo no encontrado</h1>
    <p class="note"><router-link to="/analisis">Volver al índice de análisis</router-link></p>
  </section>
</template>
