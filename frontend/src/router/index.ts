import {createRouter, createWebHistory} from 'vue-router'

import AppShell from '../layouts/AppShell.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import KeywordsPage from '../pages/KeywordsPage.vue'
import JobsPage from '../pages/JobsPage.vue'
import SourcesPage from '../pages/SourcesPage.vue'
import SearchPage from '../pages/SearchPage.vue'
import Register from "../views/register.vue";
import Login from "../views/login.vue";
import ForbiddenPage from "../views/forbidden-page.vue";
import NotFoundPage from "../views/not-found-page.vue";


import {useAuthStore} from "../stores/auth";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/register', name: 'register', component: Register },
        { path: '/login', name: 'login', component: Login },
        { path: '/403', name: 'forbidden', component: ForbiddenPage },
        {
            path: '/',
            component: AppShell,
            children: [
                { path: '', name: 'dashboard', component: DashboardPage, meta: { requiresAuth: true } },
                { path: 'keywords', name: 'keywords', component: KeywordsPage, meta: { requiresAuth: true } },
                { path: 'jobs', name: 'jobs', component: JobsPage, meta: { requiresAuth: true } },
                { path: 'sources', name: 'sources', component: SourcesPage, meta: { requiresAuth: true } },
                { path: 'search', name: 'search', component: SearchPage, meta: { requiresAuth: true } },
            ],
        },
        {path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundPage},
    ],
});

let initPromise : Promise<void> | null = null;

router.beforeEach(async (to) => {
    const authStore = useAuthStore();
    initPromise ??= authStore.initFromStorage();
    await initPromise;

    if(to.meta.requiresAuth && !authStore.isAuthenticated) {
        return {
            name: 'login',
            query: { returnUrl: to.fullPath }
        }
    }

    return true;
});

export default router;
