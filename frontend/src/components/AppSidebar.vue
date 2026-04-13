<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClusterStore }    from '@/stores/cluster'
import { useOperationsStore } from '@/stores/operations'
import { useVersionStore }    from '@/stores/version'
import { useQueryClient }     from '@tanstack/vue-query'

const props = defineProps<{ collapsed: boolean }>()
const emit  = defineEmits<{ toggle: [] }>()

const route        = useRoute()
const router       = useRouter()
const clusterStore = useClusterStore()
const opsStore     = useOperationsStore()
const versionStore = useVersionStore()
const qc           = useQueryClient()

const clusterId = computed(() => clusterStore.selectedCluster?.id ?? 0)

// ── Contour switcher — динамически из store ──────────────────────────────────
// Цвет назначается по позиции в массиве; первые два — amber/green, дальше neutral.
const CONTOUR_COLORS = ['amber', 'green', 'blue', 'purple', 'red']
const contours = computed(() => clusterStore.contours.map((c, i) => ({
  ...c,
  color: CONTOUR_COLORS[i] ?? 'neutral',
})))

const selectedContourId = computed(() => clusterStore.selectedContourId)
const selectedContour   = computed(() => contours.value.find(c => c.id === selectedContourId.value) ?? null)

function switchContour(id: number) {
  if (id === selectedContourId.value) return
  clusterStore.selectContour(id)
}

// ── Nav items ───────────────────────────────────────────────────────────────
interface NavItem {
  key:    string
  label:  string
  icon:   string
  to?:    () => object
  group?: string
}

const navItems = computed((): NavItem[] => [
  { key: 'overview',    label: 'Overview',    icon: 'pi-chart-bar',  group: 'monitor', to: () => ({ name: 'overview'    }) },
  { key: 'topology',   label: 'Topology',    icon: 'pi-sitemap',    group: 'monitor', to: () => ({ name: 'topology'    }) },
  { key: 'nodes',      label: 'Nodes',       icon: 'pi-server',     group: 'monitor', to: () => ({ name: 'nodes'       }) },
  { key: 'recovery',   label: 'Recovery',    icon: 'pi-replay',     group: 'ops',     to: () => ({ name: 'recovery'    }) },
  { key: 'maintenance',label: 'Maintenance', icon: 'pi-wrench',     group: 'ops',     to: () => ({ name: 'maintenance' }) },
  { key: 'diagnostics',label: 'Diagnostics', icon: 'pi-search',     group: 'ops',     to: () => ({ name: 'diagnostics' }) },
  { key: 'settings',   label: 'Settings',    icon: 'pi-sliders-h',  group: 'system',  to: () => ({ name: 'settings'   }) },
  { key: 'docs',       label: 'Docs',        icon: 'pi-book',       group: 'system',  to: () => ({ name: 'docs'       }) },
])

const groups: { key: string; label: string }[] = [
  { key: 'monitor', label: 'Monitor' },
  { key: 'ops',     label: 'Operations' },
  { key: 'system',  label: 'System' },
]

function isActive(item: NavItem)  { return route.name === item.key }
function navigate(item: NavItem)  {
  if (isItemLocked(item)) return
  if (item.to) router.push(item.to())
}

// ── Active operation ───────────────────────────────────────────────────────────
const isLocked = computed(() =>
  clusterId.value ? opsStore.isLocked(clusterId.value) : false
)

// ── Lock check per item ───────────────────────────────────────────────────────
function isItemLocked(item: NavItem) {
  return isLocked.value && item.group === 'ops'
}

// ── Version (load once) ───────────────────────────────────────────────────────
// loadVersion вызывается в AppFooter — здесь просто читаем
const checkResult  = computed(() => versionStore.checkResult)
const checkStatus  = computed(() => checkResult.value?.status ?? null)
const isChecking   = computed(() => versionStore.checking)

function handleCheckClick() {
  versionStore.checkUpdate()
}
</script>

