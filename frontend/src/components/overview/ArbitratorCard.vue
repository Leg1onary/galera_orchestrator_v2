<script setup lang="ts">
interface Arbitrator {
  id: number
  name: string
  host: string
  port: number
  dc?: { name: string } | null
  is_reachable?: boolean | null
}

const props = defineProps<{ arbitrator: Arbitrator }>()
</script>

<template>
  <article class="arb-card anim-fade-in">
    <div class="arb-stripe" :class="arbitrator.is_reachable ? 'arb-stripe--ok' : 'arb-stripe--fail'" />
    <div class="arb-body">
      <div class="arb-header">
        <div class="arb-title-group">
          <span class="arb-name">{{ arbitrator.name }}</span>
          <span v-if="arbitrator.dc?.name" class="arb-dc">{{ arbitrator.dc.name }}</span>
        </div>
        <div :class="['arb-badge', arbitrator.is_reachable ? 'arb-badge--ok' : 'arb-badge--fail']">
          <span class="arb-dot" />
          {{ arbitrator.is_reachable ? 'Reachable' : 'Unreachable' }}
        </div>
      </div>
      <div class="arb-host">
        <span>{{ arbitrator.host }}:{{ arbitrator.port }}</span>
        <span class="arb-tag">arbitrator</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.arb-card {
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.arb-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-sm);
}

.arb-stripe {
  width: 3px;
  flex-shrink: 0;
}

.arb-stripe--ok   { background: var(--color-synced); }
.arb-stripe--fail { background: var(--color-offline); }

.arb-body {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.arb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-2);
}

.arb-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.arb-name {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arb-dc {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 500;
}

.arb-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 1px solid transparent;
  flex-shrink: 0;
  white-space: nowrap;
}

.arb-badge--ok   { background: var(--color-synced-dim);  color: var(--color-synced);  border-color: rgba(74,222,128,0.20); }
.arb-badge--fail { background: var(--color-offline-dim); color: var(--color-offline); border-color: rgba(248,113,113,0.20); }

.arb-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.arb-host {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.arb-tag {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-faint);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0 4px;
}
</style>
