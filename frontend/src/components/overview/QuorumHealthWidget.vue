<script setup lang="ts">
/**
 * #15 Quorum Health Score Widget
 * Shows live quorum status: primary count, non-primary, offline,
 * with visual severity indicator and link to Split-Brain Recovery.
 */
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'
import { recoveryAdvancedApi, type QuorumStatusResponse } from '@/api/recovery-advanced'

const props = defineProps<{
  clusterId: number | null
}>()

const router  = useRouter()
const data    = ref<QuorumStatusResponse | null>(null)
const loading = ref(false)
const error   = ref<string | null>(null)

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value   = null
  try {
    data.value = await recoveryAdvancedApi.getQuorumStatus(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })

// ── Computed ──────────────────────────────────────────────────────────────────
const severityMap = {
  healthy:  { label: 'Healthy',  severity: 'success' as const, icon: 'pi pi-check-circle' },
  degraded: { label: 'Degraded', severity: 'warn'    as const, icon: 'pi pi-exclamation-triangle' },
  critical: { label: 'Critical', severity: 'danger'  as const, icon: 'pi pi-times-circle' },
}

const cfg = computed(() => {
  const s = data.value?.status ?? 'critical'
  return severityMap[s] ?? severityMap.critical
})

const showSplitBrainButton = computed(() =>
  data.value && !data.value.quorum_ok && (data.value.non_primary_count > 0 || data.value.offline_count > 0)
)

function formatPct(part: number, total: number): string {
  if (!total) return '0%'
  return Math.round((part / total) * 100) + '%'
}
</script>

<template>
  <div class="qhw anim-fade-in" :class="`qhw--${data?.status ?? 'critical'}`">

    <!-- Header row -->
    <div class="qhw-header">
      <div class="qhw-title-row">
        <i class="pi pi-circle-fill qhw-dot" />
        <span class="qhw-title">Quorum</span>
      </div>
      <div v-if="loading"><Skeleton height="1.4rem" width="80px" /></div>
      <Tag
        v-else-if="data"
        :value="cfg.label"
        :severity="cfg.severity"
        :icon="cfg.icon"
        class="qhw-tag"
      />
    </div>

    <!-- Stats grid -->
    <div v-if="loading" class="qhw-stats">
      <div v-for="i in 3" :key="i" class="qhw-stat"><Skeleton height="2rem" /></div>
    </div>

    <div v-else-if="data" class="qhw-stats">
      <!-- Primary -->
      <div class="qhw-stat qhw-stat--primary">
        <span class="qhw-stat-val">{{ data.primary_count }}</span>
        <span class="qhw-stat-label">Primary</span>
      </div>
      <div class="qhw-stat-sep" />
      <!-- Non-Primary -->
      <div class="qhw-stat" :class="data.non_primary_count > 0 ? 'qhw-stat--warn' : ''">
        <span class="qhw-stat-val">{{ data.non_primary_count }}</span>
        <span class="qhw-stat-label">Non-Primary</span>
      </div>
      <div class="qhw-stat-sep" />
      <!-- Offline -->
      <div class="qhw-stat" :class="data.offline_count > 0 ? 'qhw-stat--error' : ''">
        <span class="qhw-stat-val">{{ data.offline_count }}</span>
        <span class="qhw-stat-label">Offline</span>
      </div>
    </div>

    <!-- Progress bar: primary fraction -->
    <div v-if="data && !loading" class="qhw-bar-wrap">
      <div
        class="qhw-bar-fill"
        :style="{
          width: formatPct(data.primary_count, data.total_configured),
          background: data.quorum_ok ? 'var(--color-synced)' : 'var(--color-error)',
        }"
      />
    </div>
    <div v-if="data && !loading" class="qhw-bar-caption">
      {{ data.primary_count }}/{{ data.total_configured }} nodes in Primary component
      <span v-if="data.cluster_size != null" class="qhw-wsrep-size">
        (wsrep_cluster_size: {{ data.cluster_size }})
      </span>
    </div>

    <!-- Node list -->
    <div v-if="data && !loading" class="qhw-nodes">
      <div
        v-for="node in data.nodes"
        :key="node.node_id"
        class="qhw-node"
        :class="{
          'qhw-node--primary':     (node.wsrep_cluster_status ?? '').toUpperCase() === 'PRIMARY',
          'qhw-node--nonprimary':  (node.wsrep_cluster_status ?? '').toUpperCase() === 'NON-PRIMARY',
          'qhw-node--offline':     !!node.error || (node.wsrep_cluster_status ?? '') === 'OFFLINE',
        }"
      >
        <span class="qhw-node-dot" />
        <span class="qhw-node-name">{{ node.node_name }}</span>
        <span class="qhw-node-state">
          {{ node.error ? 'OFFLINE' : (node.wsrep_cluster_status ?? '—') }}
        </span>
        <span v-if="node.wsrep_local_state_comment" class="qhw-node-comment">
          {{ node.wsrep_local_state_comment }}
        </span>
      </div>
    </div>

    <!-- Action buttons -->
    <div v-if="data && !loading" class="qhw-actions">
      <Button
        size="small"
        text
        icon="pi pi-refresh"
        label="Refresh"
        @click="load()"
      />
      <Button
        v-if="showSplitBrainButton"
        size="small"
        severity="danger"
        icon="pi pi-replay"
        label="Split-Brain Recovery"
        @click="router.push({ name: 'recovery' })"
      />
    </div>

    <!-- Error state -->
    <div v-if="error && !loading" class="qhw-error">
      <i class="pi pi-exclamation-circle" />
      <span>{{ error }}</span>
      <Button size="small" text icon="pi pi-refresh" @click="load()" />
    </div>

  </div>
