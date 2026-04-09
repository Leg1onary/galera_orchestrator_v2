<template>
  <RouterView />
</template>

<script setup>
// App.vue is intentionally minimal — it is the root mount point.
// Layout (header, sidebar) is handled by AppLayout.vue for authenticated routes.
// LoginPage.vue handles its own layout.
</script>

<style>
/* ============================================================
   Global base styles
   These styles are unscoped and apply to the entire application.
   Component-specific styles live in each component's <style scoped>.
   ============================================================ */

:root {
  /* Color tokens — dark theme optimised for technical admin panels */
  --color-bg:              #0f1117;
  --color-surface:         #161b27;
  --color-surface-2:       #1e2436;
  --color-surface-3:       #252d3d;
  --color-border:          #2d3748;
  --color-border-muted:    #1e2a3a;

  /* Text */
  --color-text:            #e2e8f0;
  --color-text-muted:      #8892a4;
  --color-text-faint:      #4a5568;

  /* Accent — teal, matching Galera/MariaDB branding space */
  --color-primary:         #38b2ac;
  --color-primary-hover:   #2c9c96;
  --color-primary-dim:     rgba(56, 178, 172, 0.15);

  /* Status colors — matches ТЗ section 7.3 exactly */
  --color-synced:          #22c55e;
  --color-donor:           #38bdf8;
  --color-readonly:        #eab308;
  --color-degraded:        #f97316;
  --color-offline:         #ef4444;
  --color-success:         #22c55e;
  --color-warning:         #f59e0b;
  --color-error:           #ef4444;
  --color-info:            #60a5fa;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Typography */
  --font-body:    'Inter', system-ui, -apple-system, sans-serif;
  --font-mono:    'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  --text-xs:   0.75rem;    /* 12px */
  --text-sm:   0.875rem;   /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg:   1.125rem;   /* 18px */
  --text-xl:   1.25rem;    /* 20px */
  --text-2xl:  1.5rem;     /* 24px */

  /* Borders */
  --radius-sm:  0.25rem;
  --radius-md:  0.375rem;
  --radius-lg:  0.5rem;
  --radius-xl:  0.75rem;

  /* Transitions */
  --transition-fast:   120ms ease;
  --transition-normal: 200ms ease;

  /* Layout */
  --sidebar-width:     220px;
  --header-height:     56px;
}

/* Base reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--color-text);
  background-color: var(--color-bg);
  min-height: 100dvh;
  line-height: 1.6;
}

#app {
  min-height: 100dvh;
}

img, picture, video, canvas, svg {
  display: block;
  max-width: 100%;
}

input, button, textarea, select {
  font: inherit;
  color: inherit;
}

button {
  cursor: pointer;
  background: none;
  border: none;
}

a {
  color: inherit;
  text-decoration: none;
}

h1, h2, h3, h4, h5, h6 {
  line-height: 1.25;
}

/* Focus ring */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

/* Scrollbar styling for webkit browsers */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-faint);
}

/* Utility classes used across components */
.text-muted   { color: var(--color-text-muted); }
.text-faint   { color: var(--color-text-faint); }
.text-mono    { font-family: var(--font-mono); }
.text-sm      { font-size: var(--text-sm); }
.text-xs      { font-size: var(--text-xs); }

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>