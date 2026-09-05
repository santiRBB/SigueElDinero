<script setup lang="ts">
defineProps<{
  valor: string
  etiqueta: string
}>()
</script>

<template>
  <div class="stat">
    <span class="s-v">{{ valor }}</span>
    <span class="s-l">{{ etiqueta }}</span>
  </div>
</template>

<style scoped>
.stat {
  padding: 20px 22px 22px;
  border-left: 1px solid var(--rule2);
}
.stat:first-child {
  border-left: 0;
  padding-left: 0;
}
.s-v {
  display: block;
  font-family: 'Newsreader', serif;
  font-size: 30px;
  line-height: 1.1;
  color: var(--navy);
  letter-spacing: -0.02em;
  overflow-wrap: break-word;
}
.s-l {
  display: block;
  margin-top: 8px;
  font-size: 11.5px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--dim);
}

@media (max-width: 860px) {
  .stat {
    border-left: 1px solid var(--rule2);
    padding-left: 18px;
  }
  .stat:nth-child(odd) {
    border-left: 0;
    padding-left: 0;
  }
  .stat:nth-child(n + 3) {
    border-top: 1px solid var(--rule2);
  }
}
</style>
