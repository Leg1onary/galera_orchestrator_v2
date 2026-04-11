<template>
  <div class="tab-content">
    <div v-if="isLoading" class="loading-state">
      <span class="skeleton skeleton-text" style="width:200px;height:16px" />
    </div>

    <form v-else-if="form" class="settings-form" @submit.prevent="save">

      <div class="field-group">
        <label for="polling-interval" class="field-label">
          Polling interval (seconds)
          <span class="field-hint">How often backend polls node status via SSH/DB</span>
        </label>
        <input
          id="polling-interval"
          type="number"
          v-model.number="form.polling_interval_sec"
          :min="5" :max="300"
          class="field-input"
        />
      </div>

      <div class="field-group">
        <label for="event-log-limit" class="field-label">
          Event log limit
          <span class="field-hint">Maximum number of events stored per cluster</span>
        </label>
        <input
          id="event-log-limit"
          type="number"
          v-model.number="form.event_log_limit"
          :min="100" :max="10000"
          class="field-input"
        />
      </div>

      <!-- Timezone searchable select -->
      <div class="field-group">
        <label class="field-label">
          Timezone
          <span class="field-hint">Used for displaying timestamps in the UI</span>
        </label>

        <div class="tz-wrapper" ref="tzWrapperRef">
          <!-- Trigger -->
          <button
            type="button"
            class="tz-trigger field-input"
            :class="{ 'tz-trigger--open': tzOpen }"
            @click="toggleTz"
            aria-haspopup="listbox"
            :aria-expanded="tzOpen"
          >
            <span class="tz-value">{{ form.timezone }}</span>
            <svg class="tz-chevron" :class="{ 'tz-chevron--up': tzOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>

          <!-- Dropdown -->
          <div v-if="tzOpen" class="tz-dropdown" role="listbox" :aria-label="'Timezone'">
            <div class="tz-search-wrap">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tz-search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input
                ref="tzSearchRef"
                v-model="tzSearch"
                type="text"
                class="tz-search"
                placeholder="Search timezone…"
                autocomplete="off"
                @keydown.esc="closeTz"
                @keydown.enter.prevent="selectFirstFiltered"
              />
            </div>
            <div class="tz-list" ref="tzListRef">
              <template v-for="group in filteredGroups" :key="group.label">
                <div class="tz-group-label">{{ group.label }}</div>
                <div
                  v-for="tz in group.zones"
                  :key="tz"
                  class="tz-option"
                  :class="{ 'tz-option--active': tz === form.timezone }"
                  role="option"
                  :aria-selected="tz === form.timezone"
                  @click="selectTz(tz)"
                >{{ tz }}</div>
              </template>
              <div v-if="filteredGroups.length === 0" class="tz-empty">No timezones found</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="apiError" class="error-alert">
        <i class="pi pi-exclamation-circle" />
        {{ apiError }}
      </div>

      <div class="form-footer">
        <button type="submit" class="btn-save" :disabled="saving">
          <i v-if="saving" class="pi pi-spin pi-spinner" style="font-size:0.85rem" />
          <i v-else class="pi pi-check" style="font-size:0.85rem" />
          {{ saving ? 'Saving…' : 'Save settings' }}
        </button>
        <span v-if="savedAt" class="saved-at">Saved at {{ savedAt }}</span>
      </div>

      <div v-if="data" class="system-meta">
        <span class="meta-text">Last updated: {{ formatDate(data.updated_at) }}</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'primevue/usetoast'
import { settingsApi } from '@/api/settings'
import { extractApiError } from '@/utils/api'
import { useSettingsStore } from '@/stores/settings'

const qc            = useQueryClient()
const toast         = useToast()
const settingsStore = useSettingsStore()

const { data, isLoading } = useQuery({
  queryKey: ['system-settings'],
  queryFn:  () => settingsApi.getSystem(),
})

const form = reactive({
  polling_interval_sec: 30,
  event_log_limit:      1000,
  timezone:             'UTC',
})

watch(data, (val) => {
  if (!val) return
  form.polling_interval_sec = val.polling_interval_sec
  form.event_log_limit      = val.event_log_limit
  form.timezone             = val.timezone
}, { immediate: true })

const saving   = ref(false)
const apiError = ref<string | null>(null)
const savedAt  = ref<string | null>(null)

function formatDate(raw: string): string {
  try { return new Date(raw).toLocaleString() } catch { return raw }
}

