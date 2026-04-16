<script setup lang="ts">
/**
 * #3 grastate.dat Inspector Panel
 * Shows parsed grastate.dat from all nodes with analysis warnings,
 * contextual playbook, and one-click wsrep-recover via orchestrator.
 */
import { ref, computed, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import { recoveryAdvancedApi, type GrastateResponse, type GrastateNodeResult, type WsrepRecoverResult } from '@/api/recovery-advanced'

const props = defineProps<{ clusterId: number | null }>()

const data    = ref<GrastateResponse | null>(null)
const loading = ref(false)
const error   = ref<string | null>(null)
const expanded = ref<Set<number>>(new Set())

// wsrep-recover per-node state
const recoverLoading = ref<Record<number, boolean>>({})
const recoverResults = ref<Record<number, WsrepRecoverResult>>({})

async function load() {
  if (!props.clusterId) return
  loading.value = true
  error.value = null
  try {
    data.value = await recoveryAdvancedApi.getGrastate(props.clusterId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Error'
  } finally {
    loading.value = false
  }
}

watch(() => props.clusterId, (id) => { if (id) load() }, { immediate: true })

function toggleExpand(nodeId: number) {
  if (expanded.value.has(nodeId)) expanded.value.delete(nodeId)
  else expanded.value.add(nodeId)
}

async function runWsrepRecover(node: GrastateNodeResult) {
  if (!props.clusterId) return
  recoverLoading.value = { ...recoverLoading.value, [node.node_id]: true }
  try {
    const result = await recoveryAdvancedApi.runWsrepRecover(props.clusterId, node.node_id)
    recoverResults.value = { ...recoverResults.value, [node.node_id]: result }
    // Re-scan to get updated grastate.dat
    if (result.patched_grastate) await load()
  } catch (e: any) {
    recoverResults.value = {
      ...recoverResults.value,
      [node.node_id]: {
        node_id: node.node_id,
        node_name: node.node_name,
        recovered_uuid: null,
        recovered_seqno: null,
        raw_output: '',
        patched_grastate: false,
        error: e?.response?.data?.detail ?? e?.message ?? 'Failed',
      }
    }
  } finally {
    recoverLoading.value = { ...recoverLoading.value, [node.node_id]: false }
  }
}

function seqnoClass(node: GrastateNodeResult): string {
  if (node.error) return 'cell-err-text'
  if (node.seqno === null) return 'cell-muted'
  if (node.seqno === -1) return 'cell-warn'
  if (node.seqno === data.value?.analysis?.max_seqno) return 'cell-max'
  return 'cell-mono'
}

function stbSeverity(v: boolean | null): 'success' | 'secondary' | 'danger' {
  if (v === true) return 'success'
  if (v === false) return 'danger'
  return 'secondary'
}

// ── Scenario detection ──────────────────────────────────────────────────────
const scenario = computed((): 'clean' | 'dirty' | 'no_safe' | 'ready' | null => {
  if (!data.value) return null
  const a = data.value.analysis
  if (a.safe_bootstrap_count > 0 && a.dirty_crash_count === 0) return 'ready'
  if (a.dirty_crash_count > 0) return 'dirty'
  if (a.safe_bootstrap_count === 0 && a.dirty_crash_count === 0) return 'no_safe'
  return 'clean'
})

// Whether any node still needs wsrep-recover (seqno=-1 and not yet recovered)
const nodesNeedingRecover = computed(() =>
  data.value?.nodes.filter(n =>
    n.seqno === -1 &&
    !n.error &&
    !recoverResults.value[n.node_id]?.recovered_seqno
  ) ?? []
)
</script>

<template>
  <div class="gs-panel">

    <!-- Header -->
    <div class="gs-header">
      <div class="gs-header-left">
        <h3 class="gs-title">grastate.dat Inspector</h3>
        <p class="gs-desc">Reads <code>grastate.dat</code> from all nodes. Use before Bootstrap to identify the best recovery candidate.</p>
      </div>
      <Button
        icon="pi pi-refresh"
        label="Scan"
        :loading="loading"
        size="small"
        @click="load()"
      />
    </div>

    <!-- Warnings from analysis -->
    <template v-if="data?.analysis?.warnings?.length">
      <Message
        v-for="(w, i) in data.analysis.warnings"
        :key="i"
        :severity="w.level === 'danger' ? 'error' : 'warn'"
        :closable="false"
        class="gs-warning"
      >
        {{ w.message }}
      </Message>
    </template>

    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

    <!-- Analysis summary -->
    <div v-if="data && !loading" class="gs-summary">
      <div class="gs-stat">
        <span class="gs-stat-label">Max seqno</span>
        <span class="gs-stat-val gs-stat-val--max">{{ data.analysis.max_seqno ?? '—' }}</span>
      </div>
      <div class="gs-stat-sep" />
      <div class="gs-stat">
        <span class="gs-stat-label">Safe to bootstrap</span>
        <span class="gs-stat-val" :class="data.analysis.safe_bootstrap_count > 0 ? 'gs-stat-val--ok' : 'gs-stat-val--warn'">
          {{ data.analysis.safe_bootstrap_count }} node{{ data.analysis.safe_bootstrap_count !== 1 ? 's' : '' }}
        </span>
      </div>
      <div class="gs-stat-sep" />
      <div class="gs-stat">
        <span class="gs-stat-label">Dirty crash</span>
        <span class="gs-stat-val" :class="data.analysis.dirty_crash_count > 0 ? 'gs-stat-val--warn' : ''">
          {{ data.analysis.dirty_crash_count }} node{{ data.analysis.dirty_crash_count !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !data" class="gs-skeleton">
      <Skeleton v-for="i in 3" :key="i" height="52px" />
    </div>

    <!-- Table -->
    <DataTable
      v-else-if="data"
      :value="data.nodes"
      dataKey="node_id"
      size="small"
      class="settings-table gs-table"
    >
      <template #empty>
        <div class="panel-empty"><i class="pi pi-inbox" /><span>No nodes</span></div>
      </template>

      <Column field="node_name" header="Node">
        <template #body="{ data: row }">
          <div class="cell-node">
            <span class="cell-node-name">{{ row.node_name }}</span>
            <span class="cell-node-host">{{ row.host }}</span>
          </div>
        </template>
      </Column>

      <Column header="seqno" style="width: 120px">
        <template #body="{ data: row }">
          <div class="cell-seqno-wrap">
            <div class="cell-seqno-row">
              <span :class="seqnoClass(row)">
                {{ row.error ? 'ERR' : (row.seqno ?? '—') }}
              </span>
              <Tag
                v-if="row.seqno === data?.analysis?.max_seqno && row.seqno !== null && row.seqno >= 0"
                value="MAX"
                severity="success"
                class="max-tag"
              />
            </div>
            <!-- Show recovered seqno inline if wsrep-recover was run -->
            <div v-if="recoverResults[row.node_id]?.recovered_seqno != null" class="cell-recovered">
              <i class="pi pi-arrow-right" />
              recovered: <strong>{{ recoverResults[row.node_id].recovered_seqno }}</strong>
            </div>
            <span v-else-if="row.seqno === -1" class="cell-seqno-note">needs wsrep-recover</span>
          </div>
        </template>
      </Column>

      <Column header="safe_to_btsp" style="width: 130px">
        <template #body="{ data: row }">
          <Tag
            v-if="row.safe_to_bootstrap !== null"
            :value="row.safe_to_bootstrap ? 'YES' : 'NO'"
            :severity="stbSeverity(row.safe_to_bootstrap)"
            :icon="!row.safe_to_bootstrap ? 'pi pi-times' : 'pi pi-check'"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

      <Column header="UUID" style="width: 240px">
        <template #body="{ data: row }">
          <span class="cell-uuid">{{ row.uuid ?? (row.error ? '—' : '—') }}</span>
        </template>
      </Column>

      <Column header="gvwstate" style="width: 90px">
        <template #body="{ data: row }">
          <Tag
            v-if="!row.error"
            :value="row.gvwstate_exists ? 'EXISTS' : 'ABSENT'"
            :severity="row.gvwstate_exists ? 'info' : 'secondary'"
          />
          <span v-else class="cell-muted">—</span>
        </template>
      </Column>

      <!-- Actions column -->
      <Column header="" style="width: 160px">
        <template #body="{ data: row }">
          <div class="cell-actions">
            <!-- wsrep-recover button for dirty-crash nodes -->
            <Button
              v-if="row.seqno === -1 && !row.error"
              size="small"
              :label="recoverLoading[row.node_id] ? 'Running…' : 'wsrep-recover'"
              icon="pi pi-play"
              :loading="recoverLoading[row.node_id]"
              severity="warn"
              outlined
              v-tooltip.bottom="'Run mysqld --wsrep-recover on this node via SSH. MySQL must be stopped.'"
              @click="runWsrepRecover(row)"
            />
            <!-- result badge -->
            <Tag
              v-if="recoverResults[row.node_id] && !recoverResults[row.node_id].error"
              :value="recoverResults[row.node_id].patched_grastate ? 'Patched ✓' : 'Recovered'"
              severity="success"
            />
            <span
              v-if="recoverResults[row.node_id]?.error"
              class="cell-recover-err"
              v-tooltip.bottom="recoverResults[row.node_id].error ?? ''"
            >
              <i class="pi pi-exclamation-circle" /> Failed
            </span>
            <!-- raw grastate expand button -->
            <Button
              v-if="row.raw && row.seqno !== -1"
              size="small"
              text
              :icon="expanded.has(row.node_id) ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"
              @click="toggleExpand(row.node_id)"
            />
            <!-- error cell -->
            <div v-if="row.error" class="cell-error">
              <i class="pi pi-exclamation-circle" />
              {{ row.error }}
            </div>
          </div>
        </template>
      </Column>

    </DataTable>

    <!-- Expanded raw grastate.dat -->
    <template v-if="data">
      <div
        v-for="node in data.nodes"
        :key="`raw-${node.node_id}`"
        v-show="expanded.has(node.node_id) && node.raw"
        class="gs-raw-block"
      >
        <div class="gs-raw-label">{{ node.node_name }} — grastate.dat</div>
        <pre class="gs-raw">{{ node.raw }}</pre>
      </div>
    </template>

    <!-- wsrep-recover raw output (collapsible per node) -->
    <template v-if="Object.keys(recoverResults).length">
      <div
        v-for="(res, nid) in recoverResults"
        :key="`recover-out-${nid}`"
        class="gs-raw-block"
      >
        <div class="gs-raw-label gs-raw-label--recover">
          <i class="pi pi-terminal" />
          {{ res.node_name }} — wsrep-recover output
          <Tag v-if="res.patched_grastate" value="grastate.dat patched" severity="success" class="raw-patch-tag" />
          <Tag v-if="res.error" value="Error" severity="danger" class="raw-patch-tag" />
        </div>
        <pre class="gs-raw gs-raw--dim">{{ res.raw_output || res.error || '(no output)' }}</pre>
      </div>
    </template>

    <!-- ══ Scenario Playbook ════════════════════════════════════════════════ -->
    <div v-if="data && scenario" class="gs-guide">

      <!-- READY: all good -->
      <div v-if="scenario === 'ready'" class="gs-guide-scenario gs-guide-scenario--ok">
        <div class="gs-guide-icon"><i class="pi pi-check-circle" /></div>
        <div class="gs-guide-body">
          <div class="gs-guide-title">Кластер готов к Bootstrap</div>
          <p class="gs-guide-text">
            Есть нода с <code>safe_to_bootstrap=1</code> — Galera сама пометила её как безопасного донора.
            Запускай Full Cluster Recovery: бэкенд автоматически выберет правильную ноду.
          </p>
        </div>
      </div>

      <!-- DIRTY: seqno=-1, need wsrep-recover -->
      <div v-if="scenario === 'dirty'" class="gs-guide-scenario gs-guide-scenario--warn">
        <div class="gs-guide-icon"><i class="pi pi-exclamation-triangle" /></div>
        <div class="gs-guide-body">
          <div class="gs-guide-title">Грязное завершение (seqno = −1)</div>
          <p class="gs-guide-text">
            Ноды упали без чистого shutdown — MariaDB не успела записать финальный seqno.
            Перед Bootstrap нужно определить настоящий seqno каждой ноды.
          </p>

          <!-- Orchestrator way -->
          <div class="gs-guide-block gs-guide-block--primary">
            <div class="gs-guide-block-title">
              <i class="pi pi-bolt" />
              Через оркестратор (рекомендуется)
            </div>
            <p>
              Нажми кнопку <strong>wsrep-recover</strong> напротив каждой ноды выше.
              Оркестратор подключится по SSH, запустит <code>mysqld --wsrep-recover</code>,
              распарсит seqno и автоматически запишет его в <code>grastate.dat</code>.
              После — нажми <strong>Scan</strong> и запускай Full Cluster Recovery.
            </p>
            <div v-if="nodesNeedingRecover.length" class="gs-guide-nodes-need">
              <span class="gs-guide-nodes-label">Нужно запустить на:</span>
              <Tag
                v-for="n in nodesNeedingRecover"
                :key="n.node_id"
                :value="n.node_name"
                severity="warn"
              />
            </div>
            <div v-else class="gs-guide-done">
              <i class="pi pi-check" /> wsrep-recover выполнен на всех нодах — можно делать Scan
            </div>
          </div>

          <!-- Manual way -->
          <div class="gs-guide-block">
            <div class="gs-guide-block-title">
              <i class="pi pi-terminal" />
              Вручную по SSH (если оркестратор недоступен)
            </div>
            <p>На каждой ноде с <code>seqno=-1</code> (MySQL должна быть остановлена):</p>
            <pre class="gs-code"># 1. Запустить wsrep-recover (выведет Recovered position)
mysqld --wsrep-recover 2>&1 | grep "Recovered position"
# Пример вывода: Recovered position: fbcd4181-...:12345

# 2. Вписать seqno в grastate.dat вручную
sed -i 's/^seqno:.*/seqno:   12345/' /var/lib/mysql/grastate.dat

# 3. На ноде с MAX seqno — разрешить bootstrap
sed -i 's/^safe_to_bootstrap:.*/safe_to_bootstrap: 1/' /var/lib/mysql/grastate.dat</pre>
          </div>
        </div>
      </div>

      <!-- NO_SAFE: all nodes have seqno but nobody is safe_to_bootstrap -->
      <div v-if="scenario === 'no_safe'" class="gs-guide-scenario gs-guide-scenario--warn">
        <div class="gs-guide-icon"><i class="pi pi-question-circle" /></div>
        <div class="gs-guide-body">
          <div class="gs-guide-title">Нет safe_to_bootstrap=1</div>
          <p class="gs-guide-text">
            У всех нод корректный seqno, но ни одна не помечена как безопасная для Bootstrap.
            Обычно это значит, что кластер остановили не через <code>systemctl stop</code>,
            а всех убили одновременно.
          </p>

          <div class="gs-guide-block gs-guide-block--primary">
            <div class="gs-guide-block-title">
              <i class="pi pi-bolt" />
              Через оркестратор
            </div>
            <p>
              Full Cluster Recovery автоматически выберет ноду с максимальным seqno
              как Bootstrap-донора, даже без <code>safe_to_bootstrap=1</code>.
            </p>
          </div>

          <div class="gs-guide-block">
            <div class="gs-guide-block-title">
              <i class="pi pi-terminal" />
              Вручную по SSH
            </div>
            <p>Определи ноду с MAX seqno из таблицы выше, затем:</p>
            <pre class="gs-code"># На ноде с максимальным seqno:
sed -i 's/^safe_to_bootstrap:.*/safe_to_bootstrap: 1/' /var/lib/mysql/grastate.dat
# После — возвращайся в оркестратор и запускай Full Cluster Recovery</pre>
          </div>
        </div>
      </div>

      <!-- CLEAN: safe_to_bootstrap есть, нет dirty -->
      <div v-if="scenario === 'clean'" class="gs-guide-scenario gs-guide-scenario--info">
        <div class="gs-guide-icon"><i class="pi pi-info-circle" /></div>
        <div class="gs-guide-body">
          <div class="gs-guide-title">Частично чистое состояние</div>
          <p class="gs-guide-text">
            Есть <code>safe_to_bootstrap=1</code>, но остальные ноды в нечистом состоянии.
            Full Cluster Recovery справится — выберет безопасного донора автоматически.
          </p>
        </div>
      </div>

      <!-- Shared footer: concepts glossary -->
      <details class="gs-glossary">
        <summary class="gs-glossary-title"><i class="pi pi-book" /> Что означают эти поля?</summary>
        <div class="gs-glossary-body">
          <div class="gs-glossary-item">
            <span class="gs-glossary-term">seqno</span>
            <span class="gs-glossary-def">
              Порядковый номер последней транзакции, зафиксированной на ноде.
              <strong>-1</strong> = нода упала без чистого shutdown, настоящий seqno неизвестен и требует <code>wsrep-recover</code>.
            </span>
          </div>
          <div class="gs-glossary-item">
            <span class="gs-glossary-term">safe_to_bootstrap</span>
            <span class="gs-glossary-def">
              Флаг Galera: <strong>1</strong> = нода видела все транзакции и её можно поднять первой.
              Ставится автоматически при корректном <code>systemctl stop</code> на последней живой ноде.
            </span>
          </div>
          <div class="gs-glossary-item">
            <span class="gs-glossary-term">gvwstate.dat</span>
            <span class="gs-glossary-def">
              Файл состояния Primary Component. Наличие (<code>EXISTS</code>) означает, что нода
              была частью primary-компонента в момент остановки — дополнительный индикатор кандидата.
            </span>
          </div>
          <div class="gs-glossary-item">
            <span class="gs-glossary-term">wsrep-recover</span>
            <span class="gs-glossary-def">
              Режим запуска MariaDB, при котором движок читает binlog и вычисляет реальный seqno
              без присоединения к кластеру. Занимает 2–30 сек, не меняет данные.
              <strong>MySQL должна быть остановлена.</strong>
            </span>
          </div>
        </div>
      </details>

    </div>
    <!-- end Guide -->

  </div>
</template>

<style scoped>
.gs-panel { display: flex; flex-direction: column; gap: var(--space-4); }

.gs-header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4);
}
.gs-header-left { display: flex; flex-direction: column; gap: var(--space-1); }
.gs-title { font-size: var(--text-lg); font-weight: 700; color: var(--color-text); margin: 0; letter-spacing: -0.02em; }
.gs-desc  { font-size: var(--text-xs); color: var(--color-text-muted); margin: 0; }
.gs-desc code {
  font-family: var(--font-mono); font-size: 0.9em;
  background: var(--color-surface-3); border-radius: var(--radius-sm); padding: 1px 4px;
  color: var(--color-primary);
}

.gs-warning { width: 100%; }

.gs-summary {
  display: flex; align-items: center; gap: 0;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-5);
}
.gs-stat { display: flex; flex-direction: column; gap: 3px; flex: 1; align-items: center; }
.gs-stat-sep { width: 1px; height: 32px; background: var(--color-border); }
.gs-stat-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-faint); font-weight: 600; }
.gs-stat-val {
  font-size: var(--text-md); font-weight: 800; color: var(--color-text-muted);
  font-family: var(--font-mono); line-height: 1;
}
.gs-stat-val--max  { color: var(--color-synced); }
.gs-stat-val--ok   { color: var(--color-synced); }
.gs-stat-val--warn { color: var(--color-warning); }

