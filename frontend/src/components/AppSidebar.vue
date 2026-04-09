<template>
  <nav class="sidebar" aria-label="Main navigation">
    <ul class="sidebar__nav" role="list">
      <li v-for="item in navItems" :key="item.name" class="sidebar__item">
        <RouterLink
            :to="item.to"
            class="sidebar__link"
            :aria-label="item.label"
            :title="item.label"
        >
          <span class="sidebar__icon" aria-hidden="true">{{ item.icon }}</span>
          <span class="sidebar__label">{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>

<script setup>
/**
 * AppSidebar — navigation links for all 9 routes per ТЗ section 6.3.
 *
 * Phase 0: static links, no active state beyond router-link-active.
 * Phase 5: add cluster-status colour indicators on Recovery/Maintenance links.
 */

const navItems = [
  { name: 'overview',     to: '/',             icon: '⬡',  label: 'Overview' },
  { name: 'nodes',        to: '/nodes',        icon: '◈',  label: 'Nodes' },
  { name: 'topology',     to: '/topology',     icon: '⬡',  label: 'Topology' },
  { name: 'recovery',     to: '/recovery',     icon: '↺',  label: 'Recovery' },
  { name: 'maintenance',  to: '/maintenance',  icon: '⚙',  label: 'Maintenance' },
  { name: 'diagnostics',  to: '/diagnostics',  icon: '⬥',  label: 'Diagnostics' },
  { name: 'settings',     to: '/settings',     icon: '≡',  label: 'Settings' },
  { name: 'docs',         to: '/docs',         icon: '?',  label: 'Documentation' },
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100%;
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--space-4) 0;
  overflow-y: auto;
}

.sidebar__nav {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: 0 var(--space-3);
}

.sidebar__item {
  /* Each item is full width */
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background-color var(--transition-fast), color var(--transition-fast);
  white-space: nowrap;
  overflow: hidden;
}

.sidebar__link:hover {
  background-color: var(--color-surface-2);
  color: var(--color-text);
}

/* Active state — applied by Vue Router when route matches */
.sidebar__link.router-link-active,
.sidebar__link.router-link-exact-active {
  background-color: var(--color-primary-dim);
  color: var(--color-primary);
  font-weight: 600;
}

.sidebar__icon {
  width: 20px;
  text-align: center;
  font-size: var(--text-base);
  flex-shrink: 0;
  /* Prevent emoji/symbol from scaling weirdly */
  line-height: 1;
}

.sidebar__label {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>