<template>
  <nav
    class="sidebar"
    :class="{ 'sidebar--collapsed': collapsed }"
    aria-label="Main navigation"
  >

    <!-- ══ HEADER ═════════════════════════════════════════════════════ -->
    <div class="sidebar-header">
      <div class="sidebar-logo" v-show="!collapsed">
        <div class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="10" stroke="#2dd4bf" stroke-width="1.5" opacity="0.25"/>
            <circle cx="11" cy="11" r="6.5" stroke="#2dd4bf" stroke-width="1.5" opacity="0.5"/>
            <circle cx="11" cy="11" r="3" fill="#2dd4bf" opacity="0.9"/>
            <circle cx="11" cy="1.5" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="11" cy="20.5" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="1.5" cy="11" r="1.2" fill="#2dd4bf" opacity="0.4"/>
            <circle cx="20.5" cy="11" r="1.2" fill="#2dd4bf" opacity="0.4"/>
          </svg>
        </div>
        <div class="logo-text-group">
          <span class="logo-text">Galera</span>
          <span class="logo-sub">Orchestrator</span>
        </div>
        <span class="logo-version">v2</span>
      </div>

      <button
        class="toggle-btn"
        :class="{ 'toggle-btn--solo': collapsed }"
        @click="emit('toggle')"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        v-tooltip.right="collapsed ? 'Expand sidebar' : ''"
      >
        <i :class="collapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'" />
      </button>
    </div>

    <!-- ══ CONTOUR SWITCHER ══════════════════════════════════════════════ -->
    <div
      v-if="!collapsed && contours.length > 0"
      class="contour-switcher"
      role="group"
      aria-label="Contour"
    >
      <button
        v-for="c in contours"
        :key="c.id"
        :class="['contour-btn', `contour-btn--${c.color}`, { 'is-active': selectedContourId === c.id }]"
        @click="switchContour(c.id)"
        :aria-pressed="selectedContourId === c.id"
        v-tooltip.right="`Switch to ${c.name} contour`"
      >
        {{ c.name }}
      </button>
    </div>
    <!-- collapsed: single dot с текущим контуром -->
    <div
      v-else-if="collapsed && selectedContour"
      class="contour-collapsed"
      v-tooltip.right="`Contour: ${selectedContour.name}`"
    >
      <span
        class="contour-dot"
        :class="`contour-dot--${selectedContour.color}`"
      />
    </div>

    <!-- ══ NAV ══════════════════════════════════════════════════════════ -->
    <div class="sidebar-nav">
      <template v-for="group in groups" :key="group.key">
        <div v-if="!collapsed" class="nav-section-head">
          <span class="nav-section-line" />
          <span class="nav-section-label">{{ group.label }}</span>
          <span class="nav-section-line" />
        </div>
        <div v-else class="nav-section-sep" />

        <button
          v-for="item in navItems.filter(i => i.group === group.key)"
          :key="item.key"
          class="nav-item"
          :class="{
            'nav-item--active':  isActive(item),
            'nav-item--locked':  isItemLocked(item),
          }"
          @click="navigate(item)"
          v-tooltip.right="collapsed ? item.label : isItemLocked(item) ? 'Locked — operation in progress' : ''"
          :aria-label="item.label"
          :aria-current="isActive(item) ? 'page' : undefined"
        >
          <i :class="'pi ' + item.icon" class="nav-icon" />
          <span class="nav-label" v-show="!collapsed">{{ item.label }}</span>
          <i v-if="isItemLocked(item) && !collapsed" class="pi pi-lock nav-lock-icon" aria-hidden="true" />
          <span v-if="isActive(item)" class="nav-active-bar" aria-hidden="true" />
        </button>
      </template>
    </div>

    <!-- ══ FOOTER: версия + check-update ════════════════════════════════ -->
    <div class="sidebar-footer" :class="{ 'sidebar-footer--collapsed': collapsed }">
      <template v-if="!collapsed">
        <div class="footer-version-row">
          <span class="footer-version">{{ versionStore.currentVersion }}</span>
          <button
            class="check-btn"
            :class="{ 'check-btn--loading': isChecking }"
            :disabled="isChecking"
            v-tooltip.top="'Check for updates'"
            @click="handleCheckClick"
          >
            <svg
              class="check-btn-icon"
              :class="{ spin: isChecking }"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M13.65 2.35A8 8 0 1 0 15 8h-1.5A6.5 6.5 0 1 1 8 1.5a6.45 6.45 0 0 1 4.24 1.6L10 5.5h5v-5l-1.35 1.85z"
                fill="currentColor"
              />
            </svg>
          </button>
          <Transition name="fade-result">
            <span v-if="checkStatus === 'update_available'" class="check-result check-result--update">↑ update</span>
            <span v-else-if="checkStatus === 'up_to_date'" class="check-result check-result--ok">✓ ok</span>
            <span v-else-if="checkStatus === 'registry_unavailable'" class="check-result check-result--warn">⚠</span>
          </Transition>
        </div>
      </template>
      <template v-else>
        <!-- collapsed: только иконка обновления -->
        <button
          class="check-btn check-btn--solo"
          :disabled="isChecking"
          v-tooltip.right="'Check for updates'"
          @click="handleCheckClick"
        >
          <svg
            class="check-btn-icon"
            :class="{ spin: isChecking }"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M13.65 2.35A8 8 0 1 0 15 8h-1.5A6.5 6.5 0 1 1 8 1.5a6.45 6.45 0 0 1 4.24 1.6L10 5.5h5v-5l-1.35 1.85z"
              fill="currentColor"
            />
          </svg>
        </button>
      </template>
    </div>

  </nav>
