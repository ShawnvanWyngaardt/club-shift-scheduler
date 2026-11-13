import '@fontsource-variable/montserrat'
import '@fontsource/titan-one'
import './assets/main.css'
import './assets/utilities.scss'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')
