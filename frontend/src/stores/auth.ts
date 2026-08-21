import { defineStore } from 'pinia'
import { api } from '../services/api'
import {ref, computed, watch} from 'vue'
import {TokenPair, RefreshRequest, UserCreate} from '../models/types';


export const useAuthStore = defineStore('auth', () => {

    const access_token = ref<string | null>(null);
    const refresh_token = ref<string | null>(null);
    const roles = ref<string[] | null>(null);
    const permissions = ref<string[] | null>(null);
    
    const isAuthenticated = computed(() => !!access_token.value);
    const hasRole = (name: string) => roles.value?.includes(name);
    const hasPermission = (name: string) => permissions.value?.includes(name);
    const hasAnyPermission = (list: string[]) => 
        list.some(name => hasPermission(name));


    async function register(cred: UserCreate) {
        await api.post("/auth/register", cred);
    }

    async function login(cred: { email: string, password: string }) {

        const { data } = await api.post<TokenPair>("/auth/login", cred);

        access_token.value = data.access_token;
        refresh_token.value = data.refresh_token;
        
        localStorage.setItem("refresh_token", data.refresh_token);

        api.defaults.headers.common['Authorization'] =
            `Bearer ${access_token.value}`;
    }   

    async function logout() {
        await api.post("/auth/logout", {
            'refresh_token': refresh_token.value
        });
        access_token.value = null;
        refresh_token.value = null;
        roles.value = [];
        permissions.value = [];

        localStorage.removeItem("refresh_token");
        delete api.defaults.headers.common['Authorization'];
    }

    async function refresh() {
        const request = {
            'refresh_token': refresh_token.value
        }
        const { data } = await api.post<TokenPair>("/auth/refresh", request);

        access_token.value = data.access_token;
        refresh_token.value = data.refresh_token;

        localStorage.setItem('refresh_token', data.refresh_token);
        api.defaults.headers.common['Authorization'] = refresh_token.value;
    }

    function initFromStorage() {
        const stored = localStorage.getItem('refresh_token');
        if (stored) {
            refresh_token.value = stored;
        }
        refresh().catch(() => {
            localStorage.removeItem('refresh_token');
            logout();
        });
    }

    watch(refresh_token, (newValue) => {
        if (newValue) {
            localStorage.setItem('refresh_token', newValue);
        } else {
            localStorage.removeItem('refresh_token');
        }
    });

    return {
        roles,
        permissions,
        isAuthenticated,
        hasPermission,
        hasRole,
        login,
        logout,
        refresh,
        initFromStorage,
        register
    };
});

