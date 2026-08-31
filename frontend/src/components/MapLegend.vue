<script setup lang="ts">
import { RAMP } from '../utils/mapaColores'
</script>

<template>
  <div class="legend">
    <span class="lg-label">Menos</span>
    <span v-for="color in RAMP" :key="color" class="lg-sw" :style="{ background: color }"></span>
    <span class="lg-label">Más</span>
    <span class="lg-sw lg-none"></span>
    <span class="lg-label">Sin datos</span>
  </div>
</template>

<style scoped>
.legend {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 14px;
  flex-wrap: wrap;
}
.lg-sw {
  width: 26px;
  height: 9px;
  display: inline-block;
}
.lg-none {
  background: #e6e1d7;
}
.lg-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dim);
  margin: 0 8px 0 4px;
}
</style>
