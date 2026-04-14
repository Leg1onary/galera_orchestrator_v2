<template>
  <div class="docs-page">
    <!-- ── Page header ──────────────────────────────────────────── -->
    <div class="docs-page__header">
      <h1 class="docs-page__title">Документация</h1>
      <p class="docs-page__subtitle">
        Справочник по командам, wsrep-переменным, архитектуре и типовым сценариям.
      </p>
    </div>

    <!-- ── Search ──────────────────────────────────────────────── -->
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

    <!-- ── Search results ──────────────────────────────────────────── -->
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
            <div class="docs-cards-grid">
              <DocCard
                v-for="card in tabGroup.cards"
                :key="card.id"
                :title="card.title"
                :badge="card.badge"
                :description="card.description"
                :code="card.code"
                :code-lang="card.codeLang"
                :note="card.note"
              />
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- ── Tabbed view ──────────────────────────────────────────────── -->
    <template v-else>
      <div class="docs-tabs">
        <!-- Tab switcher -->
        <div class="docs-tabs__nav" role="tablist">
          <button
            v-for="(tab, index) in DOC_TABS"
            :key="tab.id"
            role="tab"
            :id="`docs-tab-${tab.id}`"
            :aria-selected="activeTab === tab.id"
            :aria-controls="`docs-tabpanel-${tab.id}`"
            class="docs-tabs__tab"
            :class="{ 'docs-tabs__tab--active': activeTab === tab.id }"
            @click="activeTab = tab.id"
            @keydown="handleTabKeydown($event, index)"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content -->
        <div
          class="docs-tabs__content"
          role="tabpanel"
          :id="`docs-tabpanel-${activeTab}`"
          :aria-labelledby="`docs-tab-${activeTab}`"
        >
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
import { ref, computed, watch } from 'vue'
import DocCard from '@/components/docs/DocCard.vue'
import DocSection from '@/components/docs/DocSection.vue'
import { DOCS, DOC_TABS, type DocTab } from '@/data/docs'
import { plural } from '@/utils/plural'

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

// ── Search with debounce ──

const search = ref('')
const debouncedSearch = ref('')

watch(
  search,
  (value) => {
    clearTimeout((debouncedSearch as any)._t)
    ;(debouncedSearch as any)._t = setTimeout(() => {
      debouncedSearch.value = value
    }, 150)
  },
  { flush: 'post' },
)

const searchResults = computed(() => {
  const q = debouncedSearch.value.trim().toLowerCase()
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

// ── Tab helpers ──

const tabLabelMap = computed(() =>
  DOC_TABS.reduce((acc, t) => {
    acc[t.id] = t.label
    return acc
  }, {} as Record<DocTab, string>),
)

function getTabLabel(tabId: DocTab): string {
  return tabLabelMap.value[tabId] ?? tabId
}

function handleTabKeydown(event: KeyboardEvent, currentIndex: number) {
  if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
    event.preventDefault()
    const dir = event.key === 'ArrowRight' ? 1 : -1
    const tabs = DOC_TABS
    const nextIndex = (currentIndex + dir + tabs.length) % tabs.length
    activeTab.value = tabs[nextIndex].id
    requestAnimationFrame(() => {
      const el = document.getElementById(`docs-tab-${tabs[nextIndex].id}`)
      el?.focus()
    })
  }
}
</script>

<style scoped>
/* ── Page: full-width, left-aligned ── */
.docs-page {
  width: 100%;
  padding: var(--space-8) var(--space-8);
}

/* ── Header ── */
.docs-page__header {
  margin-bottom: var(--space-6);
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
  max-width: 520px;
}

.docs-page__search-box {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}
.docs-page__search-box:focus-within {
  border-color: var(--color-border-active);
  box-shadow: 0 0 0 3px var(--color-primary-dim);
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
  background: var(--color-surface-4);
}
.docs-page__search-clear .pi { font-size: 0.75rem; }

/* ── Empty ── */
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

/* ── Custom tab switcher ── */
.docs-tabs__nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  padding: var(--space-1);
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
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
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 180ms ease;
  white-space: nowrap;
  line-height: 1.4;
}
.docs-tabs__tab:hover {
  color: var(--color-text);
  background: var(--color-surface-3);
}
.docs-tabs__tab--active {
  background: var(--color-primary-dim);
  color: var(--color-primary);
  border-color: var(--color-border-hover);
}
.docs-tabs__tab--active:hover {
  background: var(--color-primary-glow);
}

.docs-tabs__content {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

/* ── Shared card grid (used in search results too) ── */
.docs-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: var(--space-5);
}
</style>
