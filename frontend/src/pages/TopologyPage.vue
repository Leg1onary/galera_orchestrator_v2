<script setup lang="ts">
import { computed } from 'vue'
import { useClusterStore } from '@/stores/cluster'
import { useClusterStatus } from '@/composables/useClusterStatus'

const clusterStore = useClusterStore()
const clusterId    = computed(() => clusterStore.selectedClusterId!)
const { data, isLoading } = useClusterStatus(clusterId)

const nodes       = computed(() => data.value?.nodes ?? [])
const arbitrators = computed(() => data.value?.arbitrators ?? [])

function stateColor(comment: string | null, ready: string | null, sshOk: boolean): string {
  const s = (comment ?? '').toUpperCase()
  if (!sshOk || s === 'OFFLINE') return 'var(--color-offline)'
  if (ready === 'OFF')           return 'var(--color-degraded)'
  if (s === 'SYNCED')            return 'var(--color-synced)'
  if (s === 'DONOR' || s === 'JOINER') return 'var(--color-donor)'
  return 'var(--color-text-muted)'
}
</script>

<template>
  <div class="topology-page anim-fade-in">

    <div v-if="!clusterStore.selectedClusterId" class="pg-empty">
      <i class="pi pi-server" /><span>No cluster selected</span>
    </div>

    <template v-else>
      <div class="section-title">Topology</div>

      <div v-if="isLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner" /><span>Loading&hellip;</span>
      </div>

      <div v-else class="topo-layout">
        <!-- Ring visualisation -->
        <div class="topo-ring-wrap">
          <div class="topo-ring">
            <div class="ring-label">Galera Cluster</div>
            <div class="ring-nodes">
              <div
                v-for="node in nodes"
                :key="node.id"
                class="ring-node"
                :style="{ '--node-color': stateColor(node.wsrep_local_state_comment, node.wsrep_ready, node.ssh_ok) }"
              >
                <div class="rn-dot" />
                <div class="rn-info">
                  <span class="rn-name">{{ node.name }}</span>
                  <span class="rn-host">{{ node.host }}</span>
                  <span class="rn-dc" v-if="node.dc?.name">{{ node.dc.name }}</span>
                </div>
              </div>
            </div>
            <!-- Arbitrators -->
            <div v-if="arbitrators.length" class="ring-arbitrators">
              <div class="ring-arb-label">Arbitrators</div>
              <div
                v-for="arb in arbitrators"
                :key="arb.id"
                class="ring-node ring-node--arb"
                :style="{ '--node-color': arb.is_reachable ? 'var(--color-synced)' : 'var(--color-offline)' }"
              >
                <div class="rn-dot" />
                <div class="rn-info">
                  <span class="rn-name">{{ arb.name }}</span>
                  <span class="rn-host">{{ arb.host }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Table -->
        <div class="topo-table-wrap">
          <DataTable :value="nodes" size="small" class="topo-table">
            <Column field="name" header="Name">
              <template #body="{ data: n }">
                <span class="font-medium">{{ n.name }}</span>
              </template>
            </Column>
            <Column field="host" header="Host">
              <template #body="{ data: n }">
                <span class="text-mono text-muted">{{ n.host }}:{{ n.port }}</span>
              </template>
            </Column>
            <Column header="State">
              <template #body="{ data: n }">
                <span
                  class="topo-state"
                  :style="{ color: stateColor(n.wsrep_local_state_comment, n.wsrep_ready, n.ssh_ok) }"
                >
                  {{ n.wsrep_local_state_comment ?? '—' }}
                </span>
              </template>
            </Column>
            <Column header="DC">
              <template #body="{ data: n }">
                <span class="text-muted text-xs">{{ n.dc?.name ?? '—' }}</span>
              </template>
            </Column>
            <Column header="Mode">
              <template #body="{ data: n }">
                <span class="topo-mode" :class="n.readonly ? 'topo-mode--ro' : 'topo-mode--rw'">
                  {{ n.readonly ? 'RO' : 'RW' }}
                </span>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.topology-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.pg-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-muted);
  padding: var(--space-12);
  justify-content: center;
  font-size: var(--text-sm);
}

.topo-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 900px) {
  .topo-layout { grid-template-columns: 1fr; }
}

/* Ring block */
.topo-ring-wrap {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
}

.topo-ring {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.ring-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  font-weight: 600;
}

.ring-nodes {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.ring-node {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border-muted);
  border-left: 3px solid var(--node-color, var(--color-text-faint));
  border-radius: var(--radius-md);
  transition: border-color var(--transition-normal);
}

.ring-node--arb {
  opacity: 0.75;
}

.rn-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--node-color, var(--color-text-faint));
  flex-shrink: 0;
  box-shadow: 0 0 6px var(--node-color, transparent);
}

.rn-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.rn-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rn-host {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.rn-dc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.ring-arbitrators {
  border-top: 1px solid var(--color-border-muted);
  padding-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.ring-arb-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  font-weight: 600;
}

/* Table */
.topo-table-wrap {
  overflow: hidden;
  border-radius: var(--radius-lg);
}

.topo-state {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.topo-mode {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  border-radius: var(--radius-sm);
  padding: 1px 5px;
}

.topo-mode--rw { background: rgba(74,222,128,0.10); color: var(--color-synced); }
.topo-mode--ro { background: rgba(251,191,36,0.10);  color: var(--color-readonly); }
</style>