async function save() {
  saving.value = true; apiError.value = null
  try {
    await settingsApi.patchSystem({
      polling_interval_sec: form.polling_interval_sec,
      event_log_limit:      form.event_log_limit,
      timezone:             form.timezone,
    })
    await settingsStore.reload()
    await qc.invalidateQueries({ queryKey: ['system-settings'] })
    savedAt.value = new Date().toLocaleTimeString()
    toast.add({ severity: 'success', summary: 'Settings saved', life: 2500 })
  } catch (err) {
    apiError.value = extractApiError(err)
  } finally {
    saving.value = false
  }
}

// ── Timezone select ────────────────────────────────────────────
const TZ_GROUPS: { label: string; zones: string[] }[] = [
  {
    label: 'Universal',
    zones: ['UTC'],
  },
  {
    label: 'Africa',
    zones: [
      'Africa/Abidjan','Africa/Accra','Africa/Addis_Ababa','Africa/Algiers','Africa/Asmara',
      'Africa/Bamako','Africa/Bangui','Africa/Banjul','Africa/Bissau','Africa/Blantyre',
      'Africa/Brazzaville','Africa/Bujumbura','Africa/Cairo','Africa/Casablanca','Africa/Ceuta',
      'Africa/Conakry','Africa/Dakar','Africa/Dar_es_Salaam','Africa/Djibouti','Africa/Douala',
      'Africa/El_Aaiun','Africa/Freetown','Africa/Gaborone','Africa/Harare','Africa/Johannesburg',
      'Africa/Juba','Africa/Kampala','Africa/Khartoum','Africa/Kigali','Africa/Kinshasa',
      'Africa/Lagos','Africa/Libreville','Africa/Lome','Africa/Luanda','Africa/Lubumbashi',
      'Africa/Lusaka','Africa/Malabo','Africa/Maputo','Africa/Maseru','Africa/Mbabane',
      'Africa/Mogadishu','Africa/Monrovia','Africa/Nairobi','Africa/Ndjamena','Africa/Niamey',
      'Africa/Nouakchott','Africa/Ouagadougou','Africa/Porto-Novo','Africa/Sao_Tome',
      'Africa/Tripoli','Africa/Tunis','Africa/Windhoek',
    ],
  },
  {
    label: 'America',
    zones: [
      'America/Adak','America/Anchorage','America/Anguilla','America/Antigua','America/Araguaina',
      'America/Argentina/Buenos_Aires','America/Argentina/Catamarca','America/Argentina/Cordoba',
      'America/Argentina/Jujuy','America/Argentina/La_Rioja','America/Argentina/Mendoza',
      'America/Argentina/Rio_Gallegos','America/Argentina/Salta','America/Argentina/San_Juan',
      'America/Argentina/San_Luis','America/Argentina/Tucuman','America/Argentina/Ushuaia',
      'America/Aruba','America/Asuncion','America/Atikokan','America/Bahia',
      'America/Bahia_Banderas','America/Barbados','America/Belem','America/Belize',
      'America/Blanc-Sablon','America/Boa_Vista','America/Bogota','America/Boise',
      'America/Cambridge_Bay','America/Campo_Grande','America/Cancun','America/Caracas',
      'America/Cayenne','America/Cayman','America/Chicago','America/Chihuahua',
      'America/Costa_Rica','America/Creston','America/Cuiaba','America/Curacao',
      'America/Danmarkshavn','America/Dawson','America/Dawson_Creek','America/Denver',
      'America/Detroit','America/Dominica','America/Edmonton','America/Eirunepe',
      'America/El_Salvador','America/Fort_Nelson','America/Fortaleza','America/Glace_Bay',
      'America/Godthab','America/Goose_Bay','America/Grand_Turk','America/Grenada',
      'America/Guadeloupe','America/Guatemala','America/Guayaquil','America/Guyana',
      'America/Halifax','America/Havana','America/Hermosillo','America/Indiana/Indianapolis',
      'America/Indiana/Knox','America/Indiana/Marengo','America/Indiana/Petersburg',
      'America/Indiana/Tell_City','America/Indiana/Vevay','America/Indiana/Vincennes',
      'America/Indiana/Winamac','America/Inuvik','America/Iqaluit','America/Jamaica',
      'America/Juneau','America/Kentucky/Louisville','America/Kentucky/Monticello',
      'America/Kralendijk','America/La_Paz','America/Lima','America/Los_Angeles',
      'America/Lower_Princes','America/Maceio','America/Managua','America/Manaus',
      'America/Marigot','America/Martinique','America/Matamoros','America/Mazatlan',
      'America/Menominee','America/Merida','America/Metlakatla','America/Mexico_City',
      'America/Miquelon','America/Moncton','America/Monterrey','America/Montevideo',
      'America/Montserrat','America/Nassau','America/New_York','America/Nipigon',
      'America/Nome','America/Noronha','America/North_Dakota/Beulah',
      'America/North_Dakota/Center','America/North_Dakota/New_Salem','America/Nuuk',
      'America/Ojinaga','America/Panama','America/Pangnirtung','America/Paramaribo',
      'America/Phoenix','America/Port-au-Prince','America/Port_of_Spain','America/Porto_Velho',
      'America/Puerto_Rico','America/Punta_Arenas','America/Rainy_River','America/Rankin_Inlet',
      'America/Recife','America/Regina','America/Resolute','America/Rio_Branco',
      'America/Santarem','America/Santiago','America/Santo_Domingo','America/Sao_Paulo',
      'America/Scoresbysund','America/Sitka','America/St_Barthelemy','America/St_Johns',
      'America/St_Kitts','America/St_Lucia','America/St_Thomas','America/St_Vincent',
      'America/Swift_Current','America/Tegucigalpa','America/Thule','America/Thunder_Bay',
      'America/Tijuana','America/Toronto','America/Tortola','America/Vancouver',
      'America/Whitehorse','America/Winnipeg','America/Yakutat','America/Yellowknife',
    ],
  },
  {
    label: 'Antarctica',
    zones: [
      'Antarctica/Casey','Antarctica/Davis','Antarctica/DumontDUrville','Antarctica/Macquarie',
      'Antarctica/Mawson','Antarctica/McMurdo','Antarctica/Palmer','Antarctica/Rothera',
      'Antarctica/Syowa','Antarctica/Troll','Antarctica/Vostok',
    ],
  },
  {
    label: 'Arctic',
    zones: ['Arctic/Longyearbyen'],
  },
  {
    label: 'Asia',
    zones: [
      'Asia/Aden','Asia/Almaty','Asia/Amman','Asia/Anadyr','Asia/Aqtau','Asia/Aqtobe',
      'Asia/Ashgabat','Asia/Atyrau','Asia/Baghdad','Asia/Bahrain','Asia/Baku',
      'Asia/Bangkok','Asia/Barnaul','Asia/Beirut','Asia/Bishkek','Asia/Brunei',
      'Asia/Chita','Asia/Choibalsan','Asia/Colombo','Asia/Damascus','Asia/Dhaka',
      'Asia/Dili','Asia/Dubai','Asia/Dushanbe','Asia/Famagusta','Asia/Gaza',
      'Asia/Hebron','Asia/Ho_Chi_Minh','Asia/Hong_Kong','Asia/Hovd','Asia/Irkutsk',
      'Asia/Jakarta','Asia/Jayapura','Asia/Jerusalem','Asia/Kabul','Asia/Kamchatka',
      'Asia/Karachi','Asia/Kathmandu','Asia/Khandyga','Asia/Kolkata','Asia/Krasnoyarsk',
      'Asia/Kuala_Lumpur','Asia/Kuching','Asia/Kuwait','Asia/Macau','Asia/Magadan',
      'Asia/Makassar','Asia/Manila','Asia/Muscat','Asia/Nicosia','Asia/Novokuznetsk',
      'Asia/Novosibirsk','Asia/Omsk','Asia/Oral','Asia/Phnom_Penh','Asia/Pontianak',
      'Asia/Pyongyang','Asia/Qatar','Asia/Qostanay','Asia/Qyzylorda','Asia/Riyadh',
      'Asia/Sakhalin','Asia/Samarkand','Asia/Seoul','Asia/Shanghai','Asia/Singapore',
      'Asia/Srednekolymsk','Asia/Taipei','Asia/Tashkent','Asia/Tbilisi','Asia/Tehran',
      'Asia/Thimphu','Asia/Tokyo','Asia/Tomsk','Asia/Ulaanbaatar','Asia/Urumqi',
      'Asia/Ust-Nera','Asia/Vientiane','Asia/Vladivostok','Asia/Yakutsk',
      'Asia/Yangon','Asia/Yekaterinburg','Asia/Yerevan',
    ],
  },
  {
    label: 'Atlantic',
    zones: [
      'Atlantic/Azores','Atlantic/Bermuda','Atlantic/Canary','Atlantic/Cape_Verde',
      'Atlantic/Faroe','Atlantic/Madeira','Atlantic/Reykjavik','Atlantic/South_Georgia',
      'Atlantic/St_Helena','Atlantic/Stanley',
    ],
  },
  {
    label: 'Australia',
    zones: [
      'Australia/Adelaide','Australia/Brisbane','Australia/Broken_Hill','Australia/Darwin',
      'Australia/Eucla','Australia/Hobart','Australia/Lindeman','Australia/Lord_Howe',
      'Australia/Melbourne','Australia/Perth','Australia/Sydney',
    ],
  },
  {
    label: 'Europe',
    zones: [
      'Europe/Amsterdam','Europe/Andorra','Europe/Astrakhan','Europe/Athens',
      'Europe/Belgrade','Europe/Berlin','Europe/Bratislava','Europe/Brussels',
      'Europe/Bucharest','Europe/Budapest','Europe/Busingen','Europe/Chisinau',
      'Europe/Copenhagen','Europe/Dublin','Europe/Gibraltar','Europe/Guernsey',
      'Europe/Helsinki','Europe/Isle_of_Man','Europe/Istanbul','Europe/Jersey',
      'Europe/Kaliningrad','Europe/Kiev','Europe/Kirov','Europe/Lisbon',
      'Europe/Ljubljana','Europe/London','Europe/Luxembourg','Europe/Madrid',
      'Europe/Malta','Europe/Mariehamn','Europe/Minsk','Europe/Monaco',
      'Europe/Moscow','Europe/Nicosia','Europe/Oslo','Europe/Paris',
      'Europe/Podgorica','Europe/Prague','Europe/Riga','Europe/Rome',
      'Europe/Samara','Europe/San_Marino','Europe/Sarajevo','Europe/Saratov',
      'Europe/Simferopol','Europe/Skopje','Europe/Sofia','Europe/Stockholm',
      'Europe/Tallinn','Europe/Tirane','Europe/Ulyanovsk','Europe/Uzhgorod',
      'Europe/Vaduz','Europe/Vatican','Europe/Vienna','Europe/Vilnius',
      'Europe/Volgograd','Europe/Warsaw','Europe/Zagreb','Europe/Zaporozhye',
      'Europe/Zurich',
    ],
  },
  {
    label: 'Indian',
    zones: [
      'Indian/Antananarivo','Indian/Chagos','Indian/Christmas','Indian/Cocos',
      'Indian/Comoro','Indian/Kerguelen','Indian/Mahe','Indian/Maldives',
      'Indian/Mauritius','Indian/Mayotte','Indian/Reunion',
    ],
  },
  {
    label: 'Pacific',
    zones: [
      'Pacific/Apia','Pacific/Auckland','Pacific/Bougainville','Pacific/Chatham',
      'Pacific/Chuuk','Pacific/Easter','Pacific/Efate','Pacific/Enderbury',
      'Pacific/Fakaofo','Pacific/Fiji','Pacific/Funafuti','Pacific/Galapagos',
      'Pacific/Gambier','Pacific/Guadalcanal','Pacific/Guam','Pacific/Honolulu',
      'Pacific/Kiritimati','Pacific/Kosrae','Pacific/Kwajalein','Pacific/Majuro',
      'Pacific/Marquesas','Pacific/Midway','Pacific/Nauru','Pacific/Niue',
      'Pacific/Norfolk','Pacific/Noumea','Pacific/Pago_Pago','Pacific/Palau',
      'Pacific/Pitcairn','Pacific/Pohnpei','Pacific/Port_Moresby','Pacific/Rarotonga',
      'Pacific/Saipan','Pacific/Tahiti','Pacific/Tarawa','Pacific/Tongatapu',
      'Pacific/Wake','Pacific/Wallis',
    ],
  },
]

