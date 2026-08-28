import { defineStore } from 'pinia'
import { authClient } from '../lib/axios'
import {ref, computed, watch, handleError} from 'vue'
import { TokenPair, UserCreate } from '../models/types'
import { jwtDecode } from 'jwt-decode'
import type { JwtPayload} from 'jwt-decode'


interface NewsJwtPayload extends JwtPayload {
    roles?: string[];
    permissions?: string[];
}

export const useAuthStore = defineStore('auth', () => {

    const access_token = ref<string | null>(null);
    const refresh_token = ref<string | null>(null);
    const roles = ref<string[] | null>(null);
    const permissions = ref<string[] | null>(null);
    
    const isAuthenticated = computed(() => !!access_token.value);
    const currentUserId = ref<string | null>(null);
    const hasRole = (name: string) => roles.value?.includes(name);
    const hasPermission = (name: string) => permissions.value?.includes(name);
    const hasAnyPermission = (list: string[]) => 
        list.some(name => hasPermission(name));


    async function register(cred: UserCreate) {
        await authClient.post("/auth/register", cred);
    }

    async function login(cred: URLSearchParams) {

        const { data } = await authClient.post<TokenPair>("/auth/login", cred,
            { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

        access_token.value = data.access_token;
        refresh_token.value = data.refresh_token;
        decodeToken(access_token.value);
    }

    /** Drops local session state without calling the server. */
    function clearSession() {
        access_token.value = null;
        refresh_token.value = null;
        roles.value = [];
        permissions.value = [];
    }

    async function logout() {
        try {
            if (refresh_token.value) {
                await authClient.post("/auth/logout", {
                    'refresh_token': refresh_token.value
                });
            }
        } finally {
            clearSession();
        }
    }

    async function refresh() {
        if (!refresh_token.value) {
            throw new Error('No refresh token available');
        }

        const { data } = await authClient.post<TokenPair>("/auth/refresh", {
            'refresh_token': refresh_token.value
        });

        access_token.value = data.access_token;
        // The server rotates the refresh token, so the new one must replace it.
        refresh_token.value = data.refresh_token;
        decodeToken(access_token.value)
    }

    async function initFromStorage() {
        const stored = localStorage.getItem('refresh_token');
        if (!stored) return;

        refresh_token.value = stored;
        try {
            await refresh();
        } catch {
            clearSession();
        }
    }

    function decodeToken(token: string | null) {

        if (!token) {
            return;
        }
        try {
            const decodedToken: NewsJwtPayload = jwtDecode<NewsJwtPayload>(token);    
            currentUserId.value = decodedToken.sub || null;

            if (decodedToken.roles) {
            roles.value = decodedToken.roles;
            }

            if (decodedToken.permissions) {
                permissions.value = decodedToken.permissions;
            }
        } catch(e) {
            clearSession();
        }
    }



    watch(refresh_token, (newValue) => {
        if (newValue) {
            localStorage.setItem('refresh_token', newValue);
        } else {
            localStorage.removeItem('refresh_token');
        }
    });

    return {
        access_token,
        refresh_token,
        roles,
        permissions,
        isAuthenticated,
        currentUserId,
        hasPermission,
        hasRole,
        hasAnyPermission,
        login,
        logout,
        clearSession,
        refresh,
        initFromStorage,
        register
    };
});

