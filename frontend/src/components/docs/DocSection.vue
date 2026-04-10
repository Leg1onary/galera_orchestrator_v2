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

<style scoped>
.docs-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.docs-section__title {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* Responsive grid: 1 col → 2 col → 3 col depending on available width */
.docs-section__grid {
  display: grid;
  /* min 280px per card — browser auto-fills columns */
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: var(--space-5);
}

/* Wider screens: cap card width so they don't become huge */
@media (min-width: 1400px) {
  .docs-section__grid {
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    max-width: none;
  }
}
</style>