const tzOpen       = ref(false)
const tzSearch     = ref('')
const tzWrapperRef = ref<HTMLElement | null>(null)
const tzSearchRef  = ref<HTMLInputElement | null>(null)
const tzListRef    = ref<HTMLElement | null>(null)

const filteredGroups = computed(() => {
  const q = tzSearch.value.trim().toLowerCase()
  if (!q) return TZ_GROUPS
  return TZ_GROUPS
    .map(g => ({ label: g.label, zones: g.zones.filter(z => z.toLowerCase().includes(q)) }))
    .filter(g => g.zones.length > 0)
})

function toggleTz() {
  tzOpen.value = !tzOpen.value
  if (tzOpen.value) {
    tzSearch.value = ''
    nextTick(() => tzSearchRef.value?.focus())
  }
}

function closeTz() {
  tzOpen.value = false
  tzSearch.value = ''
}

function selectTz(tz: string) {
  form.timezone = tz
  closeTz()
}

function selectFirstFiltered() {
  const first = filteredGroups.value[0]?.zones[0]
  if (first) selectTz(first)
}

function onClickOutside(e: MouseEvent) {
  if (tzWrapperRef.value && !tzWrapperRef.value.contains(e.target as Node)) {
    closeTz()
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.tab-content   { max-width: 32rem; display: flex; flex-direction: column; }

.loading-state { padding: var(--space-8) 0; }

.settings-form { display: flex; flex-direction: column; gap: var(--space-5); }

.field-group   { display: flex; flex-direction: column; gap: var(--space-2); }
.field-label   { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); }
.field-hint    { display: block; font-size: var(--text-xs); color: var(--color-text-muted); font-weight: 400; margin-top: 2px; }

.field-input {
  width: 100%;
  background: #0f1015;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: inherit;
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
  outline: none;
  transition: border-color 150ms ease, box-shadow 150ms ease;
  -webkit-appearance: none;
  appearance: none;
  box-sizing: border-box;
}
.field-input::placeholder { color: var(--color-text-faint); }
.field-input:focus {
  border-color: rgba(45,212,191,0.45);
  box-shadow: 0 0 0 3px rgba(45,212,191,0.08);
}

/* ── Timezone select ── */
.tz-wrapper { position: relative; width: 100%; }

.tz-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  text-align: left;
  user-select: none;
}
.tz-trigger--open {
  border-color: rgba(45,212,191,0.45);
  box-shadow: 0 0 0 3px rgba(45,212,191,0.08);
}
.tz-value  { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tz-chevron { flex-shrink: 0; color: var(--color-text-muted); transition: transform 150ms ease; }
.tz-chevron--up { transform: rotate(180deg); }

.tz-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: #0f1015;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  z-index: 100;
  display: flex;
  flex-direction: column;
  max-height: 280px;
  overflow: hidden;
}

