import {createRouter, createWebHistory} from 'vue-router'

import AppShell from '../layouts/AppShell.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import KeywordsPage from '../pages/KeywordsPage.vue'
import JobsPage from '../pages/JobsPage.vue'
import SourcesPage from '../pages/SourcesPage.vue'
import SearchPage from '../pages/SearchPage.vue'

export default createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: AppShell,
            children: [
                {path: '', name: 'dashboard', component: DashboardPage},
                {path: 'keywords', name: 'keywords', component: KeywordsPage},
                {path: 'jobs', name: 'jobs', component: JobsPage},
                {path: 'sources', name: 'sources', component: SourcesPage},
                {path: 'search', name: 'search', component: SearchPage},
            ],
        },
    ],
})
