<script setup lang="ts">
import type { Proyecto } from '../services/api'
import AmountBadge from './AmountBadge.vue'

defineProps<{
  proyecto: Proyecto
  importeEstandar: boolean
}>()

function formatEUR(valor: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(valor)
}
</script>

<template>
  <div class="project-card">
    <h3>{{ proyecto.titulo ?? proyecto.aid }}</h3>
    <p class="organismo">{{ proyecto.organismo_ejecutor ?? 'Organismo no especificado' }}</p>
    <p class="importe">{{ formatEUR(proyecto.importe_pais_eur) }}</p>
    <AmountBadge :porcentaje-fuente="proyecto.porcentaje_fuente" />
    <p v-if="importeEstandar" class="nota-estandar">Importe estándar de esta convocatoria</p>
    <p class="fechas">{{ proyecto.start_date }} — {{ proyecto.end_date ?? 'en curso' }}</p>
  </div>
</template>

<style scoped>
.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
}
.organismo {
  color: #6b7280;
  font-size: 0.875rem;
}
.importe {
  font-weight: 600;
  font-size: 1.1rem;
}
.nota-estandar {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
}
.fechas {
  font-size: 0.75rem;
  color: #9ca3af;
}
</style>
