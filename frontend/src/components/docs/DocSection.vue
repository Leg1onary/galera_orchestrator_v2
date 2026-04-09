<template>
  <section class="docs-section">
    <h3 class="docs-section__title">{{ sectionName }}</h3>
    <div class="docs-section__grid">
      <DocCard
          v-for="card in cards"
          :key="card.id"
          :title="card.title"
          :badge="card.badge"
          :description="card.description"
          :code="card.code"
          :note="card.note"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import type { DocCard as DocCardType } from '@/data/docs'
import DocCard from './DocCard.vue'

defineProps<{
  sectionName: string
  cards: DocCardType[]
}>()
</script>