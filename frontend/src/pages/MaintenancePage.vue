<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import MaintenancePanel from '@/components/maintenance/MaintenancePanel.vue'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId)
</script>

<template>
  <div class="maintenance-page anim-fade-in">

    <div class="pg-head">
      <div class="section-title">Maintenance</div>
      <p class="pg-desc">Controlled maintenance operations for MariaDB Galera cluster nodes.</p>
    </div>

    <!-- Info banner -->
    <div class="info-banner">
      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-lock" />
          <span>Maintenance Mode</span>
        </div>
        <p>
          Puts a node into <strong>read-only</strong> state
          (<code>SET GLOBAL read_only = ON</code>). The node stays in the
          cluster and continues replication — writes are just blocked.
          Use it before manual work: config changes, disk ops, upgrades.
        </p>
      </div>

      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-sync" />
          <span>Rolling Restart</span>
        </div>
        <p>
          Restarts MariaDB on each node <strong>one by one</strong>, in the
          order you choose. Each node is put into maintenance, restarted via
          <code>systemctl restart mariadb</code>, then held until it reaches
          <strong>SYNCED</strong> state before the next node begins.
          Zero-downtime for the cluster as a whole.
        </p>
      </div>

      <div class="info-card">
        <div class="info-card-header">
          <i class="pi pi-exclamation-triangle" />
          <span>Safety notes</span>
        </div>
        <p>
          Never put <strong>all nodes</strong> into maintenance simultaneously
          — the cluster will lose quorum. If a rolling restart fails mid-way,
          the affected node stays in maintenance: use <em>Exit</em> to release
          it manually after resolving the issue.
        </p>
      </div>
    </div>

    <div v-if="!clusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <MaintenancePanel v-else :cluster-id="clusterId" />
  </div>
</template>

<style scoped>
.maintenance-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.pg-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.pg-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* ── Info banner ──────────────────────────────────────────────── */
.info-banner {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

@media (max-width: 900px) {
  .info-banner { grid-template-columns: 1fr; }
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.info-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.info-card-header .pi {
  font-size: 0.875rem;
  color: var(--color-primary);
  flex-shrink: 0;
}

/* третья карточка (Safety) — иконка предупреждения в amber */
.info-card:last-child .info-card-header .pi {
  color: var(--color-warning);
}

.info-card p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.65;
  margin: 0;
}

.info-card p strong {
  color: var(--color-text);
  font-weight: 600;
}

.info-card p code {
  font-family: var(--font-mono, monospace);
  font-size: 0.75em;
  background: var(--color-surface-offset);
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  color: var(--color-primary);
}

.info-card p em {
  font-style: normal;
  font-weight: 600;
  color: var(--color-text);
}

/* ── Empty state ────────────────────────────────────────────────── */
.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}
</style>