.gs-skeleton { display: flex; flex-direction: column; gap: var(--space-2); }

/* Table cells */
.cell-node      { display: flex; flex-direction: column; gap: 2px; }
.cell-node-name { font-weight: 600; font-size: var(--text-sm); color: var(--color-text); }
.cell-node-host { font-size: var(--text-xs); color: var(--color-text-muted); font-family: var(--font-mono); }
.cell-mono      { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-text-muted); }
.cell-muted     { color: var(--color-text-faint); font-size: var(--text-xs); }
.cell-error     { display: flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-error); }
.cell-error .pi { font-size: 0.7rem; }
.cell-err-text  { color: var(--color-error); font-size: var(--text-xs); font-family: var(--font-mono); }
.cell-warn      { color: var(--color-warning); font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 700; }
.cell-max       { color: var(--color-synced); font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 800; }
.cell-uuid      { font-family: var(--font-mono); font-size: 0.65rem; color: var(--color-text-faint); }
.cell-seqno-wrap { display: flex; flex-direction: column; gap: 3px; }
.cell-seqno-row  { display: flex; align-items: center; gap: var(--space-2); }
.cell-seqno-note { font-size: 0.6rem; color: var(--color-warning); font-style: italic; }
.cell-recovered  {
  font-size: 0.65rem; color: var(--color-synced); font-family: var(--font-mono);
  display: flex; align-items: center; gap: 4px;
}
.cell-recovered .pi { font-size: 0.6rem; }
.cell-recovered strong { color: var(--color-synced); }
.max-tag { font-size: 0.6rem !important; }