</template>

<style scoped>
.qhw {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  border-left: 3px solid var(--color-border);
  transition: border-left-color 300ms ease;
}
.qhw--healthy  { border-left-color: var(--color-synced); }
.qhw--degraded { border-left-color: var(--color-warning); }
.qhw--critical { border-left-color: var(--color-error); }

/* Header */
.qhw-header { display: flex; align-items: center; justify-content: space-between; }
.qhw-title-row { display: flex; align-items: center; gap: var(--space-2); }
.qhw-dot {
  font-size: 0.45rem;
  color: var(--color-text-faint);
  .qhw--healthy & { color: var(--color-synced); }
  .qhw--degraded & { color: var(--color-warning); }
  .qhw--critical & { color: var(--color-error); }
}
.qhw-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}
.qhw-tag { font-size: var(--text-xs) !important; }

/* Stats */
.qhw-stats {
  display: flex;
  align-items: center;
  gap: 0;
}
.qhw-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  flex: 1;
}
.qhw-stat-sep {
  width: 1px;
  height: 32px;
  background: var(--color-border);
  opacity: 0.6;
  flex-shrink: 0;
}
.qhw-stat-val {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text-muted);
  line-height: 1;
  font-family: var(--font-mono);
  transition: color 200ms;
}
.qhw-stat-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  font-weight: 600;
}
.qhw-stat--primary .qhw-stat-val { color: var(--color-synced); }
.qhw-stat--warn    .qhw-stat-val { color: var(--color-warning); }
.qhw-stat--error   .qhw-stat-val { color: var(--color-error); }

/* Bar */
.qhw-bar-wrap {
  height: 4px;
  background: var(--color-surface-3);
  border-radius: 99px;
  overflow: hidden;
}
.qhw-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 500ms cubic-bezier(0.16, 1, 0.3, 1), background 300ms ease;
}
.qhw-bar-caption {
  font-size: 0.68rem;
  color: var(--color-text-faint);
  line-height: 1.4;
}
.qhw-wsrep-size { color: var(--color-text-muted); }

/* Nodes */
.qhw-nodes {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-top: 1px solid var(--color-border-muted);
  padding-top: var(--space-3);
}
.qhw-node {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  padding: 3px 0;
}
.qhw-node-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-text-faint);
  .qhw-node--primary &     { background: var(--color-synced); }
  .qhw-node--nonprimary &  { background: var(--color-warning); }
  .qhw-node--offline &     { background: var(--color-error); }
}
.qhw-node-name {
  font-weight: 600;
  color: var(--color-text);
  min-width: 80px;
}
.qhw-node-state {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  letter-spacing: 0.06em;
  .qhw-node--primary &    { background: var(--color-synced-dim); color: var(--color-synced); }
  .qhw-node--nonprimary & { background: color-mix(in oklch, var(--color-warning) 12%, transparent); color: var(--color-warning); }
  .qhw-node--offline &    { background: var(--color-offline-dim); color: var(--color-error); }
}
.qhw-node-comment {
  color: var(--color-text-muted);
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 0.65rem;
}

/* Actions */
.qhw-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  border-top: 1px solid var(--color-border-muted);
  padding-top: var(--space-2);
}

/* Error */
.qhw-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-error);
}
.qhw-error .pi { font-size: 0.8rem; }
</style>
