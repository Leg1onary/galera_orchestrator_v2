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

// ─── Galera Orchestrator v2 — Terminal Precision theme ───────────────────────
// Zinc dark surfaces, teal accent (interactive only)
// Built on Aura base — only semantic tokens overridden
const GaleraPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50:  '#f0fdfa',
      100: '#ccfbf1',
      200: '#99f6e4',
      300: '#5eead4',
      400: '#2dd4bf',
      500: '#14b8a6',
      600: '#0d9488',
      700: '#0f766e',
      800: '#115e59',
      900: '#134e4a',
      950: '#042f2e',
    },
    colorScheme: {
      dark: {
        surface: {
          0:   '#ffffff',
          50:  '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b',
        },
        primary: {
          color:         '#2dd4bf',
          contrastColor: '#09090b',
          hoverColor:    '#14b8a6',
          activeColor:   '#0d9488',
        },
        highlight: {
          background:      'rgba(45,212,191,0.10)',
          focusBackground: 'rgba(45,212,191,0.18)',
          color:           '#2dd4bf',
          focusColor:      '#5eead4',
        },
      },
    },
  },
  components: {
    // Button: ghost teal style for primary, semantic for others
    button: {
      colorScheme: {
        dark: {
          root: {
            primary: {
              background:       'rgba(45,212,191,0.10)',
              borderColor:      'rgba(45,212,191,0.28)',
              color:            '#2dd4bf',
              hoverBackground:  'rgba(45,212,191,0.16)',
              hoverBorderColor: 'rgba(45,212,191,0.48)',
              hoverColor:       '#5eead4',
              activeBackground: 'rgba(45,212,191,0.22)',
              activeBorderColor:'rgba(45,212,191,0.65)',
              activeColor:      '#99f6e4',
            },
          },
        },
      },
    },
    // Card overrides
    card: {
      colorScheme: {
        dark: {
          root: {
            background: '#0f1015',
            borderColor: 'rgba(255,255,255,0.07)',
            color:       '#e4e4e7',
            shadow:      '0 4px 16px rgba(0,0,0,0.5)',
          },
        },
      },
    },
    // Input text
    inputtext: {
      colorScheme: {
        dark: {
          root: {
            background:       '#1a1b24',
            borderColor:      'rgba(255,255,255,0.07)',
            color:            '#e4e4e7',
            placeholderColor: '#3f3f46',
            focusBorderColor: '#2dd4bf',
            hoverBorderColor: 'rgba(45,212,191,0.30)',
            shadow:           'none',
          },
        },
      },
    },
    // Select dropdown
    select: {
      colorScheme: {
        dark: {
          root: {
            background:       '#1a1b24',
            borderColor:      'rgba(255,255,255,0.07)',
            color:            '#e4e4e7',
            hoverBorderColor: 'rgba(45,212,191,0.30)',
            focusBorderColor: '#2dd4bf',
          },
          overlay: {
            background:  '#14151c',
            borderColor: 'rgba(255,255,255,0.07)',
            shadow:      '0 16px 48px rgba(0,0,0,0.65)',
          },
          option: {
            focusBackground:    '#1a1b24',
            selectedBackground: 'rgba(45,212,191,0.10)',
            selectedColor:      '#2dd4bf',
          },
        },
      },
    },
    // Dialog
    dialog: {
      colorScheme: {
        dark: {
          root: {
            background:  '#14151c',
            borderColor: 'rgba(255,255,255,0.07)',
            color:       '#e4e4e7',
          },
        },
      },
    },
    // Drawer
    drawer: {
      colorScheme: {
        dark: {
          root: {
            background:  '#14151c',
            borderColor: 'rgba(255,255,255,0.07)',
          },
        },
      },
    },
    // DataTable
    datatable: {
      colorScheme: {
        dark: {
          root: {
            borderColor: 'rgba(255,255,255,0.07)',
          },
          header: {
            background: '#14151c',
            borderColor: 'rgba(255,255,255,0.07)',
            color:       '#71717a',
          },
          bodyRow: {
            background:      '#0f1015',
            hoverBackground: '#1a1b24',
            borderColor:     'rgba(255,255,255,0.04)',
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