.cell-actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.cell-recover-err {
  font-size: var(--text-xs); color: var(--color-error);
  display: flex; align-items: center; gap: 4px; cursor: default;
}
.cell-recover-err .pi { font-size: 0.7rem; }

.panel-empty {
  display: flex; align-items: center; gap: var(--space-3);
  color: var(--color-text-faint); padding: var(--space-6); font-size: var(--text-sm);
}

:deep(.settings-table .p-datatable-table-container) { border: none; box-shadow: none; border-radius: 0; }
:deep(.settings-table .p-datatable-thead > tr > th) {
  padding: var(--space-4) var(--space-6) !important; font-size: var(--text-xs) !important;
  font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--color-text-faint) !important; background: var(--color-surface-2) !important;
  border-bottom: 1px solid var(--color-border) !important;
}
:deep(.settings-table .p-datatable-tbody > tr > td) {
  padding: var(--space-4) var(--space-6) !important;
  border-bottom: 1px solid var(--color-border-muted) !important; vertical-align: middle;
}
:deep(.settings-table .p-datatable-tbody > tr:hover > td) { background: rgba(45,212,191,0.04) !important; }

/* Raw grastate blocks */
.gs-raw-block {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.gs-raw-label {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface-3);
  border-bottom: 1px solid var(--color-border);
}
.gs-raw-label--recover { color: var(--color-primary); }
.raw-patch-tag { margin-left: auto; }
.gs-raw {
  margin: 0;
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-primary);
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre;
  max-height: 240px;
  overflow-y: auto;
}
.gs-raw--dim { color: var(--color-text-faint); }

