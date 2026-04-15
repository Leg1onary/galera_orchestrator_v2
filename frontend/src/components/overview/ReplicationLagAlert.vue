<script setup lang="ts">
import { computed } from 'vue'
import type { NodeStatusItem } from '@/api/nodes'

interface Props {
  nodes: NodeStatusItem[]
}

const props = defineProps<Props>()

interface LagNode {
  id: number
  name: string
  avgRecvQueue: number
}

const lagNodes = computed<LagNode[]>(() =>
  props.nodes
    .filter((n) => {
      const hist = n.live?.recv_queue_history
      if (!hist || hist.length === 0) return false
      const avg = hist.reduce((a, b) => a + (b ?? 0), 0) / hist.length
      return avg > 0
    })
    .map((n) => {
      const hist = n.live!.recv_queue_history
      const avg = hist.reduce((a, b) => a + (b ?? 0), 0) / hist.length
      return { id: n.id, name: n.name, avgRecvQueue: avg }
    })
    .sort((a, b) => b.avgRecvQueue - a.avgRecvQueue)
)

const show = computed(() => lagNodes.value.length > 0)
</script>

<template>
  <Transition name="rla-fade">
    <Message
      v-if="show"
      severity="warn"
      :closable="false"
      class="rla-message"
    >
      <div class="rla-body">
        <div class="rla-header">
          <i class="pi pi-exclamation-triangle rla-icon" />
          <span class="rla-title">Replication lag detected</span>
        </div>
        <div class="rla-nodes">
          <span
            v-for="node in lagNodes"
            :key="node.id"
            class="rla-node"
          >
            <span class="rla-node-name">{{ node.name }}</span>
            <span class="rla-node-val">avg {{ node.avgRecvQueue.toFixed(1) }}</span>
          </span>
        </div>
        <span class="rla-hint">
          Consider increasing <code>wsrep_slave_threads</code> on lagging nodes.
        </span>
      </div>
    </Message>
  </Transition>
</template>

<style scoped>
.rla-message { width: 100%; }

.rla-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.rla-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.rla-icon {
  font-size: 0.85rem;
}

.rla-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
}

.rla-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.rla-node {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  background: rgba(96,165,250,0.12);
  border: 1px solid rgba(96,165,250,0.25);
  border-radius: var(--radius-full);
  padding: 2px var(--space-3);
  font-size: var(--text-xs);
}

.rla-node-name {
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--color-text);
}

.rla-node-val {
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.rla-hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.rla-hint code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: rgba(228,228,231,0.08);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
}

.rla-fade-enter-active { transition: opacity 250ms ease, transform 250ms cubic-bezier(0.16,1,0.3,1); }
.rla-fade-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.rla-fade-enter-from, .rla-fade-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
