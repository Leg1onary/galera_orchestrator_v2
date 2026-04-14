<template>
  <section class="docs-section">
    <h3 class="docs-section__title section-title">{{ sectionName }}</h3>
    <div class="docs-section__grid">
      <DocCard
        v-for="card in cards"
        :key="card.id"
        :title="card.title"
        :badge="card.badge"
        :description="card.description"
        :code="card.code"
        :code-lang="card.codeLang"
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

<style scoped>
.docs-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.docs-section__title {
  border-bottom: 1px solid var(--color-border-muted);
  padding-bottom: var(--space-3);
}

.docs-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: var(--space-5);
}
</style>