</template>

<style scoped>
/* ════════════════════════════════════════════════════════
   SHELL
════════════════════════════════════════════════════════ */
.sidebar {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width, 220px);
  background: var(--color-bg);
  border-right: 1px solid rgba(255,255,255,0.055);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width 240ms cubic-bezier(0.16,1,0.3,1);
  overflow: hidden;
}
.sidebar--collapsed { width: var(--sidebar-width-collapsed, 56px); }

/* ════════════════════════════════════════════════════════
   HEADER
════════════════════════════════════════════════════════ */
.sidebar-header {
  height: var(--header-height, 56px);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  gap: var(--space-2);
  min-width: 0;
}
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.logo-icon { flex-shrink: 0; display: flex; align-items: center; }
.logo-text-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  line-height: 1.1;
}
.logo-text {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--color-text);
  white-space: nowrap;
}
.logo-sub {
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-faint);
  white-space: nowrap;
}
.logo-version {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--color-synced);
  background: color-mix(in oklch, var(--color-synced) 10%, transparent);
  border: 1px solid color-mix(in oklch, var(--color-synced) 22%, transparent);
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  letter-spacing: 0.04em;
  flex-shrink: 0;
  align-self: flex-start;
  margin-top: 2px;
}
.toggle-btn {
  flex-shrink: 0;
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.07);
  background: rgba(255,255,255,0.03);
  color: var(--color-text-faint);
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 150ms;
}
.toggle-btn:hover { color: var(--color-text); background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.12); }
.toggle-btn--solo { margin: 0 auto; }

/* ════════════════════════════════════════════════════════
   CONTOUR SWITCHER
════════════════════════════════════════════════════════ */
.contour-switcher {
  display: flex;
  align-items: center;
  gap: 2px;
  margin: var(--space-3) var(--space-3) 0;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 2px;
}
.contour-btn {
  flex: 1;
  padding: 4px 0;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  cursor: pointer;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-faint);
  transition: all 200ms cubic-bezier(0.16,1,0.3,1);
  white-space: nowrap;
  line-height: 1.5;
  text-align: center;
}
/* amber */
.contour-btn--amber:hover:not(.is-active) { color: var(--color-warning); background: color-mix(in oklch, var(--color-warning) 7%, transparent); }
.contour-btn--amber.is-active {
  background: color-mix(in oklch, var(--color-warning) 12%, transparent);
  border-color: color-mix(in oklch, var(--color-warning) 28%, transparent);
  color: var(--color-warning);
  box-shadow: 0 0 10px color-mix(in oklch, var(--color-warning) 12%, transparent), inset 0 1px 0 rgba(255,255,255,0.06);
}
/* green */
.contour-btn--green:hover:not(.is-active) { color: var(--color-synced); background: color-mix(in oklch, var(--color-synced) 7%, transparent); }
.contour-btn--green.is-active {
  background: color-mix(in oklch, var(--color-synced) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-synced) 25%, transparent);
  color: var(--color-synced);
  box-shadow: 0 0 10px color-mix(in oklch, var(--color-synced) 10%, transparent), inset 0 1px 0 rgba(255,255,255,0.06);
}
/* blue */
.contour-btn--blue:hover:not(.is-active) { color: var(--color-primary); background: color-mix(in oklch, var(--color-primary) 7%, transparent); }
.contour-btn--blue.is-active {
  background: color-mix(in oklch, var(--color-primary) 10%, transparent);
  border-color: color-mix(in oklch, var(--color-primary) 25%, transparent);
  color: var(--color-primary);
}
/* purple / red / neutral — fallback */
.contour-btn--purple:hover:not(.is-active),
.contour-btn--red:hover:not(.is-active),
.contour-btn--neutral:hover:not(.is-active) { color: var(--color-text-muted); background: rgba(255,255,255,0.05); }
.contour-btn--purple.is-active,
.contour-btn--red.is-active,
.contour-btn--neutral.is-active {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.15);
  color: var(--color-text);
}

