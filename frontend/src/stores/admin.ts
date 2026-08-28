import { defineStore } from 'pinia'
import { ref } from 'vue'
import {AdminStats, UserRead, RoleRead, UserCreate, UserUpdate} from '../models/types';
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

    async function getUser(user_id: string): Promise<UserRead | null> {
        clearError();
        loading.value = true;
        try {
            const response = await api.get(`/admin/users/${user_id}`);
            return response.data;
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
        return null;
    }

    async function createUser(email: string, username: string, is_active: boolean, password: string): Promise<UserRead | null> {
        clearError();
        loading.value = true;
        try {
            const new_user: UserCreate = {
                email: email,
                username: username,
                is_active: is_active,
                password: password
            };

            const response = await api.post('/admin/users', new_user);
            addUserToList(response.data);
            return response.data;        
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
        return null;
    }

    async function updateUser(user_id: string,  email: string, username: string, is_active: boolean): Promise<UserRead | null>{
        clearError();
        loading.value = true;
        try{
            const updated_user: UserUpdate = {
                email: email,
                username: username,
                is_active: is_active
            };
            const response = await api.put(`/admin/users/${user_id}`, updated_user);
            updateUserInTheList(response.data);
            return response.data;
        }catch(e){
            handleError(e);
        }finally {
            loading.value = false;
        }
        return null;
    }
    async function deleteUser(user_id: string): Promise<boolean> {
        clearError();
        loading.value = true;
        try {
            await api.delete(`/admin/users/${user_id}`);
            deleteUserFromList(user_id);
            return true;
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
        return false;
    }

    async function activate(user_id: string): Promise<any>{
        clearError();
        loading.value = true;
        try {
            await api.post(`/admin/users/${user_id}/activate`);
        } finally {
            loading.value = false;
        }
    }

    async function deactivate(user_id: string): Promise<any>{
        clearError();
        loading.value = true;
        try {
            await api.post(`/admin/users/${user_id}/deactivate`);
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

    function addUserToList(user: UserRead | null) {
        if (!user) return;
        users.value = [...users.value, user];
    }

    function updateUserInTheList(updatedUser: UserRead) {
        users.value = users.value.map(u => u.id === updatedUser.id ? updatedUser : u);        
    }

    function deleteUserFromList(user_id: string) {
        users.value = users.value.filter(u => u.id !== user_id)
    }

    return {
        loading,
        state,
        users,
        roles,
        error,
        getStats,
        getUsers,
        getRoles,
        getUser,
        createUser,
        updateUser,
        deleteUser,
        activate,
        deactivate
    };
});
