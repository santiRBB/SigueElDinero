<script setup lang="ts">
import { nextTick, onMounted, watch } from 'vue'
import { adsConsent, openCookiePreferences } from '../utils/cookieConsent'

const adClientId = import.meta.env.VITE_ADSENSE_PUBLISHER_ID as string | undefined
const adSlotId = import.meta.env.VITE_ADSENSE_SLOT_ID as string | undefined
const hasAdConfig = Boolean(adClientId && adSlotId)

function requestAd(): void {
  window.adsbygoogle = window.adsbygoogle || []
  window.adsbygoogle.push({})
}

onMounted(() => {
  if (adsConsent.value && hasAdConfig) void nextTick(requestAd)
})

watch(adsConsent, (accepted) => {
  if (accepted && hasAdConfig) void nextTick(requestAd)
})
</script>

<template>
  <aside class="ad-slot">
    <ins
      v-if="adsConsent && hasAdConfig"
      class="adsbygoogle"
      style="display: block"
      :data-ad-client="adClientId"
      :data-ad-slot="adSlotId"
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
    <div v-else-if="!adsConsent" class="ad-placeholder">
      <p>Apoya el proyecto viendo anuncios.</p>
      <button type="button" @click="openCookiePreferences">Configurar cookies</button>
    </div>
  </aside>
</template>

<style scoped>
.ad-slot {
  display: none;
}
@media (min-width: 1760px) {
  .ad-slot {
    display: block;
    position: fixed;
    right: 24px;
    bottom: 96px;
    width: 280px;
    z-index: 15;
  }
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