/* ══ Scenario Playbook ═══════════════════════════════════════════════════════ */
.gs-guide {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.gs-guide-scenario {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid;
}
.gs-guide-scenario--ok {
  background: rgba(74,222,128,0.05);
  border-color: rgba(74,222,128,0.2);
}
.gs-guide-scenario--warn {
  background: rgba(251,191,36,0.05);
  border-color: rgba(251,191,36,0.2);
}
.gs-guide-scenario--info {
  background: rgba(96,165,250,0.05);
  border-color: rgba(96,165,250,0.2);
}

.gs-guide-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 2px;
  line-height: 1;
}
.gs-guide-scenario--ok   .gs-guide-icon { color: var(--color-synced); }
.gs-guide-scenario--warn .gs-guide-icon { color: var(--color-warning); }
.gs-guide-scenario--info .gs-guide-icon { color: var(--color-info); }

.gs-guide-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.gs-guide-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--color-text);
}

.gs-guide-text {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
}
.gs-guide-text code {
  font-family: var(--font-mono);
  background: var(--color-surface-3);
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  font-size: 0.9em;
  color: var(--color-primary);
}

/* Inner step blocks */
.gs-guide-block {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.gs-guide-block--primary {
  border-color: rgba(45,212,191,0.25);
  background: rgba(45,212,191,0.04);
}
.gs-guide-block-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-faint);
}
.gs-guide-block--primary .gs-guide-block-title { color: var(--color-primary); }
.gs-guide-block-title .pi { font-size: 0.8rem; }