.contour-collapsed {
  display: flex;
  justify-content: center;
  margin: var(--space-3) auto 0;
  cursor: default;
}
.contour-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
}
.contour-dot--amber   { background: var(--color-warning); box-shadow: 0 0 5px color-mix(in oklch, var(--color-warning) 60%, transparent); }
.contour-dot--green   { background: var(--color-synced);  box-shadow: 0 0 5px color-mix(in oklch, var(--color-synced) 60%, transparent); }
.contour-dot--blue    { background: var(--color-primary); box-shadow: 0 0 5px color-mix(in oklch, var(--color-primary) 60%, transparent); }
.contour-dot--purple,
.contour-dot--red,
.contour-dot--neutral { background: var(--color-text-muted); }

/* ════════════════════════════════════════════════════════
   NAV
════════════════════════════════════════════════════════ */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: 1px;
  scrollbar-width: none;
}
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-section-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--space-3) var(--space-2) var(--space-1);
  user-select: none;
}
.nav-section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
}
.nav-section-label {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-text-faint);
  font-weight: 700;
  white-space: nowrap;
  flex-shrink: 0;
}
.nav-section-sep {
  height: 1px;
  background: rgba(255,255,255,0.04);
  margin: var(--space-2) var(--space-2);
}
.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 7px var(--space-2);
  border-radius: 7px;
  color: var(--color-text-faint);
  font-size: 0.855rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 150ms ease, background 150ms ease;
  width: 100%;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  border: none;
  background: transparent;
  font-family: inherit;
}
.nav-item:hover { color: var(--color-text-muted); background: rgba(255,255,255,0.04); }
.nav-item:hover .nav-icon { color: var(--color-text); transform: scale(1.1); }
.nav-item:hover .nav-label { transform: translateX(2px); }
.nav-item--active {
  color: var(--color-text);
  background: color-mix(in oklch, var(--color-synced) 7%, transparent);
  font-weight: 600;
}
.nav-item--active:hover { background: color-mix(in oklch, var(--color-synced) 10%, transparent); }
.nav-item--active .nav-icon { color: var(--color-synced); }
.nav-item--locked { opacity: 0.55; cursor: not-allowed; }
.nav-item--locked:hover { background: transparent; color: var(--color-text-faint); }
.nav-item--locked:hover .nav-icon { color: var(--color-text-faint); transform: none; }
.sidebar--collapsed .nav-item { justify-content: center; padding: 8px; }
.nav-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
  transition: color 150ms ease, transform 150ms cubic-bezier(0.16,1,0.3,1);
}
.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: transform 150ms cubic-bezier(0.16,1,0.3,1);
}
.nav-lock-icon { font-size: 0.65rem; color: var(--color-warning); opacity: 0.7; flex-shrink: 0; margin-left: auto; }
.nav-active-bar {
  position: absolute;
  right: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 18px;
  background: var(--color-synced);
  border-radius: 2px 0 0 2px;
  box-shadow: 0 0 10px color-mix(in oklch, var(--color-synced) 70%, transparent),
              0 0 20px color-mix(in oklch, var(--color-synced) 30%, transparent);
}

/* ════════════════════════════════════════════════════════
   FOOTER: версия + check-update
════════════════════════════════════════════════════════ */
.sidebar-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid rgba(255,255,255,0.04);
  flex-shrink: 0;
  min-height: 36px;
  display: flex;
  align-items: center;
}
.sidebar-footer--collapsed { justify-content: center; padding: var(--space-3); }

.footer-version-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
}
.footer-version {
  font-size: 0.68rem;
  font-family: var(--font-mono, monospace);
  color: var(--color-text-faint);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.check-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-faint);
  border-radius: 3px;
  transition: color 200ms ease;
  flex-shrink: 0;
}
.check-btn:hover:not(:disabled) { color: var(--color-text-muted); }
.check-btn:disabled { cursor: default; }
.check-btn--solo { width: 22px; height: 22px; }
.check-btn-icon { width: 11px; height: 11px; flex-shrink: 0; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.spin { animation: spin 0.9s linear infinite; }

.check-result {
  font-size: 0.65rem;
  font-family: var(--font-mono, monospace);
  white-space: nowrap;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}
.check-result--update { color: var(--color-synced); }
.check-result--ok     { color: var(--color-success, #4ade80); }
.check-result--warn   { color: var(--color-warning); }

.fade-result-enter-active { transition: opacity 350ms ease, transform 350ms ease; }
.fade-result-leave-active { transition: opacity 200ms ease; }
.fade-result-enter-from   { opacity: 0; transform: translateX(-4px); }
.fade-result-leave-to     { opacity: 0; }
</style>
