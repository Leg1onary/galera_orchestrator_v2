<template>
  <div class="nc-skeleton">
    <div class="ncs-stripe" />
    <div class="ncs-body">
      <div class="ncs-header">
        <Skeleton height="1.1rem" width="8rem" />
        <Skeleton height="1.4rem" width="5rem" border-radius="99px" />
      </div>
      <Skeleton height="0.75rem" width="10rem" />
      <div class="ncs-metrics">
        <Skeleton v-for="i in 3" :key="i" height="2.2rem" />
      </div>
      <Skeleton height="0.7rem" width="5rem" />
      <div class="ncs-actions">
        <Skeleton height="2rem" width="2rem" border-radius="50%" />
        <Skeleton height="2rem" width="100%" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.nc-skeleton {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
}
.ncs-stripe {
  width: 3px;
  background: var(--color-surface-3);
  flex-shrink: 0;
}
.ncs-body {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.ncs-header { display: flex; justify-content: space-between; align-items: flex-start; }
.ncs-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.ncs-actions { display: flex; gap: var(--space-2); padding-top: var(--space-1); border-top: 1px solid var(--color-border-muted); }
</style>
