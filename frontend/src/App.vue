<template>
  <RouterView />
  <Toast position="bottom-right" />
</template>

<script setup lang="ts">
import Toast from 'primevue/toast'
// App.vue is intentionally minimal — root mount point.
// Layout handled by AppLayout.vue. LoginPage handles its own layout.
</script>