<template>
  <div class="docs-page">
    <!-- ── Page header ── -->
    <div class="docs-page__header">
      <h1 class="docs-page__title">Документация</h1>
      <p class="docs-page__subtitle">
        Справочник по командам, wsrep-переменным, архитектуре и типовым сценариям.
      </p>
    </div>

    <!-- ── Search ── -->
    <div class="docs-page__search-wrap">
      <div class="docs-page__search-box">
        <i class="pi pi-search docs-page__search-icon" />
        <input
          v-model="search"
          type="text"
          placeholder="Поиск по заголовку, описанию, коду…"
          class="docs-page__search-input"
        />
        <button
          v-if="search"
          class="docs-page__search-clear"
          @click="clearSearch"
          aria-label="Очистить поиск"
        >
          <i class="pi pi-times" />
        </button>
      </div>
    </div>

    <!-- ── Search results ── -->
    <template v-if="search.trim()">
      <div v-if="searchResults.length === 0" class="docs-page__empty">
        <i class="pi pi-search docs-page__empty-icon" />
        <p>Ничего не найдено по запросу <strong>"{{ search }}"</strong></p>
      </div>

      <div v-else class="docs-page__search-results">
        <div class="docs-page__search-count">
          Найдено: {{ searchResults.length }} {{ plural(searchResults.length, 'карточка', 'карточки', 'карточек') }}
        </div>
        <template v-for="tabGroup in searchGrouped" :key="tabGroup.tabId">
          <div class="docs-page__search-group">
            <span class="docs-page__search-group-label">{{ getTabLabel(tabGroup.tabId) }}</span>
            <div class="docs-section__grid">
              <DocCard
                v-for="card in tabGroup.cards"
                :key="card.id"
                :title="card.title"
                :badge="card.badge"
                :description="card.description"
                :code="card.code"
                :note="card.note"
              />
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- ── Tabbed view ── -->
    <template v-else>
      <div class="docs-tabs">
        <!-- Tab switcher -->
        <div class="docs-tabs__nav" role="tablist">
          <button
            v-for="tab in DOC_TABS"
            :key="tab.id"
            role="tab"
            :aria-selected="activeTab === tab.id"
            class="docs-tabs__tab"
            :class="{ 'docs-tabs__tab--active': activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content -->
        <div class="docs-tabs__content">
          <DocSection
            v-for="section in getSections(activeTab)"
            :key="section.name"
            :section-name="section.name"
            :cards="section.cards"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import DocCard from '@/components/docs/DocCard.vue'
import DocSection from '@/components/docs/DocSection.vue'
import { DOCS, DOC_TABS, type DocTab } from '@/data/docs'

const activeTab = ref(DOC_TABS[0].id)

function getSections(tabId: DocTab): { name: string; cards: typeof DOCS }[] {
  const cards = DOCS.filter((c) => c.tab === tabId)
  const sectionMap = new Map<string, typeof DOCS>()
  for (const card of cards) {
    if (!sectionMap.has(card.section)) sectionMap.set(card.section, [])
    sectionMap.get(card.section)!.push(card)
  }
  return Array.from(sectionMap.entries()).map(([name, cards]) => ({ name, cards }))
}

const search = ref('')

const searchResults = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return []
  return DOCS.filter(
    (c) =>
      c.title.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      (c.code ?? '').toLowerCase().includes(q) ||
      (c.note ?? '').toLowerCase().includes(q) ||
      c.section.toLowerCase().includes(q),
  )
})

const searchGrouped = computed(() => {
  const groups = new Map<DocTab, typeof DOCS>()
  for (const card of searchResults.value) {
    if (!groups.has(card.tab)) groups.set(card.tab, [])
    groups.get(card.tab)!.push(card)
  }
  return Array.from(groups.entries()).map(([tabId, cards]) => ({ tabId, cards }))
})

function clearSearch() { search.value = '' }

function getTabLabel(tabId: DocTab): string {
  return DOC_TABS.find((t) => t.id === tabId)?.label ?? tabId
}

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few
  return many
}
</script>

<style scoped>
.docs-page {
  max-width: 1100px;
  margin-inline: auto;
  padding: var(--space-8) var(--space-6);
}

/* ── Header ── */
.docs-page__header {
  margin-bottom: var(--space-8);
}
.docs-page__title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-2);
}
.docs-page__subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 60ch;
}

/* ── Search ── */
.docs-page__search-wrap {
  margin-bottom: var(--space-8);
  max-width: 560px;
}

.docs-page__search-box {
  position: relative;
  display: flex;
  align-items: center;
  background: #13141a;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-lg);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}
.docs-page__search-box:focus-within {
  border-color: rgba(45,212,191,0.4);
  box-shadow: 0 0 0 3px rgba(45,212,191,0.08);
}

.docs-page__search-icon {
  position: absolute;
  left: var(--space-4);
  color: var(--color-text-faint);
  font-size: 0.875rem;
  pointer-events: none;
  transition: color 180ms ease;
}
.docs-page__search-box:focus-within .docs-page__search-icon {
  color: var(--color-primary);
}

.docs-page__search-input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: inherit;
  padding: 0.75rem var(--space-4) 0.75rem 2.5rem;
  line-height: 1.5;
}
.docs-page__search-input::placeholder {
  color: var(--color-text-faint);
}

.docs-page__search-clear {
  flex-shrink: 0;
  margin-right: var(--space-2);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--color-text-faint);
  transition: all 180ms ease;
  background: transparent;
  border: none;
  cursor: pointer;
}
.docs-page__search-clear:hover {
  color: var(--color-text);
  background: rgba(255,255,255,0.06);
}
.docs-page__search-clear .pi { font-size: 0.75rem; }

/* ── Empty state ── */
.docs-page__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-16) 0;
  color: var(--color-text-muted);
  text-align: center;
}
.docs-page__empty-icon {
  font-size: 2.5rem;
  color: var(--color-text-faint);
}

/* ── Search results ── */
.docs-page__search-count {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
}
.docs-page__search-group {
  margin-bottom: var(--space-8);
}
.docs-page__search-group-label {
  display: inline-block;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-primary);
  margin-bottom: var(--space-3);
}

/* ── Custom tabs ── */
.docs-tabs {}

.docs-tabs__nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  padding: var(--space-1);
  background: #13141a;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-8);
  width: fit-content;
}

.docs-tabs__tab {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 180ms ease;
  white-space: nowrap;
  line-height: 1.4;
}
.docs-tabs__tab:hover {
  color: var(--color-text);
  background: rgba(255,255,255,0.05);
}
.docs-tabs__tab--active {
  background: rgba(45,212,191,0.1);
  color: #2dd4bf;
  border: 1px solid rgba(45,212,191,0.2);
}
.docs-tabs__tab--active:hover {
  background: rgba(45,212,191,0.15);
}

.docs-tabs__content {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

/* Section grid (used by DocSection.vue and search results) */
.docs-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: var(--space-4);
}
</style>
