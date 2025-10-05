import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './components/HomePage.vue'
import DemoPage from './components/DemoPage.vue'
import './style.css'

const routes = [
  { path: '/', component: HomePage },
  { path: '/demo', component: DemoPage }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
