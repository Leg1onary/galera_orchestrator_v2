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
import Timeline from 'primevue/timeline'
import MeterGroup from 'primevue/metergroup'
import Skeleton from 'primevue/skeleton'
import Knob from 'primevue/knob'
import SplitButton from 'primevue/splitbutton'
import Breadcrumb from 'primevue/breadcrumb'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import StepPanels from 'primevue/steppanels'
import Step from 'primevue/step'
import StepPanel from 'primevue/steppanel'

import 'primeicons/primeicons.css'
import './assets/main.css'
import App from './App.vue'
import router from './router'

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
          color:         '{primary.400}',
          contrastColor: '#09090b',
          hoverColor:    '{primary.500}',
          activeColor:   '{primary.600}',
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
    inputtext: {
      colorScheme: {
        dark: {
          root: {
            background:       '#13141a',
            borderColor:      'rgba(255,255,255,0.08)',
            color:            '#e4e4e7',
            placeholderColor: '#52525b',
            focusBorderColor: '#2dd4bf',
            hoverBorderColor: 'rgba(45,212,191,0.30)',
            shadow:           'none',
          },
        },
      },
    },
    select: {
      colorScheme: {
        dark: {
          root: {
            background:       '#13141a',
            borderColor:      'rgba(255,255,255,0.08)',
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
    datatable: {
      colorScheme: {
        dark: {
          root: { borderColor: 'rgba(255,255,255,0.07)' },
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
    // ── Toast ────────────────────────────────────────────────────────
    toast: {
      colorScheme: {
        dark: {
          root: {
            background:  '#1a1b22',
            borderColor: 'rgba(255,255,255,0.08)',
            color:       '#e4e4e7',
            shadow:      '0 16px 48px rgba(0,0,0,0.6)',
          },
          // success
          success: {
            background:  'rgba(74,222,128,0.08)',
            borderColor: 'rgba(74,222,128,0.2)',
            color:       '#4ade80',
            detailColor: '#a3a3a3',
          },
          // error
          error: {
            background:  'rgba(248,113,113,0.08)',
            borderColor: 'rgba(248,113,113,0.2)',
            color:       '#f87171',
            detailColor: '#a3a3a3',
          },
          // warn
          warn: {
            background:  'rgba(251,191,36,0.08)',
            borderColor: 'rgba(251,191,36,0.2)',
            color:       '#fbbf24',
            detailColor: '#a3a3a3',
          },
          // info
          info: {
            background:  'rgba(96,165,250,0.08)',
            borderColor: 'rgba(96,165,250,0.2)',
            color:       '#60a5fa',
            detailColor: '#a3a3a3',
          },
          closeButton: {
            hoverBackground: 'rgba(255,255,255,0.07)',
          },
        },
      },
    },
    // ── Tag ──────────────────────────────────────────────────────────
    tag: {
      colorScheme: {
        dark: {
          root: {
            primaryBackground:  'rgba(45,212,191,0.12)',
            primaryColor:       '#2dd4bf',
            successBackground:  'rgba(74,222,128,0.12)',
            successColor:       '#4ade80',
            dangerBackground:   'rgba(248,113,113,0.12)',
            dangerColor:        '#f87171',
            warningBackground:  'rgba(251,191,36,0.12)',
            warningColor:       '#fbbf24',
            infoBackground:     'rgba(96,165,250,0.12)',
            infoColor:          '#60a5fa',
            secondaryBackground:'rgba(255,255,255,0.07)',
            secondaryColor:     '#a1a1aa',
          },
        },
      },
    },
  },
})

const pinia = createPinia()

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(VueQueryPlugin, { queryClient })
app.use(PrimeVue, {
  theme: {
    preset: GaleraPreset,
    options: {
      // класс app-dark вешается на <html> в index.html — PrimeVue всегда в dark mode
      darkModeSelector: '.app-dark',
      cssLayer: { name: 'primevue', order: 'base, primevue' },
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
app.component('Timeline', Timeline)
app.component('MeterGroup', MeterGroup)
app.component('Skeleton', Skeleton)
app.component('Knob', Knob)
app.component('SplitButton', SplitButton)
app.component('Breadcrumb', Breadcrumb)
app.component('Stepper', Stepper)
app.component('StepList', StepList)
app.component('StepPanels', StepPanels)
app.component('Step', Step)
app.component('StepPanel', StepPanel)

app.mount('#app')
