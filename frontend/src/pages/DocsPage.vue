<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Документация</h1>
        <p class="page-subtitle">Справочник команд, API и wsrep-переменных</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="docs-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="docs-tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >{{ tab.label }}</button>
    </div>

    <!-- Tab: Сервис -->
    <div v-if="activeTab === 'service'" class="doc-section">
      <div class="doc-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94"/>
        </svg>
        Управление MariaDB / Galera
      </div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in serviceCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc">{{ card.desc }}</div>
          <div class="doc-cmd">{{ card.cmd }}</div>
          <div v-if="card.note" class="doc-note">⚠ {{ card.note }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: Recovery -->
    <div v-if="activeTab === 'recovery'" class="doc-section">
      <div class="doc-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 1 1-.02-8.49"/>
        </svg>
        Recovery — восстановление кластера
      </div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in recoveryCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc" v-html="card.desc"></div>
          <div class="doc-cmd">{{ card.cmd }}</div>
          <div v-if="card.note" class="doc-note">⚠ {{ card.note }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: Метрики -->
    <div v-if="activeTab === 'metrics'" class="doc-section">
      <div class="doc-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        Ключевые метрики
      </div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in metricsCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc">{{ card.desc }}</div>
          <div v-if="card.normal" style="margin-top:8px;font-size:0.72rem;color:var(--success)">✓ Норма: {{ card.normal }}</div>
          <div v-if="card.warn" style="margin-top:4px;font-size:0.72rem;color:var(--warning)">⚠ Внимание: {{ card.warn }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: Диагностика -->
    <div v-if="activeTab === 'diag'" class="doc-section">
      <div class="doc-section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        Диагностика
      </div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in diagCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc">{{ card.desc }}</div>
          <div class="doc-cmd">{{ card.cmd }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: Режимы -->
    <div v-if="activeTab === 'modes'" class="doc-section">
      <div class="doc-section-title">Режимы работы</div>
      <div class="doc-grid">
        <div class="doc-card">
          <div class="doc-card-header">
            <div class="doc-btn-label">MOCK режим</div>
            <span class="doc-category-badge cat-warning">Симуляция</span>
          </div>
          <div class="doc-desc">Фронтенд работает с симулированными данными генерируемыми бэкендом. Все API-запросы идут на /api/status который возвращает mock-данные. Безопасен для демонстрации и разработки. Сценарии позволяют симулировать различные ситуации кластера.</div>
          <div class="doc-cmd">GET /api/status → { use_mock: true, nodes: [...] }</div>
        </div>
        <div class="doc-card">
          <div class="doc-card-header">
            <div class="doc-btn-label">REAL режим</div>
            <span class="doc-category-badge cat-success">Продакшн</span>
          </div>
          <div class="doc-desc">Данные получаются с реальных нод MariaDB Galera через SSH и MySQL-соединения. Требует корректной конфигурации nodes.yaml. Поддерживает несколько контуров (TEST/PROD) и кластеров.</div>
          <div class="doc-cmd">GET /api/status → { use_mock: false, nodes: [...реальные данные...] }</div>
        </div>
        <div class="doc-card">
          <div class="doc-card-header">
            <div class="doc-btn-label">Контуры TEST / PROD</div>
            <span class="doc-category-badge cat-info">Info</span>
          </div>
          <div class="doc-desc">В REAL-режиме доступны кнопки TEST и PROD в заголовке. Каждый контур может содержать несколько кластеров (выбираются через dropdown). Переключение изменяет активный кластер через /api/contours/select.</div>
          <div class="doc-cmd">POST /api/contours/select → { contour: "test", cluster_index: 0 }</div>
        </div>
        <div class="doc-card">
          <div class="doc-card-header">
            <div class="doc-btn-label">WebSocket live-feed</div>
            <span class="doc-category-badge cat-info">Info</span>
          </div>
          <div class="doc-desc">Бэкенд поддерживает WebSocket на /ws/cluster для получения данных в реальном времени. Используется вместо polling. Автоматически переподключается при разрыве.</div>
          <div class="doc-cmd">WS /ws/cluster → { type: "status", nodes: [...] }</div>
        </div>
      </div>
    </div>

    <!-- Tab: Настройки -->
    <div v-if="activeTab === 'settings'" class="doc-section">
      <div class="doc-section-title">Настройки системы</div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in settingsCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc">{{ card.desc }}</div>
          <div class="doc-cmd">{{ card.cmd }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: WebSocket -->
    <div v-if="activeTab === 'websocket'" class="doc-section">
      <div class="doc-section-title">WebSocket API</div>
      <div class="doc-grid">
        <div class="doc-card" v-for="card in wsCards" :key="card.title">
          <div class="doc-card-header">
            <div class="doc-btn-label">{{ card.title }}</div>
            <span class="doc-category-badge" :class="card.badge">{{ card.badgeText }}</span>
          </div>
          <div class="doc-desc">{{ card.desc }}</div>
          <div class="doc-cmd">{{ card.cmd }}</div>
        </div>
      </div>
    </div>

    <!-- Tab: wsrep-справочник -->
    <div v-if="activeTab === 'wsrep'" class="doc-section">
      <div class="doc-section-title">wsrep-справочник</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Переменная</th>
              <th>Значение / Норма</th>
              <th>Описание</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in wsrepRef" :key="r.var">
              <td class="mono" style="font-size:0.78rem;white-space:nowrap">{{ r.var }}</td>
              <td>
                <span class="node-state-badge" :class="r.okClass">{{ r.ok }}</span>
              </td>
              <td style="font-size:var(--text-sm);color:var(--text-muted);line-height:1.6">{{ r.desc }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab: FAQ -->
    <div v-if="activeTab === 'faq'" class="doc-section">
      <div class="doc-section-title">FAQ — Часто задаваемые вопросы</div>
      <div class="doc-grid">
        <div class="doc-card" v-for="faq in faqCards" :key="faq.q">
          <div class="doc-card-header">
            <div class="doc-btn-label" style="font-family:var(--font-body)">{{ faq.q }}</div>
          </div>
          <div class="doc-desc">{{ faq.a }}</div>
          <div v-if="faq.cmd" class="doc-cmd">{{ faq.cmd }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('service')

const tabs = [
  { id: 'service',   label: 'Сервис' },
  { id: 'recovery',  label: 'Recovery' },
  { id: 'metrics',   label: 'Метрики' },
  { id: 'diag',      label: 'Диагностика' },
  { id: 'modes',     label: 'Режимы' },
  { id: 'settings',  label: 'Настройки' },
  { id: 'websocket', label: 'WebSocket' },
  { id: 'wsrep',     label: 'wsrep-справочник' },
  { id: 'faq',       label: 'FAQ' },
]

const serviceCards = [
  {
    title: 'start (mariadb.service)',
    badge: 'cat-action', badgeText: 'Action',
    desc: 'Запустить MariaDB через systemctl. Нода автоматически подключится к кластеру и начнёт синхронизацию через IST или SST.',
    cmd: 'POST /api/nodes/{id}/start\nsystemctl start mariadb.service',
  },
  {
    title: 'stop (mariadb.service)',
    badge: 'cat-danger', badgeText: 'Danger',
    desc: 'Остановить MariaDB через systemctl. Нода исключается из кластера. wsrep_cluster_size уменьшится на 1.',
    cmd: 'POST /api/nodes/{id}/stop\nsystemctl stop mariadb.service',
    note: 'При остановке последней ноды кластер перейдёт в non-Primary состояние.',
  },
  {
    title: 'restart',
    badge: 'cat-warning', badgeText: 'Warning',
    desc: 'Перезапустить MariaDB. Эквивалентно stop + start. Нода временно выйдет из кластера.',
    cmd: 'POST /api/nodes/{id}/restart\nsystemctl restart mariadb.service',
  },
  {
    title: 'readonly-on / readonly-off',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Включить/выключить READ_ONLY на ноде. Используется при плановом обслуживании для предотвращения записи.',
    cmd: 'POST /api/nodes/{id}/readonly-on\nSET GLOBAL read_only = ON',
  },
  {
    title: 'ping (SSH)',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Проверить доступность ноды по SSH. Возвращает время ответа в миллисекундах.',
    cmd: 'POST /api/nodes/{id}/ping',
  },
  {
    title: 'rejoin',
    badge: 'cat-action', badgeText: 'Action',
    desc: 'Переподключить ноду к кластеру. Нода получит данные через IST (если gcache позволяет) или SST.',
    cmd: 'POST /api/nodes/{id}/rejoin\n{ "method": "auto" | "ist" | "sst" }',
  },
]

const recoveryCards = [
  {
    title: 'bootstrap (galera_new_cluster)',
    badge: 'cat-danger', badgeText: 'Danger',
    desc: 'Поднять новый кластер из одной ноды. Использовать только когда <strong>все ноды остановлены</strong> и нужно восстановить кластер с нуля. Нода с наибольшим seqno должна быть выбрана для bootstrap.',
    cmd: 'POST /api/nodes/{id}/bootstrap\ngalera_new_cluster',
    note: 'Выполнять только на ноде с наибольшим seqno из grastate.dat',
  },
  {
    title: 'pc.bootstrap (non-Primary Fix)',
    badge: 'cat-danger', badgeText: 'Danger',
    desc: 'Восстановить кворум без перезапуска MariaDB — для ситуации когда MariaDB работает, но кластер завис в состоянии non-Primary.',
    cmd: "SET GLOBAL wsrep_provider_options = 'pc.bootstrap=YES';",
    note: 'Применять только когда wsrep_cluster_status = non-Primary а сетевая связность восстановлена.',
  },
  {
    title: 'wsrep-recover',
    badge: 'cat-danger', badgeText: 'Danger',
    desc: 'Определить seqno ноды при остановленном MariaDB. Используется для выбора кандидата на bootstrap.',
    cmd: 'POST /api/wsrep-recover-all\nmysqld --wsrep-recover',
    note: 'MariaDB должна быть остановлена перед запуском',
  },
  {
    title: 'SST (State Snapshot Transfer)',
    badge: 'cat-warning', badgeText: 'Warning',
    desc: 'Полная синхронизация данных. Донор передаёт весь снимок базы данных реципиенту. Используется когда IST невозможен (gcache переполнен).',
    cmd: 'wsrep_sst_method = mariabackup | rsync | mysqldump',
    note: 'SST блокирует донора на время передачи (кроме mariabackup)',
  },
  {
    title: 'IST (Incremental State Transfer)',
    badge: 'cat-success', badgeText: 'Safe',
    desc: 'Инкрементальная синхронизация через gcache. Значительно быстрее SST. Используется когда отставшая нода может получить нужные транзакции из кэша донора.',
    cmd: 'wsrep_provider_options = "gcache.size=512M"',
  },
  {
    title: 'sst-donor (принудительный донор)',
    badge: 'cat-action', badgeText: 'Action',
    desc: 'Явно указать какая нода будет донором SST. По умолчанию Galera выбирает донора автоматически.',
    cmd: "POST /api/sst-donor\nSET GLOBAL wsrep_sst_donor = 'gc02';",
  },
]

const metricsCards = [
  {
    title: 'wsrep_flow_control_paused',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Доля времени (0.0–1.0) когда репликация была приостановлена из-за перегрузки медленной ноды.',
    normal: '0.000',
    warn: '>0.1 — серьёзная проблема производительности',
  },
  {
    title: 'wsrep_local_recv_queue',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Очередь входящих транзакций ожидающих применения. Показывает отставание ноды от кластера.',
    normal: '0',
    warn: '>0 длительно — нода не справляется с нагрузкой',
  },
  {
    title: 'wsrep_local_send_queue',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Очередь исходящих транзакций ожидающих отправки. Проблема сети или перегрузка.',
    normal: '0',
    warn: '>0 — проблема отправки',
  },
  {
    title: 'wsrep_cert_deps_distance',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Среднее расстояние между зависимыми транзакциями — показывает потенциал параллельного применения.',
    normal: '>1.0',
    warn: '=0 — все транзакции последовательные',
  },
  {
    title: 'wsrep_cluster_conf_id',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Номер конфигурации кластера. Увеличивается при каждом изменении состава нод. Должен совпадать.',
    normal: 'одинаковый на всех нодах',
    warn: 'расхождение — нода была переподключена',
  },
  {
    title: 'wsrep_local_cert_failures',
    badge: 'cat-warning', badgeText: 'Warning',
    desc: 'Число транзакций отклонённых из-за конфликтов сертификации. Конкурирующая запись на разных нодах.',
    normal: '0',
    warn: '>0 — конкурирующие записи или hotspot',
  },
]

const diagCards = [
  {
    title: 'SHOW PROCESSLIST',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Просмотр активных запросов и соединений на ноде. Позволяет увидеть долгие запросы и убить их.',
    cmd: 'GET /api/nodes/{id}/processlist\nSHOW FULL PROCESSLIST',
  },
  {
    title: 'SHOW ENGINE INNODB STATUS',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Детальный статус InnoDB движка: deadlocks, buffer pool, транзакции. Полезно при проблемах с производительностью.',
    cmd: 'GET /api/nodes/{id}/innodb-status\nSHOW ENGINE INNODB STATUS',
  },
  {
    title: 'Журнал garbd',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Получить последние N строк журнала арбитратора garbd. Помогает диагностировать проблемы кворума.',
    cmd: 'GET /api/arbitrators/{id}/log?lines=50',
  },
  {
    title: 'Сравнение galera.cnf',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Сравнить конфигурационные файлы galera.cnf на всех нодах. Выявляет расхождения в параметрах.',
    cmd: 'GET /api/diag/compare-cnf',
  },
  {
    title: 'Системные ресурсы',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'CPU, RAM, Disk по всем нодам через SSH. Помогает найти перегруженную ноду.',
    cmd: 'GET /api/diag/sys-resources',
  },
  {
    title: 'Δ seqno (репликация)',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Разница wsrep_last_committed между нодами. Показывает отставание в транзакциях. В норме = 0.',
    cmd: 'Вычисляется из /api/status → nodes[].wsrep_last_committed',
  },
]

const settingsCards = [
  {
    title: 'nodes.yaml',
    badge: 'cat-info', badgeText: 'Config',
    desc: 'Основной конфигурационный файл. Содержит список нод, арбитраторов, учётные данные SSH и DB, параметры контуров.',
    cmd: 'backend/nodes.yaml\ncontours:\n  test:\n    - name: cluster-1\n      nodes: [...]',
  },
  {
    title: 'galera_data_mode',
    badge: 'cat-info', badgeText: 'localStorage',
    desc: 'Ключ localStorage для сохранения режима mock/real между сессиями. Автоматически синхронизируется с бэкендом.',
    cmd: "localStorage.setItem('galera_data_mode', 'mock')",
  },
  {
    title: 'galera_theme',
    badge: 'cat-info', badgeText: 'localStorage',
    desc: 'Сохранённая тема (dark/light). Применяется через data-theme на html-элементе.',
    cmd: "document.documentElement.setAttribute('data-theme', 'dark')",
  },
]

const wsCards = [
  {
    title: 'WS /ws/cluster',
    badge: 'cat-action', badgeText: 'Push',
    desc: 'Основной WebSocket endpoint. Бэкенд отправляет обновления статуса каждые N секунд. Используется вместо HTTP polling.',
    cmd: 'ws://localhost:8000/ws/cluster\n{ type: "status", nodes: [...], cluster_status: "..." }',
  },
  {
    title: 'Сообщение status',
    badge: 'cat-info', badgeText: 'Info',
    desc: 'Тип сообщения "status" содержит полный снимок состояния кластера идентичный ответу /api/status.',
    cmd: '{ type: "status", cluster_name: "...", nodes: [...], arbitrators: [...] }',
  },
  {
    title: 'Автореконнект',
    badge: 'cat-success', badgeText: 'Safe',
    desc: 'WebSocket автоматически переподключается при разрыве. Начальная задержка 1 сек, экспоненциально до 30 сек.',
    cmd: 'useWebSocket("/ws/cluster", { autoReconnect: true })',
  },
]

const wsrepRef = [
  { var: 'wsrep_cluster_status',       ok: 'Primary',   okClass: 'badge-synced', desc: 'Primary — кворум есть. non-Primary — нет кворума, запись блокируется.' },
  { var: 'wsrep_local_state_comment',  ok: 'Synced',    okClass: 'badge-synced', desc: 'Synced — полностью синхронизирована. Donor — отдаёт SST. Joining — получает данные.' },
  { var: 'wsrep_cluster_size',         ok: 'N (ожид.)', okClass: 'badge-primary', desc: 'Число нод в кластере. Должно совпадать на всех нодах с ожидаемым значением.' },
  { var: 'wsrep_connected',            ok: 'ON',        okClass: 'badge-synced', desc: 'ON — нода подключена к кластеру. OFF — изолирована от кластера.' },
  { var: 'wsrep_ready',                ok: 'ON',        okClass: 'badge-synced', desc: 'ON — нода готова обрабатывать запросы. OFF — в процессе синхронизации.' },
  { var: 'wsrep_flow_control_paused',  ok: '0.000',     okClass: 'badge-synced', desc: 'Доля времени паузы репликации. >0.1 — критично.' },
  { var: 'wsrep_local_recv_queue',     ok: '0',         okClass: 'badge-synced', desc: 'Очередь входящих транзакций. Норма = 0. >10 длительно — проблема.' },
  { var: 'wsrep_local_send_queue',     ok: '0',         okClass: 'badge-synced', desc: 'Очередь исходящих транзакций. Норма = 0.' },
  { var: 'wsrep_cert_deps_distance',   ok: '>1.0',      okClass: 'badge-primary', desc: 'Потенциал параллельного применения. Чем выше — тем лучше.' },
  { var: 'wsrep_local_commits',        ok: 'растёт',    okClass: 'badge-primary', desc: 'Число зафиксированных транзакций на этой ноде с момента запуска.' },
  { var: 'wsrep_local_cert_failures',  ok: '0',         okClass: 'badge-synced', desc: 'Конфликты сертификации. >0 — конкурирующие записи на разных нодах.' },
  { var: 'wsrep_bf_aborts',            ok: 'мало',      okClass: 'badge-primary', desc: 'Brute Force Aborts. Небольшое число при нагрузке — норма.' },
  { var: 'wsrep_cluster_conf_id',      ok: 'одинак.',   okClass: 'badge-synced', desc: 'Номер конфигурации. Должен совпадать на всех нодах.' },
  { var: 'wsrep_cluster_state_uuid',   ok: 'одинак.',   okClass: 'badge-synced', desc: 'UUID кластера. Расхождение — Split-Brain.' },
  { var: 'wsrep_last_committed',       ok: '≈одинак.',  okClass: 'badge-synced', desc: 'Последний применённый seqno. Большая разница — нода отстала.' },
  { var: 'wsrep_replicated_bytes',     ok: 'растёт',    okClass: 'badge-primary', desc: 'Байт реплицированных этой нодой.' },
  { var: 'wsrep_received_bytes',       ok: 'растёт',    okClass: 'badge-primary', desc: 'Байт полученных от других нод.' },
]

const faqCards = [
  {
    q: 'Почему кластер в non-Primary состоянии?',
    a: 'Кластер потерял кворум. Это происходит когда меньше половины нод доступны. Проверьте сетевую связность между нодами. При наличии арбитратора garbd — проверьте его статус.',
    cmd: 'SHOW STATUS LIKE "wsrep_cluster_status"',
  },
  {
    q: 'Что такое Split-Brain?',
    a: 'Ситуация когда кластер разделился на две изолированные части и каждая считает себя Primary. В кластере из 2 нод без арбитратора при потере связи обе ноды перейдут в non-Primary. С арбитратором garbd — только одна часть получит кворум.',
  },
  {
    q: 'Когда нужен garbd (Galera Arbitrator)?',
    a: 'При чётном числе нод для предотвращения Split-Brain. Для кластера из 2 нод — обязателен. garbd — лёгкий процесс без хранения данных, нужен только для голосования.',
    cmd: 'garbd --group=galera_cluster --address="gcomm://node1:4567,node2:4567"',
  },
  {
    q: 'Как работает IST vs SST?',
    a: 'IST (Incremental State Transfer) — быстрая синхронизация через gcache. Возможна если нода недавно была в кластере. SST (State Snapshot Transfer) — полная синхронизация, медленная, нужна при большом отставании или пустой ноде.',
  },
  {
    q: 'Почему flow_control > 0?',
    a: 'Одна или несколько нод не успевают применять транзакции и тормозят репликацию. Возможные причины: медленный диск, нехватка CPU, большой recv_queue. При FC кластер ждёт отстающую ноду.',
    cmd: 'SHOW STATUS LIKE "wsrep_flow_control%"',
  },
  {
    q: 'Как безопасно остановить ноду для обслуживания?',
    a: 'Используйте Maintenance Wizard: 1) включить READ_ONLY, 2) дождаться пустого recv_queue, 3) остановить MariaDB, 4) выполнить работы, 5) запустить MariaDB, 6) дождаться Synced, 7) выключить READ_ONLY.',
  },
  {
    q: 'Что делать при полном отказе кластера?',
    a: 'Используйте Bootstrap Wizard: 1) найти ноду с наибольшим seqno через wsrep-recover, 2) запустить galera_new_cluster на этой ноде, 3) последовательно запустить остальные ноды.',
    cmd: 'mysqld --wsrep-recover\ngalera_new_cluster',
  },
  {
    q: 'Почему wsrep_cluster_size меньше ожидаемого?',
    a: 'Одна или несколько нод выпали из кластера. Проверьте: доступность нод по SSH, статус mariadb.service, логи /var/log/mysql/error.log, сетевую связность по портам 4567 (репликация), 4568 (IST), 4444 (SST).',
  },
]
</script>
