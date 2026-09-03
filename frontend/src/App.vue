<script setup lang="ts">
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import AdSlot from './components/AdSlot.vue'
</script>

<template>
  <AppHeader />
  <main>
    <div class="wrap">
      <router-view />
    </div>
  </main>
  <AppFooter />
  <AdSlot />
</template>
