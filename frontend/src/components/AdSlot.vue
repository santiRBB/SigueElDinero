<script setup lang="ts">
import { computed, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { adsConsent, openCookiePreferences } from '../utils/cookieConsent'

const props = defineProps<{ contenidoListo: boolean }>()

const route = useRoute()
const adClientId = import.meta.env.VITE_ADSENSE_PUBLISHER_ID as string | undefined
const adSlotId = import.meta.env.VITE_ADSENSE_SLOT_ID as string | undefined
const hayConfig = Boolean(adClientId && adSlotId)

// Tres condiciones, y las tres tienen que cumplirse: la ruta debe ser apta, el contenido del editor
// debe estar ya en pantalla, y el usuario debe haber aceptado las cookies de publicidad. Sin esto,
// AdSense marca el sitio por servir anuncios en pantallas sin contenido.
const huecoVisible = computed(() => route.meta.anuncios === true && props.contenidoListo)
const muestraAnuncio = computed(() => huecoVisible.value && adsConsent.value && hayConfig)
const muestraAviso = computed(() => huecoVisible.value && !adsConsent.value && hayConfig)

function pedirAnuncio(): void {
  window.adsbygoogle = window.adsbygoogle || []
  window.adsbygoogle.push({})
}

// route.path entra en las fuentes del watcher, no solo route.meta.anuncios en el computed:
// cuando Vue Router reutiliza esta misma instancia entre dos rutas del mismo registro (dos
// artículos de /analisis/:slug, por ejemplo), muestraAnuncio no cambia de valor y por tanto
// nunca dispararía este watcher por sí solo, aunque el :key="route.path" del <ins> sí monte
// un nodo nuevo. Sin este segundo disparador, ese nodo nuevo nunca se procesa: un hueco de
// anuncio vacío en silencio para siempre.
watch(
  [muestraAnuncio, () => route.path],
  () => {
    if (muestraAnuncio.value) void nextTick(pedirAnuncio)
  },
  { immediate: true },
)
</script>

<template>
  <aside v-if="muestraAnuncio" class="ad-slot">
    <p class="ad-label">Publicidad</p>
    <ins
      :key="route.path"
      class="adsbygoogle"
      style="display: block"
      :data-ad-client="adClientId"
      :data-ad-slot="adSlotId"
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
  </aside>
  <aside v-else-if="muestraAviso" class="ad-slot ad-placeholder">
    <p>Apoya el proyecto viendo anuncios.</p>
    <button type="button" @click="openCookiePreferences">Configurar cookies</button>
  </aside>
</template>

<style scoped>
.ad-slot {
  margin: 46px auto 0;
  max-width: 728px;
  border-top: 1px solid var(--rule);
  padding-top: 12px;
}
.ad-label {
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--dim);
  margin: 0 0 10px;
}
.ad-placeholder {
  border: 1px solid var(--rule);
  background: var(--paper);
  padding: 18px;
  text-align: center;
  font-size: 13px;
  color: var(--dim);
}
.ad-placeholder p {
  margin: 0 0 10px;
}
.ad-placeholder button {
  border: 1px solid var(--ink);
  background: none;
  padding: 6px 14px;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink);
}
.ad-placeholder button:hover {
  border-color: var(--amber);
  color: var(--amber);
}
</style>
