<script setup lang="ts">
import { ref } from 'vue'
import BackupReviewTab from '@/components/backup/BackupReviewTab.vue'

const TABS = [
  { value: 'review', label: 'Review', icon: 'pi-search' },
]

const activeTab = ref('review')
</script>

<template>
  <div class="backups-page anim-fade-in">

    <!-- Page header -->
    <div class="pg-head">
      <div class="pg-head-icon"><i class="pi pi-database" /></div>
      <div>
        <h1 class="pg-title">Backup Center</h1>
        <p class="pg-desc">Review backup files stored on configured backup servers.</p>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="page-tabbar-wrap">
      <div class="page-tabbar" role="tablist">
        <button
          v-for="t in TABS"
          :key="t.value"
          role="tab"
          :aria-selected="activeTab === t.value"
          class="page-tab"
          :class="{ 'page-tab--active': activeTab === t.value }"
          @click="activeTab = t.value"
        >
          <i :class="'pi ' + t.icon" class="page-tab-icon" />
          <span>{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- Tab body -->
    <div class="page-body">
      <BackupReviewTab v-if="activeTab === 'review'" />
    </div>

  </div>
</template>

<style scoped>
.backups-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
  gap: var(--space-5);
}

/* ── Page header ── */
.pg-head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.pg-head-icon {
  width: 36px; height: 36px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-primary-highlight);
  border: 1px solid rgba(45,212,191,0.18);
  border-radius: var(--radius-lg);
  color: var(--color-primary);
  font-size: 1rem;
}
.pg-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}
.pg-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* ── Tab bar ── */
.page-tabbar-wrap {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: calc(-1 * var(--space-5));
}
.page-tabbar {
  display: flex;
  gap: 0;
  align-items: stretch;
}
.page-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 150ms ease, border-color 150ms ease;
  white-space: nowrap;
  margin-bottom: -1px;
}
.page-tab:hover { color: var(--color-text); }
.page-tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}
.page-tab-icon { font-size: 0.8rem; }

/* ── Body ── */
.page-body {
  flex: 1;
  min-height: 0;
  padding-top: var(--space-5);
}
</style>
