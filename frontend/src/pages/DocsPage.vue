<template>
  <div class="page-docs">
    <!-- wsrep variables reference -->
    <Card class="mb-4">
      <template #header><div class="card-title"><i class="pi pi-book" />wsrep-переменные</div></template>
      <template #content>
        <DataTable :value="wsrepVars" size="small" striped-rows>
          <Column field="variable" header="Переменная" style="min-width:220px">
            <template #body="{ data }">
              <span class="mono var-name">{{ data.variable }}</span>
            </template>
          </Column>
          <Column field="description" header="Описание" />
          <Column field="source" header="Источник" style="width:200px">
            <template #body="{ data }">
              <span class="mono" style="font-size:11px">{{ data.source }}</span>
            </template>
          </Column>
          <Column field="norm" header="Норма" style="width:140px">
            <template #body="{ data }">
              <Tag :class="normClass(data.norm)" class="norm-tag">{{ data.norm }}</Tag>
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <!-- FAQ -->
    <Card>
      <template #header><div class="card-title"><i class="pi pi-question-circle" />FAQ — типичные проблемы</div></template>
      <template #content>
        <Accordion :multiple="true" :active-index="[]">
          <AccordionPanel v-for="faq in faqs" :key="faq.title" :value="faq.title">
            <AccordionHeader>{{ faq.title }}</AccordionHeader>
            <AccordionContent>
              <div class="faq-body" v-html="faq.content" />
            </AccordionContent>
          </AccordionPanel>
        </Accordion>
      </template>
    </Card>
  </div>
</template>

<script setup>
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Accordion from 'primevue/accordion'
import AccordionPanel from 'primevue/accordionpanel'
import AccordionHeader from 'primevue/accordionheader'
import AccordionContent from 'primevue/accordioncontent'

const wsrepVars = [
  { variable: 'wsrep_cluster_status',       description: 'Статус кластера. Primary = все ноды видят друг друга',         source: 'SHOW STATUS LIKE ...', norm: 'Primary' },
  { variable: 'wsrep_cluster_size',          description: 'Число нод в кластере (включая арбитры)',                        source: 'SHOW STATUS LIKE ...', norm: '≥ 3' },
  { variable: 'wsrep_local_state_comment',   description: 'Состояние ноды',                                               source: 'SHOW STATUS LIKE ...', norm: 'Synced' },
  { variable: 'wsrep_flow_control_paused',   description: 'Доля времени в flow control за последний период',               source: 'SHOW STATUS LIKE ...', norm: '< 0.05' },
  { variable: 'wsrep_local_recv_queue',      description: 'Очередь входящих транзакций ожидающих применения',             source: 'SHOW STATUS LIKE ...', norm: '0' },
  { variable: 'wsrep_local_send_queue',      description: 'Очередь исходящих транзакций',                                 source: 'SHOW STATUS LIKE ...', norm: '0' },
  { variable: 'wsrep_local_cert_failures',   description: 'Ошибки сертификации транзакций',                               source: 'SHOW STATUS LIKE ...', norm: '0' },
  { variable: 'wsrep_bf_aborts',             description: 'BF (Brute Force) прерывания транзакций конфликтов',            source: 'SHOW STATUS LIKE ...', norm: '≈ 0' },
  { variable: 'wsrep_last_committed',        description: 'Последний применённый seqno. Должен совпадать на всех нодах',   source: 'SHOW STATUS LIKE ...', norm: 'одинаков' },
  { variable: 'wsrep_cluster_state_uuid',    description: 'UUID кластера. Расхождение означает Split-Brain',               source: 'SHOW STATUS LIKE ...', norm: 'одинаков' },
  { variable: 'wsrep_connected',             description: 'Подключена ли нода к кластерной сети',                        source: 'SHOW STATUS LIKE ...', norm: 'ON' },
  { variable: 'wsrep_ready',                 description: 'Готова ли нода принимать запросы',                             source: 'SHOW STATUS LIKE ...', norm: 'ON' },
  { variable: 'wsrep_provider_name',         description: 'Имя Galera провайдера',                                       source: 'SHOW STATUS LIKE ...', norm: 'Galera' },
  { variable: 'wsrep_local_commits',         description: 'Количество успешных commit (информационно)',                   source: 'SHOW STATUS LIKE ...', norm: 'растёт' },
  { variable: 'wsrep_replicated',            description: 'Число реплицированных событий',                               source: 'SHOW STATUS LIKE ...', norm: 'растёт' },
  { variable: 'wsrep_received',              description: 'Число полученных событий с других нод',                       source: 'SHOW STATUS LIKE ...', norm: 'растёт' },
]

