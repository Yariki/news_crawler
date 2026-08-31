import { defineStore } from 'pinia'
import { ref } from 'vue'
import {AdminStats, UserRead, RoleRead, UserCreate, UserUpdate, RoleCreateUpdate, PermissionRead, PermissionCreateUpdate, UserRoles} from '../models/types';
import {api } from '../services/api'

export const useAdminStore = defineStore('admin', () => {

    const loading = ref<boolean>(false);
    const state = ref<AdminStats | null>(null);
    const error = ref<string | null>(null);
    const users = ref<UserRead[]>([]);
    const roles = ref<RoleRead[]>([]);

    const resources = ref<string[]>(['source', 'article', 'alert', 'job', 'keyword', 'dashboard']);
    const actions = ref<string[]>(['create', 'read', 'update', 'delete', 'run']);
    const scopes = ref<string[]>(['*', 'own', 'any']);


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

    // user management

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

    //  roles management

    async function getRoleById(role_id: string): Promise<RoleRead | null> {
        return await processRemoteCall(async () => {
            const response = await api.get(`/admin/roles/${role_id}`);
            return response.data;
        });
    }

    async function createRole(name: string, description: string, is_system: boolean = false): Promise<RoleRead | null> {
        return await processRemoteCall(async () => {
            const new_role :  RoleCreateUpdate = {
                name: name,
                description: description,
                is_system: is_system
            };
            const response = await api.post('/admin/roles', new_role);
            addRoleToList(response.data);
            return response.data;
        });
    }

    async function updateRole(role_id: string, name: string, description: string, is_system: boolean = false): Promise<RoleRead | null> {
        return await processRemoteCall(async () => {
            const updated_role :  RoleCreateUpdate = {
                name: name,
                description: description,
                is_system: is_system
            };
            const response = await api.put(`/admin/roles/${role_id}`, updated_role);
            updateRoleInTheList(response.data);
            return response.data;
        });
    }

    async function deleteRole(role_id: string): Promise<boolean | null> {
        return await processRemoteCall(async () => {
            await api.delete(`/admin/roles/${role_id}`);
            deleteRoleFromList(role_id);
            return true;
        });
    }   

    // permissions

    async function getPermissions(role_id: string): Promise<PermissionRead[] | null> {
        return await processRemoteCall(async () => {
            const response = await api.get(`/admin/roles/${role_id}/permissions`);
            return response.data;
        });
    }

    async function createPermission(role_id: string, description: string,
        resource: 'source' | 'article' | 'alert' | 'job' | 'keyword' | 'dashboard',
        action: 'create' | 'read' | 'update' | 'delete' | 'run',
        scope: 'own' | 'any' | '*'): Promise<PermissionRead | null> {
        return await processRemoteCall(async () => {
            const new_permission: PermissionCreateUpdate = {
                description: description,
                resource: resource,
                action: action,
                scope: scope,
            };
            const response = await api.post(`/admin/roles/${role_id}/permissions`, new_permission);
            return response.data;
        });
    }

    async function deletePermission(role_id: string, permission_id: string): Promise<boolean> {
        const response =  await processRemoteCall(async () => {
            await api.delete(`/admin/roles/${role_id}/permissions/${permission_id}`);
            return true;
        });
        return response === null ? false : response;
    }   

    // utils 

    // assign roles to user

    async function assignRolesToUser(user_id: string, roles_ids: string[]): Promise<boolean> {

        const request: UserRoles = {
            roles_ids: roles_ids
        };

        return await processRemoteCall(async () => {
            const response = await api.post(`/admin/users/${user_id}/roles`, request);
            return response.status === 200;
        }) || false;
    }

    async function getUserRoles(user_id: string): Promise<RoleRead[] | null> {
        return await processRemoteCall(async () => {
            const response = await api.get(`/admin/users/${user_id}/roles`);
            return response.data;
        });
    }
    
    async function removeRoleFromUser(user_id: string, role_id: string): Promise<boolean> {
        return await processRemoteCall(async () => {
            const response = await api.delete(`/admin/users/${user_id}/roles/${role_id}`);
            return response.status === 200;
        }) || false;
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

    function addRoleToList(role: RoleRead | null) {
        if (!role) return;
        roles.value = [...roles.value, role];
    }

    function updateRoleInTheList(updatedRole: RoleRead) {
        roles.value = roles.value.map(r => r.id === updatedRole.id ? updatedRole : r);        
    }

    function deleteRoleFromList(role_id: string) {
        roles.value = roles.value.filter(r => r.id !== role_id)
    }

    async function processRemoteCall<T>(apiCall: () => Promise<T>): Promise<T | null> {
        clearError();
        loading.value = true;
        try {
            const response = await apiCall();
            return response;
        } catch (e) {
            handleError(e);
        } finally {
            loading.value = false;
        }
        return null;
    }

    return {
        loading,
        state,
        users,
        roles,
        error,
        resources,
        actions,
        scopes,
        getStats,
        getUsers,
        getRoles,
        getUser,
        createUser,
        updateUser,
        deleteUser,
        activate,
        deactivate,
        getRoleById,
        createRole,
        updateRole,
        deleteRole,
        getPermissions,
        createPermission,
        deletePermission,
        assignRolesToUser,
        getUserRoles,
        removeRoleFromUser
    };
});