.gs-guide-block p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0;
}
.gs-guide-block p strong { color: var(--color-text); }
.gs-guide-block p code {
  font-family: var(--font-mono);
  background: var(--color-surface-3);
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  font-size: 0.9em;
  color: var(--color-primary);
}

.gs-guide-nodes-need {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-1);
}
.gs-guide-nodes-label {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}
.gs-guide-done {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-synced);
  font-weight: 600;
}
.gs-guide-done .pi { font-size: 0.75rem; }

.gs-code {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  line-height: 1.75;
  background: #0a0b0e;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  overflow-x: auto;
  white-space: pre;
}
.gs-code ::v-deep(span) { color: var(--color-primary); }

/* Glossary */
.gs-glossary {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.gs-glossary-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-text-faint);
  cursor: pointer;
  user-select: none;
  list-style: none;
}
.gs-glossary-title::-webkit-details-marker { display: none; }
.gs-glossary-title .pi { font-size: 0.75rem; }
.gs-glossary[open] .gs-glossary-title { border-bottom: 1px solid var(--color-border); }
.gs-glossary-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.gs-glossary-item {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-muted);
  align-items: baseline;
}
.gs-glossary-item:last-child { border-bottom: none; }
.gs-glossary-term {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--color-primary);
}
.gs-glossary-def {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  line-height: 1.6;
}
.gs-glossary-def strong { color: var(--color-text); }
.gs-glossary-def code {
  font-family: var(--font-mono);
  background: var(--color-surface-3);
  border-radius: var(--radius-sm);
  padding: 1px 4px;
  font-size: 0.9em;
  color: var(--color-primary);
}
</style>