function normClass(norm) {
  if (norm === 'Primary' || norm === 'ON' || norm === 'Synced' || norm === 'Galera') return 'norm-ok'
  if (norm === '0') return 'norm-ok'
  if (norm.includes('≥') || norm.includes('одинаков')) return 'norm-info'
  return 'norm-neutral'
}

const faqs = [
  {
    title: 'non-Primary — кластер не видит большинства нод',
    content: `<p><strong>Причины:</strong> сетевой сбой, нода упала, split-brain.</p>
<p><strong>Диагностика:</strong> Страница Топология → wsrep_cluster_status, wsrep_cluster_size.</p>
<p><strong>Восстановление:</strong> Страница Recovery → Bootstrap Wizard. Wizard автоматически выберет ноду с максимальным seqno и выполнит восстановление.</p>`,
  },
  {
    title: 'Flow Control — высокий wsrep_flow_control_paused',
    content: `<p><strong>Что это:</strong> Механизм замедления быстрых нод, когда одна нода не успевает применять транзакции.</p>
<p><strong>Норма:</strong> fc_paused &lt; 0.05. При fc_paused &gt; 0.1 кластер замедляется.</p>
<p><strong>Действия:</strong> Найти «медленную» ноду по wsrep_local_recv_queue. Уменьшить нагрузку на запись. Проверить дисковую I/O и RAM на медленной ноде.</p>`,
  },
  {
    title: 'Безопасная остановка ноды без прерывания работы',
    content: `<p>Используйте <strong>Maintenance Wizard</strong> (страница «Обслуживание»):</p>
<ol>
<li>R/O ON — переводим ноду в read-only</li>
<li>Дренаж — ждём recv_queue = 0</li>
<li>Stop MariaDB — systemctl stop mariadb</li>
<li>Ваши работы — обслуживание</li>
<li>Start MariaDB — systemctl start mariadb</li>
<li>Синхронизация — ждём Synced</li>
<li>R/W ON — возвращаем write mode</li>
</ol>`,
  },
  {
    title: 'SST vs IST — в чём разница',
    content: `<p><strong>IST (Incremental State Transfer)</strong> — нода догоняет кластер применяя только пропущенные транзакции. Быстро, без полного копирования.</p>
<p><strong>SST (State Snapshot Transfer)</strong> — полное копирование базы данных с донора. Медленно, нода-донор временно переходит в Donor/Desync.</p>
<p>SST запускается если нода пропустила слишком много транзакций или gcache недостаточен для IST.</p>
<p>Прогресс SST: страница «Обслуживание» → SST Progress Monitor.</p>`,
  },
  {
    title: 'garbd (арбитр) — зачем нужен',
    content: `<p><strong>Garbd</strong> — легковесный процесс-арбитр, обеспечивающий кворум для кластера из 2 нод.</p>
<p>Без арбитра кластер из 2 нод при падении одной ноды теряет кворум и переходит в non-Primary.</p>
<p><strong>Проверка статуса:</strong> Страница «Обзор» → карточки арбитров. RUNNING = работает нормально.</p>
<p>Garbd не хранит данные, не участвует в репликации — только в кворуме.</p>`,
  },
  {
    title: 'cluster_size=1 — нода видит себя одну',
    content: `<p><strong>Причины:</strong></p>
<ul>
<li>Сетевой сбой (firewall, маршрутизация)</li>
<li>Нода перезапустилась после split-brain и bootstrap не был выполнен</li>
<li>garbd не работает (кластер из 2 нод)</li>
</ul>
<p><strong>Диагностика:</strong> Страница «Топология» → сравните wsrep_cluster_state_uuid на всех нодах.</p>
<p><strong>Восстановление:</strong> Страница «Recovery» → Bootstrap Wizard.</p>`,
  },
]
</script>

<style scoped>
.page-docs { display: flex; flex-direction: column; gap: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.card-title { display: flex; align-items: center; gap: 0.5rem; font-size: 14px; font-weight: 600; padding: 0.875rem 1.25rem; }
.var-name { font-size: 12px; }
.norm-tag { font-size: 11px; padding: 2px 6px; }
.norm-ok      { background: rgba(34,197,94,.15); color: #4ade80; border: 1px solid rgba(34,197,94,.3); }
.norm-info    { background: rgba(59,130,246,.15); color: #60a5fa; border: 1px solid rgba(59,130,246,.3); }
.norm-neutral { background: rgba(107,114,128,.1); color: #9ca3af; border: 1px solid rgba(107,114,128,.2); }

.faq-body { font-size: 13px; color: var(--color-text-secondary); line-height: 1.7; }
.faq-body p { margin-bottom: 0.5rem; }
.faq-body ol, .faq-body ul { padding-left: 1.25rem; margin-bottom: 0.5rem; }
.faq-body li { margin-bottom: 0.25rem; }
.faq-body strong { color: var(--color-text-primary); }
.mono { font-family: var(--font-mono); }
</style>
