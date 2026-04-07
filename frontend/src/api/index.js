import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  timeout: 30000,
})

// Inject auth token
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('galera_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Handle 401 — redirect to login
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('galera_token')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
