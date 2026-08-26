import { defineStore } from 'pinia'
import { ref } from 'vue'
import { AdminStats, UserRead, RoleRead } from '../models/types';
import {api } from '../services/api'

export const useAdminStore = defineStore('admin', () => {

    const loading = ref<boolean>(false);
    const state = ref<AdminStats | null>(null);
    const error = ref<string | null>(null);
    const users = ref<UserRead[]>([]);
    const roles = ref<RoleRead[]>([]);

    async function getStats() {
        clearError();
        loading.value = true;
        try {
            const status = await api.get('/admin/stats');
            state.value = status.data;
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
    }

    async function getUsers() {
        clearError();
        loading.value = true;
        try {
            const users_data = await api.get('/admin/users');
            users.value = users_data.data;  
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
    }

    async function getRoles() {
        clearError();
        loading.value = true;
        try {
            const roles_data = await api.get('/admin/roles');
            roles.value = roles_data.data;
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
    }

    function handleError(cause: unknown, message: string | null = null) {
        error.value = cause instanceof Error ? cause.message : message || 'Failed to load data.';
    }

    function clearError() {
        error.value = null;
    }

    return {
        loading,
        state,
        users,
        roles,
        error,
        getStats,
        getUsers,
        getRoles
    };
});
