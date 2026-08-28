<script setup lang="ts">
defineProps<{
  porcentajeFuente: 'declared' | 'assumed_equal_split' | null
}>()
</script>

<template>
  <span v-if="porcentajeFuente === 'assumed_equal_split'" class="amount-badge">
    Reparto estimado entre países
  </span>
</template>

<style scoped>
.amount-badge {
  display: inline-block;
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: #fef3c7;
  color: #92400e;
}
</style>
