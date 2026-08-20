import {createApp} from 'vue'
import {createPinia} from 'pinia'

import App from './App.vue'
import router from './router'
import vuetify from './plugins_vuetify'
import { useAuthStore } from './stores/auth'

const app = createApp(App);
app.use(createPinia());

const auth = useAuthStore();
auth.initFromStorage();

app.use(router).use(vuetify).mount('#app')
