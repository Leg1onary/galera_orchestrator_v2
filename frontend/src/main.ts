import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Tabs from 'primevue/tabs'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanels from 'primevue/tabpanels'
import Dialog from 'primevue/dialog'
import Drawer from 'primevue/drawer'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import ToggleSwitch from 'primevue/toggleswitch'
import Badge from 'primevue/badge'

import 'primeicons/primeicons.css'
import './assets/main.css'
import App from './App.vue'
import router from './router'

// ─── Custom PrimeVue Preset ───────────────────────────────────────────────────
// Строим поверх Aura. Переопределяем только токены — не трогаем логику компонентов.
const GaleraPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50:  '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '{teal.500}',
      600: '{teal.600}',
      700: '{teal.700}',
      800: '{teal.800}',
      900: '{teal.900}',
      950: '{teal.950}',
    },
    colorScheme: {
      dark: {
        surface: {
          0:   '#ffffff',
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        primary: {
          color:          '#2dd4bf',
          contrastColor:  '#0a0f1e',
          hoverColor:     '#14b8a6',
          activeColor:    '#0d9488',
        },
        highlight: {
          background:     'rgba(45,212,191,0.12)',
          focusBackground:'rgba(45,212,191,0.2)',
          color:          '#2dd4bf',
          focusColor:     '#2dd4bf',
        },
      },
    },
  },
  components: {
    button: {
      colorScheme: {
        dark: {
          root: {
            primary: {
              background: 'rgba(45,212,191,0.12)',
              borderColor: 'rgba(45,212,191,0.35)',
              color: '#2dd4bf',
              hoverBackground: 'rgba(45,212,191,0.2)',
              hoverBorderColor: 'rgba(45,212,191,0.55)',
              hoverColor: '#5eead4',
              activeBackground: 'rgba(45,212,191,0.28)',
              activeBorderColor: 'rgba(45,212,191,0.7)',
              activeColor: '#99f6e4',
            },
          },
        },
      },
    },
    card: {
      colorScheme: {
        dark: {
          root: {
            background: '#0d1424',
            borderColor: 'rgba(45,212,191,0.08)',
            color: '#e2e8f0',
            shadow: '0 4px 24px rgba(0,0,0,0.4)',
          },
        },
      },
    },
  },
})

const pinia = createPinia()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(VueQueryPlugin, { queryClient })
app.use(PrimeVue, {
  theme: {
    preset: GaleraPreset,
    options: {
      darkModeSelector: false,
      cssLayer: {
        name: 'primevue',
        order: 'base, primevue',
      },
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)

app.directive('tooltip', Tooltip)

app.component('Button', Button)
app.component('InputText', InputText)
app.component('Password', Password)
app.component('Select', Select)
app.component('Tag', Tag)
app.component('Message', Message)
app.component('ProgressSpinner', ProgressSpinner)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('Tabs', Tabs)
app.component('Tab', Tab)
app.component('TabList', TabList)
app.component('TabPanels', TabPanels)
app.component('Dialog', Dialog)
app.component('Drawer', Drawer)
app.component('Toast', Toast)
app.component('ConfirmDialog', ConfirmDialog)
app.component('ToggleSwitch', ToggleSwitch)
app.component('Badge', Badge)

app.mount('#app')