.tz-search-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}
.tz-search-icon { color: var(--color-text-faint); flex-shrink: 0; }
.tz-search {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text);
  font-size: var(--text-sm);
  font-family: inherit;
}
.tz-search::placeholder { color: var(--color-text-faint); }

.tz-list {
  overflow-y: auto;
  flex: 1;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.tz-group-label {
  padding: var(--space-1) var(--space-3);
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-faint);
  background: rgba(255,255,255,0.02);
  position: sticky;
  top: 0;
  z-index: 1;
}

.tz-option {
  padding: 6px var(--space-3);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 100ms ease, color 100ms ease;
  font-family: var(--font-mono, monospace);
}
.tz-option:hover { background: rgba(255,255,255,0.05); color: var(--color-text); }
.tz-option--active {
  background: rgba(45,212,191,0.1);
  color: #2dd4bf;
}

.tz-empty {
  padding: var(--space-4) var(--space-3);
  font-size: var(--text-sm);
  color: var(--color-text-faint);
  text-align: center;
}

/* ── Form footer ── */
.form-footer { display: flex; align-items: center; gap: var(--space-3); margin-top: var(--space-2); }
.saved-at    { font-size: var(--text-xs); color: var(--color-text-muted); }

.btn-save {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-sm); font-weight: 600; font-family: inherit;
  color: #0d1117; background: #2dd4bf;
  border: none; cursor: pointer;
  transition: all 150ms ease;
}
.btn-save:hover:not(:disabled) { background: #5eead4; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.system-meta { padding-top: var(--space-4); border-top: 1px solid var(--color-divider); }
.meta-text   { font-size: var(--text-xs); color: var(--color-text-muted); }

.error-alert {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-3);
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  color: #f87171;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.skeleton { display: inline-block; border-radius: var(--radius-sm); background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.05) 75%); background-size: 200% 100%; animation: shimmer 1.5s ease-in-out infinite; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
</style>
