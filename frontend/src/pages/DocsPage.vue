<template>
    <div class="docs-page">
      <!-- ── Page header ───────────────────────────────────────────── -->
      <div class="docs-page__header">
        <h1 class="docs-page__title">Документация</h1>
        <p class="docs-page__subtitle">
          Справочник по командам, wsrep-переменным, архитектуре и типовым сценариям.
        </p>
      </div>

      <!-- ── Search ─────────────────────────────────────────────────── -->
      <div class="docs-page__search-wrap">
        <IconField class="docs-page__search-input-wrap">
          <InputIcon class="pi pi-search" />
          <InputText
              v-model="search"
              placeholder="Поиск по заголовку, описанию, коду…"
              class="docs-page__search"
              size="large"
              fluid />
        </IconField>
        <Button
            v-if="search"
            icon="pi pi-times"
            text
            rounded
            class="docs-page__search-clear"
            @click="clearSearch"
        />
      </div>

      <!-- ── Search results (cross-tab) ────────────────────────────── -->
      <template v-if="search.trim()">
        <div v-if="searchResults.length === 0" class="docs-page__empty">
          <i class="pi pi-search docs-page__empty-icon" />
          <p>Ничего не найдено по запросу <strong>"{{ search }}"</strong></p>
        </div>

        <div v-else class="docs-page__search-results">
          <div class="docs-page__search-count">
            Найдено: {{ searchResults.length }} {{ plural(searchResults.length, 'карточка', 'карточки', 'карточек') }}
          </div>

          <!-- Group results by tab for readability -->
          <template v-for="tabGroup in searchGrouped" :key="tabGroup.tabId">
            <div class="docs-page__search-group">
              <span class="docs-page__search-group-label">
                {{ getTabLabel(tabGroup.tabId) }}
              </span>
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

      <!-- ── Tabbed view ────────────────────────────────────────────── -->
      <template v-else>
        <Tabs v-model:value="activeTab" lazy class="docs-page__tabs" :scrollable="true">
          <TabList>
            <Tab v-for="tab in DOC_TABS" :key="tab.id" :value="tab.id">
              {{ tab.label }}
            </Tab>
          </TabList>
          <TabPanels>
            <TabPanel v-for="tab in DOC_TABS" :key="tab.id" :value="tab.id">
              <DocSection
                  v-for="section in getSections(tab.id)"
                  :key="section.name"
                  :section-name="section.name"
                  :cards="section.cards"
              />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </template>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import DocCard from '@/components/docs/DocCard.vue'
import DocSection from '@/components/docs/DocSection.vue'
import { DOCS, DOC_TABS, type DocTab } from '@/data/docs'

// ── Tabs ─────────────────────────────────────────────────────────────────────
const activeTab = ref(DOC_TABS[0].id)

// Lazy render: mark tab as rendered when first activated

// ── Sections per tab ──────────────────────────────────────────────────────────
function getSections(tabId: DocTab): { name: string; cards: typeof DOCS }[] {
  const cards = DOCS.filter((c) => c.tab === tabId)
  const sectionMap = new Map<string, typeof DOCS>()
  for (const card of cards) {
    if (!sectionMap.has(card.section)) sectionMap.set(card.section, [])
    sectionMap.get(card.section)!.push(card)
  }
  return Array.from(sectionMap.entries()).map(([name, cards]) => ({ name, cards }))
}

// ── Search ────────────────────────────────────────────────────────────────────
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

function clearSearch() {
  search.value = ''
}

function getTabLabel(tabId: DocTab): string {
  return DOC_TABS.find((t) => t.id === tabId)?.label ?? tabId
}

// ── Utils ─────────────────────────────────────────────────────────────────────
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

/* Header */
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

/* Search */
.docs-page__search-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-8);
  max-width: 560px;
}
.docs-page__search-input-wrap {
  flex: 1;
}
.docs-page__search {
  width: 100%;
}

/* Empty */
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

/* Search results */
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

/* Tabs */
.docs-page__tabs {
  --p-tabview-tab-font-size: var(--text-sm);
}

/* Section grid */
.docs-section {
  margin-bottom: var(--space-8);
}
.docs-section__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border);
}
.docs-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr));
  gap: var(--space-4);
}
</style>